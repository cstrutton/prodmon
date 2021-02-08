#!/bin/bash

# Must be run with sudo or as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

print_menu() {
  local MENU=("$@")
  for index in "${!MENU[@]}"; do
    printf "%s) %s\n" $(( $index+1 )) "${MENU[$index]}"
  done
  printf "Enter to continue:"
  read choice
  return $(( choice ))
}

set_plc_network() {
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

set_plant_network() {
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
  connmanctl config ${SERVICE_NAME} --ipv4 manual ${IP} ${NETMASK} ${GATEWAY} --nameservers ${NAMESERVERS}
  echo "Result: "$?
}

set_configuration_files() {
  while true; do
    MENU=("Choose Collect Configuration File"\
          "Choose Post Configuration File")
    print_menu "${MENU[@]}"

    case $? in
      1) printf "Load Collect Configuration from:\n"
         local FILES=(./configs/*-collect.yml)
         print_menu "${FILES[@]}"

         local result=$(( $? )) # converts bad characters to zero

         if ! [[ $result == 0 ]]; then
           local FILENAME=${FILES[((--result))]}
           printf "Installing %s as /etc/prodmon/collect.config :" $FILENAME
           cp $FILENAME /etc/prodmon/collect.config
           printf "%d\n\n" $?

           if (systemctl -q is-active collect.service); then
             printf "Restarting the Collect service: "
             systemctl restart collect
             printf "%d\n\n" $?
           fi
         fi ;;

      2) printf "Load Post Configuration from:\n"
         local FILES=(./configs/*-post.yml)
         print_menu "${FILES[@]}"

         local result=$(( $? )) # converts bad characters to zero

         if ! [[ $result == 0 ]]; then
           local FILENAME=${FILES[((--result))]}
           printf "Installing %s as /etc/prodmon/post.config :" $FILENAME
           cp $FILENAME /etc/prodmon/post.config
           printf "%d\n\n" $?
           if (systemctl -q is-active post.service); then
             printf "Restarting the Post service: "
             systemctl restart post
             printf "%d\n\n" $?
           fi
         fi ;;

      0) break ;;
    esac
  done
}

configure_service_files() {
  while true; do
    local CHANGED=0
    MENU=("Choose Collect Service Unit File"\
          "Enable Collect Service to run at boot"\
          "Choose Post Service Unit File"\
          "Enable Post Service File to run at boot")
    print_menu "${MENU[@]}"
    case $? in
      1) printf "Copying Collect Service Unit File: "
         cp service_files/collect.service /etc/systemd/system/collect.service
         printf "%d\n" $?
         (( CHANGED++ )) ;;

      2) systemctl is-enabled collect.service
         local ENABLED=$?
         if (( ENABLED == 0 )); then
           local NEW_MODE="enable"
         else
           local NEW_MODE="disable"
         if
         printf "%s Collect Service: " ${NEW_MODE^}
         systemctl $NEW_MODE collect.service
         printf "%d\n" $?
         (( CHANGED++ )) ;;

      3) printf "Copying Post Service Unit File: "
         cp service_files/post.service /etc/systemd/system/post.service
         printf "%d\n" $?
         (( CHANGED++ )) ;;

      4) systemctl is-enabled post.service
         local ENABLED=$?
         if (( ENABLED == 0 )); then
           local NEW_MODE="enable"
         else
           local NEW_MODE="disable"
         if
         printf "%s Post Service: " ${NEW_MODE^}
         systemctl $NEW_MODE post.service
         printf "%d\n" $?
         (( CHANGED++ )) ;;

      0) break ;;
    esac
    if (( CHANGED > 0 )); then
      printf "Running systemclt daemon-reload: \n"
      systemctl daemon-reload
      printf "%d\n\n" $?
    fi
  done
}

force_reboot() {
  while true; do
    local yn=""
    read -p "Do you want to reboot now?" yn
    case $yn in
        [Yy]* ) reboot now; break;;
        [Nn]* ) return;;
        * ) echo "Please answer yes or no.";;
    esac
  done
}

clear
while true; do
  MENU=("Set PLC Network"\
        "Set Plant Network"\
        "Set Configuration Files"\
        "Configure Service Unit Files"\
        "Force Reboot")
  print_menu "${MENU[@]}"
  case $? in
    1) set_plc_network
       ;;

    2) set_plant_network
       ;;

    3) set_configuration_files
       ;;

    4) configure_service_files
       ;;

    5) force_reboot
       ;;

    0) break
       ;;
  esac
done


