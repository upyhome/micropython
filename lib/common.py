"""
This file is part of upyHome
Copyright (c) 2020 ng-galien
Licensed under the MIT license:
http://www.opensource.org/licenses/mit-license.php
Project home:
https://github.com/upyhome/upyhome
"""
import sys
from micropython import const
import uos
import machine

MAX_PRIORITY = const(100)

ERROR_FILE = 'error.log'
CONFIG_NAME = 'name'
CONFIG_FILE = 'config.json'
CONFIG_NET = 'network'
CONFIG_HOSTNAME = 'hostname'
CONFIG_WIFI = 'wifi'
CONFIG_DIN = 'digital-inputs'
CONFIG_DOUT = 'digital-outputs'
CONFIG_LED = 'leds'
CONFIG_I2C = 'i2c'
CONFIG_SPI = 'spi'
CONFIG_DRIVER = 'drivers'

KEY_PLATFORM = 'platform'
KEY_DEBUG = 'debug'
KEY_NETWORKS = 'networks'
KEY_NET = 'net'

KEY_TOPIC = 'topic'
KEY_MUTE = 'mute'
KEY_USER_CB = 'user'
KEY_SUSCRIBES = 'suscribes'

KEY_EVENT = 'event'
KEY_STATE = 'state'
KEY_NEXT = 'next'
PRIORITY = 'priority'

PLATFORM = {
    'value': True
}
MODE_DEBUG = {
    'value': False
}

__VERSION__ = '0.1.0'



def print_logo():
    """
    Print the logo
    """
    logo = """
                 __ __               
 __ _____  __ __/ // /__  __ _  ___ 
/ // / _ \/ // / _  / _ \/  ' \/ -_)
\_,_/ .__/\_, /_//_/\___/_/_/_/\__/ 
   /_/   /___/                      
"""
    print(logo)

def log_error(err):
    """
    Log the last error, maximum size is 2kb
    """
    
    mode = 'w'
    if ERROR_FILE in uos.ilistdir():
        return
        #size = uos.stat(ERROR_FILE)[6]
        #if size > 2000:
        #    mode = 'w'
    if MODE_DEBUG['value']:
            sys.print_exception(err)
    with open('err.log', mode) as f:
        dt = machine.RTC().datetime()
        f.write('timestamp = %d/%02d/%02d - %02d:%02d:%02d\n'%(dt[0],dt[1],dt[2],dt[4],dt[5],dt[6]))
        f.write('%s\n'%(err))

def _debug(msg):
    """
    Debug a message with the correct output format
    """
    if MODE_DEBUG['value']:
        print('#debug=[%s]'%(msg))

