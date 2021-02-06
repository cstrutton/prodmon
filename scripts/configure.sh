read -p 'PLC IP Address: ' PLC_IP
read -p 'PLC Netmask: ' PLC_NETMASK
echo It\'s nice to meet you $PLC_IP $PLC_NETMASK

# connmanctl config ethernet_de3c0bf795c2_cable --ipv4 manual $(PLC_IP) $(PLC_NETMASK)