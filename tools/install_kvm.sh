#!/bin/bash
wget http://wiki.qemu-project.org/download/qemu-1.7.0.tar.bz2
apt-get install -y gcc libsdl1.2-dev zlib1g-dev libasound2-dev linux-kernel-headers pkg-config libgnutls-dev libpci-dev libaio-dev autoconf
tar -jxvf qemu-1.7.1.tar.bz2
cd qemu-1.7.1/
./configure  --target-list=x86_64-softmmu --enable-kvm --enable-attr --enable-linux-aio --bindir=/usr/bin/
make
make install
modprobe kvm
modprobe kvm-intel
