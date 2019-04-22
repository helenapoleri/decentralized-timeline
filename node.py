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

SERVER = None
USERNAME = None
LIST_LOOP = None
TIMELINE = None

async def node_server(reader, writer):
    global LIST_LOOP, TIMELINE

    while True:
        data = await reader.read(100)  # Max number of bytes to read
        if not data:
            break
        json_string = data.decode()
        data = json.loads(json_string)
        print(data)
        if "follow" in data:
            new_follower = data["follow"]["username"]
            result = await SERVER.get(USERNAME)
            info = json.loads(result)

            if new_follower in info['followers']:
                writer.write(b'0')
            else:
                info["followers"].append(new_follower)
                value = json.dumps(info)
                await SERVER.set(USERNAME, value)
                writer.write(b'1')

        elif 'post' in data:
            sender = data["post"]["username"]
            message =  data["post"]["message"]
            TIMELINE.add_message(sender, message)

        await writer.drain()

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
        #loop = asyncio.get_event_loop()
        server = await asyncio.start_server(node_server, self.address, self.port)
        await server.serve_forever()

    def run(self):
        global LIST_LOOP

        LIST_LOOP = asyncio.new_event_loop()
        #asyncio.set_event_loop(loop)
        result = LIST_LOOP.run_until_complete(self.start_listener())

class Node:
    def __init__(self, address, port, username, server, state=None):   
        global SERVER, USERNAME, TIMELINE

        TIMELINE = Timeline(username)
        USERNAME = username
        self.address = address
        self.port = port
        SERVER = server
        self.connections = {} # ainda n sei bem como é que vai ser
        self.listener = Listener(self.address, self.port, self.connections)
        self.listener.start()

    def get_username(self):
        return USERNAME

    async def post_message(self, message, followers):
        global USERNAME, TIMELINE
        
        # add to timeline
        TIMELINE.add_message(USERNAME, message)
        # increment vetor clock
        # create message
        # send message
        print("ola")
        print(followers)
        print(followers.values())
        for follower in followers.keys():
            if follower not in self.connections:
                print(followers.get(follower))
                (reader, writer) = await asyncio.open_connection(followers.get(follower)[0], followers.get(follower)[1],
                loop=asyncio.get_event_loop())
                self.connections[follower] = (reader, writer)

            (reader, writer) = self.connections.get(follower)
            data = {
                "post": {
                    "username": USERNAME,
                    "message": message
                }
            }
            json_string = json.dumps(data)
            writer.write(json_string.encode())
                

    def show_timeline(self):
        global TIMELINE
        print(TIMELINE)

    async def follow_user(self, ip, port, loop, to_follow):
        global USERNAME

        if to_follow == USERNAME:
            print("You can't follow yourself!")
            return

        try: 
            (reader, writer) = await asyncio.open_connection(ip, port,
            loop=loop)
        except Exception:
            print("It's not possible to follow that user right now! (user offline)")
            return
        
        data = {
            "follow": {
                "username": USERNAME
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