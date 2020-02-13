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

class Base:

    def __init__(self, topic, user_cb, mute=False):
        self._topic = topic
        self._state = {}
        self._proxy = None
        self._val = None
        self._mute = mute
        self._custom_cb = user_cb
        self._user_cb = self._user_eval if user_cb else None
        self._context = {'event': None, 
                        'topic': topic, 
                        'next': True, 
                        'emit': True, 
                        'state': self._state}  
        
    def _set_callback(self, user_cb):
        self._user_cb = user_cb

    def _user_eval(self, data):
        exec(self._custom_cb, data)
        return data['next']

    def mute(self, m=None):
        if m is None:
            return self._mute
        else:
            self._mute = m

    def value(self):
        return None 

    def _message(self):
        return '#{}=[{}]'.format(self._topic,self.value())

    def start(self):
        pass

    def stop(self):
        pass
