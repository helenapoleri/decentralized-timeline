import asyncio
import json
import utils.snowflake as snowflake
from datetime import datetime

from threading import Thread
from timeline import Timeline
from kademlia.network import Server

KS = None
LOOP = None
USERNAME = None
LIST_LOOP = None
TIMELINE = None
NODE = None

async def node_server(reader, writer):
    global LIST_LOOP, TIMELINE, KS

    while True:
        data = (await reader.readline()).strip()   #Payload
        if not data:
            break
        json_string = data.decode()
        print(json_string)
        data = json.loads(json_string)
        print(data)
        if "follow" in data:
            new_follower = data["follow"]["username"]
            info = await KS.get_user(USERNAME)

            if new_follower in info['followers']:
                writer.write(b'0\n')
            else:
                info["followers"].append(new_follower)
                value = json.dumps(info)
                await KS.set_user(USERNAME, value)
                writer.write(b'1\n')

        elif 'post' in data:
            sender = data["post"]["username"]
            message =  data["post"]["message"]
            msg_id =  data["post"]["id"]
            time = datetime.strptime(data["post"]["time"], '%Y-%m-%d %H:%M:%S')
            TIMELINE.add_message(sender, message, msg_id, time)

        elif 'online' in data:
            username = data['online']['username']
            NODE.add_follower_connection(username, reader, writer)

        await writer.drain()

    writer.close()

class Listener(Thread):
    
    def __init__(self, address, port):
        super(Listener, self).__init__()
        self.address = address
        self.port = port

    async def start_listener(self):
        server = await asyncio.start_server(node_server, self.address, self.port)
        await server.serve_forever()

    def run(self):
        global LIST_LOOP
        LIST_LOOP = asyncio.new_event_loop()
        #asyncio.set_event_loop(loop)
        result = LIST_LOOP.run_until_complete(self.start_listener())

class Node:
    def __init__(self, address, port, username, ks, state):   
        global KS, LOOP, USERNAME, TIMELINE, NODE

        TIMELINE = Timeline(username)
        USERNAME = username
        self.address = address
        self.port = port
        self.state = state
        self.id_generator = snowflake.generator(1,1)
        KS = ks
        LOOP = asyncio.get_event_loop()
        self.followers_cons = {} 
        # não estou a inicialializar as conexões para os followers
        # porque pensando num contexto real a maior parte das vezes um utilizador
        # vai à aplicação e não quer enviar nenhuma mensagem, pelo que criar todas
        # as conexões sempre não seria o ideal
        print("OKEY")
        self.following_cons = {}
        self.listener = Listener(self.address, self.port)
        self.listener.start()

    def get_username(self):
        return USERNAME

    async def post_message(self, message, followers):
        global USERNAME, TIMELINE
        
        msg_id = self.id_generator.__next__()
        time = snowflake.snowflake_to_datetime(msg_id)

        # add to timeline
        TIMELINE.add_message(USERNAME, message, msg_id, time)

        data = {
            "post": {
                "username": USERNAME,
                "message": message,
                "id": msg_id,
                "time": time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        json_string = json.dumps(data) + '\n'

        for follower in followers.keys():
            try:          
                try:
                    if (follower not in self.followers_cons):
                        print(followers.get(follower))
                        (reader, writer) = await asyncio.open_connection(followers.get(follower)[0], followers.get(follower)[1],
                        loop=asyncio.get_event_loop())
                        self.followers_cons[follower] = (reader, writer)

                    writer.write(json_string.encode())
                except ConnectionRefusedError:
                    pass
                except UnboundLocalError:
                    #não conseguimos fazer write porque o utilizador se desconectou e a conexão guardada já n serve
                    (reader, writer) = await asyncio.open_connection(followers.get(follower)[0], followers.get(follower)[1],
                    loop=asyncio.get_event_loop())
                    self.followers_cons[follower] = (reader, writer)
                    writer.write(json_string.encode())
            except Exception:
                pass
  

    def show_timeline(self):
        global TIMELINE
        print(TIMELINE)

    async def follow_user(self, to_follow, loop):
        global USERNAME

        my_info = await KS.get_user(USERNAME)

        if to_follow in my_info["following"]:
            print("You already follow that user!!")

        (ip, port) = await KS.get_user_ip(to_follow)

        if to_follow == USERNAME:
            print("You can't follow yourself!")
            return

        try: 
            (reader, writer) = await asyncio.open_connection(ip, port, loop=loop)
        except Exception:
            print("It's not possible to follow that user right now! (user offline)")
            return
        
        my_info["following"].append(to_follow)
        value = json.dumps(my_info)
        await KS.set_user(USERNAME, value)
        data = {
            "follow": {
                "username": USERNAME
            }
        }
        json_string = json.dumps(data) + '\n'
        writer.write(json_string.encode())
        data = (await reader.readline()).strip()
        writer.close()

        if data.decode() == '1':
            print("You followed %s successfully" % to_follow)
        else:
            print("It's not possible to follow %s (already followed)" % to_follow)