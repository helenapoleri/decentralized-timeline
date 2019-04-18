import time
import socket
import configparser
import os
import argparse
import regex as re
import sys
import asyncio
import logging
import threading
import async_tasks

from Menu.menu import Menu
from Menu.item import Item
from kademlia.network import Server
from kademlia_server import KademliaServer
from node import Node

SERVER = None
LOOP = None
NODE = None
ADDRESS = None
PORT = None
KS = None

def build_menu():
    menu = Menu('Menu')
    menu.add_item(Item('1 - Register', register))
    return menu

def register():
    print("OLA")
    if LOOP == asyncio.get_event_loop():
        print("Caralho2")
    print(threading.enumerate())
    user = input('User Nickname: ')

    task = asyncio.create_task(async_tasks.register(user, ADDRESS, PORT, SERVER, KS))

    return False

def main(address, port):
    global KS
    global LOOP
    global ADDRESS
    global PORT
    global SERVER

    ADDRESS = address
    PORT = port
    
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config/configuration.ini'))

    bt_addresses_p = [address_port.split(":") for address_port in config.get("BOOTSTRAP", "INITIAL_NODES").split(",")]
    bt_addresses = [(x, int(y)) for [x, y] in bt_addresses_p]

    KS = KademliaServer(address, port)
    (SERVER, LOOP) = KS.start_server(bt_addresses)

    if LOOP == asyncio.get_event_loop():
        print("Não entendo")

    m = build_menu()
    asyncio.ensure_future(async_tasks.show_auth_menu(m, LOOP))

    try:
        print("Hello")
        LOOP.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        SERVER.stop()
    LOOP.close()

if __name__ == "__main__":

    ap = argparse.ArgumentParser()
    ap.add_argument('-a', '--address', type=str, help="Listen IP Address", default="localhost", required=True)
    ap.add_argument('-p', '--port', type=int, help="Listen port", default=2222, required=True)
    args = vars(ap.parse_args())

    address = args.get("address")
    port = args.get("port")

    if not re.match(r'^(\d{1,3})(\.\d{1,3}){3}$', address) \
        and address != "localhost" :
        sys.stderr.write('Address format is not valid.')
        sys.exit()
        
    main(address, port)