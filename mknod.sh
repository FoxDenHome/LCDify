#!/bin/sh
set -ex

mkdir -p /vdev
for i in `seq 0 $1`
do
    mknod -m 666 "/vdev/ttyUSB$i" c 188 "$i"
done
