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

from lib.base import Base

class Publisher(Base):

    def __init__(self, topic, proxy, user_cb=None):
        super().__init__(topic, user_cb)
        if proxy is not None:
            proxy.add_pub(self)
        self._proxy = proxy  
        
    def _push(self, event):
        _push = True
        self._context['event'] = event
        if self._user_cb is not None:
            self._context['next'] = True
            _next = self._user_cb(self._context)
            _push = _next
        if _push:
            self._on_event(self._context)

    def _on_event(self, event):
        pass

