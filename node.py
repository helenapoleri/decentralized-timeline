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
            msg_nr = data["post"]["msg_nr"]
            time = flake.get_datetime_from_id(data["post"]["id"])
            user_knowledge = STATE["following"][sender][0]
            TIMELINE.add_message(sender, message, msg_id, msg_nr, time, user_knowledge)

            if (user_knowledge == None or msg_nr == user_knowledge + 1):
                STATE["following"][sender] = (msg_nr, msg_id)
                value = json.dumps(STATE)
                future = asyncio.run_coroutine_threadsafe(
                                    KS.set_user(USERNAME, value),
                                    LOOP)
                future.result()
            else:
                # TODO - questionar por mais informação
                pass

        elif 'online' in data:
            username = data['online']['username']
            NODE.add_follower_connection(username, reader, writer)

        elif 'msgs_request' in data:
            print(0)
            user = data["msgs_request"]["username"]
            print(1)
            messages_ids = data["msgs_request"]["messages"]
            print(2)
            messages = TIMELINE.get_user_messages(user, messages_ids)

            data = {
                "messages": messages
            }
            print(3)
            json_string = json.dumps(data) + '\n'
            print(4)
            writer.write(json_string.encode())
            print(5)
            

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
        global USERNAME, TIMELINE, STATE

        msg_id = self.id_generator.__next__()
        time = flake.get_datetime_from_id(msg_id)

        # add to timeline
        TIMELINE.add_message(USERNAME, message, msg_id, STATE['msg_nr'], time)

        data = {
            "post": {
                "username": USERNAME,
                "message": message,
                "msg_nr": STATE['msg_nr'],
                "id": msg_id
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

        # incrementar contagem das mensagens
        STATE['msg_nr'] += 1
        value = json.dumps(STATE)
        await KS.set_user(USERNAME, value)

    async def update_timeline_messages(self):
        print(0)
        outdated_follw = await KS.get_outdated_user_following(STATE["following"])
        print(1)
        for (follw, ip, port, user_knowledge) in outdated_follw:
            print(2)
            current_knowledge = STATE["following"][follw][0]
            try:
                print(3)
                (reader, writer) = await asyncio.open_connection(ip, port, loop=LOOP)
                print(4)
                print(follw)
                waiting_msgs = TIMELINE.user_waiting_messages(follw)
                print(5)
                wanted_msgs = []
                print(6)
                for msg_nr in range(current_knowledge + 1, user_knowledge + 1):
                    print(7)
                    if msg_nr not in waiting_msgs:
                        print(msg_nr)
                        wanted_msgs.append(msg_nr)

                data = {
                    "msgs_request": {
                        "username": follw,
                        "messages": wanted_msgs
                    }
                }
                print(8)
                json_string = json.dumps(data) + '\n'
                print(9)
                writer.write(json_string.encode())
                print(10)
                data = (await reader.readline()).strip()
                print(11)
                writer.close()
                print(12)
                json_string = data.decode()
                data = json.loads(json_string)
                messages = data["messages"]
                print(13)
                await handle_messages(messages)
                print(14)


            except ConnectionRefusedError:
                pass
            # tentar entrar em contacto com esses following
            # se conseguir:
                # Verificar as mensagens que n tenho
                # Enviar um pedido com o id dessas mensagens
            # se não conseguir:
                # ir contactando todos os vizinhos de forma a aumentar o meu conhecimento


    def show_timeline(self):
        global TIMELINE

        print(TIMELINE)

    async def follow_user(self, to_follow, loop):
        global USERNAME, STATE

        print(0)
        if to_follow in STATE["following"]:
            print("You already follow that user!!")
        print(1)
        (ip, port) = await KS.get_user_ip(to_follow)
        print(2)
        if to_follow == USERNAME:
            print("You can't follow yourself!")
            return
        print(3)
        try:
            (reader, writer) = await asyncio.open_connection(
                               ip, port, loop=loop)
        except Exception:
            print("It's not possible to follow that user right now!"
                  "(user offline)")
            return
        print(4)
        data = {
            "follow": {
                "username": USERNAME
            }
        }
        print(5)
        json_string = json.dumps(data) + '\n'
        writer.write(json_string.encode())
        print(6)
        data = (await reader.readline()).strip()
        print(7)
        writer.close()

        if data.decode() == '1':
            print("You followed %s successfully" % to_follow)
            print(8)
            STATE["following"][to_follow] = (None, self.id_generator.__next__())
            value = json.dumps(STATE)
            print(9)
            await KS.set_user(USERNAME, value)
            print(10)
        else:
            print("It's not possible to follow %s (already followed)"
                  % to_follow)


async def handle_messages(messages):

    for msg in messages:
        print(15)
        sender = msg["name"]
        message = msg["message"]
        msg_id = msg["id"]
        msg_nr = msg["msg_nr"]
        time = flake.get_datetime_from_id(msg_id)
        TIMELINE.add_message(sender, message, msg_id, msg_nr, time)

    print(16)
    STATE["following"][sender] = (msg_nr, msg_id)
    value = json.dumps(STATE)
    await KS.set_user(USERNAME, value)
    print(17)