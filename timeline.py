import json
import os

class TimelineEntry:
    def __init__(self, username, content):
        self.username = username
        self.content = content

    def __repr__(self):
        return "{ \"name\":" +  self.username + ", \"message\":" + self.content  + "}"
    
    def get_dict(self):
        return {
            "name": self.username,
            "message": self.content
        }
    
class Timeline:
    def __init__(self, username):
        self.username = username
        self.messages = self.get_timeline()
        
    def __repr__(self):
        result = ""
        
        for msg in self.messages:
            result += "-" * 79 + "\n"
            result += msg.get("name") + ": " + msg.get("message")
            result += "\n"

        return self.username + "'s TIMELINE" + "\n" + result
            

    def add_message(self, user, message):

        timeline_entry = TimelineEntry(user, message)

        self.messages.append(timeline_entry.get_dict())

        if not os.path.isdir('messages'):
            os.mkdir('messages')

        with open('messages/' + self.username + '-messages.json', 'w') as outfile:
            json.dump(self.messages, outfile)

    def get_timeline(self):
        try:
            with open('messages/' + self.username + '-messages.json', 'r') as infile:
                print("oi")
                data = json.load(infile)
                print("oi2")
                res = []
                for msg in data:
                    res.append(TimelineEntry(msg['name'], msg['message']).get_dict())
                return res
        except:
            return []