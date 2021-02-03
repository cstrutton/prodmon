## To set up on Seeed NPI I.MX6ULL board:

### Prepare SD Card
see [docs/sdcard.md](docs/sdcard.md)


### Networking:
See [docs/network_config.md](docs/network_config.md)

#### Clone and install Production Monitor
```
git clone https://github.com/cstrutton/prodmon
cd prodmon
python3 -m venv venv            # create virtual env
venv/bin/pip3 install wheel     # needed to bild wheels 
venv/bin/pip3 install -e .      # install prodmon into it
```

#### Install config files
```
sudo mkdir /etc/prodmon
sudo cp ./configs/generic-post.yml /etc/prodmon/post.config
sudo cp ./configs/[config] /etc/prodmon/collect.config
```

#### Add Service Files:
```
# copy service files to config directory
sudo cp service_files/collect.service /etc/systemd/system/collect.service
sudo cp service_files/post.service /etc/systemd/system/post.service
# sudo ln -f ./service_files/config.service /etc/systemd/system/config.service

# enable services
sudo systemctl enable collect
sudo systemctl enable post
# sudo systemctl enable config

# reload the systemd configuration
sudo systemctl daemon-reload
```

## Static IP addresses:
See [docs/mac-ip-addresses.md](docs/mac-ip-addresses.md)

## Add log-in status check to .bashrc ##

```
tee -a .bashrc <<EOF

if (systemctl -q is-active collect.service)
    then
    echo "Collect service is running."
fi

if (systemctl -q is-active post.service)
    then
    echo "Post service is running."
fi

EOF
``` 
