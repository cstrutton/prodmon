
using systemd timesync service:
set time server:
edit `/etc/systemd/timesyncd` to contain `NTP=10.4.1.200`
```
sudo sed -i '/#NTP=/c\NTP=10.4.1.200' /etc/systemd/timesyncd.conf
```
sudo timedatectl set-ntp true

check status : `timedatectl timesync-status`
can take a few minutes to show its sycronized

Set time zone
sudo timedatectl set-timezone America/Toronto


reference: https://wiki.archlinux.org/index.php/Systemd-timesyncd