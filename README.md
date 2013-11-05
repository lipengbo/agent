agent
=====
getting started
---------------
### 安装
    pip install -r requirements.txt
    所有服务均可配置，详细说明请查看配置文件
    务必保证装agent的机器有两个网桥，一个连接控制网络，一个连接数据层面
### 启动
    python agent.py

monitor service
---------------
### 功能
  1. 性能查询服务:
  
  向上级提供性能查询服务，包括虚拟机、宿主机

### 接口
  和vtmanager之间有接口，因为都是内部使用所以不具体描述各个接口的实现

compute service
---------------
### 功能
  1. 虚拟机管理:
  提供虚拟机的创建、删除、起停,虚拟机链路管理等方法

### 接口
  1. 和vtmanager之间有接口，因为都是内部使用所以不具体描述各个接口的实现

ovs service
-----------
### 功能
  1. 提供远程操作ovs的能力
  2. 提供ovs监控信息

gateway service
---------------
### 功能
  1. 提供生成gateway虚拟机的能力
  2. 提供gateway服务的虚拟机有两块网卡，一个用于链接基础网络的数据层面，一个用于链接虚拟及网络
  3. 提供snat功能，用于虚拟机访问外网

### 要求
  1. 需要在glance中upload一个名字为gateway的image，该image我已经制作好，并上传到了192.168.5.107的glance服务中

dhcp service
-------------
### 功能
  1. 和gateway共用一个虚拟机
  2. 目前不支持dhcp网段自定义（slice的网络中所有的地址都可以被dhcp分配）


sFlow Usage
-------------
  1. 初始化
     curl -H "Content-Type:application/json" -X PUT --data "{keys:'ipsource,ipdestination',value:'bytes',filter:'macdestination=525400B9FA73'}" http://localhost:8008/flow/${switch-port}/json
  2. 查看结果
     curl http://127.0.0.1:8008/metric/127.0.0.1/${switch-port}/json
  3. 查看完整结果
     curl http://127.0.0.1:8008/metric/127.0.0.1/json
