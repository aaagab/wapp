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

from .windows import Windows

def frontend_npm(
    direpa_sources: str,
    filenpa_npm: str,
    npm_args: list=None,
):
    if direpa_sources is None:
        msg.error("direpa_sources must be provided")
        raise Exception()

    if filenpa_npm is None:
        msg.error("filenpa_npm must be provided")
        raise Exception()

    if npm_args is None:
        msg.error("npm_args must be provided")
        raise Exception()

    os.chdir(direpa_sources)

    cmd=[
        filenpa_npm,
        *npm_args,
    ]

    proc=subprocess.Popen(cmd)
    proc.communicate()
    if proc.returncode == 0:
        msg.success(shlex.quote(" ".join(cmd)))
    else:
        sys.exit(1)

def frontend_build(
    direpa_sources: str,
    direpa_publish: str,
    basepath: str,
    filenpa_npm: str,
    minify: bool=None,
):
    if direpa_sources is None:
        msg.error("direpa_sources must be provided")
        raise Exception()

    if filenpa_npm is None:
        msg.error("filenpa_npm must be provided")
        raise Exception()

    os.chdir(direpa_sources)
    if basepath is None:
        if "PUBLIC_URL" in os.environ:
            del os.environ["PUBLIC_URL"]
    else:
        os.environ["PUBLIC_URL"]=basepath
        print("set PUBLIC_URL={}".format(basepath))

    if minify is None:
        if "MINIFY" in os.environ:
            del os.environ["MINIFY"]
    else:
        os.environ["MINIFY"]=str(minify).lower()
        print("set MINIFY={}".format(basepath))

    if direpa_publish is None:
        if "BUILD_PATH" in os.environ:
            del os.environ["BUILD_PATH"]
    else:
        os.environ["BUILD_PATH"]=direpa_publish
        print("set BUILD_PATH={}".format(direpa_publish))

    cmd=[
        filenpa_npm,
        "run",
        "build",
    ]

    print(cmd)
    proc=subprocess.Popen(cmd)
    proc.communicate()
    if proc.returncode == 0:
        if direpa_publish is None:
            msg.success("frontend build")
        else:
            msg.success("frontend published to '{}'.".format(direpa_publish))
    else:
        sys.exit(1)

def execute_script(
    script_name, 
    window_name,
    dy_vars=None
):
    filenpa_info=os.path.join(os.path.dirname(os.path.realpath(__file__)), script_name)

    with open(filenpa_info, "r") as f:
        data_str=f.read()
        if dy_vars is not None:
            tmp_dy_vars=dict()
            for key, value in dy_vars.items():
                tmp_dy_vars[key]=value
            data_str=data_str.format(**tmp_dy_vars)
   
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write("{}\n".format(data_str).encode())
            proc=subprocess.Popen([
                "start",
                "cmd",
                "/k",
                "title {} & python {}".format( window_name, tmp.name)
            ], shell=True)
            proc.communicate()
            if proc.returncode == 0:
                pass
            else:
                sys.exit(1)

def get_port_pid(port):
    result=shell.cmd_get_value("netstat -ano | findstr :{}".format(port))
    if result is None:
        return None
    else:
        result=int(result.split()[-1])
        if result == 0:
            return None
        else:
            return result

def frontend_start(
    filenpa_npm: str,
    direpa_sources: str,
    project_name: str,
    port: int,
    ignore_if: bool,
):
    if filenpa_npm is None:
        msg.error("filenpa_npm must be provided.")
        raise Exception()

    if direpa_sources is None:
        msg.error("direpa_sources must be provided.")
        raise Exception()

    if project_name is None:
        msg.error("project_name must be provided.")
        raise Exception()

    if port is None:
        port=3000
    obj_windows=Windows()
    cmd_pid=obj_windows.get_active()

    window_name="client_{}".format(project_name)
    filenpa_wapp=os.path.join(os.path.expanduser("~"), "fty", "tmp", "wapp-{}.json".format(port))

    port_pid=get_port_pid(port)
    process_cmd=False
    if port_pid is None:
        process_cmd=True
    else:
        if ignore_if is True:
            process_cmd=False
            msg.info("frontend is already started.")
        else:
            process_cmd=True
            os.kill(port_pid, signal.SIGTERM)

    if process_cmd is True:
        dy_wapp=dict({
            project_name: dict(
                pids=[],
            )
        })
        try:
            if os.path.exists(filenpa_wapp):
                with open(filenpa_wapp, "r") as f:
                    dy_wapp=json.load(f)
                    if project_name in dy_wapp:
                        if "pids" in dy_wapp[project_name]:
                            for pid in dy_wapp[project_name]["pids"]:
                                try:
                                    os.kill(pid, signal.SIGTERM)
                                except OSError:
                                    pass
        except json.decoder.JSONDecodeError:
            pass

        dy_wapp[project_name]["pids"]=[]

        with open(filenpa_wapp, "w") as f:
            f.write(json.dumps(dy_wapp, indent=4, sort_keys=True))

        execute_script(
            "frontend_server.py", 
            window_name=window_name, 
            dy_vars=dict(
            filenpa_wapp=filenpa_wapp,
            project_name=project_name,
            direpa_sources=direpa_sources,
            port=port,
            launch_pid=os.getpid(),
        ))

        try:
            while True:
                port_pid=get_port_pid(port)
                if port_pid is not None:
                    with open(filenpa_wapp, "r") as f:
                        dy_wapp=json.load(f)
                        if len(dy_wapp[project_name]["pids"]) >= 2:
                            obj_windows.rename(dy_wapp[project_name]["pids"][1], window_name)

                    msg.success("frontend development server started on port '{}'".format(port))
                    break
                time.sleep(.3)
        except KeyboardInterrupt:
            sys.exit(1)

        obj_windows.focus(cmd_pid)
