#!/usr/bin/env python3
from pprint import pprint
import json
import os
import signal
import sys
import subprocess

os.environ["BROWSER"]="None"
os.environ["HOST"]="127.0.0.1"
os.environ["PORT"]="{port}"
launch_pid="{launch_pid}"

project_name="{project_name}"
filenpa_wapp=r"{filenpa_wapp}"
direpa_sources=r"{direpa_sources}"
ppid=os.getppid()
dy_wapp=dict({{
    project_name: dict(
        pids=[],
    )
}})

pids=[]
pids.append(ppid)

if os.path.exists(filenpa_wapp):
    try:
        with open(filenpa_wapp, "r") as f:
            dy_wapp=json.load(f)
            if project_name not in dy_wapp:
                dy_wapp[project_name]=dict(
                    pids=[ppid],
                )
    except json.decoder.JSONDecodeError:
        dy_wapp[project_name]=dict(
            pids=[ppid],
        )
    
if ppid not in dy_wapp[project_name]["pids"]:
    dy_wapp[project_name]["pids"].insert(0, ppid)

with open(filenpa_wapp, "w") as f:
    f.write(json.dumps(dy_wapp, indent=4, sort_keys=True))

try:
    os.chdir(direpa_sources)
    proc=subprocess.Popen([
        r"C:\Program Files\nodejs\npm.cmd",
        "start",
    ])
    pids.append(proc.pid)
    dy_wapp[project_name]["pids"].insert(0, proc.pid)
    with open(filenpa_wapp, "w") as f:
        f.write(json.dumps(dy_wapp, indent=4, sort_keys=True))
    proc.communicate()
    if proc.returncode != 0:
        sys.exit(1)
except BaseException as e:
    os.kill(int(launch_pid), signal.SIGTERM)
    os.system("pause")
    raise
finally:
    os.remove(os.path.realpath(__file__))
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
