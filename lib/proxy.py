#
# This file is part of upyHome
# Copyright (c) 2020 ng-galien
#
# Licensed under the MIT license:
#   http://www.opensource.org/licenses/mit-license.php
#
# Project home:
#   https://github.com/upyhome/upyhome
#

from lib.base import Base

class Proxy(Base):

    def __init__(self, name='proxy', user_cb=None):
        super().__init__(name, user_cb)
        self._publisher={}
        self._subscriber={}
        self.mute(False)

    def add_pub(self, pub):
        self._publisher[pub._topic] = pub
        pub._on_event = self._emit


    def add_sub(self, sub, topic):
        if topic not in self._subscriber:
            self._subscriber[topic] = []
        self._subscriber[topic].append(sub)

    def _emit(self, event):
        topic = event['topic']
        if topic in self._subscriber:
            for sub in self._subscriber[topic]:
                next = sub._pull(event)
                if event['emit']:
                    print(sub._message())
                if not next:
                    break
        else:
            if topic in self._publisher:
                pub = self._publisher[topic]
                if not pub.mute():
                    print(pub._message())

    def get_state(self, event):
        if event in self._state:
            return self._state[event]

    def value(self):
        return self._state.keys()

    def discover(self):
        print(self._message())

