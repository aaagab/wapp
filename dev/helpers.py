#!/usr/bin/env python3
from pprint import pprint
import os
import sys
import platform

def get_direpa_publish(
    direpa_sources,
):
    return os.path.join(os.path.dirname(direpa_sources), "_publish")

class Env():
    def __init__(self):
        self.platform=platform.system()
        self.is_windows=self.platform == "Windows"
        self.is_linux=self.platform == "Linux"