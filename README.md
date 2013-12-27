agent
=====
getting started
---------------
### 环境依赖
#### Libvirt
     libvirt版本为 1.0.1
#### openvswitch
     ovs版本 >= 1.10.0

### 安装
##### 依赖库
    pip install -r requirements.txt
    所有服务均可配置，详细说明请查看配置文件
##### 执行安装脚本
    cd ${agenthome}/tools
    python setup.py install

### 启动/停止
    start ccf-agent
    stop ccf-agent

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
### 原理
    
    ovs提供monitor功能支持的协议比较多如sFlow，netFlow等。
    sFlow有两个不见组成：sFlow client, sFlow server.
    开启了sFlow功能的ovs相当与一个sFlow client.
    sFlow server咱们使用的是sFlow-rt，Floodlight的网络流量统计的核心就是基于它的.

### 部署
    
  1. 开启Agent 所在机器的sFlow功能

     ovs-vsctl -- --id=@sflow create sflow agent=lo target=\"127.0.0.1:6343\" header=128 sampling=64 polling=1 --set bridge br100 sflow=@sflow
     该命令执行的次数和需要开启sflow的网桥的数目有关
     > 参数说明：
             agent:  用于发送监控信息的网卡
             target:sFlow server的IP，端口6343
             bridge：需要开启sflow的网桥

  2. 部署sFlow server
     
     下载agent代码到sFlow server机器

  3. 启动sFlow server
     
     cd ${agent_home}/service/sflow-rt
     ./start.sh

  4. 检查sFlow是否配置好
            curl http://192.168.20.6:8008/agents/json

### sFlow-rt的json接口:供开发参考
  1. 初始化
     curl -H "Content-Type:application/json" -X PUT --data "{keys:'ipsource,ipdestination',value:'bytes',filter:'macdestination=525400B9FA73'}" http://localhost:8008/flow/${switch-port}/json
  2. 查看结果
     curl http://127.0.0.1:8008/metric/127.0.0.1/${switch-port}/json
  3. 查看完整结果
     curl http://127.0.0.1:8008/metric/127.0.0.1/json


Tools
-------------
### 虚拟机删除工具
    cd ${agenthome}/tools
    python delete_vm.py vmuuid1 vmuuid2 ... vmuuidn
