#!/bin/bash
wget http://nchc.dl.sourceforge.net/project/kvm/qemu-kvm/1.2.0/qemu-kvm-1.2.0.tar.gz
apt-get install -y gcc libsdl1.2-dev zlib1g-dev libasound2-dev linux-kernel-headers pkg-config libgnutls-dev libpci-dev libaio-dev
tar -zxvf qemu-kvm-1.2.0.tar.gz
cd qemu-kvm-1.2.0
./configure --enable-kvm --enable-attr --enable-linux-aio --bindir=/usr/bin/
make
make install
modprobe kvm
modprobe kvm-intel
