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
            print("OLA8")
            print(data)
            sender = data["post"]["username"]
            message = data["post"]["message"]
            msg_id = data["post"]["id"]
            msg_nr = data["post"]["msg_nr"]
            time = flake.get_datetime_from_id(data["post"]["id"])
            user_knowledge = STATE["following"][sender][0]
            TIMELINE.add_message(sender, message, msg_id, msg_nr, time,
                                 user_knowledge)

            if (user_knowledge is None or msg_nr == user_knowledge + 1):
                STATE["following"][sender] = (msg_nr, msg_id)
                value = json.dumps(STATE)
                future = asyncio.run_coroutine_threadsafe(
                                    KS.set_user(USERNAME, value),
                                    LOOP)
                future.result()
            else:
                # TODO - questionar por mais informação
                pass

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
        elif 'msgs_request' in data:

            user = data["msgs_request"]["username"]
            messages_ids = data["msgs_request"]["messages"]
            messages = TIMELINE.get_user_messages(user, messages_ids)

            data = {
                "messages": messages
            }
 
            json_string = json.dumps(data) + '\n'
            writer.write(json_string.encode())

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

        json_string = json.dumps(data) + '\n'

        print(list(followers.keys()))

        for follower in followers.keys():
            print("OLA1")
            print(follower)
            try:
                try:
                    if follower not in FOLLOWERS_CONS:
                        print("OLA2")
                        FOLLOWERS_CONS[follower] = await asyncio.open_connection(
                                        followers.get(follower)[0],
                                        followers.get(follower)[1],
                                        loop=asyncio.get_event_loop())
                        print("OLA11")
                    
                    FOLLOWERS_CONS[follower][1].write(json_string.encode())
                except ConnectionRefusedError:
                    print("OLA4")
                    pass
                except UnboundLocalError:
                    # não conseguimos fazer write porque o utilizador se
                    # desconectou e a conexão guardada já n serve
                    FOLLOWERS_CONS[follower] = await asyncio.open_connection(
                                    followers.get(follower)[0],
                                    followers.get(follower)[1],
                                    loop=asyncio.get_event_loop())
                    print("OLA5")
                    FOLLOWERS_CONS[follower][1].write(json_string.encode())
            except Exception:
                print("OLA9")
                pass

        # incrementar contagem das mensagens
        STATE['msg_nr'] += 1
        value = json.dumps(STATE)
        print("OLA6")
        await KS.set_user(USERNAME, value)

    async def update_timeline_messages(self):
        outdated_follw = await KS.get_outdated_user_following(
                                  STATE["following"])

        for (follw, ip, port, user_knowledge) in outdated_follw:
            current_knowledge = STATE["following"][follw][0]

            waiting_msgs = TIMELINE.user_waiting_messages(follw)
            wanted_msgs = []

            for msg_nr in range(current_knowledge + 1, user_knowledge + 1):
                if msg_nr not in waiting_msgs:
                    wanted_msgs.append(msg_nr)

            try:
                messages = await request_messages(follw, wanted_msgs, ip, port)
                await handle_messages(messages)

            except ConnectionRefusedError:
                print("burra")
                user_followers = await KS.get_users_following_user(follw)
                for user in user_followers:
                    current_knowledge = STATE["following"][follw][0]
                    if (current_knowledge < user_knowledge):
                        info = await KS.get_user(user)
                        if info['following'][follw][0] > current_knowledge:
                            try:
                                messages = await request_messages(follw, wanted_msgs, info['ip'], info['port'])
                                await handle_messages(messages)
                                for msg in messages:
                                    wanted_msgs.remove(msg['msg_nr'])
                                    
                            except ConnectionRefusedError:
                                continue
                        else:
                            continue
                    else:
                        break


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

            STATE["following"][to_follow] = (None, 
                                             self.id_generator.__next__())
            value = json.dumps(STATE)

            await KS.set_user(USERNAME, value)

        else:
            print("It's not possible to follow %s (already followed)"
                  % to_follow)


async def handle_messages(messages):

    for msg in messages:
        sender = msg["name"]
        message = msg["message"]
        msg_id = msg["id"]
        msg_nr = msg["msg_nr"]
        time = flake.get_datetime_from_id(msg_id)
        TIMELINE.add_message(sender, message, msg_id, msg_nr, time)

    STATE["following"][sender] = (msg_nr, msg_id)
    value = json.dumps(STATE)
    await KS.set_user(USERNAME, value)

async def request_messages(user, wanted_msgs, ip, port):
    (reader, writer) = await asyncio.open_connection(ip, port, loop=LOOP)

    data = {
        "msgs_request": {
            "username": user,
            "messages": wanted_msgs
        }
    }

    json_string = json.dumps(data) + '\n'
    writer.write(json_string.encode())
    data = (await reader.readline()).strip()
    writer.close()

    json_string = data.decode()
    data = json.loads(json_string)
    return data["messages"]