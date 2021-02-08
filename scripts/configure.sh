#!/bin/bash

# Must be run with sudo or as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

print_menu () {
  local MENU=("$@")
  for index in "${!MENU[@]}"; do
    printf "%s) %s\n" $(( $index+1 )) "${MENU[$index]}"
  done
  printf "Enter to continue:"
  read choice
  return $(( choice ))
}

set_plc_network () {
  echo "Set PLC Network"

  local IP=$(ip addr show eth1 |\
           grep -o "inet [0-9]*\.[0-9]*\.[0-9]*\.[0-9]*" |\
           grep -o "[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*")
  read -e -i "$IP" -p "PLC IP Address: " IP

  local NETMASK=$(ifconfig eth1 | awk '/netmask/{split($4,a,":"); print a[1]}')
  read -e -i "$NETMASK" -p 'PLC Netmask: ' NETMASK

  echo "Executing: connmanctl config ethernet_dead12345678_cable --ipv4 manual ${IP} ${NETMASK}"
  connmanctl config ethernet_dead12345678_cable --ipv4 manual ${IP} ${NETMASK}
  echo "Result: "$?
}

set_plant_network () {
  echo "Set PLANT Network"

  local MAC=$(cat /sys/class/net/eth2/address | tr -d ':')
  local SERVICE_NAME="ethernet_${MAC}_cable"

  local IP=$(ip addr show eth2 |\
             grep -o "inet [0-9]*\.[0-9]*\.[0-9]*\.[0-9]*" |\
             grep -o "[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*")
  read -e -i "$IP" -p 'PLANT IP Address: ' IP

  local NETMASK=$(ifconfig eth2 |\
                  awk '/netmask/{split($4,a,":"); print a[1]}')
  read -e -i "$NETMASK" -p 'Netmask: ' NETMASK

  local GATEWAY=$(route -n |\
                  grep 'UG[ \t]' |\
                  awk '{print $2}')
  read -e -i "$GATEWAY" -p 'Gateway: ' GATEWAY

  local NAMESERVERS=$(connmanctl services ${SERVICE_NAME} |\
                      awk '/Nameservers.Configuration/ {print}' |\
                      grep -Po '\[\K[^]]*' ${NAMESERVERS} | tr -d ',')
  read -e -i "$NAMESERVERS" -p 'Nameservers: '

  echo "Executing: connmanctl config ${SERVICE_NAME} --ipv4 manual ${IP} ${NETMASK} ${GATEWAY} --nameservers ${NAMESERVERS}"
  echo "Result: "$?
}

select_collect_config_file() {
  echo "Load Collect Configuration from:"
  local FILES=(./configs/*-collect.yml)
  print_menu "${FILES[@]}"

  local result=$(( $? )) # converts to positive int or zero

  if ! [[ $result == 0 ]]
    then
    local FILENAME=${FILES[((++result))
  fi
}

select_post_config_file() {
  echo "Load Post Configuration from:"
  local FILES=(./configs/*-post.yml)
  print_menu "${FILES[@]}"
  echo $?
}

clear
while true; do
  MENU=("Set PLC Network"\
        "Set Plant Network"\
         "Install Collect Configuration"\
         "Install Post Cofiguration"\
         "Install Config Service"\
         "Install Post Service")
  print_menu "${MENU[@]}"
  case $? in
    1) set_plc_network
       ;;

    2) set_plant_network
       ;;

    3) select_collect_config_file
       ;;

    3) select_post_config_file
       ;;

    0) break
       ;;
  esac
done


