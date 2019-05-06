import asyncio
import json
import utils.flake as flake
from datetime import datetime
import settings

from numpy.random import choice
from threading import Thread
from timeline import Timeline
from kademlia.network import Server

HIERARCHY_BASELINE = settings.HIERARCHY_BASELINE
REDIRECT_USERS = settings.REDIRECT_USERS
KS = None
LOOP = None
USERNAME = None
STATE = None
LIST_LOOP = None
TIMELINE = None
NODE = None
FOLLOWERS_CONS = None
REDIRECT_CONS = None

async def send_message_to_user(user, ip, port, message,
                               established_connections):
    res = True
    try:
        try:
            established_connections[user] = await asyncio.open_connection(
                ip, port, loop=asyncio.get_event_loop())
            
            established_connections[user][1].write(message.encode())
            await established_connections[user][1].drain()
        except ConnectionResetError:
            # não conseguimos fazer write porque o utilizador se
            # desconectou e a conexão guardada já n serve
            established_connections[user] = await asyncio.open_connection(
                            ip,
                            port,
                            loop=asyncio.get_event_loop())
            
            established_connections[user][1].write(message.encode())
            await established_connections[user][1].drain()
        except Exception as e:
            pass
    except Exception as e:
        print(e)
        res = False
    
    return res

async def send_message_to_users(users, message, established_connections):
    usernames = list(users.keys())
    tasks = [send_message_to_user(user, users[user][0], users[user][1],
             message, established_connections) for user in usernames]
    finished = await asyncio.gather(*tasks)

    true_users = []
    false_users = []
    for i in range(len(finished)):
        if finished[i] is True:
            true_users.append(usernames[i])
        else:
            false_users.append(usernames[i])
    return true_users, false_users


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
                await writer.drain()
            elif len(STATE['followers']) >= HIERARCHY_BASELINE:
                
                future = asyncio.run_coroutine_threadsafe(
                                 KS.get_location_and_followers(STATE['followers']),
                                 LOOP)
                followers = future.result()

                data = {
                    "redirect": {
                        "from": USERNAME,
                        "to": new_follower
                    }
                }

                json_string = json.dumps(data) + '\n'

                users = dict(followers)
                usernames = list(users.keys())
                weights = [len(z) for (y, w, z) in users.values()]
                weights = [1.0 / (w+.001) for w in weights]
                sum_weights = sum(weights)
                weights = [w / sum_weights for w in weights]
                users_weights = {}

                for username, weight in zip(usernames, weights):
                    users_weights[username] = weight

                redirectors = 0
                while redirectors < REDIRECT_USERS:
                    diff = REDIRECT_USERS - redirectors
                    draw_followers = choice(list(users_weights.keys()), diff,
                                            p=list(users_weights.values()))
                    draw_followers = {user: users[user][0:2]
                                      for user in draw_followers}

                    draw_cons = {}

                    success, insuccess = await send_message_to_users(
                        draw_followers, json_string, draw_cons)
                    redirectors += len(success)
                    for user in [*success, *insuccess]:
                        users_weights.pop(user)

                writer.write(b'1\n')
                await writer.drain()
            else:
                STATE["followers"].append(new_follower)
                value = json.dumps(STATE)

                future = asyncio.run_coroutine_threadsafe(
                                 KS.set_user(USERNAME, value),
                                 LOOP)
                future.result()
                writer.write(b'1\n')
                await writer.drain()

        elif 'post' in data:
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
            elif msg_nr > user_knowledge + 1:
                waiting_msgs = TIMELINE.user_waiting_messages(sender)
                wanted_msgs = []

                for msg_id in range(user_knowledge + 1, msg_nr):
                    if msg_id not in waiting_msgs:
                        wanted_msgs.append(msg_id)

                    messages = await request_messages(sender,
                                                      wanted_msgs,
                                                      reader=reader,
                                                      writer=writer)
                    if messages != []:
                        await handle_messages(messages)

            # Redirect messages if needed
            json_string = json.dumps(data) + '\n'
            if sender in STATE["redirect"]:

                future = asyncio.run_coroutine_threadsafe(
                    KS.get_location_and_followers(STATE["redirect"][sender]),
                    LOOP)
                redirects = future.result()

                await send_message_to_users(redirects, json_string,
                                            REDIRECT_CONS)

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
        self.server = None

    def close_listener(self):
        self.server.close()

    async def start_listener(self):
        self.server = await asyncio.start_server(node_server,
                                                 self.address,
                                                 self.port)

        await self.server.serve_forever()

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
        self.listener.daemon = True
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

        await send_message_to_users(followers, json_string, FOLLOWERS_CONS)

        # incrementar contagem das mensagens
        STATE['msg_nr'] += 1
        value = json.dumps(STATE)

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
                messages = await request_messages(follw, wanted_msgs, ip=ip,
                                                  port=port)
                if messages != []:
                    await handle_messages(messages)
            except ConnectionRefusedError:
                user_followers = await KS.get_users_following_user(follw)
                for user in user_followers:
                    current_knowledge = STATE["following"][follw][0]
                    if (current_knowledge < user_knowledge):
                        info = await KS.get_user(user)
                        if info['following'][follw][0] > current_knowledge:
                            try:
                                messages = await request_messages(
                                    follw, wanted_msgs, ip=info['ip'],
                                    port=info['port'])
                                if messages != []:
                                    await handle_messages(messages)
                                for msg in messages:
                                    wanted_msgs.remove(msg['msg_nr'])
                                    
                            except ConnectionRefusedError:
                                continue
                        else:
                            continue
                    else:
                        break

    def logout(self):
        self.listener.close_listener()

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
        await writer.drain()

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

    # Redirect messages if needed
    json_string = json.dumps(msg) + '\n'
    if sender in STATE["redirect"]:

        future = asyncio.run_coroutine_threadsafe(
            KS.get_location_and_followers(STATE["redirect"][sender]),
            LOOP)
        redirects = future.result()

        await send_message_to_users(redirects, json_string, REDIRECT_CONS)

    STATE["following"][sender] = (msg_nr, msg_id)
    value = json.dumps(STATE)
    await KS.set_user(USERNAME, value)

async def request_messages(user, wanted_msgs, ip=None, port=None,
                           reader=None, writer=None):
    if reader is None and writer is None:
        (reader, writer) = await asyncio.open_connection(ip, port, loop=LOOP)

    data = {
        "msgs_request": {
            "username": user,
            "messages": wanted_msgs
        }
    }

    json_string = json.dumps(data) + '\n'
    writer.write(json_string.encode())
    await writer.drain()

    data = (await reader.readline()).strip()
    writer.close()

    json_string = data.decode()
    data = json.loads(json_string)

    return data["messages"]
