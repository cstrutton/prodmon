#!/home/debian/prodmon/venv/bin/python3
'''
Get the tag list from the PLC
This will fetch all the controller and program
scoped tags from the PLC.  In the case of
Structs (UDT's), it will not give you the makeup
of each  tag, just main tag names.
'''
from pylogix import PLC

with PLC() as comm:
    comm.IPAddress = '192.168.1.50'
    tags = comm.GetTagList()
    
    for t in tags.Value:
        print(t.TagName, t.DataType)

