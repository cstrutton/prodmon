#!/home/debian/prodmon/venv/bin/python3

from pylogix import PLC

comm = PLC()
comm.IPAddress = '192.168.100.1'
ret = comm.Read('Program:MainProgram.ProdCountLine.acc')
print(ret)
comm.Close()
