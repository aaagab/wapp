#!/usr/bin/env python3
from pprint import pprint
import json
import os
import sys
import time

def has_directory_been_modified( 
    directory,
    exclude_build_folders,
    modif_time,
    _direpa_current=None,
    _level=1,
    _state=None,
):
    if _direpa_current is None:
        _direpa_current=directory
        _state=dict(found=False)

    for elem_name in sorted(os.listdir(_direpa_current)):
        if _state["found"] is True:
            return True

        path_elem=os.path.join(_direpa_current, elem_name)

        if os.path.isdir(path_elem):
            recurse=True
            if _level == 1 and elem_name in exclude_build_folders:
                recurse=False

            if recurse is True:
                elem_modif_time=os.path.getmtime(path_elem)
                if elem_modif_time > modif_time:
                    _state["found"]=True
                    return True
                has_directory_been_modified(
                    directory=directory,
                    exclude_build_folders=exclude_build_folders,
                    modif_time=modif_time,
                    _direpa_current=path_elem,
                    _level=_level+1,
                    _state=_state,
                )
        else:
            elem_modif_time=os.path.getmtime(path_elem)
            if elem_modif_time > modif_time:
                _state["found"]=True
                return True


    return False

def get_modif_time(
    filenpa_modif,
    location,
    profile_name,
    action,
    direpa_dst,
):
    if os.path.exists(filenpa_modif):
        with open(filenpa_modif, "r") as f:
            try:
                dy_modif=json.load(f)
                if location in dy_modif:
                    if profile_name in dy_modif[location]:
                        if action in dy_modif[location][profile_name]:
                            if direpa_dst in dy_modif[location][profile_name][action]:
                                return dy_modif[location][profile_name][action][direpa_dst]
            except json.decoder.JSONDecodeError as e:
                if f.read().strip() == "":
                    with open(filenpa_modif, "w") as f:
                        f.write(json.dumps(dict()))
                    return None
                else:
                    raise

    return None

def save_modif(
    filenpa_modif,
    location,
    profile_name,
    action,
    direpa_dst,
):
    dy_modif=dict()
    if os.path.exists(filenpa_modif):
        with open(filenpa_modif, "r") as f:
            try:
                dy_modif=json.load(f)
            except json.decoder.JSONDecodeError as e:
                if f.read().strip() != "":
                    raise

    if location not in dy_modif:
        dy_modif[location]=dict()

    if profile_name not in dy_modif[location]:
        dy_modif[location][profile_name]=dict()

    if action not in dy_modif[location][profile_name]:
        dy_modif[location][profile_name][action]=dict()

    dy_modif[location][profile_name][action][direpa_dst]=time.time()

    with open(filenpa_modif, "w") as f:
        f.write(json.dumps(dy_modif, indent=4, sort_keys=True))

def does_project_need_build(
    filenpa_modif: str,
    location: str,
    profile_name: str,
    action: str,
    direpa_src: str,
    direpa_dst: str,
    force: bool,
    exclude_build_folders: list,
):
    if force is True:
        return True
    else:
        modif_time=get_modif_time(
            filenpa_modif,
            location,
            profile_name,
            action,
            direpa_dst,
        )

        if modif_time is None:
            return True
        else:
            return has_directory_been_modified(
                direpa_src, 
                exclude_build_folders,
                modif_time,
            )
