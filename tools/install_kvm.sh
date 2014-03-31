#!/bin/bash
<<<<<<< HEAD
wget http://wiki.qemu-project.org/download/qemu-1.7.0.tar.bz2
apt-get install -y gcc libsdl1.2-dev zlib1g-dev libasound2-dev linux-kernel-headers pkg-config libgnutls-dev libpci-dev libaio-dev autoconf
tar -jxvf qemu-1.7.1.tar.bz2
cd qemu-1.7.1/
./configure  --target-list=x86_64-softmmu --enable-kvm --enable-attr --enable-linux-aio --bindir=/usr/bin/
=======
wget http://nchc.dl.sourceforge.net/project/kvm/qemu-kvm/1.2.0/qemu-kvm-1.2.0.tar.gz
apt-get install -y make automake autoconf gcc libsdl1.2-dev zlib1g-dev libasound2-dev linux-kernel-headers pkg-config libgnutls-dev libpci-dev libaio-dev
tar -zxvf qemu-kvm-1.2.0.tar.gz
cd qemu-kvm-1.2.0
./configure --enable-kvm --enable-attr --enable-linux-aio --bindir=/usr/bin/
>>>>>>> 5ad9de91cdd37f5c85325a7318b4060591877bca
make
make install
modprobe kvm
modprobe kvm-intel
