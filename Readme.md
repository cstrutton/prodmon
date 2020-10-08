## To setup on Seeed NPI I.MX6ULL board:

### Networking:
See [docs/network_config.md](docs/network_config.md)

#### Install required packages:
```
#currently does not work on Stackpole network.  Webfilter blocks apt.
sudo apt-get update
sudo apt install -y python3 python3-pip git
```

#### Clone and install Production Monitor
```
git clone https://github.com/cstrutton/prodmon
cd prodmon
pip3 install -e .
```
#### Install config files
sudo mkdir /etc/prodmon
sudo ln ./configs/<active_config>-collect.yml /etc/prodmon/collect.config
sudo ln ./configs/generic-post.yml /etc/prodmon/post.config

#### Add Service Files:
```
# create hard links to service files (-f forces if we are re running this)
sudo ln -f ./service_files/collect.service /etc/systemd/system/collect.service
sudo ln -f ./service_files/post.service /etc/systemd/system/post.service
# sudo ln -f ./service_files/config.service /etc/systemd/system/config.service

# enable services
sudo systemctl enable collect
sudo systemctl enable post
# sudo systemctl enable config

# reload the systemd configuration
sudo systemctl daemon-reload
```

#### Config files:
```
sudo ln -sfv ./configs/<config_file> /etc/prodmon/collect.config
sudo ln -sfv ./configs/<config_file> /etc/prodmon/post.config

```


## Static IP addresses:
See [docs/mac-ip-addresses.md](docs/mac-ip-addresses.md)