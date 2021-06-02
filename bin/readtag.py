#!/home/debian/prodmon/venv/bin/python3
import sys
from pylogix import PLC


def read_tags(ip, slot=0):
    from pylogix import PLC

    with PLC() as comm:
        comm.IPAddress = ip
        comm.ProcessorSlot = slot

        with open("./readtaglist.txt", 'r') as infile:
            for line in infile:
                print(comm.Read(line.strip()))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        read_tags(sys.argv[1])
