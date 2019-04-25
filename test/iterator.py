import os
import asyncio

previousPort = 8469
for port in range(8480, 8520):
    os.system('python3 set.py localhost ' + str(8469) + ' ' + str(port) + ' ' + str(port-8000) + ' '  + str(port-7000) + ' &')
