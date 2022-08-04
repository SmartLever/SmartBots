

def get_config(config_file_name: str) -> dict:
    """ Get the configuration from the config file. """
    import yaml
    with open(config_file_name, "r") as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
    return config