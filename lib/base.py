"""
This file is part of upyHome
Copyright (c) 2020 ng-galien
Licensed under the MIT license:
http://www.opensource.org/licenses/mit-license.php
Project home:
https://github.com/upyhome/upyhome
"""

from collections import namedtuple
from micropython import schedule
from lib.common import log_error, _debug
from lib.common import KEY_TOPIC, KEY_USER_CB, KEY_EVENT, KEY_MUTE, KEY_STATE, KEY_NEXT, KEY_SUSCRIBES

class Base:
    """
    Base class for every UPH components.
    By convention all the function prefixed with _ aren't exposed to user code
    """
    def __init__(self, **kwargs):
        self._topic = kwargs.pop(KEY_TOPIC)
        self._state = {}
        self._val = None
        self._mute = kwargs.pop(KEY_MUTE, False)
        self._context = {KEY_EVENT: None, KEY_TOPIC: self._topic, KEY_NEXT: True,
            'emit': True, KEY_STATE: self._state}
        self._init_cb(kwargs.pop(KEY_USER_CB, None))

    def _init_cb(self, user):
        """
        Init the user callback, from a text in the config or in code
        """
        self._custom_cb = user
        self._user_cb = self._user_eval if user is not None else None


    def _set_callback(self, user_cb):
        """
        Set the user callback programmaticely
        """
        self._user_cb = user_cb

    def _user_eval(self, code=None):
        """
        Evaluate the and user callbcak function
        """
        if code is None:
            if self._custom_cb is not None: 
                exec(self._custom_cb, self._context)
        else:
            exec(code, self._context)
        return self._context[KEY_NEXT]


    def mute(self, m=None):
        """
        If mute the component does not print anything to the console
        """
        if m is None:
            return self._mute
        else:
            self._mute = m

    def value(self):
        """
        Get the value of the component
        """
        return None 


    def _message(self):
        """
        Format the message to be printed
        """
        return '#{0}=[{1}]'.format(self._topic, self.value())

    def start(self):
        pass

    def stop(self):
        pass

def take_priority(elem):
    return elem._priority

class Proxy():
    """
    The proxy route messages beetween components. \
    The publishers send a message for a topic and a suscriber to the same topic recieve the message.
    """
    def __init__(self):
        self._suscribers = {}

    def add_publisher(self, pub):
        pub._on_event = self._emit

    def add_suscriber(self, suscriber, topic):
        _debug('add suscriber %s from %s'%(topic, suscriber._topic))
        if topic not in self._suscribers:
            self._suscribers[topic] = []
        self._suscribers[topic].append(suscriber)
        self._suscribers[topic].sort(key=take_priority, reverse=True)

    def _emit(self, context):
        try:
            topic = context[KEY_TOPIC]
            if topic in self._suscribers:
                for sub in self._suscribers[topic]:
                    if not sub._pull(context):
                        break
        except RuntimeError as ex:
            log_error(ex)
        


class Publisher(Base):
    """
    Publisher for a topic, typicaly a button or a sensor
    """
    def __init__(self, proxy, **kwargs):
        super().__init__(**kwargs)
        self._schedule = False
        proxy.add_publisher(self)

    def _push(self, event):
        """
        Push a message to the Proxy. Data is in the context defined in base class
        """
        _next = True
        self._context[KEY_TOPIC] = self._topic
        self._context[KEY_EVENT] = event
        if self._user_cb is not None:
            self._context[KEY_NEXT] = True
            _next = self._user_cb()
        if not self._mute and self._context['emit']:
            print(self._message())
        if _next:
            if self._schedule:
                schedule(self._on_event, self._context)
            else:
                self._on_event(self._context)

    def _on_event(self, event):
        """
        Method assigned by the proxy
        """
        pass

class Suscriber(Publisher):
    """
    Can suscribe to events.
    Can also emit scheduled events.
    """
    def __init__(self, proxy, **kwargs):# proxy=None, user=None, suscribe=None, priority=0):
        super().__init__(proxy, **kwargs)
        # A subscriber should schedule it's push
        self._schedule = True
        self._priority = kwargs.get('priority', 0)
        self._user_code = []
        self._suscribes = {}
        if proxy is not None:
            proxy.add_publisher(self)
            conf = kwargs.get(KEY_SUSCRIBES, [])
            for scb in conf:
                self._add_suscribe(proxy, scb)
            self._init_context()

    def _add_suscribe(self, proxy, conf):
        """
        Add a suscribe configuation
        """
        _debug('add suscbribe {0} to {1}'.format(conf, self._topic))
        if conf is not None:
            self._user_code.append(conf[KEY_USER_CB])
            for topic in conf['topics']:
                proxy.add_suscriber(self, topic)
                self._suscribes[topic] = self._user_code[-1]
    
    def _init_context(self):
        """
        Set the global context for the user code, public methods can by called in user code with action.method().
        """
        members = dir(self)
        _actions = {}
        for m in members:
            func = getattr(self, m)
            if callable(func) and m[:1] != '_':
                _actions[m] = func
        Actions = namedtuple('Actions', sorted(_actions))
        self._context['action'] = Actions(**_actions)

    def _pull(self, context):
        """
        Recieve the message from the proxy. Data is in the context defined in base.
        The context is owned by the sender.
        We run the user code here.
        """
        topic_from = context[KEY_TOPIC]
        if topic_from == self._topic:
            return True
        self._context[KEY_NEXT] = True
        self._context['emit'] = True
        self._context[KEY_TOPIC] = context[KEY_TOPIC]
        self._context[KEY_EVENT] = context[KEY_EVENT]
        self._context[KEY_STATE] = context[KEY_STATE]
        if self._suscribes[topic_from] is not None:
            _next = self._user_eval(self._suscribes[topic_from])
            return _next
        else:
            return True
