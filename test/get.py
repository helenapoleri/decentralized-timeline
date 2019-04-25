import logging
import asyncio
import sys

from kademlia.network import Server

if len(sys.argv) != 5:
    print("Usage: python get.py <bootstrap node> <bootstrap port> <listen port> <key>")
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
bootstrap_node = (sys.argv[1], int(sys.argv[2]))
loop.run_until_complete(server.bootstrap([bootstrap_node]))
result = loop.run_until_complete(server.get(sys.argv[4]))

print("Get result:", result)
print(server.bootstrappable_neighbors())
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    server.stop()
loop.close()

