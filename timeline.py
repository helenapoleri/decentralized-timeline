import json
import os
import configparser
import settings
import utils.flake as flake

from datetime import datetime, timedelta

DISCARD_BASELINE = settings.DISCARD_BASELINE


class TimelineEntry:
    def __init__(self, username, content, msg_id, msg_nr, time):
        self.username = username
        self.content = content
        self.id = msg_id
        self.msg_nr = msg_nr
        self.time = time
        self.seen = False

    # def __repr__(self):
    #     time = self.time.strftime('%Y-%m-%d %H:%M:%S')
    #     return "{ \"time\":" + time + ", \"name\":" + self.username + \
    #            ", \"message\":" + self.content + "\"id\":" + self.id + "}"

    def get_dict(self):
        return {
            "name": self.username,
            "message": self.content,
            "id": self.id,
            "msg_nr": self.msg_nr,
            "time": self.time,
            "seen": self.seen
        }


class Timeline:
    def __init__(self, username):
        self.username = username
        self.get_timeline()

    def __repr__(self):

        # messages = [msg for msgs in self.messages.values() for msg in msgs]
        messages = []
        for msgs in self.messages.values():
            for msg in msgs:
                msg['seen'] = True
                messages.append(msg)

        self.save_messages()

        messages = sorted(messages, key=lambda x: x['id'], reverse=True)

        result = ""

        for msg in messages:
            time = msg.get("time").strftime('%Y-%m-%d %H:%M:%S')

            result += "-" * 79 + "\n"
            result += time + "(" + str(msg.get("msg_nr")) + ")" + " - "
            result += msg.get("name") + ": " + msg.get("message")
            result += "\n"

        return self.username + "'s TIMELINE" + "\n" + result

    def get_user_messages(self, user, msgs_idx):
        # TODO meter as self.messages como um dicionario
        msgs = []
        for msg_idx in msgs_idx:
            for msg in self.messages[user]:
                if msg['msg_nr'] == msg_idx:
                    msgs.append({
                        "name": msg['name'],
                        "message": msg['message'],
                        "id": msg['id'],
                        "msg_nr": msg['msg_nr']
                    })
        return msgs


    def discard_messages(self):
        max_duration = timedelta(seconds=DISCARD_BASELINE)

        discard_time = flake.get_datetime_now() - max_duration

        for user, msgs in self.messages.items():
            if user == self.username:
                continue

            for msg in msgs:
                if msg['time'] < discard_time and msg['seen']:
                    msgs.remove(msg)
                else:
                    break


    def user_waiting_messages(self, follw):
        if follw in self.waiting_messages:
            return list(self.waiting_messages[follw].keys())
        else:
            return []

    def add_message(self, user, message, msg_id, msg_nr, time, user_knowledge = None):

        timeline_entry = TimelineEntry(user, message, msg_id, msg_nr, time)

        if  (user_knowledge == None) or (msg_nr == user_knowledge + 1):
            user_msgs = self.messages.get(user, [])
            user_msgs.append(timeline_entry.get_dict())
            user_knowledge = msg_nr

            while(user_knowledge in self.waiting_messages):
                msg = self.waiting_messages.pop(user_knowledge)
                user_msgs.append(msg)
                user_knowledge += 1

            self.messages[user] = user_msgs

        elif msg_nr > user_knowledge + 1:
            user_msgs = self.waiting_messages.get(user, {})
            user_msgs[msg_nr] = (timeline_entry.get_dict())
            self.waiting_messages[user] = user_msgs
        else:
            pass

        self.discard_messages()
        self.save_messages()


    def get_timeline(self):
        try:
            filename = 'messages/' + self.username + '-messages.json'
            with open(filename, 'r') as infile:
                data = json.load(infile)
                for msgs in data.values():
                    for msg in msgs:
                        msg['time'] = datetime.strptime(
                                               msg['time'],
                                               '%Y-%m-%d %H:%M:%S')

                self.messages = data
        except:
            self.messages = {}

        try:
            filename = 'messages/' + self.username + '-w-messages.json'
            with open(filename, 'r') as infile:
                data = json.load(infile)
                for msgs in data.values():
                    for msg in msgs.values():
                        msg['time'] = datetime.strptime(
                                               msg['time'],
                                               '%Y-%m-%d %H:%M:%S')

                self.waiting_messages = data
        except:
            self.waiting_messages = {}

    def save_messages(self):
        self.save_current_messages()
        self.save_waiting_messages()

    def save_current_messages(self):
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

        filename = 'messages/' + self.username + '-messages.json'

        with open(filename, 'w') as outfile:
            json.dump(messages, outfile)

    def save_waiting_messages(self):
        messages = {}
        for user, msgs in self.waiting_messages.items():
            user_msgs = {}
            for msg_nr, msg in msgs.items():
                new_msg = dict(msg)
                new_msg['time'] = new_msg['time'].strftime('%Y-%m-%d %H:%M:%S')
                user_msgs[msg_nr] = new_msg
            messages[user] = user_msgs

        if not os.path.isdir('messages'):
            os.mkdir('messages')

        filename = 'messages/' + self.username + '-w-messages.json'

        with open(filename, 'w') as outfile:
            json.dump(messages, outfile)