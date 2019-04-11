import time
import socket
import configparser
import os
import argparse
import regex as re
import sys

from consolemenu import *
from consolemenu.items import *

server = None
loop = None

def post_message():
    message = input("Enter Message:\n")
    #node.post_message(message)

def follow_user():
    username = input("Enter Username: ")
    print(username)
    time.sleep(5)

def show_timeline():
    print("timeline")
    time.sleep(5)

def login():
    pass

def register():
    pass

def show_main_menu():
    menu = ConsoleMenu("Decentralized Timeline", "Main Menu")
    menu.append_item(FunctionItem("Show timeline", show_timeline))
    menu.append_item(FunctionItem("Follow user", follow_user))
    menu.append_item(FunctionItem("Post a message", post_message))
    menu.show()

def show_auth_menu(server, loop):
    menu = ConsoleMenu("Decentralized Timeline", "Authentication")
    menu.append_item(FunctionItem("Login", login))
    menu.append_item(FunctionItem("Register", register))
    menu.show()
    
def main(address, port):

    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config/configuration.ini'))

    ports = [int(address_port.split(":")[1]) for address_port in config.get("BOOTSTRAP", "INITIAL_NODES").split(",")]
    
    #(server, loop) = kademlia_server.start_server(port, bootstrap_nodes)
    show_auth_menu(server, loop)

if __name__ == "__main__":

    ap = argparse.ArgumentParser()
    ap.add_argument('-a', '--address', type=str, help="Listen IP Address", default="localhost", required=True)
    ap.add_argument('-p', '--port', type=int, help="Listen port", default=2222, required=True)
    ap.add_argument('-u', '--user', type=str, help="Username", required=True)
    args = vars(ap.parse_args())

    address = args.get("address")
    port = args.get("port")

    if not re.match(r'^(\d{1,3})(\.\d{1,3}){3}$', address) \
        and address != "localhost" :
        sys.stderr.write('Address format is not valid.')
    else:
        sys.exit()
    
    main(address, port)