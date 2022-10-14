from os import mknod, makedev
from stat import S_IFCHR
from traceback import print_exc


def make_tty_dev(idx: int) -> None:
    dev = makedev(188, idx)
    mknod(path="/dev/ttyUSB{idx}", mode=0o666 | S_IFCHR, device=dev)


def make_tty_devs(count: int) -> None:
    for i in range(count):
        try:
            make_tty_dev(i)
        except Exception:
            print(f"Error creating device {i}", flush=True)
            print_exc()
