#!/bin/bash

# Must be run with sudo or as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

set_plc_network () {
  echo "Set PLC Network"

  local IP=$(ip addr show eth1 | grep -o "inet [0-9]*\.[0-9]*\.[0-9]*\.[0-9]*" | grep -o "[0-9]*\.[0-9]*$
  read -e -i "$IP" -p 'PLC IP Address: ' IP

  local NETMASK=$(ifconfig eth1 | awk '/netmask/{split($4,a,":"); print a[1]}')
  read -e -i "$NETMASK" -p 'PLC Netmask: ' NETMASK

  echo "connmanctl config ethernet_dead12345678_cable --ipv4 manual ${IP} ${NETMASK}"
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

  echo connmanctl config ${SERVICE_NAME} \
                  --ipv4 manual ${IP} ${NETMASK} ${GATEWAY} \
                  --nameservers ${NAMESERVERS}
}

select_config_files() {
  echo "Select Config Files:"
  echo "Collect Configuration:"
  # set the prompt used by select, replacing "#?"
  PS3="Use number to select a file or 'stop' to cancel: "
  # allow the user to choose a file
  select filename in ./configs/*-collect.yml; do
    # leave the loop if the user says 'stop'
    if [[ "$REPLY" == stop ]]; then break; fi
    # complain if no file was selected, and loop to ask again
    if [[ "$filename" == "" ]]; then
      echo "'$REPLY' is not a valid choice"
      continue
    fi

    # now we can use the selected file
    echo "$filename installed"
    # it'll ask for another unless we leave the loop
    break
  done

  echo "Select a post configuration"
  # set the prompt used by select, replacing "#?"
  PS3="Use number to select a file or 'stop' to cancel: "
  # allow the user to choose a file
  select filename in ./configs/*-collect.yml; do
    # leave the loop if the user says 'stop'
    if [[ "$REPLY" == stop ]]; then break; fi
    # complain if no file was selected, and loop to ask again
    if [[ "$filename" == "" ]]; then
      echo "'$REPLY' is not a valid choice"
      continue
    fi
    # now we can use the selected file
    echo "$filename installed"
    # it'll ask for another unless we leave the loop
    break
  done
}


while true; do
  clear
  cat << _EOF_
Please Select:

1. Set PLC Network
2. Set Plant Network
3. Install Config Files
4. Install Service Files
0. Quit

_EOF_

  read choice;

  case $choice in
    1) set_plc_network()
       ;;

    2) set_plant_network()
       ;;

    3) select_config_files() 
       ;;

    4) echo "Choice 4"

       files=( ./configs/*-collect.yml )
       shopt -s extglob

       string="@(${files[0]}"
       for((i=1;i<${#files[@]};i++))
       do
         string+="|${files[$i]}"
       done
       ## Close the parenthesis. $string is now @(file1|file2|...|fileN)
       string+=")"

       select file in "${files[@]}" "Skip"; do
         case $file in
           $string)
             echo "$file"
             break
             ;;
           *)
             echo "Skipping Collect Config"
             break
             ;;
         esac
       done
       ;;

    5) echo "Choice 5"
       ;;

    0) break

  esac
done


