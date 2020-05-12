"""
This file is part of upyHome
Copyright (c) 2020 ng-galien
Licensed under the MIT license:
http://www.opensource.org/licenses/mit-license.php
Project home:
https://github.com/upyhome/upyhome
"""

from lib.driver import DriverIn
from drivers.mpu6500 import MPU6500

class M5SMPU(DriverIn, MPU6500):
    def __init__(self, tid, proxy, **kwargs):
        DriverIn.__init__(self, tid, proxy, **kwargs)
        i2c = kwargs.get('i2c')
        MPU6500.__init__(self, i2c, **kwargs)

    def value(self):
        return self.acceleration


