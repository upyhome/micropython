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

from machine import Pin, Timer
from lib.pub import Publisher
"""
TODO Solve value / inverted / pullup combination
It prints tree events
    - When it's pressed -> P
    - When it's clicked -> C
    - When it's long pressed -> L
"""
class DigitalInputPin(Publisher):

    def __init__(self, topic, proxy, h_pin, tid, inverted=True, debounce=100, long=1000, user_cb=None, raw_value=False):
        super().__init__(topic, proxy, user_cb)
        self.inv = inverted
        self.dbc_t = debounce
        self.long_t = long
        self.debouncing = False
        self.suppress = False
        self.target = 0
        self._raw_value = False
        self._last_event = None
        self.dbc_tim = Timer(tid)
        self.pin = Pin(h_pin, Pin.IN, Pin.PULL_UP if self.inv else Pin.PULL_DOWN)
        self.pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.irq_cb)

    def value(self):
        if not self._raw_value:
            return self._last_event
        elif self.inv:
            return 'on' if self.pin.value()==0 else 'off'
        else:
            return 'on' if self.pin.value()==1 else 'off'
        return 

    def irq_cb(self, pin):
        self.target = pin.value()
        if self.debouncing or self.suppress:
            self.suppress = False
            self.debouncing = False
            self.dbc_tim.deinit()
            return
        self.dbc_tim.init(period=self.dbc_t, mode=Timer.ONE_SHOT, callback=self.dbc_cb)
        self.debouncing = True

    def dbc_cb(self, tim):
        self.debouncing = False
        if self.pin.value() == self.target:
            self._last_event = 'C' if (self.inv and self.target == 1) or (not self.inv and self.target == 0) else 'P'
            if(self._last_event == 'P'):
                self.dbc_tim.init(period=self.long_t, mode=Timer.ONE_SHOT, callback=self.long_cb)
            else:
                self.dbc_tim.deinit()
            self._push(self._last_event)
        
    def long_cb(self, tim):
        if self.pin.value() == self.target:
            self.suppress = True
            self._last_event = 'L'
            self._push(self._last_event)
    