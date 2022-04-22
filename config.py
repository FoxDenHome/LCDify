from yaml import safe_load

CONFIG = None

def load():
    global CONFIG
    with open('config.yml', 'r') as f:
        CONFIG = safe_load(f)

load()
