
using systemd timesync service:
set time server:
edit `/etc/systemd/timesyncd` to contain `NTP=10.4.1.200`
change RootDistanceMaxSec=5 to 50
```
sudo sed -i '/#NTP=/c\NTP=10.4.1.200' /etc/systemd/timesyncd.conf
sudo sed -i '/#RootDistanceMaxSec=/c\RootDistanceMaxSec=50' /etc/systemd/timesyncd.conf 
```
sudo timedatectl set-ntp true

check status : `timedatectl timesync-status`
can take a few minutes to show its sycronized

Set time zone
sudo timedatectl set-timezone America/Toronto


set ntp server reference: https://wiki.archlinux.org/index.php/Systemd-timesyncd
RootDistanceMaxSec reference: https://unix.stackexchange.com/a/655489
