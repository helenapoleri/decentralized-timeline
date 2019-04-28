
import ntplib

from time import ctime
from socket import inet_aton, error

# 27 April 2019 20:30:00 GMT
epoch = 1556393400000


def get_time_from_id(id):
    diff = int(id >> 16 + 32)
    timestamp = int(epoch/1000 + diff/1000)
    return ctime(timestamp)


def id_builder(timestamp, port, seq_number):
    timestamp_binary = "{0:048b}".format(timestamp)
    port_binary = "{0:032b}".format(port)
    seq_number_binary = "{0:016b}".format(seq_number)

    return int(timestamp_binary + port_binary + seq_number_binary, 2)


def timestamp_now():
    c = ntplib.NTPClient()
    response = c.request('pool.ntp.org', version=3)
    return int(response.tx_time * 1000)


def is_port_valid(port):
    return port <= 65535


def generator(port):
    assert is_port_valid(port)

    seq_number = 0
    last_timestamp = 0

    while True:
        timestamp = timestamp_now()

        if last_timestamp == timestamp:
            seq_number += 1
        else:
            seq_number = 0

        last_timestamp = timestamp

        yield id_builder(timestamp - epoch, port, seq_number)