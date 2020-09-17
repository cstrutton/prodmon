### Networking Configuration How To
For Seeed NPI I.MX6ULL

- label center plug PLC and outer plug PLANT
- connect PLC to dhcp server
- ssh into unit using the plc port
- edit /boot/uEnv.txt and add 
    ```
    # eth1
    # PLC port mac address
    ethaddr=xx:xx:xx:xx:xx:xx
    # eth2
    # Plant port mac address
    eth1addr=xx:xx:xx:xx:xx:xx
    ```
- reboot using the dhcp server
- connect the plant network to the plant
    ```
    sudo connmanctl
    # plant network config
    connmanctl> config eth<tab completion> --ipv4 manual 10.4.42.156 255.255.192.0 10.4.1.9
    connmanctl> config eth<tab completion> --nameservers 10.4.1.200 10.5.1.200
    connmanctl> exit
    ```
 - this will leave PLC network on dhcp
 - take board home and update and install packages
    ```
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip git
    ```

 - after updating linux, configure PLC network as required
    ```
    connmanctl
    connmanctl> config eth<tab completion> --ipv4 manual 192.168.1.254 255.255.255.0
    connmanctl> exit
    ```
 
 