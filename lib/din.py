"""
This file is part of upyHome
Copyright (c) 2020 ng-galien
Licensed under the MIT license:
http://www.opensource.org/licenses/mit-license.php
Project home:
https://github.com/upyhome/upyhome
"""

from machine import Pin, Timer
from lib.base import Publisher

class DigitalInputPin(Publisher):
    """
    Digital input component
    - When it's pressed -> P
    - When it's clicked -> C
    - When it's long pressed -> L
    """
    def __init__(self, tid, proxy, **kwargs):
        super().__init__(proxy, **kwargs)
        pin = kwargs.get('pin', None)
        if not isinstance(pin, int):
            raise AttributeError('Input pin number (%s) not allowd for topic %s'%(str(pin), self._topic))
        self._hpin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._inverted = kwargs.get('inverted', True)
        self._dbc_t = kwargs.get('debounce', 50)
        self._long_t = kwargs.get('long', 1000)
        self._raw_value = kwargs.get('raw_value', False)
        self._filter = kwargs.get('filter', 'PCL')
        self._debouncing = False
        self._suppress = False
        self._target = 0
        self._last_event = None
        self._timer = Timer(tid)
        self._hpin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.irq_cb)

    def value(self):
        """
        Value
        """
        if not self._raw_value:
            return self._last_event
        elif self._inverted:
            return 'on' if self._hpin.value() == 0 else 'off'
        else:
            return 'on' if self._hpin.value() == 1 else 'off'

    def irq_cb(self, pin):
        """
        IRQ
        """
        self._target = pin.value()
        if self._debouncing or self._suppress:
            self._suppress = False
            self._debouncing = False
            self._timer.deinit()
            return
        self._timer.init(period=self._dbc_t, mode=Timer.ONE_SHOT, callback=self.dbc_cb)
        self._debouncing = True

    def dbc_cb(self, tim):
        """
        Debounce
        """
        self._debouncing = False
        if self._hpin.value() == self._target:
            click = (self._inverted and self._target == 1) or (not self._inverted and self._target == 0)
            self._last_event = 'C' if click else 'P'
            if self._last_event == 'P':
                self._timer.init(period=self._long_t, mode=Timer.ONE_SHOT, callback=self.long_cb)
            else:
                self._timer.deinit()
            self._push(self._last_event)

    def long_cb(self, tim):
        """
        Long pressed CB
        """
        if self._hpin.value() == self._target:
            self._suppress = True
            self._last_event = 'L'
            self._push(self._last_event)

    def _push(self, event):
        if event in self._filter:
            super()._push(event)
