## To setup on Seeed NPI I.MX6ULL board:

### Networking:
See Networking Config how to.

#### Install required packages:
```
sudo apt-get update
sudo apt install -y python3 python3-pip git
```

#### Clone and install Production Monitor
```
git clone https://github.com/cstrutton/prodmon
cd prodmon
python3 setup.py install .
```

#### Add Service Files:
```
# create links to service files (-f forces if we are re running this)
sudo ln -f ./service_files/collect.service /etc/systemd/system/collect.service
sudo ln -f ./service_files/post.service /etc/systemd/system/post.service
sudo ln -f ./service_files/config.service /etc/systemd/system/config.service

# enable services
sudo systemctl enable collect
sudo systemctl enable post
sudo systemctl enable config

# reload the configuration
sudo systemctl daemon-reload
```


## Static IP addresses:
|IP|Machine|MAC| comment |
|-------------|------|-------------------|---------------|
| 10.4.42.153 | 1533 | d6:89:7c:ec:e0:9e |10R80 Autogauge|
| 10.4.42.154 | 1816 | 2e:1a:6d:d1:6f:1d |10R60 Autogauge|
| 10.4.42.155 |      | ee:5e:46:b3:bc:ef |               |
| 10.4.42.156 |      | 8e:fc:            |               |
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
