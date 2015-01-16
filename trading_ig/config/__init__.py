#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os

class ConfigEnvVar(object):
    def __init__(self, env_var_base):
        self.ENV_VAR_BASE = env_var_base

    def _env_var(self, key):
        return(self.ENV_VAR_BASE + "_" + key.upper())

    def get(self, key, default_value=None):
        return(os.environ.get(self._env_var(key), default_value))

    def __getattr__(self, key):
        return(os.environ[self._env_var(key)])
