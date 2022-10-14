from os import getenv
from core import serve_core

if __name__ == "__main__":
    serve_core(getenv("SERIAL_PORT_GLOB"))
