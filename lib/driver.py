"""
This file is part of upyHome
Copyright (c) 2020 ng-galien
Licensed under the MIT license:
http://www.opensource.org/licenses/mit-license.php
Project home:
https://github.com/upyhome/upyhome
"""

from machine import Timer
from lib.pub import Publisher
from lib.sub import Subscriber

class DriverIn(Publisher):
    def __init__(self, topic, proxy, tid, user_cb=None, polling=1000):
        super().__init__(topic, proxy, user_cb)
        self.polling = polling
        self.timer = Timer(tid)
        self.val = None
        
    def timer_cb(self, tim):
        if self.value() is not None:
            self._push(self.value())

    def start(self):
        self.timer.init(period=self.polling, mode=Timer.PERIODIC, callback=self.timer_cb)
    
    def stop(self):
        self.timer.deinit()

class DriverOut(Subscriber):
    def __init__(self, topic, proxy, tid, user_cb=None, topics=[]):
        super().__init__(topic, proxy, user_cb)
        self.timer = Timer(tid)
        self.val = None
        


