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
import shutil
import psutil

from ..gpkgs import message as msg
from ..gpkgs import shell_helpers as shell

from .windows import Windows
from .helpers import Env
env=Env()

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
    dy_vars:dict=None,
    terminal_execute_cmd:list=None,
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
            proc=None
            if env.is_windows:
                proc=subprocess.Popen([
                    "start",
                    "cmd",
                    "/k",
                    "title {} & python {}".format( window_name, tmp.name)
                ], shell=True)

                proc.communicate()
                if proc.returncode != 0:
                    sys.exit(1)
            elif env.is_linux:
                if terminal_execute_cmd is None:
                    msg.error("terminal_execute_cmd is required i.e. [\"/usr/bin/konsole\", \"-e\"]")
                    raise Exception()
                with tempfile.NamedTemporaryFile(delete=False) as tmp2:
                    tmp2.write("#!/bin/bash\n".encode())
                    tmp2.write("source ~/.bashrc\n".encode())
                    tmp2.write(f"rm {tmp2.name}\n".encode())
                    tmp2.write(f'echo -ne "\\033]30;{window_name}\\007"\n'.encode())
                    tmp2.write(f"python {tmp.name}\n".encode())
                    cmd=[
                        *terminal_execute_cmd,
                        f"/bin/bash --rcfile {tmp2.name}",
                    ]

                    cmd=[
                        "/usr/bin/konsole",
                        "-e",
                        f"/bin/bash",
                        "--rcfile",
                        tmp2.name,
                    ]
                    proc=subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def get_port_pid(port):
    result=None
    if env.is_windows:
        result=shell.cmd_get_value("netstat -ano | findstr :{}".format(port))
        if result is None:
            return None
        else:
            result=int(result.split()[-1])
            if result == 0:
                return None
            else:
                return result

    elif env.is_linux:
        result=shell.cmd_get_value(f"lsof -nP -iTCP:{port} -sTCP:LISTEN")
        if result is None:
            return None
        else:
            pid_index=None
            lines=result.splitlines()
            if len(lines) != 2:
                msg.error("lsof output should have only two lines.")
                print("\n".join(lines))

                raise Exception()
                
            for line in lines:
                columns=line.split()
                if pid_index is None:
                    pid_index=columns.index("PID")
                    if pid_index is None:
                        msg.error("PID has not been found in lsof command output headers.")
                        raise Exception()
                else:
                    return int(columns[pid_index])

def frontend_start(
    filenpa_npm: str,
    direpa_sources: str,
    project_name: str,
    port: int,
    ignore_if: bool,
    terminal_execute_cmd: str = None,
):
    if filenpa_npm is None:
        msg.error("filenpa_npm is required.")
        raise Exception()

    if direpa_sources is None:
        msg.error("direpa_sources is required.")
        raise Exception()

    if project_name is None:
        msg.error("project_name is required.")
        raise Exception()
    
    if env.is_linux:
        if terminal_execute_cmd is None:
            msg.error("terminal_execute_cmd is required i.e. [\"/usr/bin/konsole\", \"-e\"]")
            raise Exception()
        if shutil.which("wmctrl") is None:
            msg.error("wmctrl needs to be installed")
            raise Exception()
        if shutil.which("xdotool") is None:
            msg.error("xdotool needs to be installed")
            raise Exception()

    if port is None:
        port=3000

    win_id=None
    if env.is_windows:
        obj_windows=Windows()
        win_id=obj_windows.get_active()
    elif env.is_linux:
        win_id=hex(int(subprocess.check_output(["xdotool", "getactivewindow"]).decode().rstrip()))

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
            ),
            terminal_execute_cmd=terminal_execute_cmd,
        )

        try:
            while True:
                port_pid=get_port_pid(port)
                if port_pid is not None:
                    if env.is_windows:
                        with open(filenpa_wapp, "r") as f:
                            dy_wapp=json.load(f)
                            if len(dy_wapp[project_name]["pids"]) >= 2:
                                obj_windows.rename(dy_wapp[project_name]["pids"][1], window_name)
                    msg.success("frontend development server started on port '{}'".format(port))
                    break
                time.sleep(.3)
        except KeyboardInterrupt:
            sys.exit(1)

        if env.is_windows:
            obj_windows.focus(win_id)
        elif env.is_linux:
            os.system(f"wmctrl -i -a {win_id}")
            
