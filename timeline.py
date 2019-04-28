import json
import os
import configparser
import settings
from datetime import datetime, timedelta

DISCARD_BASELINE = settings.DISCARD_BASELINE

class TimelineEntry:
    def __init__(self, username, content, msg_id, time):
        self.username = username
        self.content = content
        self.id = msg_id
        self.time = time
        self.seen = False

    def __repr__(self):
        time = self.time.strftime('%Y-%m-%d %H:%M:%S')
        return "{ \"time\":" + time +", \"name\":" +  self.username + ", \"message\":" + self.content  + "\"id\":" + self.id  +"}"

    def get_dict(self):
        return {
            "name": self.username,
            "message": self.content,
            "id": self.id,
            "time": self.time,
            "seen": self.seen
        }
    
class Timeline:
    def __init__(self, username):
        self.username = username
        self.messages = self.get_timeline()
        self.discard_messages()
        
    def __repr__(self):

        # messages = [msg for msgs in self.messages.values() for msg in msgs]
        messages = []
        for msgs in self.messages.values():
            for msg in msgs:
                msg['seen'] = True
                messages.append(msg)

        self.save_messages()

        messages = sorted(messages, key=lambda x: x['time'], reverse=True)
        
        result = ""
        
        for msg in messages:
            time = msg.get("time").strftime('%Y-%m-%d %H:%M:%S')

            result += "-" * 79 + "\n"
            result += time + " - "
            result += msg.get("name") + ": " + msg.get("message")
            result += "\n"

        return self.username + "'s TIMELINE" + "\n" + result
            

    def save_messages(self):
        messages = {}
        for user, msgs in self.messages.items():
            user_msgs = []
            for msg in msgs:
                new_msg = dict(msg)
                new_msg['time'] = new_msg['time'].strftime('%Y-%m-%d %H:%M:%S')
                user_msgs.append(new_msg)
            messages[user] = user_msgs

        if not os.path.isdir('messages'):
            os.mkdir('messages')

        with open('messages/' + self.username + '-messages.json', 'w') as outfile:
            json.dump(messages, outfile)

    def discard_messages(self):
        max_duration = timedelta(seconds=DISCARD_BASELINE)
        discard_time = datetime.now() - max_duration

        for user, msgs in self.messages.items():
            if user == self.username:
                continue
            
            for msg in msgs:
                if msg['time'] < discard_time and msg['seen']:
                    msgs.remove(msg)
                else:
                    break
            
        self.save_messages()


    def add_message(self, user, message, msg_id, time):

        timeline_entry = TimelineEntry(user, message, msg_id, time)

        user_msgs = self.messages.get(user,[])
        user_msgs.append(timeline_entry.get_dict())
        
        self.messages[user] = user_msgs

        self.discard_messages()
        # self.save_messages() #não é necessário porque já está a ser realizado no discard_messages()


    def get_timeline(self):
        try:
            with open('messages/' + self.username + '-messages.json', 'r') as infile:

                data = json.load(infile)
                for msgs in data.values():
                    for msg in msgs:
                        msg['time'] = datetime.strptime(msg['time'], '%Y-%m-%d %H:%M:%S')

                return data

        except:
            return {}