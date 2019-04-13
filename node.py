from timeline import Timeline
from kademlia.network import Server

class Node:
    def __init__(self, address, port, username, state=None):
        self.timeline = Timeline(username)
        self.username = username
        self.address = address
        self.port = port
        self.server = None
        self.connections = [] # ainda n sei bem como é que vai ser

    def post_message(self, message):
        # add to timeline
        self.timeline.add_message(self.username, message)
        # increment vetor clock
        # create message
        # send message

    def show_timeline(self):
        print(self.timeline)
