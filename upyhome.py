"""
This file is part of upyHome
Copyright (c) 2020 ng-galien
Licensed under the MIT license:
http://www.opensource.org/licenses/mit-license.php
Project home:
https://github.com/upyhome/upyhome
"""

from lib.base import Proxy, Suscriber
from machine import Timer, I2C, Pin
import uos
import ujson
from lib.common import MODE_DEBUG, PLATFORM, _debug, MAX_PRIORITY, log_error
from lib.common import CONFIG_FILE, CONFIG_NAME, CONFIG_HOSTNAME, CONFIG_NET, CONFIG_WIFI
from lib.common import CONFIG_DIN, CONFIG_DOUT, CONFIG_LED, CONFIG_I2C, CONFIG_SPI, CONFIG_DRIVER
from lib.common import KEY_PLATFORM, KEY_DEBUG, KEY_NET, KEY_TOPIC, KEY_USER_CB, KEY_NETWORKS, KEY_SUSCRIBES

_PROXY = Proxy()

class UpyHome(Suscriber):
    """
    Upyhome main class
    """
    def __init__(self):
        args = {'topic': 'upyhome'}
        super().__init__(_PROXY, **args)
        self._name = 'upyhome'
        self._proxy = _PROXY
        self._config = None
        self._priority = MAX_PRIORITY
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
        _debug('_exec_func {0}@{1} [{2}]'.format(function, obj, args))
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
        """
        Execute a comp method, mainly used from the outside world aka REPL
        """
        _debug('exec %s %s %s'%(method, topic, data))
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
            log_error('{0}@upyhome::exec'.format(ex))
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
            log_error('{0}@upyhome::test_error'.format(ex))

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
        _debug('upyhome::_config_comp::{0}'.format(key))
        if key in self._config:
            if self._config[key]:
                comp_config = self._config[key]
                #Check if component is disabled
                if isinstance(comp_config, dict):
                    if not 'disable' in comp_config: 
                        conf_func(comp_config)
                elif isinstance(comp_config, list):
                    cmp_confs = [cc for cc in comp_config if not 'disable' in cc]
                    conf_func(cmp_confs)
            if suppress:
                del self._config[key]

    def configure(self):
        """
        Configure whole upyHome components
        """
        try:
            self._load_config()

            
            MODE_DEBUG['value'] = self._get_config_key(self._config, KEY_DEBUG, True)
            _debug('upyhome::configure')
            
            PLATFORM['value'] = self._get_config_key(self._config, KEY_PLATFORM, True)
            self._name = self._config[CONFIG_NAME]
            # Re init base cb
            self._init_cb(self._get_config_key(self._config, KEY_USER_CB, True))
            #Configure components
            suscribes = self._get_config_key(self._config, KEY_SUSCRIBES)
            if suscribes is not None and isinstance(suscribes, list):
                for scb in suscribes:
                    self._add_suscribe(self._proxy, scb)
            #Components
            CONFIG_COMPS = [
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
            log_error('{0}@upyhome::configure'.format(ex))

    def _load_config(self):
        _debug('upyhome::_load_config')
        if not CONFIG_FILE in uos.listdir():
            raise Exception("config file not found")
        cf = open(CONFIG_FILE, 'r')
        self._config = ujson.load(cf)
        cf.close()        

    def _config_network(self, conf):
        from lib.net import Net
        if CONFIG_HOSTNAME not in conf:
            conf[CONFIG_HOSTNAME] = self._name + '.local'
        conf = self._get_config_key(self._config, CONFIG_NET)
        nets = self._get_config_key(conf, CONFIG_WIFI, suppress=True)
        self._comps[KEY_NET] = Net(self._tidx, self._proxy, nets, **conf)
        self._tidx += 1

    def _config_inputs(self, confs):
        from lib.din import DigitalInputPin
        for conf in confs:
            topic = conf[KEY_TOPIC]
            self._comps[topic] = DigitalInputPin(self._tidx, self._proxy, **conf)
            self._tidx += 1
    
    def _config_outputs(self, confs):
        from lib.dout import DigitalOutputPin
        for conf in confs:
            topic = conf[KEY_TOPIC]
            self._comps[topic] = DigitalOutputPin(self._proxy, **conf)

    def _config_leds(self, confs):
        from lib.led import Led
        for conf in confs:
            topic = conf[KEY_TOPIC]
            self._comps[topic] = Led(self._tidx, self._proxy, **conf)
            self._tidx += 1
    
    def _config_i2cs(self, confs):
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

