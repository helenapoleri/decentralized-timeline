import json
import os
import utils.snowflake as snowflake
import datetime

class TimelineEntry:
    def __init__(self, username, content, msg_id, time):
        self.username = username
        self.content = content
        self.id = msg_id
        self.time = time

    def __repr__(self):
        time = self.time.strftime('%Y-%m-%d %H:%M:%S')
        return "{ \"time\":" + time +", \"name\":" +  self.username + ", \"message\":" + self.content  + "\"id\":" + self.id  +"}"
    
    def get_dict(self):
        return {
            "name": self.username,
            "message": self.content,
            "time": self.time,
            "id": self.id
        }
    
class Timeline:
    def __init__(self, username):
        self.username = username
        self.messages = self.get_timeline()
        
    def __repr__(self):
        messages = sorted(self.messages, key=lambda x: x['id'])

        result = ""
        
        for msg in messages:
            time = msg.get("time").strftime('%Y-%m-%d %H:%M:%S')

            result += "-" * 79 + "\n"
            result += time + " - "
            result += msg.get("name") + ": " + msg.get("message")
            result += "\n"

        return self.username + "'s TIMELINE" + "\n" + result
            

    def add_message(self, user, message, msg_id, time):

        timeline_entry = TimelineEntry(user, message, msg_id, time)

        self.messages.append(timeline_entry.get_dict())
        messages = []
        for msg in self.messages:
            new_msg = dict(msg)
            new_msg['time'] = new_msg['time'].strftime('%Y-%m-%d %H:%M:%S')

        if not os.path.isdir('messages'):
            os.mkdir('messages')

        with open('messages/' + self.username + '-messages.json', 'w') as outfile:
            json.dump(messages, outfile)

    def get_timeline(self):
        try:
            with open('messages/' + self.username + '-messages.json', 'r') as infile:
                print("oi")
                data = json.load(infile)
                print("oi2")
                res = []
                for msg in data:
                    time = datetime.strptime(msg['time'], '%Y-%m-%d %H:%M:%S')
                    res.append(TimelineEntry(msg['name'], msg['message'], msg['id'], time).get_dict())
                return res
        except:
            return []