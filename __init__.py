#!/usr/bin/env python3
# authors: Gabriel Auger
# name: Web App Builder
# licenses: MIT 
__version__= "2.8.0"

from .dev.backend import backend_build, backend_start, backend_publish, backend_deploy, backend_dotnet
from .dev.frontend import frontend_build, frontend_start, frontend_npm
from .dev.substitute import substitute
from .dev.helpers import get_direpa_deploy, get_direpa_publish
from .gpkgs import message as msg
from .gpkgs.nargs import Nargs
from .gpkgs.etconf import Etconf
from .gpkgs.gitlib import GitLib
