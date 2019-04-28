import asyncio
import json
import utils.flake as flake
from datetime import datetime

from numpy.random import choice
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
FOLLOWERS_CONS = None
REDIRECT_CONS = None

async def node_server(reader, writer):
    global LIST_LOOP, TIMELINE, KS, STATE, FOLLOWERS_CONS, LOOP

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
            elif len(STATE['followers']) > 2:
                followers = await KS.get_user_followers(USERNAME)
                usernames = list(followers.keys())
                weights = [len(z) for (y, w, z) in followers.values()]
                # Invert weights -> less probable if less followers
                weights = [1.0 / (w+.001) for w in weights]
                sum_weights = sum(weights)
                # Normalization
                weights = [w / sum_weights for w in weights]

                draw_followers = choice(usernames, 1, p=weights)
                draw_cons = []

                for flw in draw_followers:
                    (r, w) = await asyncio.open_connection(
                        followers.get(flw)[0],
                        followers.get(flw)[1],
                        loop=asyncio.get_event_loop())
                    draw_cons.append((r, w))

                data = {
                    "redirect": {
                        "from": USERNAME,
                        "to": new_follower
                    }
                }

                json_string = json.dumps(data) + '\n'

                for (r, w) in draw_cons:
                    w.write(json_string.encode())

                # TODO: Wait for responses, can they be negative? (ex: person
                # can't redirect messages)

                writer.write(b'1\n')
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
            TIMELINE.add_message(sender, message, msg_id, msg_nr, time)

            STATE["following"][sender] = (msg_nr, msg_id)
            value = json.dumps(STATE)
            future = asyncio.run_coroutine_threadsafe(
                                KS.set_user(USERNAME, value),
                                LOOP)
            future.result()

            # Redirect messages if needed
            if sender in STATE["redirect"]:
                for to_redirect in STATE["redirect"][sender]:

                    if to_redirect not in REDIRECT_CONS:
                        # GET HIS INFO (ADDRESS, PORT)
                        future = asyncio.run_coroutine_threadsafe(
                                KS.get_user(to_redirect),
                                LOOP)
                        result = future.result()

                        # OPEN CONNECTION
                        REDIRECT_CONS[to_redirect] = await \
                            asyncio.open_connection(
                                    result["ip"],
                                    result["port"],
                                    loop=asyncio.get_event_loop())

                    (r, w) = REDIRECT_CONS[to_redirect]

                    w.write((json.dumps(data) + '\n').encode())

        elif 'online' in data:
            username = data['online']['username']
            NODE.add_follower_connection(username, reader, writer)

        elif 'redirect' in data:
            org = data["redirect"]["from"]
            dst = data["redirect"]["to"]

            if org in STATE["redirect"]:
                STATE["redirect"].get(org).append(dst)
            else:
                STATE["redirect"][org] = [dst]

            value = json.dumps(STATE)
            future = asyncio.run_coroutine_threadsafe(
                                KS.set_user(USERNAME, value),
                                LOOP)
            future.result()

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
        global FOLLOWERS_CONS, REDIRECT_CONS

        TIMELINE = Timeline(username)
        USERNAME = username
        STATE = state
        KS = ks
        LOOP = asyncio.get_event_loop()
        self.address = address
        self.port = port
        self.id_generator = flake.generator(self.port)
        FOLLOWERS_CONS = {}
        REDIRECT_CONS = {}
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
        global USERNAME, TIMELINE, STATE, FOLLOWERS_CONS

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

        # incrementar contagem das mensagens
        STATE['msg_nr'] += 1

        json_string = json.dumps(data) + '\n'

        for follower in followers.keys():
            try:
                try:
                    if follower not in FOLLOWERS_CONS:
                        (reader, writer) = await asyncio.open_connection(
                                        followers.get(follower)[0],
                                        followers.get(follower)[1],
                                        loop=asyncio.get_event_loop())

                    FOLLOWERS_CONS[follower] = (reader, writer)
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
                    FOLLOWERS_CONS[follower] = (reader, writer)
                    writer.write(json_string.encode())
            except Exception:
                pass

    def update_timeline_messages(self):
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

            STATE["following"][to_follow] = (None, self.id_generator.__next__())
            value = json.dumps(STATE)

            await KS.set_user(USERNAME, value)

        else:
            print("It's not possible to follow %s (already followed)"
                  % to_follow)
