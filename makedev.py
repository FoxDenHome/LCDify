from os import mknod, makedev
from stat import S_IFCHR


def make_tty_dev(idx: int) -> None:
    dev = makedev(188, idx)
    mknod(path="/dev/ttyUSB{idx}", mode=0o666 | S_IFCHR, device=dev)


def make_tty_devs(count: int) -> None:
    for i in range(count):
        make_tty_dev(i)
