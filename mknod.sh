#!/bin/sh
set -ex

for i in `seq 0 $1`
do
    mknod -m 666 "/dev/ttyUSB$i" c 188 "$i"
done
