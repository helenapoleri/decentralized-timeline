
import ntplib
import time
import os 

from time import ctime, time
from socket import inet_aton, error
from datetime import datetime

# 27 April 2019 20:30:00 GMT
epoch = 1556393400000


def get_datetime_now():
    now = timestamp_now()
    now_str = ctime(now/1000)
    time = datetime.strptime(now_str, "%a %b %d %H:%M:%S %Y")
    return time


def get_datetime_from_id(id):
    return datetime.strptime(get_time_from_id(id), "%a %b %d %H:%M:%S %Y")


def get_time_from_id(id):
    return ctime(get_timestamp_from_id(id))


def get_timestamp_from_id(id):
    diff = int(id >> 16 + 32)
    timestamp = int(epoch/1000 + diff/1000)
    return timestamp


def id_builder(timestamp, address, seq_number):
    timestamp_binary = "{0:048b}".format(timestamp)
    address_binary = "".join(["{0:08b}".format(int(x))
                             for x in address.split(".")])
    seq_number_binary = "{0:016b}".format(seq_number)

    return int(timestamp_binary + address_binary + seq_number_binary, 2)


def adjust_system_clock():
    c = ntplib.NTPClient()
    try:
        response = c.request('pool.ntp.org', version=3)
        os.system('date ' + time.strftime('%m%d%H%M%Y.%S', time.localtime(response.tx_time)))
    except:
        pass


def timestamp_now():
    return int(time.time() * 1000)


def is_port_valid(port):
    return port <= 65535


def generator(port):
    assert is_port_valid(port)

    seq_number = 0
    last_timestamp = 0

    while True:
        adjust_system_clock()
        timestamp = timestamp_now()

        if last_timestamp == timestamp:
            seq_number += 1
        elif last_timestamp > timestamp:
            time.sleep(last_timestamp - timestamp)
        else:
            seq_number = 0

        last_timestamp = timestamp

        yield id_builder(timestamp - epoch, address, seq_number)