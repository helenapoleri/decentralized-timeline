import time
import socket
import configparser
import os
import argparse
import regex as re
import sys
import asyncio
import async_tasks
import logging
import threading

from Menu.menu import Menu
from Menu.item import Item
from kademlia.network import Server
from kademlia_server import KademliaServer
from node import Node
from consolemenu import *
from consolemenu.items import *

SERVER = None
LOOP = None
NODE = None
ADDRESS = None
PORT = None
KS = None

def post_message():
    message = input("Enter Message:\n")
    NODE.post_message(message)
    
    input("Press Enter to continue...")

def follow_user():
    global LOOP

    username = input("Enter username to follow: ")

    try:
        (ip, port) = KS.get_user_ip(username)
        LOOP.run_until_complete(NODE.follow_user(ip, port, LOOP, username))
    except Exception as e:
        print(e)
        input("Press Enter to continue...")

    input("Press Enter to continue...")

def build_menu():
    menu = Menu('Menu')
    menu.add_item(Item('1 - Register', register))
    return menu

def register():
    print(threading.enumerate())
    user = input('User Nickname: ')

    # loop = asyncio.get_event_loop()
    asyncio.create_task(async_tasks.register(user, ADDRESS, PORT, SERVER, KS))
    # if task is None:
    #     print("OLA")
    # else:
    #     print("OLE")

    # if loop is not None:
    #     print(type(loop))

    # loop.run_until_complete(task)
    # print("CENAS")
    return False

def show_timeline():
    NODE.show_timeline()

    input("Press Enter to continue...")

def login():
    global NODE, SERVER

    username = input("Username: ")
    try:
        state = KS.login(username)
        NODE = Node(address, port, username, SERVER, state)
        print("Login com sucesso!")
        input("Press Enter to continue...")
        show_main_menu()
    except Exception as e:
        print(e)
        input("Press Enter to continue...")




def show_main_menu():
    menu = ConsoleMenu("Decentralized Timeline", "Main Menu")
    menu.append_item(FunctionItem("Show timeline", show_timeline))
    menu.append_item(FunctionItem("Follow user", follow_user))
    menu.append_item(FunctionItem("Post a message", post_message))
    menu.show()

# def show_auth_menu(address, port):
#     menu = ConsoleMenu("Decentralized Timeline", "Authentication")
#     # menu.append_item(FunctionItem("Login", login))
#     menu.append_item(FunctionItem("Register", register, [address, port]))
#     menu.show()
    
# def register

def main(address, port):
    global KS
    global LOOP
    global ADDRESS, PORT
    global SERVER

    ADDRESS = address
    PORT = port
    print(threading.get_ident())
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config/configuration.ini'))

    bt_addresses_p = [address_port.split(":") for address_port in config.get("BOOTSTRAP", "INITIAL_NODES").split(",")]
    bt_addresses = [(x, int(y)) for [x, y] in bt_addresses_p]
    KS = KademliaServer(address, port)
    DEBUG = True
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
        
    # DEBUG
    if DEBUG:
        log = logging.getLogger('kademlia')
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)

    LOOP = asyncio.get_event_loop()
    if DEBUG:
        LOOP.set_debug(True)

    #asyncio.set_event_loop(LOOP)
    #(SERVER, LOOP) = ks.start_server(bt_addresses)
    SERVER = Server()

    print(threading.enumerate())

    LOOP.run_until_complete(SERVER.listen(port))
    LOOP.run_until_complete(SERVER.bootstrap(bt_addresses))

    m = build_menu()

    print(threading.enumerate())
    asyncio.ensure_future(async_tasks.show_auth_menu(m))
    print(1)
    print(threading.enumerate())
    print(2)
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