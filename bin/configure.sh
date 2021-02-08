#!/bin/bash

# Must be run with sudo or as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

print_menu() {
  local MENU=("$@")
  for index in "${!MENU[@]}"; do
    printf "%s) %s\n" $(( index+1 )) "${MENU[$index]}"
  done
  printf "Enter to continue:"
  read -r -n 1 choice
  return $(( choice ))
}

areyousure() {
  read -p "$*" -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]
  then
    return 1
  fi
}

set_plc_network() {
  local IP NETMASK

  printf "\n\nConfigure PLC Network\n"

  IP=$(ip addr show eth1 |\
       grep -o "inet [0-9]*\.[0-9]*\.[0-9]*\.[0-9]*" |\
       grep -o "[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*")
  read -er -i "$IP" -p "PLC IP Address: " IP

  NETMASK=$(ifconfig eth1 | awk '/netmask/{split($4,a,":"); print a[1]}')
  read -er -i "$NETMASK" -p 'PLC Netmask: ' NETMASK

  printf "Execute: connmanctl config ethernet_dead12345678_cable --ipv4 manual %s %s \n" "$IP" "$NETMASK"
  if areyousure "Proceed?:[yN]"; then
    connmanctl config ethernet_dead12345678_cable --ipv4 manual "${IP}" "${NETMASK}"
    printf "Command returned: %d\n" $?
  fi
}

set_plant_network() {
  local MAC SERVICE_NAME IP NETMASK GATEWAY NAMESERVERS
  printf "\n\nConfigure Plant Network\n"

  MAC=$(tr -d ':' < /sys/class/net/eth2/address)
  SERVICE_NAME="ethernet_${MAC}_cable"

  IP=$(ip addr show eth2 |\
             grep -o "inet [0-9]*\.[0-9]*\.[0-9]*\.[0-9]*" |\
             grep -o "[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*")
  read -er -i "$IP" -p 'PLANT IP Address: ' IP

  NETMASK=$(ifconfig eth2 | awk '/netmask/{split($4,a,":"); print a[1]}')
  read -er -i "$NETMASK" -p 'Netmask: ' NETMASK

  GATEWAY=$(route -n |\
                  grep 'UG[ \t]' |\
                  awk '{print $2}')
  read -er -i "$GATEWAY" -p 'Gateway: ' GATEWAY

  NAMESERVERS=$(connmanctl services "${SERVICE_NAME}" |\
                      awk '/Nameservers.Configuration/ {print}' |\
                      grep -Po '\[\K[^]]*' "${NAMESERVERS}" | tr -d ',')
  read -er -i "$NAMESERVERS" -p 'Nameservers: '

  printf "Execute: connmanctl config %s --ipv4 manual %s %s %s --nameservers %s\n" \
         "${SERVICE_NAME}" "${IP}" "${NETMASK}" "${GATEWAY}" "${NAMESERVERS}"
  if areyousure "Proceed?:[yN]"; then
    connmanctl config "${SERVICE_NAME}" --ipv4 manual "${IP}" "${NETMASK}"\
                      "${GATEWAY}" --nameservers "${NAMESERVERS}"
    printf "Command returned: %d\n" $?
  fi
}

set_configuration_files() {
  local MENU FILES result FILENAME
  while true; do
    printf "\n\nInstall Configuration Files\n"

    MENU=("Choose Collect Configuration File"\
          "Choose Post Configuration File")
    print_menu "${MENU[@]}"

    case $? in
      1) printf "Load Collect Configuration from:\n"
         local FILES=(./configs/*-collect.yml)
         print_menu "${FILES[@]}"

         result=$?
         if ! [[ "$result" =~ ^[0-9]+$ ]]
           then
           (( result = 0 ))
         fi

         if ! [[ $result == 0 ]]; then
           FILENAME=${FILES[((--result))]}
           printf "Installing %s as /etc/prodmon/collect.config\n" "$FILENAME"
           cp "$FILENAME" /etc/prodmon/collect.config
           printf "Command returned: %d\n\n" $?

           if (systemctl -q is-active collect.service); then
             printf "Restarting the Collect service: "
             systemctl restart collect
             printf "Command returned: %d\n\n" "$?"
           fi
         fi ;;

      2) printf "Load Post Configuration from:\n"
         FILES=(./configs/*-post.yml)
         print_menu "${FILES[@]}"

         result=$?
         if ! [[ "$result" =~ ^[0-9]+$ ]]
           then
           (( result = 0 ))
         fi

         if ! [[ $result == 0 ]]; then
           FILENAME=${FILES[((--result))]}
           printf "Installing %s as /etc/prodmon/post.config :" "$FILENAME"
           cp "$FILENAME" /etc/prodmon/post.config
           printf "%d\n\n" "$?"
           if (systemctl -q is-active post.service); then
             printf "Restarting the Post service: "
             systemctl restart post
             printf "%d\n\n" "$?"
           fi
         fi ;;

      0) break ;;
    esac
  done
}

configure_service_files() {
  local CHANGED MENU
  while true; do
    printf "\nConfigure Systemd Services\n"
    CHANGED=0
    MENU=("Install Collect Service Unit File"\
          "Enable/Disable Collect Service to run at boot"\
          "Install Post Service Unit File"\
          "Enable/Disable Post Service File to run at boot")
    print_menu "${MENU[@]}"
    case $? in
      1) printf "Copying Collect Service Unit File: "
         cp service_files/collect.service /etc/systemd/system/collect.service
         printf "%d\n" $?
         (( CHANGED++ )) ;;

      2) systemctl is-enabled collect.service --quiet
         local ENABLED=$?
         if (( ENABLED == 0 )); then
           local MODE="disabled"
           local NEW_MODE="enable"
         else
           local MODE="enabled"
           local NEW_MODE="disable"
         fi
         printf "Collect Service is %s\n" $MODE
         if areyousure "${NEW_MODE^} Collect Service? [yN]"; then
           systemctl $NEW_MODE collect.service --quiet
           systemctl is-enabled collect.service
           (( CHANGED++ ))
         fi ;;

      3) printf "Copying Post Service Unit File: "
         cp service_files/post.service /etc/systemd/system/post.service
         printf "%d\n" $?
         (( CHANGED++ )) ;;

      4) systemctl is-enabled post.service --quiet
         local ENABLED=$?
         if (( ENABLED == 0 )); then
           local NEW_MODE="enable"
         else
           local NEW_MODE="disable"
         fi
         printf "Post Service is %s\n" $MODE
         if areyousure "${NEW_MODE^} Post Service? [yN]"; then
           systemctl $NEW_MODE post.service --quiet
           systemctl is-enabled post.service
           (( CHANGED++ ))
         fi ;;

      0) if (( CHANGED > 0 )); then
           printf "Running systemclt daemon-reload: "
           systemctl daemon-reload
           printf "%d\n\n" $?
         fi
         break ;;

    esac
  done
}

force_reboot() {
  if areyousure "Reboot System Now? [yN]"; then
    printf "Rebooting.... Wait 10 seconds before attempting to reconnect"
    reboot now
  fi
}

clear
while true; do
  printf "\n"
  MENU=("Configure PLC Network"\
        "Configure Plant Network"\
        "Install Configuration Files"\
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


