from aqualogic import AquaLogic, Keys
import zope.event
import socket
import threading
import logging

logging.basicConfig(level=logging.INFO)

def data_changed(aq):
    print('Pool Temp: {}'.format(aq.pool_temp))
    print('Air Temp: {}'.format(aq.air_temp))
    print(aq.leds())

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('192.168.1.109', 23))
reader = s.makefile(mode='rb')
writer = s.makefile(mode='wb')

aq = AquaLogic(reader, writer)

zope.event.subscribers.append(data_changed)

reader_thread = threading.Thread(target=aq.data_reader)
reader_thread.start()

while True:
    key = Keys[input()]
    aq.send_key(key)
