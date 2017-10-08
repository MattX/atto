import yaml
from collections import namedtuple

Parameter = namedtuple('Parameter', ['name', 'optional', 'default'])


class Config:
    def __init__(self, parameters, path):
        try:
            with open(path, "r") as config_file:
                config_opts = yaml.load(config_file)
        except FileNotFoundError:
            raise RuntimeError("Could not find configuration file {}".format(path))

        self.cfg = {}

        for parameter in parameters:
            if parameter.name in config_opts:
                self.cfg[parameter.name] = config_opts[parameter.name]
                del config_opts[parameter.name]
            elif parameter.optional:
                self.cfg[parameter.name] = parameter.default
            else:
                raise RuntimeError("Required parameter {} not found".format(parameter.name))

        if config_opts:
            raise RuntimeError("Unknown parameters: {}".format(",".join(config_opts.keys())))

    def __getattr__(self, item):
        return self.cfg[item]
