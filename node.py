import asyncio
import json
import utils.flake as flake
from datetime import datetime

from threading import Thread
from timeline import Timeline
from kademlia.network import Server

KS = None
LOOP = None
USERNAME = None
STATE = None
LIST_LOOP = None
TIMELINE = None
NODE = None

async def node_server(reader, writer):
    global LIST_LOOP, TIMELINE, KS, STATE

    while True:
        data = (await reader.readline()).strip()

        if not data:
            break

        json_string = data.decode()
        data = json.loads(json_string)

        if "follow" in data:
            new_follower = data["follow"]["username"]

            if new_follower in STATE['followers']:
                writer.write(b'0\n')
            else:
                STATE["followers"].append(new_follower)
                value = json.dumps(STATE)
                future = asyncio.run_coroutine_threadsafe(
                                 KS.set_user(USERNAME, value),
                                 LOOP)
                future.result()
                writer.write(b'1\n')
        elif 'post' in data:
            sender = data["post"]["username"]
            message = data["post"]["message"]
            msg_id = data["post"]["id"]
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
        server = await asyncio.start_server(node_server,
                                            self.address,
                                            self.port)
        await server.serve_forever()

    def run(self):
        global LIST_LOOP
        LIST_LOOP = asyncio.new_event_loop()
        result = LIST_LOOP.run_until_complete(self.start_listener())


class Node:
    def __init__(self, address, port, username, ks, state):
        global KS, LOOP, USERNAME, TIMELINE, NODE, STATE

        TIMELINE = Timeline(username)
        USERNAME = username
        STATE = state
        KS = ks
        LOOP = asyncio.get_event_loop()
        self.address = address
        self.port = port
        self.id_generator = flake.generator(self.port)
        self.followers_cons = {}
        # não estou a inicialializar as conexões para os followers
        # porque pensando num contexto real a maior parte das vezes
        # um utilizador vai à aplicação e não quer enviar nenhuma
        # mensagem, pelo que criar todas as conexões sempre não
        # seria o ideal
        self.following_cons = {}
        self.listener = Listener(self.address, self.port)
        self.listener.start()

    def get_username(self):
        global USERNAME

        return USERNAME

    def get_state(self):
        global STATE

        return STATE

    async def post_message(self, message, followers):
        global USERNAME, TIMELINE

        msg_id = self.id_generator.__next__()
        time = datetime.strptime(flake.get_time_from_id(msg_id),
                                 "%a %b %d %H:%M:%S %Y")

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
                    if follower not in self.followers_cons:
                        (reader, writer) = await asyncio.open_connection(
                                        followers.get(follower)[0],
                                        followers.get(follower)[1],
                                        loop=asyncio.get_event_loop())

                    self.followers_cons[follower] = (reader, writer)
                    writer.write(json_string.encode())
                except ConnectionRefusedError:
                    pass
                except UnboundLocalError:
                    # não conseguimos fazer write porque o utilizador se
                    # desconectou e a conexão guardada já n serve
                    (reader, writer) = await asyncio.open_connection(
                                    followers.get(follower)[0],
                                    followers.get(follower)[1],
                                    loop=asyncio.get_event_loop())
                    self.followers_cons[follower] = (reader, writer)
                    writer.write(json_string.encode())
            except Exception:
                pass

    def show_timeline(self):
        global TIMELINE

        print(TIMELINE)

    async def follow_user(self, to_follow, loop):
        global USERNAME, STATE

        if to_follow in STATE["following"]:
            print("You already follow that user!!")

        (ip, port) = await KS.get_user_ip(to_follow)

        if to_follow == USERNAME:
            print("You can't follow yourself!")
            return

        try:
            (reader, writer) = await asyncio.open_connection(
                               ip, port, loop=loop)
        except Exception:
            print("It's not possible to follow that user right now!"
                  "(user offline)")
            return

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

            STATE["following"].append(to_follow)
            value = json.dumps(STATE)

            await KS.set_user(USERNAME, value)
        else:
            print("It's not possible to follow %s (already followed)"
                  % to_follow)
