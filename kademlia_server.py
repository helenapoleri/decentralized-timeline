import logging
import asyncio
import sys
from kademlia.network import Server

DEBUG = True

def start_server(port, bootstrap_nodes): 
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # DEBUG
    if DEBUG:
        log = logging.getLogger('kademlia')
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)

    server = Server()
    server.listen(port)

    loop = asyncio.get_event_loop()
    if DEBUG:
        loop.set_debug(True)
  
    # bootstrap_node = (bt_Ip, int(bt_port))
    loop.run_until_complete(server.bootstrap(bootstrap_nodes))

    return (server, loop)