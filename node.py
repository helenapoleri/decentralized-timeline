import asyncio
import json

from threading import Thread
from timeline import Timeline
from kademlia.network import Server

'''class EchoProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        json_string = data.decode()
        data = json.loads(json_string)
        print(data)
        # Recebeu (connection request) 
        # existe ou nao como follower
        # se sim:
        ## adicionar o self.transport às conexões

        ## adicionar conexao às conexoes
        # se nao:
        ## 

        #self.transport.write(data)
'''

async def node_server(reader, writer):

    while True:
        data = await reader.read(100)  # Max number of bytes to read
        if not data:
            break
        json_string = data.decode()
        data = json.loads(json_string)
        if "follow" in data:
            new_follower = data["follow"]["username"]
            #result = self.loop.run_until_complete(self.server.get(USERNAME))
            print(data)
            print(new_follower)
        writer.write(b'1')
        await writer.drain()  # Flow control, see later
    writer.close()

class Listener(Thread):
    
    def __init__(self, address, port, connections):
        super(Listener, self).__init__()
        self.address = address
        self.port = port
        self.connections = connections
        
    '''async def start_listener(self):
        loop = asyncio.get_event_loop()
        server = await loop.create_server(EchoProtocol, self.address, self.port)
        await server.serve_forever()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.start_listener())
    '''

    async def start_listener(self):
        loop = asyncio.get_event_loop()
        server = await asyncio.start_server(node_server, self.address, self.port)
        await server.serve_forever()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.start_listener())

class Node:
    def __init__(self, address, port, username, state=None):        
        self.timeline = Timeline(username)
        self.username = username
        self.address = address
        self.port = port
        self.server = None
        self.connections = {} # ainda n sei bem como é que vai ser
        self.listener = Listener(self.address, self.port, self.connections)
        self.listener.start()

    def post_message(self, message):
        
        # add to timeline
        self.timeline.add_message(self.username, message)
        # increment vetor clock
        # create message
        # send message

    def show_timeline(self):
        print(self.timeline)

    async def follow_user(self, ip, port, loop, to_follow):

        if to_follow == self.username:
            print("You can't follow yourself!")
            return

        try: 
            reader, writer = await asyncio.open_connection(ip, port,
            loop=loop)
        except Exception:
            print("It's not possible to follow that user right now! (user offline)")
            return
        
        data = {
            "follow": {
                "username": self.username
            }
        }
        json_string = json.dumps(data)
        writer.write(json_string.encode())
        data = await reader.read(100)
        writer.close()

        if data.decode() == '1':
            print("You followed %s successfully" % to_follow)
        else:
            print("It's not possible to follow %s (already followed)" % to_follow)