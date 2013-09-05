#!/bin/bash
apt-get install -y libvirt-bin gcc make  pkg-config libxml2-dev libgnutls-dev  libdevmapper-dev gnutls-bin libgnutls-dev  virtinst  pm-utils  libyajl-dev libnl-dev python-libvirt

unzip libvirt-1.0.1.zip

cd libvirt-1.0.1
chmod 777 autogen.sh
chmod 777 configure
./autogen.sh --system

make && make install

sed -i 's/#listen_tls = 0/listen_tls = 0/' /etc/libvirt/libvirtd.conf

sed -i 's/#listen_tcp = 1/listen_tcp = 1/' /etc/libvirt/libvirtd.conf


sed -i 's/# vnc_listen = "0.0.0.0"/vnc_listen = "0.0.0.0"/' /etc/libvirt/qemu.conf

sed -i 's/libvirtd_opts="-d"/libvirtd_opts="-d -l"/' /etc/default/libvirt-bin

service libvirt-bin restart


echo "start to install sasl2 for libvirt rpc"
apt-get install -y sasl2-bin

echo "set sasl user as root"

saslpasswd2 -a libvirt root
