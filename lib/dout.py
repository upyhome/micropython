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

from machine import Pin
from lib.sub import Subscriber
from lib.pub import Publisher 

class DigitalOutputPin(Subscriber, Publisher):

    def __init__(self, proxy, topic=None, pin=0, topics=[], inverted=False, user_cb=None):
        Subscriber.__init__(self, topic, proxy, topics, user_cb)
        Publisher.__init__(self, topic, proxy)
        self._hpin = Pin(pin, Pin.OUT)
        self.inverted = inverted

    def on(self, topic=None):
        if self.value() == 'on':
            return
        if self.inverted:
            self._hpin.off()
        else:
            self._hpin.on()
        self._push(self.value())

    def off(self, topic=None):
        if self.value() == 'off':
            return
        if self.inverted:
            self._hpin.on()
        else:
            self._hpin.off()
        self._push(self.value())
        

    def toggle(self, topic=None):
        val = self.value()
        if val == 'on':
            self.off()
        else:
            self.on()
        val = self.value()


    def value(self):
        if self.inverted:
            return 'on' if self._hpin.value() == 0 else 'off'
        else:
            return 'on' if self._hpin.value() == 1 else 'off'

    

    
