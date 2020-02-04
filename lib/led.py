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
from neopixel import NeoPixel
from lib.sub import Subscriber

class Led(Subscriber):
    def __init__(self, topic, h_pin, num, tid, proxy=None, user_cb=None):
        super().__init__(topic, proxy, user_cb)
        self.num = num
        self.pix = NeoPixel(Pin(h_pin, Pin.OUT), num)
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