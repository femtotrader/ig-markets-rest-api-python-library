- config file (YAML or .py which could be overwritten by environment variable)
- continuous integration using Travis-CI config file using environment variable (because of CI)
- merge ig-markets-rest-api-python-library and ig-markets-stream-api-python-library
- build a pip package, register, upload
- add badge (pypi, 

.. code:: python

    import os

    ENV_VAR_CONFIG = 'IG_SERVICE_'

    def get_config(key='', value=''):
        #if issinstance(key, basestring):
        #    key = list(key)

        if value=='' or value is None:
            try:
                env_var =  ENV_VAR_CONFIG + key.upper()
                return(os.environ[env_var])
            except:
                logging.warning("You should have %s and pass it using environment variable %r" % (key, env_var))
                return('')
        else:
            return(value)

    class IGServiceConfig(IGServiceConfigBase):
        username = ""
        password = ""
        api_key = ""
        acc_type = "DEMO" # LIVE / DEMO
        acc_number = ""

    config = IGServiceConfig(username, password, api_key, acc_type, acc_number)
