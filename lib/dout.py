"""
This file is part of upyHome
Copyright (c) 2020 ng-galien
Licensed under the MIT license:
http://www.opensource.org/licenses/mit-license.php
Project home:
https://github.com/upyhome/upyhome
"""

from machine import Pin
from lib.base import Suscriber

class DigitalOutputPin(Suscriber):
    """
    Digital output component
    """
    def __init__(self, proxy, topic, **kwargs):#, pin=0, suscribe=None, inverted=False, user=None):
        super().__init__(topic, proxy, **kwargs)
        pin = kwargs.get('pin', None)
        if not isinstance(pin, int):
            raise AttributeError('Input pin number (%s) not allowd for topic %s'%(str(pin), topic))
        self._hpin = Pin(pin, Pin.OUT)
        self._inverted = kwargs.get('inverted', True)

    def on(self):
        if self.value() == 'on':
            return
        if self._inverted:
            self._hpin.off()
        else:
            self._hpin.on()
        self._push(self.value())

    def off(self):
        if self.value() == 'off':
            return
        if self._inverted:
            self._hpin.on()
        else:
            self._hpin.off()
        self._push(self.value())

    def toggle(self):
        val = self.value()
        if val == 'on':
            self.off()
        else:
            self.on()
        val = self.value()


    def value(self):
        if self._inverted:
            return 'on' if self._hpin.value() == 0 else 'off'
        else:
            return 'on' if self._hpin.value() == 1 else 'off'

