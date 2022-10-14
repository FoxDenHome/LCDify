from time import sleep
from core import serve_core
from os import getenv, getgid, getuid, setresgid, setresuid
from makedev import make_tty_devs

uid = int(getenv("PUID", "0"), 10)
gid = int(getenv("PGID", "0"), 10)

tty_dev_count = int(getenv("MAKE_TTY_DEVS", "0"), 0)
if tty_dev_count > 0:
    make_tty_devs(tty_dev_count)

if gid > 0:
    setresgid(gid, gid, gid)
if uid > 0:
    setresuid(uid, uid, uid)

print(f"Running as UID {getuid()}, GID {getgid()}")

try:
    serve_core()
finally:
    sleep(1000)
