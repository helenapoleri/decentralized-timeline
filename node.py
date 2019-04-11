from timeline import Timeline
from kademlia.network import Server

class Node:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.timeline = Timeline()
        self.server = None
        self.connections = [] # ainda n sei bem como é que vai ser

    def post_message(self, message):
        # add to timeline
        self.timeline.add_message(message)
        # increment vetor clock
        # create message
        # send message
