#
# This file is part of µpyhone
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

class DigitalOutputPin(Subscriber):

    def __init__(self, topic, h_pin, proxy=None, topics=[], inverted=False, user_cb=None):
        super().__init__(topic, proxy, topics, user_cb)
        self.pin = Pin(h_pin, Pin.OUT)
        self.inverted = inverted

    def on(self, topic=None):
        if self.value() == 'on':
            return
        if self.inverted:
            self.pin.off()
        else:
            self.pin.on()

    def off(self, topic=None):
        if self.value() == 'off':
            return
        if self.inverted:
            self.pin.on()
        else:
            self.pin.off()
        

    def toggle(self, topic=None):
        val = self.value()
        if val == 'on':
            self.off()
        else:
            self.on()
        val = self.value()


    def value(self):
        if self.inverted:
            return 'on' if self.pin.value() == 0 else 'off'
        else:
            return 'on' if self.pin.value() == 1 else 'off'

    

    
