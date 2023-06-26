#!/usr/bin/env python3
from pprint import pprint
import json
import os
import signal
import subprocess
import shlex
import sys
import tempfile
import time

from ..gpkgs import message as msg
from ..gpkgs import shell_helpers as shell

def substitute(
    dy_vars: dict,
    filenpas_dst: list,
):
    for filenpa_dst in filenpas_dst:
        org_text=None
        text=None
        with open(filenpa_dst, "r") as f:
            text=f.read()
            org_text=f.read()
            for key, value in dy_vars.items():
                text=text.replace("{{{{{}}}}}".format(key), value)

        if org_text != text:
            with open(filenpa_dst, "w") as f:
                f.write(text)
            msg.success("vars substituted in file '{}'".format(os.path.basename(filenpa_dst)))