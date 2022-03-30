
Setup IP aliasing:

https://linuxhint.com/how-to-assign-multiple-ip-addresses-to-single-nic-in-ubuntu-20-04-lts/


Setup port forwarding:
https://www.qsl.net/kb9mwr/wapr/tcpip/1to1nat.html#:~:text=Iptables%201%3A1%20NAT,IP%20to%20one%20internal%20IP.


Iptables 1:1 NAT

1:1 NAT maps a single Public IP Address to one of your computer within your local area network (LAN).
Unlike port forwarding, 1:1 NAT forwards all ports from one external IP to one internal IP.

```
iptables -t nat -A POSTROUTING -o eth0 -s 10.25.39.2 -j SNAT --to-source 44.92.21.5
iptables -t nat -A PREROUTING -i eth0 -d 44.92.21.5 -j DNAT --to-destination 10.25.39.2
iptables -A FORWARD -s 44.92.21.5 -j ACCEPT
iptables -A FORWARD -d 10.25.392 -j ACCEPT
```
