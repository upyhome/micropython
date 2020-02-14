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

ERROR_FILE = 'error.log'
CONFIG_FILE = 'config.json'
CONFIG_NET = 'network'
CONFIG_WIFI = 'wifi'
CONFIG_DIN = 'digital-inputs'
CONFIG_DOUT = 'digital-outputs'
CONFIG_LED = 'leds'
CONFIG_I2C = 'i2c'
CONFIG_SPI = 'spi'
CONFIG_DRIVER = 'drivers'

KEY_DEBUG = 'debug'
KEY_NET = 'net'
KEY_PLATFORM = 'platform'
KEY_TOPIC = 'topic'
KEY_USER_CB = 'user'
KEY_NETWORKS = 'networks'

platform = ''
mode_debug = False

__VERSION__ = '0.1.0'



def print_logo():
    logo = """
                 __ __               
 __ _____  __ __/ // /__  __ _  ___ 
/ // / _ \/ // / _  / _ \/  ' \/ -_)
\_,_/ .__/\_, /_//_/\___/_/_/_/\__/ 
   /_/   /___/                      
"""
    print(logo)

def _DEBUG(msg):
    """
    Debug a message with the correct output format
    """
    if mode_debug:
        print('#debug=[%s]'%(msg))

from base import Publisher, Proxy

_PROXY = Proxy()

class UpyHome(Publisher):
    """
    Upyhome main class
    """
    def __init__(self):
        from machine import Timer
        super().__init__('upyhome', _PROXY)
        self._proxy = _PROXY
        self._config = None
        self._comps = {}
        self._tidx = 1
        self._tick = 0
        self._live_tim = Timer(self._tidx)
        self._live_tim.init(period=1000, mode=Timer.PERIODIC, callback=self._alive)
        self._tidx += 1

    def _alive(self, timer): 
        """
        Trick to avoid garbage collection from main execution
        """
        self._tick += 1        

    def _exec_func(self, obj, function, args):
        _DEBUG('_exec_func {0}@{1} [{2}]'.format(function, obj, args))
        if hasattr(obj, function):
            func = getattr(obj, function)
            if callable(func):
                if args is not None:
                    func(args)
                else:
                    func()
        else:
            raise Exception('Function %s not found on %s'%(function, obj))

    def exec(self, method, topic=None, data=None):
        _DEBUG('exec %s %s %s'%(method, topic, data))
        """
        Execute a comp method, mainly used from the outside world aka REPL
        """
        try:
            if method == 'broadcast':
                self._context['topic'] = topic
                self._push(data)
            else:
                comps = None
                if topic is None:
                    comps = self._comps.values()
                else:
                    if topic in self._comps:
                        comps = [self._comps[topic]]
                if comps is not None:
                    for comp in comps:
                        self._exec_func(comp, method, data)
                return True
        except Exception as ex:
            if mode_debug:
                import sys
                sys.print_exception(ex)
            self._log_error('{0}@upyhome::exec'.format(ex))
            return False

    def ping(self):
        """
        Respond to a ping, mainly used by WebREPL client
        """
        print('#pong')

    def _test_error(self):
        """
        make an error
        """
        try:
            raise Exception('Test exception')
        except Exception as ex:
            self._log_error('{0}@upyhome::test_error'.format(ex))

    def _log_error(self, err):
        """
        Log the last error, maximum size is 2kb
        """
        import sys
        import uos
        import machine
        mode = 'a'
        if ERROR_FILE in uos.ilistdir():
            size = uos.stat(ERROR_FILE)[6]
            if size > 2000:
                mode = 'w'
        with open('err.log', mode) as f:
            dt = machine.RTC().datetime()
            f.write('timestamp = %d/%02d/%02d - %02d:%02d:%02d\n'%(dt[0],dt[1],dt[2],dt[4],dt[5],dt[6]))
            f.write('%s\n'%(err))


    def _get_config_key(self, config, key, suppress=False):
        """
        Get a key value in a dictionnary, optionnaly suppress it
        """
        val = config[key] if key in config else None
        if val is not None and suppress:
            del config[key]
        return val

    def _config_comp(self, key, conf_func, suppress=True):
        """
        Configure a component
        """
        _DEBUG('upyhome::_config_comp::{0}'.format(key))
        if key in self._config:
            if self._config[key]:
                conf_func(self._config[key])
            if suppress:
                del self._config[key]

    def configure(self):
        """
        Configure whole upyHome components
        """
        try:
            self._load_config()
            global mode_debug
            mode_debug= self._get_config_key(self._config, KEY_DEBUG, True)
            _DEBUG('upyhome::configure')
            global platform 
            platform = self._get_config_key(self._config, KEY_PLATFORM, True)
            # Re init base cb
            self._init_cb(self._get_config_key(self._config, KEY_USER_CB, True))
            
            #components
            CONFIG_COMPS= [
                (CONFIG_NET, self._config_network),
                (CONFIG_DIN, self._config_inputs),
                (CONFIG_DOUT, self._config_outputs),
                (CONFIG_LED, self._config_leds),
                (CONFIG_I2C, self._config_i2cs),
                (CONFIG_SPI, self._config_spis),
                (CONFIG_DRIVER, self._config_drivers)
            ] 
            for CONF in CONFIG_COMPS:
                self._config_comp(*CONF)
        except Exception as ex:
            if mode_debug:
                import sys
                sys.print_exception(ex)
            self._log_error('{0}@upyhome::configure'.format(ex))

    def _load_config(self):
        _DEBUG('upyhome::_load_config')
        import uos
        if not CONFIG_FILE in uos.listdir():
            raise Exception("config file not found")
        import ujson
        cf = open(CONFIG_FILE, 'r')
        self._config = ujson.load(cf)
        cf.close()        

    def _config_network(self, conf):
        from lib.net import Net
        conf = self._get_config_key(self._config, CONFIG_NET)
        nets = self._get_config_key(conf, CONFIG_WIFI, suppress=True)
        self._comps[KEY_NET] = Net(self._tidx, self._proxy, nets, **conf)
        self._tidx += 1

    def _config_inputs(self, confs):
        from lib.din import DigitalInputPin
        for conf in confs:
            topic = conf[KEY_TOPIC]
            self._comps[topic] = DigitalInputPin(self._tidx, self._proxy, **conf)
            self._tidx  += 1
    
    def _config_outputs(self, confs):
        from lib.dout import DigitalOutputPin
        for conf in confs:
            topic = conf[KEY_TOPIC]
            self._comps[topic] = DigitalOutputPin(self._proxy, **conf)

    def _config_leds(self, confs):
        from lib.led import Led
        for conf in confs:
            topic = conf[KEY_TOPIC]
            self._comps[topic] = Led(self._tidx, **conf)
            self._tidx += 1
    
    def _config_i2cs(self, confs):
        from machine import I2C
        from machine import Pin
        for conf in confs:
            name = self._get_config_key(conf, "name", True)
            hard = self._get_config_key(conf, "hard", True)
            num = self._get_config_key(conf, "num", True)
            if hard:
                self._comps[name] = I2C(num, **conf) 
            else:
                conf["sda"] = Pin(conf["sda"])
                conf["scl"] = Pin(conf["scl"])
                self._comps[name] = I2C(**conf)

    def _config_spis(self, confs):
        # TODO Implements SPI
        pass

    def _config_drivers(self, confs):
        # TODO: rewrite code
        for conf in self._config[CONFIG_DRIVER]:
            if CONFIG_I2C in conf:
                i2c_port = self._get_config_key(conf, "i2c", True)
                driver = self._get_config_key(conf, "driver", True)
                name = self._get_config_key(conf, "name", True)
                address = int(self._get_config_key(conf, "address", True), 16)
                polling = self._get_config_key(conf, "polling", True)
                if address in self._comps[i2c_port].scan():
                    module = __import__(driver)
                    class_ = getattr(module, driver.upper())
                    i2c_port = self._comps[i2c_port]
                    self._comps[name] = class_(name, self._tidx, i2c=i2c_port, address=address, polling=polling, **conf)
                    self._tidx += 1
                else:
                        print("address {} not found in the i2c network {}".format(address, i2c_port))
