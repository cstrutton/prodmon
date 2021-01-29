### Networking Configuration How To
For Seeed NPI I.MX6ULL

- label center plug PLC and outer plug PLANT

#####Setup

- computer and PLC Port connected to Edge Router
- Edge Router has DHCP Server 
- connect PLC to Edge Router
- connect PLANT to plant network
- Random MAC Generator: https://www.hellion.org.uk/cgi-bin/randmac.pl?scope=local&type=unicast

####Setup fixed IP Addresses
- units are flashed so PLC MAC is DE:AD:12:34:56:78
- Edge router sets fixed IP of 192.1687.1.245
- ssh into 192.168.1.245
- edit /boot/uEnv.txt and add inserting random mac adresses
    ```
    # eth1
    # PLC port mac address
    ethaddr=<uniqe mac address>
    # eth2
    # Plant port mac address
    eth1addr=<uniqe mac address>
    ```
- reboot and connect using DHCP address assigned by Edge Router 
- configure the network fixed IP addresses using `connmanctl`:
  when the last 
    ```
    sudo connmanctl
    # list network interface names:
    connmnctl> services
    ...
    # plant network config
    connmanctl> config eth<tab completion> --ipv4 manual 10.4.42.XXX 255.255.192.0 10.4.1.9
    connmanctl> config eth<tab completion> --nameservers 10.4.1.200 10.5.1.200
    connmanctl> config eth<tab completion> --ipv4 manual 192.168.1.254 255.255.255.0
    ```
- the last line will cause the ssh session to disconnect.
- Reconnect using the configured plant network IP and continue software setup.
 
