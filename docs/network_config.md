## Networking Configuration How To
### For Nano Pi R2S

Wiki: https://wiki.friendlyarm.com/wiki/index.php/NanoPi_R2S

`/etc/network/interfaces.d/eth0`
```
auto eth0
iface eth0 inet static
  address 10.4.42.176
  netmask 255.255.192.0
  gateway 10.4.1.9
```
 
`/etc/network/interfaces.d/eth1`
```
auto eth1
iface eth1 inet static
  address 192.168.1.254
  netmask 255.255.255.0
```
 
`/etc/systemd/resolved.conf`
```
DNS=10.4.1.200 10.5.1.200
```

## For Seeed NPI I.MX6ULL
- label center plug PLC and outer plug PLANT

#####Setup

- computer and PLC Port connected to Edge Router
- Edge Router has DHCP Server 
- connect PLC to Edge Router
- connect PLANT to plant network
- [Random MAC Generator](https://www.hellion.org.uk/cgi-bin/randmac.pl?scope=local&type=unicast)

####Setup fixed IP Addresses
- units are flashed so PLC MAC is DE:AD:12:34:56:78
- Edge router sets fixed IP of 192.1687.1.254
- ssh into 192.168.1.254
- edit /boot/Env.txt and add inserting random mac address for the Plant network.
    ```
    # eth2
    # Plant port mac address
    eth1addr=<uniqe mac address>
    ```
- reboot and connect again to 192.168.1.254 
- configure the plant network fixed IP addresses using `connmanctl`:
    ```
    sudo connmanctl
    # list network interface names:
    connmnctl> services
    ...
    # plant network config
    connmanctl> config eth<tab completion> --ipv4 manual 10.4.42.XXX 255.255.192.0 10.4.1.9 --nameservers 10.4.1.200 10.5.1.200
    ```
- Reboot and reconnect using the configured plant network IP address 
- if DNS resolution doesn't work, re-do the nameserver set above. 
and continue software setup.
 
