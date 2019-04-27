import logging
import asyncio
import sys
import json

from threading import *
from kademlia.network import Server

DEBUG = False

class KademliaServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.loop = None

    def start_server(self, bootstrap_nodes): 
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # DEBUG
        if DEBUG:
            log = logging.getLogger('kademlia')
            log.addHandler(handler)
            log.setLevel(logging.DEBUG)

        self.loop = asyncio.get_event_loop()
        if DEBUG:
            self.loop.set_debug(True)

        self.server = Server()
        self.loop.run_until_complete(self.server.listen(self.port))

        # bootstrap_node = (bt_Ip, int(bt_port))
        self.loop.run_until_complete(self.server.bootstrap(bootstrap_nodes))

        return self.loop

    async def register(self, username):
        result = await self.server.get(username)
        if result is None:
            value = {
                "followers": [],
                "following": [],
                "ip": self.ip,
                "port": self.port
            }
            value = json.dumps(value)
            await self.server.set(username, value)
            return value

        else:
            raise Exception("Username already exists")
    
    async def login(self, username):
        result = await self.server.get(username)
        result = json.loads(result)

        if result is not None:
            value = {
                "followers": result['followers'],
                "following": result['following'],
                "ip": self.ip,
                "port": self.port
            }
            value = json.dumps(value)
            await self.server.set(username, value)
            return value

        else:
            raise Exception("User doesn't exist! Please register")
    
    async def get_user_ip(self, username):
        result = await self.server.get(username)
        result = json.loads(result)
        
        if result is None:
            raise Exception("User doesn't exist!")
        else:
            return (result["ip"], result["port"])

    async def get_user_followers(self, username):
        followers = {}
        result = await self.server.get(username)
        result = json.loads(result)
        for follower in result["followers"]:
            result = await self.server.get(follower)
            result = json.loads(result)
            if result is not None:
                followers[follower] = (result["ip"], result["port"])
        
        return followers

    async def get_user_following(self, username):
        following = {}
        result = await self.server.get(username)
        result = json.loads(result)
        for follw in result["following"]:
            result = await self.server.get(follw)
            result = json.loads(result)
            if result is not None:
                following[follw] = (result["ip"], result["port"])
        
        return following

    async def get_user(self, username):
        result = await self.server.get(username)
        result = json.loads(result)
        return result

    async def set_user(self, username, value):
        await self.server.set(username, value)

