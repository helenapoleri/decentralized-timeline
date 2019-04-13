import time
import socket
import configparser
import os
import argparse
import regex as re
import sys

from kademlia_server import KademliaServer
from node import Node
from consolemenu import *
from consolemenu.items import *

server = None
loop = None
NODE = None

def post_message():
    message = input("Enter Message:\n")
    NODE.post_message(message)
    
    input("Press Enter to continue...")

def follow_user():
    username = input("Enter Username: ")
    print(username)
    time.sleep(5)

def show_timeline():
    NODE.show_timeline()

    input("Press Enter to continue...")

def login():
    global NODE

    username = input("Username: ")
    try:
        state = KS.login(username)
        NODE = Node(address, port, username, state)
        print("Login com sucesso!")
        input("Press Enter to continue...")
        show_main_menu()
    except Exception as e:
        print(e)
        input("Press Enter to continue...")


def register(address, port):
    global NODE

    username = input("Username: ")
    try:
        KS.register(username)
        NODE = Node(address, port, username)
        print("Registado com sucesso!")
        show_main_menu()
    except Exception as e:
        print(e)
    

    input("Press Enter to continue...")
    # verificar se nodo existe
    # set das infooos
    #

def show_main_menu():
    menu = ConsoleMenu("Decentralized Timeline", "Main Menu")
    menu.append_item(FunctionItem("Show timeline", show_timeline))
    menu.append_item(FunctionItem("Follow user", follow_user))
    menu.append_item(FunctionItem("Post a message", post_message))
    menu.show()

def show_auth_menu(server, loop, address, port):
    menu = ConsoleMenu("Decentralized Timeline", "Authentication")
    menu.append_item(FunctionItem("Login", login))
    menu.append_item(FunctionItem("Register", register, [address, port]))
    menu.show()
    
def main(address, port):
    global KS
    
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config/configuration.ini'))

    bt_addresses_p = [address_port.split(":") for address_port in config.get("BOOTSTRAP", "INITIAL_NODES").split(",")]
    print(bt_addresses_p)
    bt_addresses = [(x, int(y)) for [x, y] in bt_addresses_p]
    print(bt_addresses)
    KS = KademliaServer(address, port)
    (server, loop) = KS.start_server(bt_addresses)

    show_auth_menu(server, loop, address, port)

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