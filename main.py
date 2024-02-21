#!/usr/bin/env python3

if __name__ == "__main__":
    from pprint import pprint
    import importlib
    import json
    import os
    import sys
    import time

    direpa_script=os.path.dirname(os.path.realpath(__file__))
    direpa_script_parent=os.path.dirname(direpa_script)
    module_name=os.path.basename(direpa_script)
    sys.path.insert(0, direpa_script_parent)
    pkg = importlib.import_module(module_name)
    del sys.path[0]

    def seed(pkg_major, direpas_configuration=dict(), fun_auto_migrate=None):
        fun_auto_migrate()
    
    def get_path(path_elem: str, is_dir: bool):
        if path_elem is None:
            return None
        else:
            if not os.path.isabs(path_elem):
                path_elem=os.path.abspath(path_elem)
            if not os.path.exists(path_elem):
                pkg.msg.error("Provided path '{}' not found.".format(path_elem))
                raise Exception()


            if is_dir is True:
                if not os.path.isdir(path_elem):
                    pkg.msg.error("Provided path '{}' is not a directory.".format(path_elem))
                    raise Exception()
            else:
                if not os.path.isfile(path_elem):
                    pkg.msg.error("Provided path '{}' is not a file.".format(path_elem))
                    raise Exception()
            return os.path.normpath(path_elem)

    def substitute(
        direpa_project,
        profile_name,
        user_settings,
        arg,
        pkg,
    ):
        dy_vars=dict()
        filenpas_dst=[]
        if "substitute" in user_settings:
            if profile_name in user_settings["substitute"]:
                if "vars" in user_settings["substitute"][profile_name]:
                    for filenpa_var in user_settings["substitute"][profile_name]["vars"]:
                        if os.path.isabs(filenpa_var) is False:
                            filenpa_var=os.path.join(direpa_project, filenpa_var)
                        filenpa_var=os.path.normpath(filenpa_var)
                        if os.path.exists(filenpa_var):
                            with open(filenpa_var, "r") as f:
                                dy_vars.update(json.load(f))
                        else:
                            pkg.msg.warning("vars file not found '{}'".format(filenpa_var))

                if "dst" in user_settings["substitute"][profile_name]:
                    for filenpa_dst in user_settings["substitute"][profile_name]["dst"]:
                        if os.path.isabs(filenpa_dst) is False:
                            filenpa_dst=os.path.join(direpa_project, filenpa_dst)
                        filenpa_dst=os.path.normpath(filenpa_dst)
                        if os.path.exists(filenpa_dst):
                            filenpas_dst.append(filenpa_dst)
                        else:
                            pkg.msg.warning("destination file not found '{}'".format(filenpa_dst))

        count=1
        for dy in arg.vars._values:
            if count == 1:
                dy_vars=dict()
            dy_vars.update(dy)

        count=1
        for filenpa_dst in arg.dst._values:
            if count == 1:
                filenpas_dst=[]
            filenpas_dst.append(filenpa_dst)

        if len(dy_vars) == 0:
            pkg.msg.error("In --substitute command no vars have been provided.", exit=1)

        if len(filenpas_dst) == 0:
            pkg.msg.error("In --substitute command no destination files have been provided", exit=1)

        pkg.substitute(
            dy_vars=dy_vars,
            filenpas_dst=filenpas_dst,
        )

        pkg.msg.info("execution-time: {}s".format(int(time.time()-start)))
    
    etconf=pkg.Etconf(enable_dev_conf=False, tree=dict( files=dict({ "settings.json": dict() })), seed=seed)
    args=pkg.Nargs(
        options_file="config/options.yaml", 
        path_etc=etconf.direpa_configuration,
    ).get_args()

    if args.not_git._here is False:
        git=pkg.GitLib(direpa=os.getcwd())
        if git.is_direpa_git():
            os.chdir(git.get_direpa_root())

    direpa_project=os.getcwd()
    filenpa_modif=os.path.join(direpa_project, ".wappmodif.json")

    filenpa_global_settings=os.path.join(etconf.direpa_configuration, "settings.json")
    global_settings=dict(
        filenpa_msbuild=None,
        filenpa_msdeploy=None,
        filenpanpm=None,
        profiles=None,
    )
    with open(filenpa_global_settings, "r") as f:
        global_settings.update(json.load(f))

    for name in ["msbuild", "msdeploy"]:
        if args.backend.settings._[name]._value is None:
            if "filenpa_{}".format(name) not in global_settings:
                pkg.msg.error("filenpa_{name} must be provided with --{name} or global settings.json".format(name=name), exit=1)
        else:
            global_settings["filenpa_{}".format(name)]=args.backend.settings._[name]._value

    name="npm"
    if args.frontend.settings._[name]._value is None:
        if "filenpa_{}".format(name) not in global_settings:
            pkg.msg.error("filenpa_{name} must be provided with --{name} or global settings.json".format(name=name), exit=1)
    else:
        global_settings["filenpa_{}".format(name)]=args.frontend.settings._[name]._value

    filenpa_user_settings=os.path.join(direpa_project, ".wapp.json")
    user_settings=dict(
        direpa_deploy=None,
        direpa_backend_sources=None,
        direpa_frontend_sources=None,
        basepath=None,
        filenpa_csproj=None,
        project_name=None,
        msdeploy_parameters=None,
        webroot=None,
    )
    if os.path.exists(filenpa_user_settings):
        with open(filenpa_user_settings, "r") as f:
            user_settings.update(json.load(f))
    else:
        pkg.msg.error("File not found '{}'".format(filenpa_user_settings), exit=1)

    if args.backend.settings.csproj._value is None:
        user_settings["filenpa_csproj"]=get_path(user_settings["filenpa_csproj"], is_dir=False)
    else:
        user_settings["filenpa_csproj"]=args.backend.settings.csproj._value

    if args.backend.settings.sources._value is None:
        user_settings["direpa_backend_sources"]=get_path(user_settings["direpa_backend_sources"], is_dir=True)
    else:
        user_settings["direpa_backend_sources"]=args.backend.settings.sources._value

    if args.frontend.settings.sources._value is None:
        user_settings["direpa_frontend_sources"]=get_path(user_settings["direpa_frontend_sources"], is_dir=True)
    else:
        user_settings["direpa_frontend_sources"]=args.frontend.settings.sources._value

    if args.project._value is not None:
        user_settings["project_name"]=args.project._value

    if args.deploy_path._value is not None:
        user_settings["direpa_deploy"]=os.path.normpath(args.deploy_path._value)
    else:
        if user_settings["direpa_deploy"] is not None:
            user_settings["direpa_deploy"]=os.path.normpath(user_settings["direpa_deploy"])

    exclude_build_folders=[]
    if "exclude_build_folders" in global_settings:
        exclude_build_folders=global_settings["exclude_build_folders"]

    start=time.time()

    profile_name=args.profile._value

    if "env" in user_settings:
        if profile_name in user_settings["env"]:
            for key in sorted(user_settings["env"][profile_name]):
                os.environ[key]=user_settings["env"][profile_name][key]

    if args.backend.build._here is True or \
        args.backend.start._here is True or \
        args.backend.publish._here is True or \
        args.backend.deploy._here is True or \
        args.substitute._here is True:


        if profile_name is None:
            pkg.msg.error("--profile must be provided")
            raise Exception()

        profile_name=profile_name.lower()


        if args.basepath._value is not None:
            user_settings["basepath"]=args.basepath._value

        if user_settings["basepath"] is not None:
            if user_settings["basepath"][0] != "/":
                pkg.msg.error("basepath must start with '/' '{}'".format(user_settings["basepath"]))
                raise Exception()

            if args.profile.default._here is True:
                if "default_url" in global_settings:
                    with open(os.path.join(direpa_project, "hostname_url.txt"), "w") as f:
                        f.write(global_settings["default_url"])
            else:
                if "profiles" in global_settings:
                    if profile_name in global_settings["profiles"]:
                        if "public_url" in global_settings["profiles"][profile_name]:
                            domain=global_settings["profiles"][profile_name]["public_url"]
                            with open(os.path.join(direpa_project, "hostname_url.txt"), "w") as f:
                                f.write(domain+user_settings["basepath"])

        direpa_profiles=os.path.join(
            os.getcwd(), 
            user_settings["direpa_backend_sources"],
            "Properties",
            "PublishProfiles",
        )

        if os.path.exists(direpa_profiles):
            profiles=[elem[:-7].lower() for elem in sorted(os.listdir(direpa_profiles)) if elem[-6:] == "pubxml"]
            if profile_name not in profiles:
                pkg.msg.error("Profile '{}' not found in {}".format(profile_name, profiles))
                raise Exception()
        else:
            pkg.msg.error("Profiles directory not found '{}'".format(direpa_profiles))
            raise Exception()

    if args.backend._here:

        if args.backend.build._here is True:
            pkg.backend_build(
                filenpa_csproj=user_settings["filenpa_csproj"],
                filenpa_msbuild=global_settings["filenpa_msbuild"],
                profile_name=profile_name,
            )
        elif args.backend.start._here is True:
            pkg.backend_start(
                direpa_sources=user_settings["direpa_backend_sources"],
                profile_name=profile_name,
            )
        elif args.backend.publish._here is True:
            pkg.backend_publish(
                filenpa_csproj=user_settings["filenpa_csproj"],
                filenpa_msbuild=global_settings["filenpa_msbuild"],
                profile_name=profile_name,
                exclude_build_folders=exclude_build_folders,
                filenpa_modif=filenpa_modif,
                force=args.backend.publish.force._here,
            )
        elif args.backend.deploy._here is True:
            if user_settings["direpa_deploy"] is None:
                pkg.msg.error("direpa_deploy must be provided")            

            pkg.backend_publish(
                filenpa_csproj=user_settings["filenpa_csproj"],
                filenpa_msbuild=global_settings["filenpa_msbuild"],
                profile_name=profile_name,
                exclude_build_folders=exclude_build_folders,
                filenpa_modif=filenpa_modif,
                force=args.backend.deploy.force._here,
            )

            if args.backend.deploy.substitute._here is True:
                substitute(
                    direpa_project,
                    profile_name,
                    user_settings,
                    args.backend.deploy.substitute,
                    pkg,
                )

            pkg.backend_deploy(
                filenpa_msdeploy=global_settings["filenpa_msdeploy"],
                filenpa_csproj=user_settings["filenpa_csproj"],
                direpa_deploy=user_settings["direpa_deploy"],
                force=args.backend.deploy.force._here,
                filenpa_modif=filenpa_modif,
                profile_name=profile_name,
                msdeploy_parameters=user_settings["msdeploy_parameters"],
                project_name=user_settings["project_name"],
            )
        elif args.backend.dotnet._here is True:
            pkg.backend_dotnet(
                direpa_sources=user_settings["direpa_backend_sources"],
                filenpa_dotnet=global_settings["filenpa_dotnet"],
                dotnet_args=args.backend.dotnet._values,
            )
        else:
            pkg.msg.error("For --backend: either --build, --start, --publish, or --deploy must be provided", exit=1)

        pkg.msg.info("execution-time: {}s".format(int(time.time()-start)))

    if args.frontend._here:
        direpa_publish=None

        if args.frontend.settings.webroot._value is None:
            if user_settings["webroot"] is None:
                pkg.msg.error("webroot must be set")
                raise Exception()
        else:
            user_settings["webroot"]=args.frontend.settings.webroot._value

        if args.frontend.build._here or args.frontend.deploy._here or args.frontend.publish._here:
            if args.frontend.build._here is True:
                pass
            elif args.frontend.deploy._here is True:
                if user_settings["direpa_deploy"] is None:
                    pkg.msg.error("direpa_deploy must be provided")

                direpa_publish=os.path.join(
                    user_settings["direpa_deploy"],
                    user_settings["webroot"],
                )
            elif args.frontend.publish._here is True:
                direpa_publish=os.path.join(
                    pkg.get_direpa_publish(user_settings["direpa_frontend_sources"]),
                    user_settings["webroot"],
                )

            pkg.frontend_build(
                direpa_sources=user_settings["direpa_frontend_sources"],
                direpa_publish=direpa_publish,
                basepath=user_settings["basepath"],
                filenpa_npm=global_settings["filenpa_npm"],
                minify=args.frontend.settings.minify._value,
            )
        elif args.frontend.npm._here is True:
            pkg.frontend_npm(
                direpa_sources=user_settings["direpa_frontend_sources"],
                filenpa_npm=global_settings["filenpa_npm"],
                npm_args=args.frontend.npm._values,
            )
        elif args.frontend.start._here is True:
            pkg.frontend_start(
                filenpa_npm=global_settings["filenpa_npm"],
                direpa_sources=user_settings["direpa_frontend_sources"],
                project_name=user_settings["project_name"],
                port=args.frontend.start.port._value,
                ignore_if=args.frontend.start.ignore_if._here,
            )
        else:
            pkg.msg.error("For --frontend: either --build, --start, --publish, or --deploy must be provided", exit=1)

        pkg.msg.info("execution-time: {}s".format(int(time.time()-start)))

    if args.substitute._here is True:
        substitute(
            direpa_project,
            profile_name,
            user_settings,
            args.substitute,
            pkg,
        )


    if args.msal._here is True:
        pkg.msal_signin(
            direpa_project,
            filenpa_cache=os.path.join(etconf.direpa_configuration, "cache.bin"),
            filenpa_conf=args.msal.conf._value,
            filenpa_token=args.msal.token._value,
            interactive=args.msal.interactive._here,
            refresh=args.msal.refresh._here,
            show=args.msal.show._here,
        )
