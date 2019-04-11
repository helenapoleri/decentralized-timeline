import logging
import asyncio
import sys
import time

from kademlia.network import Server

if len(sys.argv) != 6:
    print("Usage: python set.py <bootstrap node> <bootstrap port> <listen-port> <key> <value>")
    sys.exit(1)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

loop = asyncio.get_event_loop()
loop.set_debug(True)

server = Server()
loop.run_until_complete(server.listen(int(sys.argv[3])))


print("ole")
print(server.bootstrappable_neighbors())
# try:
#     loop.run_forever()
# except KeyboardInterrupt:
#     pass
# finally:
#     server.stop()
# loop.close()

loop.run_until_complete(server.set(sys.argv[4], sys.argv[5]))
print(server.bootstrappable_neighbors())
try:
    loop.run_forever()
        
except KeyboardInterrupt:
    pass
finally:
    server.stop()
loop.close()