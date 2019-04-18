import asyncio
import threading

from kademlia_server import KademliaServer
from consolemenu import *
from consolemenu.items import *

#mostrar o menu

async def show_auth_menu(menu, loop):
    loop2 = asyncio.get_event_loop()
    if loop2 == loop:
        print("Caralho")
    menu.draw()
    while True:
        # msg = yield from queue.get()
        msg = input("Opção: ")
        if not msg == '\n' and menu.run(int(msg)):
            break
        menu.draw()
    loop.call_soon_threadsafe(loop.stop)


async def register(username, address, port, server,ks):

    print(threading.enumerate())
    print("xim")
    try:

        await ks.register(username)
        #NODE = Node(address, port, username, SERVER)
        print("Registado com sucesso!")
        #show_main_menu()
    except Exception as e:
        print(e)
    
    input("Press Enter to continue...")
    # verificar se nodo existe
    # set das infooos
    #

# async def show_auth_menu(address, port, ks, loop):
#     menu = ConsoleMenu("Decentralized Timeline", "Authentication")
#     #menu.append_item(FunctionItem("Login", login))
#     menu.append_item(FunctionItem("Register", register1, [address, port, ks, loop]))
#     menu.show()

#register

