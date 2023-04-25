#!/usr/bin/env python3
from pprint import pprint
import json
import os
import signal
import subprocess
import sys
import tempfile
import time

from ..gpkgs import message as msg
from ..gpkgs import shell_helpers as shell

from .windows import Windows
from .helpers import get_direpa_deploy, get_direpa_publish


def backend_build(
    filenpa_csproj: str,
    filenpa_msbuild: str,
    profile_name: str,
):
    if filenpa_csproj is None:
        msg.error("filenpa_csproj must be provided.")
        raise Exception()
    
    if filenpa_msbuild is None:
        msg.error("filenpa_msbuild must be provided.")
        raise Exception()

    if profile_name is None:
        msg.error("profile_name must be provided.")
        raise Exception()

    cmd=[
        filenpa_msbuild,
        filenpa_csproj,
        "/v:Normal",
        "/nologo",
        "/m",
        "/p:EnvironmentName={}".format(profile_name),
        # "/p:Configuration={}".format(profile_name.capitalize()),
    ]
    pprint(cmd)
    process=subprocess.Popen(cmd)
    process.communicate()
    if process.returncode == 0:
        msg.success("Backend built.")
    else:
        sys.exit(1)

def backend_start(
    direpa_sources: str,
    profile_name: str,
):
    if direpa_sources is None:
        msg.error("direpa_sources must be provided.")
        raise Exception()

    if profile_name is None:
        msg.error("profile_name must be provided.")
        raise Exception()

    cmd=[
        "dotnet",
        "run",
        # "--configuration",
        "--environment",
        profile_name,
        "--project",
        direpa_sources,
    ]
    pprint(cmd)
    process=subprocess.Popen(cmd)
    process.communicate()
    if process.returncode != 0:
        sys.exit(1)

def backend_publish(
    filenpa_csproj: str,
    filenpa_msbuild: str,
    profile_name: str,

):
    if filenpa_csproj is None:
        msg.error("filenpa_csproj must be provided.")
        raise Exception()
    
    if filenpa_msbuild is None:
        msg.error("filenpa_msbuild must be provided.")
        raise Exception()

    if profile_name is None:
        msg.error("profile_name must be provided.")
        raise Exception()

    direpa_publish=get_direpa_publish(os.path.dirname(filenpa_csproj))
    os.makedirs(direpa_publish, exist_ok=True)

    cmd=[
        filenpa_msbuild,
        filenpa_csproj,
        '/v:Normal',
        '/nologo',
        '/m',
        # "/p:Configuration={}".format(profile_name),
        # "/p:EnvironmentName={}".format(profile_name),
        "/p:DeployTarget=Package",
        "/p:PublishProvider=FileSystem",
        "/p:PublishProfile={}".format(profile_name),
        '/p:DeployOnBuild=True',
        '/p:DeleteExistingFiles=True',
        '/p:ExcludeApp_Data=False',
        '/p:WebPublishMethod=FileSystem',
        '/p:publishUrl={}'.format(direpa_publish),
    ]

    pprint(cmd)
    process=subprocess.Popen(cmd)
    process.communicate()
    if process.returncode == 0:
        msg.success("backend published at '{}'".format(direpa_publish))
    else:
        sys.exit(1)

def backend_deploy(
    filenpa_msdeploy: str,
    filenpa_csproj: str,
    direpa_deploy: str,
    project_name: str,
    basepath:str=None,
    msdeploy_parameters:list=None,

):
    if filenpa_msdeploy is None:
        msg.error("filenpa_msdeploy must be provided.")
        raise Exception()

    if filenpa_csproj is None:
        msg.error("filenpa_csproj must be provided.")
        raise Exception()

    if project_name is None:
        msg.error("project_name must be provided.")
        raise Exception()

    if direpa_deploy is None:
        if basepath is None:
            msg.error("Either direpa_deploy or basepath must be provided.")
            raise Exception()
        else:
            direpa_deploy=get_direpa_deploy(basepath)

    direpa_publish=get_direpa_publish(os.path.dirname(filenpa_csproj))

    if direpa_deploy == direpa_publish:
        msg.error("direpa_deploy can't be the same as publish path")
        raise Exception()

    shell.cmd_devnull([
        "pm2",
        "start",
        project_name
    ])

    cmd=[
        filenpa_msdeploy,
        "-verb:sync",
        r"-source:dirPath={}".format(direpa_publish),
        r"-dest:dirPath={}".format(direpa_deploy),
    ]

    if msdeploy_parameters is not None:
        cmd.extend(msdeploy_parameters)

    pprint(cmd)

    process=subprocess.Popen(cmd)
    process.communicate()
    if process.returncode == 0:
        shell.cmd_devnull([
            "pm2",
            "start",
            project_name
        ])
        msg.success("backend deployed at '{}'".format(direpa_deploy))
    else:
        sys.exit(1)
