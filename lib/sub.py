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
from collections import namedtuple
from lib.base import Base

class Subscriber(Base):

    def __init__(self, topic, proxy=None, topics=[], user_cb=None):
        super().__init__(topic, user_cb)
        if proxy is not None:
            proxy.add_sub(self, topic)
            for t in topics:
                proxy.add_sub(self, t)
        self._proxy = proxy
        self._init_context()

    def _init_context(self):  

        members = dir(self)
        _actions = {}
        for m in members:
            func = getattr(self, m)
            if callable(func) and m[:1] != '_':
                _actions[m]=func
        Actions = namedtuple('Actions', sorted(_actions))
        self._context['action'] = Actions(**_actions)

    def _pull(self, event):
        _pull = True 
        if self._user_cb is not None:
            self._context['next'] = True
            self._context['emit'] = True
            self._context['topic'] = event['topic']
            self._context['event'] = event['event']
            _next = self._user_cb(self._context)
            _pull = _next
        return _pull
