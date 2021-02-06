#!/bin/bash

# Must be run with sudo or as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

while true ; do
  echo "1) Set PLC Network"
  echo "2) Set PLANT Network"
  echo "3) Set Config Files"
  echo "4) Install Service Files"
  echo "5) View Logs"
  echo "Enter Exit"
  read choice;

  case $choice in
    1) echo "Set PLC Network"

       PLC_IP=$(ip addr show eth1 | grep -o "inet [0-9]*\.[0-9]*\.[0-9]*\.[0-9]*" | grep -o "[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*")
       read -e -i "$PLC_IP" -p 'PLC IP Address: ' PLC_IP

       PLC_NETMASK=$(ifconfig eth1 | awk '/netmask/{split($4,a,":"); print a[1]}')
       read -e -i "$PLC_NETMASK" -p 'PLC Netmask: ' PLC_NETMASK

       echo "connmanctl config ethernet_dead12345678_cable --ipv4 manual ${PLC_IP} ${PLC_NETMASK}"
       ;;

    2) echo "Set PLANT Network"

       PLANT_MAC=$(cat /sys/class/net/eth2/address | tr -d ':')
       PLANT_SERVICE="ethernet_${PLANT_MAC}_cable"

       PLANT_IP=$(ip addr show eth2 | grep -o "inet [0-9]*\.[0-9]*\.[0-9]*\.[0-9]*" | grep -o "[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*")
       read -e -i "$PLANT_IP" -p 'PLANT IP Address: ' PLANT_IP

       PLANT_NETMASK=$(ifconfig eth2 | awk '/netmask/{split($4,a,":"); print a[1]}')
       read -e -i "$PLANT_NETMASK" -p 'Netmask: ' PLANT_NETMASK

       PLANT_GATEWAY=$(route -n | grep 'UG[ \t]' | awk '{print $2}')
       read -e -i "$PLANT_GATEWAY" -p 'Gateway: ' PLANT_GATEWAY

       PLANT_NAMESERVERS=$(connmanctl services ${PLANT_SERVICE} |\
                awk '/Nameservers.Configuration/ {print}' |\
                grep -Po '\[\K[^]]*' ${PLANT_NAMESERVERS} | tr -d ',')

       read -e -i "$PLANT_NAMESERVERS" -p 'Nameservers: '

       echo connmanctl config ${PLANT_SERVICE} \
                       --ipv4 manual ${PLANT_IP} ${PLANT_NETMASK} ${PLANT_GATEWAY} \
                       --nameservers ${PLANT_NAMESERVERS}
       ;;

    3) echo "Select Config Files: \n\n"
       echo "Select a collect configuration"
       # set the prompt used by select, replacing "#?"
       PS3="Use number to select a file or 'stop' to cancel: "

       # allow the user to choose a file
       select filename in ./configs/*-collect.yml
       do
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

    *) break

  esac
done

set_post_config () {
  echo "Select a Post Configuration File"
  # set the prompt used by select, replacing "#?"
  PS3="Use number to select a file or 'stop' to cancel: "

  # allow the user to choose a file
  select filename in ./configs/*-post.yml
    do
      # leave the loop if the user says 'stop'
      if [[ "$REPLY" == stop ]]; then break; fi

      # complain if no file was selected, and loop to ask again
      if [[ "$filename" == "" ]]
      then
        echo "'$REPLY' is not a valid choice"
        continue
      fi

      # now we can use the selected file
      echo "$filename installed"

      # it'll ask for another unless we leave the loop
    break
  done
}


