## To setup on Seeed NPI I.MX6ULL board:

#### Install required packages:
```
sudo apt-get update
sudo apt install -y python3 python3-pip python3-venv openssh-server git
```
#### Setup python:

```
git clone https://github.com/cstrutton/prodmon
cd prodmon
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
# create SQL file directory
sudo mkdir /var/local/SQL
```

#### Add Service Files:

```
# create hard links to service files
sudo ln ./service_files/collect.service /etc/systemd/system/collect.service
sudo ln ./service_files/post.service /etc/systemd/system/post.service
sudo ln ./service_files/config.service /etc/systemd/system/config.service

# enable services
sudo systemctl enable collect
sudo systemctl enable post
sudo systemctl enable config

# reload the configuration
sudo systemctl daemon-reload
```
#### Network Configuration:

Use connman interactive mode to configure the PLANT network:
```
root@npi:~# connmanctl
# Plug in the PLANT network and run 
connmanctl> services # prints out the name of the plant network
connmanctl> config ethernet_<mac-address>_cable --ipv4 manual 10.2.42.155 255.255.192.0 10.4.1.9
# network connection will drop after above line is run.
connmanctl> config ethernet_<mac-address>_cable --nameservers 10.4.1.200 10.5.1.200
connmanctl> exit
```
Use connman interactive mode to configure the PLC network:
```
root@npi:~# connmanctl
# Plug in the PLC network and run 
connmanctl> services # prints out the name of the networks
connmanctl> config ethernet_<mac-address>_cable --ipv4 manual 192.168.1.254 255.255.255.0
# network connection will drop after above line is run.
connmanctl> exit
```

## Notes:
- service files:
  - https://www.devdungeon.com/content/creating-systemd-service-files
  - https://www.freedesktop.org/software/systemd/man/systemd.service.html#

 - rock pi boot from emmc:
    - https://forum.radxa.com/t/rock-pi-4b-v1-4-no-boot-on-emmc/3812

- Network configuration with connman
  - https://developer.toradex.com/knowledge-base/ethernet-network-(linux)
  - http://variwiki.com/index.php?title=Static_IP_Address


## Static IP adresses:
|IP|Machine|MAC| comment |
|-------------|------|-------------------|---------------|
| 10.4.42.153 | 1533 | d6:89:7c:ec:e0:9e |10R80 Autogauge|
| 10.4.42.154 | 1816 | 2e:1a:6d:d1:6f:1d |10R60 Autogauge|
| 10.4.42.155 ||||
| 10.4.42.156 ||||
| 10.4.42.157 ||||
| 10.4.42.158 ||||
| 10.4.42.160 ||||
| 10.4.42.161 ||||
| 10.4.42.162 ||||
| 10.4.42.163 ||||
| 10.4.42.164 ||||
| 10.4.42.165 ||||
| 10.4.42.166 ||||
| 10.4.42.167 ||||
| 10.4.42.168 ||||
pi| 10.4.42.169 |  650 |00:D0:C9:FE:83:5D| Trilobe Slurry |4
