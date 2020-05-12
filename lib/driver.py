"""
This file is part of upyHome
Copyright (c) 2020 ng-galien
Licensed under the MIT license:
http://www.opensource.org/licenses/mit-license.php
Project home:
https://github.com/upyhome/upyhome
"""

from machine import Timer
from lib.base import Publisher, Suscriber

class DriverIn(Publisher):
    def __init__(self, tid, proxy, **kwargs):
        super().__init__(proxy, **kwargs)
        self.timer = Timer(tid)
        self.polling = kwargs.get('polling', 1000)
        self.val = None
        
    def timer_cb(self, tim):
        if self.value() is not None:
            self._push(self.value())

    def start(self):
        self.timer.init(period=self.polling, mode=Timer.PERIODIC, callback=self.timer_cb)
    
    def stop(self):
        self.timer.deinit()

class DriverOut(Suscriber):

    def __init__(self, proxy, **kwargs):
        super().__init__(proxy, **kwargs)
        self.val = None
        


