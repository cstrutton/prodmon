## Setup on NanoPi using Ubuntu Core

### Basics:

```bash
# Ubuntu Mirrors are blocked by Stackpole's web filter
cp /etc/apt/sources.list /etc/apt/sources.list.bak
cp /etc/apt/sources.list.orig /etc/apt/sources.list

# Update the system
apt update
apt upgrade -y

# Install prerequisites
apt install -y python3-pip nano

# Install Prodmon software
cd /opt
git clone https://github.com/cstrutton/prodmon
cd prodmon
pip3 install wheel
pip3 install -e . 

# Install the service unit files
cp service_files/collect.service /etc/systemd/system/collect.service
cp service_files/post.service /etc/systemd/system/post.service

# Enable services
sudo systemctl enable collect
sudo systemctl enable post

# reload the systemd configuration
sudo systemctl daemon-reload

# Install config files
sudo mkdir /etc/prodmon
sudo cp ./configs/generic-post.yml /etc/prodmon/post.config
sudo cp ./configs/[config] /etc/prodmon/collect.config
```
