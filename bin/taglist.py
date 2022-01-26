#!/home/debian/prodmon/venv/bin/python3
import sys

'''
Get the tag list from the PLC
This will fetch all the controller and program
scoped tags from the PLC.  In the case of
Structs (UDT's), it will not give you the makeup
of each  tag, just main tag names.
'''


def get_tag_list(ip, slot=0):
    from pylogix import PLC

    with PLC() as comm:
        comm.IPAddress = ip
        comm.ProcessorSlot = slot
        tags = comm.GetTagList()

    for t in tags.Value:
        print(t.TagName, t.DataType)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        get_tag_list(sys.argv[1])
    else:
        get_tag_list("10.4.42.135", 3)
