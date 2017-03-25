import yaml


REQUIRED_OPTIONS = ["content_root", "site_name", "server_name"]
LEGAL_OPTIONS = ["markdown_extras", "main_page", "cache_marker", "generate_feeds"]
LEGAL_DEFAULTS = [[], None, None, False]


def read_config(path):
    try:
        with open(path, "r") as config_file:
            cfg = yaml.load(config_file)
    except FileNotFoundError:
        raise RuntimeError("Could not find configuration file {}".format(path))

    if REQUIRED_OPTIONS and not cfg:
        raise RuntimeError("Empty configuration file")

    for key in cfg:
        if key not in LEGAL_OPTIONS + REQUIRED_OPTIONS:
            raise RuntimeError("Configuration error: unknown option {}".format(key))

    for opt in REQUIRED_OPTIONS:
        if opt not in cfg:
            raise RuntimeError("Required option {} not found".format(opt))

    for opt, default in zip(LEGAL_OPTIONS, LEGAL_DEFAULTS):
        if opt not in cfg:
            cfg[opt] = default

    return cfg
