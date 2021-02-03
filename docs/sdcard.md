- get the latest image from Seeed
- burn to the card using Etcher
- boot from the sdcard and connect via ssh (both ports default to dhcp)
- `sudo apt-get update` 
- `sudo apt install -y python3 python3-pip python3-venv git python3-dev build-essential`
- edit `/boot/uEnv.txt` to include MAC address info (add to end)
```
# eth1
# PLC port mac address
ethaddr=de:ad:12:34:56:78
# eth2
# Plant port mac address
eth1addr=xx:xx:xx:xx:xx:xx
```
- reboot so new MAC address takes effect.  My DHCP is configured to give that MAC 192.168.1.254
- ssh into 192.168.1.254 and continue

Configure PLC network to static IP Address:
```
sudo connmanctl config ethernet_dead12345678_cable --ipv4 manual 192.168.1.254 255.255.255.0
```

### Create config directory

```
sudo mkdir /etc/prodmon
sudo touch /etc/prodmon/post.config
sudo touch /etc/prodmon/collect.config
```

- run sudo fire-config and enable flashing.  The card will flash machines until 
  `flash-firmware=enable` is commented out in `/boot/uEnv.txt`


add to .bashrc:
```
statuscollect () {
  if (systemctl -q is-active collect.service)
      then
      echo "Collect service is running."
      else
      echo "Collect service is not running."
  fi
}

statuspost () {
  if (systemctl -q is-active post.service)
      then
      echo "Post service is running."
      else
      echo "Post service is not running."
  fi
}

statuscollect
statuspost
```