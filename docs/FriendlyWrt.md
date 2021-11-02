## Using the NanoPi R2S

Install FriendlyWrt on an SDCard and boot the system

### Set up Static Networking


### Set up the `prodmon` system:
```
git clone https://github.com/cstrutton/prodmon.git
cd prodmon
docker run --volume sql:/code/tempSQL --name collect --file prodmon-collect.dockerfile <configfile>
docker run --volume sql:/code/tempSQL --name post --file prodmon-post.dockerfile <configfile>
```

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