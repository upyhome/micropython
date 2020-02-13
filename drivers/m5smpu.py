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

from lib.driver import DriverIn
from mpu6500 import MPU6500

class M5SMPU(DriverIn, MPU6500): 
    def __init__(self, topic, proxy, tid, polling=1000, i2c=None, address=None, user_cb=None, **kwargs):
        DriverIn.__init__(self, topic, proxy, tid, polling=polling, user_cb=user_cb)
        MPU6500.__init__(self, i2c = i2c, address=address, **kwargs)
        
    def value(self):
        return self.acceleration

