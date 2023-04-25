#!/usr/bin/env python3
from pprint import pprint
import os
import sys

def get_direpa_deploy(basepath: str)-> str:
    if basepath[0] == "/":
        basepath=basepath[1:]
    return os.path.normpath(os.path.join(
        os.path.expanduser("~"),
        "fty",
        "local",
        basepath,
    ))

def get_direpa_publish(
    direpa_sources,
):
    return os.path.join(os.path.dirname(direpa_sources), "_publish")