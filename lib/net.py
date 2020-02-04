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
from machine import Timer
import network
from lib.pub import Publisher

class Net(Publisher):
    def __init__(self, tid, nets, proxy=None, user_cb=None, polling=3000):
        super().__init__('net', proxy, user_cb)
        self.net = None
        self.nets = nets
        self.polling = polling
        self.timer = Timer(tid)
        self.wlan = network.WLAN(network.STA_IF)
    
    def value(self):
        return self.wlan.status() 

    def timer_cb(self, tim):
        if not self.wlan.isconnected():
            if self.wlan.status() == network.STAT_CONNECTING:
                self._push('P')
            else:
                self._push('D')
                self.connect()
        else:
            self._push('C')
            self.timer.deinit()
            self.timer.init(period=self.polling, mode=Timer.ONE_SHOT, callback=self.timer_cb)

    def start(self):
        self.connect()

    def stop(self):
        self.timer.deinit()

    def connect(self):
        #print('connect')
        self.timer.deinit()
        self.wlan.active(True)
        if not self.wlan.isconnected():
            wans = self.wlan.scan()
            #print(wans)
            self.net = None
            rssi = -100 
            for net in self.nets:
                for wan in wans:
                    if wan[0].decode() == net['ssid']:
                        if wan[3] > rssi:
                            rssi = wan[3]
                            self.net = net
            if self.net:
                #print('connect to %s'%(sel['ssid']))
                self.name = self.net['name']
                self.wlan.config(dhcp_hostname=self.net['name'])
                if not self.net['use_dhcp']:
                    self.wlan.ifconfig((self.net['ip'], self.net['mask'], self.net['gateway'], self.net['dns']))
                self.wlan.connect(self.net["ssid"], self.net["pwd"])
                self.timer.init(period=1000, mode=Timer.PERIODIC, callback=self.timer_cb)
        else:
            cur_ssid = self.wlan.config('essid')
            for net in self.nets:
                if cur_ssid == net['ssid']:
                    self.net = net
                    self._name = net['name']
            self.timer.init(period=self.polling, mode=Timer.ONE_SHOT, callback=self.timer_cb)


