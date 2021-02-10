#!/home/debian/prodmon/venv/bin/python3

from pylogix import PLC

comm = PLC()
comm.IPAddress = '192.168.1.50'
ret = comm.Read('Program:MainProgram.ProdCount.acc')
print(ret)
comm.Close()
