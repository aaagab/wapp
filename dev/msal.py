#!/usr/bin/env python3
from pprint import pprint
import atexit
import json
import msal
import os
import sys
import tempfile

from ..gpkgs.prompt import prompt_multiple, prompt

def msal_signin(
    direpa_project:str,
    filenpa_cache:str,
    filenpa_conf:str = None,
    filenpa_token:str = None,
    interactive: bool = False,
    refresh: bool = False,
    show:bool = False,
):
    cache = msal.SerializableTokenCache()

    if refresh is True:
        os.remove(filenpa_cache)

    if os.path.exists(filenpa_cache):
        with open(filenpa_cache, "r") as f:
            cache.deserialize(f.read())

    atexit.register(lambda:
        open(filenpa_cache, "w").write(cache.serialize())
        if cache.has_state_changed else None
    )

    if filenpa_conf is None:
        filenpa_conf=os.path.join(direpa_project, ".msal.json")
        if os.path.exists(filenpa_conf) == False:
            raise FileNotFoundError(f"File not found '{filenpa_conf}'")
        
    config=dict()
    with open(filenpa_conf, "r") as f:
        config=json.load(f)

    for prop in [
        "client-id",
        "tenant-id",
    ]:
        if config.get(prop) is None:
            raise Exception(f"property {prop} not set in {filenpa_conf}.")
        
    authority=f"https://login.microsoftonline.com/{config['tenant-id']}"

    if filenpa_token is None:
        filenpa_token=os.path.join(tempfile.gettempdir(), "_requests_cmd", "data")
        os.makedirs(os.path.join(tempfile.gettempdir(), "_requests_cmd"), exist_ok=True)

    msal_user=os.environ.get("msal_email")
    if  msal_user is None:
        msal_user=config.get("email")

    msal_pass=os.environ.get("msal_password")
    if  msal_pass is None:
        msal_pass=config.get("password")

    scopes=[]
    if isinstance(config.get("scopes"), list): 
        for elem in config["scopes"]:
            if elem[:6] == "api://":
                scopes.append(elem)
            else:
                scopes.append(f"api://{config['client-id']}/{elem}")

    app = msal.PublicClientApplication(
        config["client-id"], 
        authority=authority,
        token_cache=cache,
    )

    result = None

    accounts = app.get_accounts(username=msal_user)
    if accounts:
        chosen=None
        if len(accounts) == 1:
            chosen=accounts[0]
        elif len(accounts) > 1:
            usernames=[account["username"] for account in accounts]
            user_index=prompt_multiple(usernames, title="Choose an account to connect to: ", index_only=True, values=list(range(len(usernames))))
            chosen=accounts[user_index]

        if chosen is not None:
            if msal_user is not None:
                if msal_user != chosen["username"]:
                    raise Exception(f"Chosen email '{msal_user}' is different from selected account in cache '{chosen['username']}'.")
            result = app.acquire_token_silent(scopes=scopes, account=chosen)
            

    if not result:
        if interactive is True:
            result = app.acquire_token_interactive(  
                scopes,
                login_hint=msal_user,
            )
        else:
            if msal_user is None:
                msal_user=prompt("email")

            if msal_pass is None:
                msal_pass=prompt("password", hidden=True)
            result= app.acquire_token_by_username_password(username=msal_user, password=msal_pass, scopes=scopes)

    if "access_token" in result:
        if show is True:
            print(result['access_token'])
        with open(filenpa_token, "w") as f:
            f.write(result['access_token'])
    else:
        raise Exception(f"""
        {result.get("error")}
        {result.get("error_description")}
        {result.get("correlation_id")}
        """)