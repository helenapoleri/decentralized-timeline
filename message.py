
class Message:
    
    def __init__(self, content, vector, sender):
        self.sender = sender
        self.content = content
        self.vector_clock = vector

    def __repr__(self):
        return "{" + self.sender + ": " + self.content + "}"