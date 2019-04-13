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

        # timeline_entry = {
        #     "name": user,
        #     "message": message
        # }
        print(timeline_entry)
        self.messages.append(timeline_entry.get_dict())

        input("...")
        print("cheguei aqui")
        if not os.path.isdir('messages'):
            print("vou criar pasta")
            os.mkdir('messages')

        with open('messages/' + self.username + '-messages.json', 'w') as outfile:
            print("OI")
            print(self.username)
            print(self.messages)
            print(type(self.messages))
            json.dump(self.messages, outfile)

    def get_timeline(self):
        try:
            print("WWWWWWTTTTTTTFFFFFF")
            with open('messages/' + self.username + '-messages.json', 'r') as infile:
                print("burro")
                data = json.load(infile)
                print("burro2")
                res = []
                #print(self.username)
                print(data)
                for msg in data:
                    print(msg)
                    res.append(TimelineEntry(msg['name'], msg['message']).get_dict())
                for i in res:
                    print("oi")
                    print(i)
                print("burr2")
                print(data)
                print(res)
                return res
        except:
            return []