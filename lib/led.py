"""
This file is part of upyHome
Copyright (c) 2020 ng-galien
Licensed under the MIT license:
http://www.opensource.org/licenses/mit-license.php
Project home:
https://github.com/upyhome/upyhome
"""

from machine import Pin, Timer
from neopixel import NeoPixel
from lib.base import Suscriber

class Led(Suscriber):
    def __init__(self, tid, proxy, **kwargs):#='led', pin=0, num=1, user=None):
        super().__init__(proxy, **kwargs)
        pin = kwargs.get('pin', None)
        if not isinstance(pin, int):
            raise AttributeError('Input pin number (%s) not allowd for topic %s'%(str(pin), topic))
        self.num = kwargs.get('num', 1)
        self.pix = NeoPixel(Pin(pin, Pin.OUT), self.num)
        self.tim = Timer(tid)
        self.rgb = (0, 0, 0)
        self.alpha = 1

    def value(self):
        return self.rgb

    def set_rgba(self, r, g, b, alpha=1):
        self.alpha = alpha
        self.rgb = (int(r*alpha), int(g*alpha), int(b*alpha))

    def fill(self, r, g, b, alpha=1): 
        self.set_rgba(r, g, b, alpha)
        for i in range(self.num):
            self.pix[i] = self.rgb
        self.pix.write()

    def off(self):
        for i in range(self.num):
            self.pix[i] = (0, 0, 0)
        self.pix.write()

    def on(self):
        for i in range(self.num):
            self.pix[i] = self.rgb
        self.pix.write()

    def toggle(self):
        is_off = True
        for i in range(self.num):
            col = self.pix[i]
            if col[0]+col[1]+col[2] > 0:
                is_off = False
                break
        if is_off:
            self.on()
        else:
            self.off()

    def white(self):
        self.fill(255, 255, 255)

    def red(self):
        self.fill(255, 0, 0)

    def green(self):
        self.fill(0, 255, 0)

    def blue(self):
        self.fill(0, 0, 255)

    def fade_in(self):
        pass

    def fade_on(self):
        pass