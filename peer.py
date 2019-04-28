import time
import socket
import configparser
import os
import argparse
import regex as re
import sys
import asyncio
import settings
from utils.prompt import Prompt

from threading import Thread
from kademlia_server import KademliaServer
from node import Node
from menu.menu import Menu
from menu.menu_item import MenuItem

SERVER = None
LOOP = None
NODE = None
PROMPT = None
KS = None
AUTH_MENU = None
MAIN_MENU = None

async def post_message():
    global KS, NODE, PROMPT

    message = await PROMPT("Enter Message: \n")

    try:
        followers = await KS.get_user_followers(NODE.get_username())
    except Exception as e:
        print(e)

    await NODE.post_message(message, followers)
    

async def follow_user():
    global LOOP, KS, NODE, PROMPT

    username = await PROMPT("Enter username: ")

    try:
        (ip, port) = await KS.get_user_ip(username)
        await NODE.follow_user(ip, port, LOOP, username)
    except Exception as e:
        print(e)
        return


def show_timeline():
    global MAIN_MENU, NODE

    NODE.show_timeline()

async def login():
    global NODE, SERVER, KS, PROMPT

    username = await PROMPT("Username: ")

    try:
        state = await KS.login(username)
        NODE = Node(address, port, username, SERVER, state)
        print("Login com sucesso!")
        
        return 1

    except Exception as e:
        print(e)
        return 0

async def register(address, port):
    global NODE, KS, SERVER, PROMPT

    username = await PROMPT("Username: ")

    try:
        await KS.register(username)
        NODE = Node(address, port, username, SERVER)
        print("Registado com sucesso!")
        return 1
        
    except Exception as e:
        print(e)
        
        return 0

def build_main_menu():
    menu = Menu("Main Menu")

    menu.append_item(MenuItem("Show timeline", show_timeline))
    menu.append_item(MenuItem("Follow user", follow_user))
    menu.append_item(MenuItem("Post a message", post_message))
    return menu

def build_auth_menu(address, port):
    menu = Menu("Authentication")
    menu.append_item(MenuItem("Login", login))
    menu.append_item(MenuItem("Register", register, address, port))

    return menu

def run_main_menu():
    global MAIN_MENU
    MAIN_MENU = build_main_menu()
    while True:
        MAIN_MENU.execute()
        input("press enter to continue...")

def run_auth_menu():
    global AUTH_MENU
    AUTH_MENU = build_auth_menu(address, port)
    while True:
        auth_successful = AUTH_MENU.execute()
        input("press enter to continue..")
        if auth_successful == 1:
            run_main_menu()

def main(address, port):
    global KS, LOOP, SERVER, PROMPT
    
    bt_addresses_p = [address_port.split(":") for address_port in settings.BOOTSTRAP_NODES.split(",")]
    bt_addresses = [(x, int(y)) for [x, y] in bt_addresses_p]
    KS = KademliaServer(address, port)
    (SERVER, LOOP) = KS.start_server(bt_addresses)

    PROMPT = Prompt(LOOP)

    Thread(target=LOOP.run_forever, daemon=True).start()
    
    run_auth_menu()

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