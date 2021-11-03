## Using the NanoPi R2S

Install FriendlyWrt on an SDCard and boot the system

### Set up Static Networking

#### Plant network:
edit the wan interface in `/etc/config/network` as follows:
```
config interface 'wan'
        option ifname 'eth0'
        option proto 'static'
        option ipaddr '10.4.42.170'         # set desired IP
        option netmask '255.255.192.0'      # correct value for PMDS
        option gateway '10.4.1.9'           # correct value for PMDS
        option dns '10.4.1.200 10.5.1.200'  # correct values for PMDS
```

#### PLC network:
edit the lan interface in `/etc/config/network` as follows:
```
config interface 'lan'
        option type 'bridge'                # not sure if this is needed 
        option ifname 'eth1'
        option proto 'static'               
        option ipaddr '192.168.1.254'       # set to suit the machine network
        option netmask '255.255.255.0'
```

### Set up the `prodmon` system:
```
git clone https://github.com/cstrutton/prodmon.git
cd prodmon
git pull # get the latest copy from the repo
docker build -t prodmon-collect --file prodmon-collect.dockerfile .
docker build -t prodmon-post --file prodmon-post.dockerfile .

docker run -d --restart=unless-stopped --volume sql:/code/tempSQL --name collect prodmon-collect <configfile> 
docker run -d --restart=unless-stopped --volume sql:/code/tempSQL --name post prodmon-post <configfile> 
```
# ****** From here down needs to be tested ******


### Set up as Gateway to an internal device
- create an alias to the wan port with a new ip address:
```
    config interface 'wan1'
        option ifname 'eth0'
        option proto 'static'
        option ipaddr '192.168.1.240' # this is the new IP Address
        option netmask '255.255.255.0'
```
- under Network|Firewall|Port Forwards create a new rule:
```
General Settings:
    Name: AllPorts
    Protocol: Any
    Source Zone: wan
    Destination Zone: lan
    Internal IP Address: <PLC's IP Address>
Advanced Settings:
    External IP address: <to the WAN1 alias in network config>
```
** The internal device needs to set its network gateway to point to the gateway device.