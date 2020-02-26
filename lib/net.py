"""
This file is part of upyHome
Copyright (c) 2020 ng-galien
Licensed under the MIT license:
http://www.opensource.org/licenses/mit-license.php
Project home:
https://github.com/upyhome/upyhome
"""

from machine import Timer
import network
from lib.base import Publisher
from upyhome import KEY_TOPIC

KEY_SSID = 'ssid'
KEY_PWD = 'pwd'
KEY_DHCP = 'dhcp'
KEY_IP = 'ip'
KEY_MASK = 'mask'
KEY_GATEWAY = 'gateway'
KEY_DNS = 'dns'


class Net(Publisher):
    """
    Network component
    """
    def __init__(self, tid, proxy, nets, **kwargs):# nets, repl='repl', user=None, polling=3000):
        super().__init__(proxy, **kwargs)
        self.net = None
        self.nets = nets
        self._host_name = kwargs.get('hostname')
        self._polling = kwargs.get('polling', 3000)
        self._repl = kwargs.get('repl', 'upyhome')
        self._timer = Timer(tid)
        self.wlan = network.WLAN(network.STA_IF)
        self._mdns = None
        self.val = network.STAT_IDLE
        self.connect()

    def value(self):
        return self.wlan.status()

    def _timer_cb(self, tim):
        if self.wlan.status() != self._val:
            self._val = self.wlan.status()
            self._push(self._val)
        if not self.wlan.isconnected():
            if not self.wlan.status() == network.STAT_CONNECTING:
                self.connect()
        else:
            if self._mdns is None:
                self.init_mdns()
            else:
                self._mdns.advertise_hostname("upyhome.local")
            self._timer.deinit()
            self._timer.init(period=self._polling, mode=Timer.ONE_SHOT, callback=self._timer_cb)

    def connect(self):
        self._timer.deinit()
        self.wlan.active(True)
        if not self.wlan.isconnected():
            wans = self.wlan.scan()
            self.net = None
            rssi = -100
            for net in self.nets:
                for wan in wans:
                    if wan[0].decode() == net[KEY_SSID]:
                        if wan[3] > rssi:
                            rssi = wan[3]
                            self.net = net
            if self.net:
                self.wlan.config(dhcp_hostname=self._host_name)
                if KEY_DHCP in self.net and not self.net[KEY_DHCP]:
                    self.wlan.ifconfig((self.net[KEY_IP], self.net[KEY_MASK], self.net[KEY_GATEWAY], self.net[KEY_DNS]))
                self.wlan.connect(self.net[KEY_SSID], self.net[KEY_PWD])
                self._timer.init(period=1000, mode=Timer.PERIODIC, callback=self._timer_cb)
        else:
            cur_ssid = self.wlan.config('essid')
            for net in self.nets:
                if cur_ssid == net[KEY_SSID]:
                    self.net = net
            self._timer.init(period=self._polling, mode=Timer.ONE_SHOT, callback=self._timer_cb)

    def init_mdns(self):
        pass
            