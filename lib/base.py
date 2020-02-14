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

from collections import namedtuple
import micropython

class Base:
    """
    Base class for every UPH components.
    By convention all the function prefixed with _ aren't exposed to user code
    """
    def __init__(self, topic, user, mute=False):
        self._topic = topic
        self._state = {}
        self._proxy = None
        self._val = None
        self._mute = mute
        self._init_cb(user)
        self._context = {
            'event': None, 'topic': self._topic, 'next': True, 
            'emit': True, 'state': self._state, 'emitter': self._topic}  
    """
    Init the user callback, from a text in the config or in code
    """
    def _init_cb(self, user):
        self._custom_cb = user
        self._user_cb = self._user_eval if user else None

    """
    Set the user callback programmaticely
    """
    def _set_callback(self, user_cb):
        self._user_cb = user_cb
    """
    Evaluate the and user callbcak function
    """
    def _user_eval(self, code=None):
        if code is None:
            if self._custom_cb is not None: 
                exec(self._custom_cb, self._context)
        else:
            exec(code, self._context)
        return self._context['next']

    """
    If mute the component does not print anything to the console
    """
    def mute(self, m=None):
        if m is None:
            return self._mute
        else:
            self._mute = m

    """
    Get the value of the component
    """
    def value(self):
        return None 

    """
    Format the message to be printed
    """
    def _message(self):
        return '#{}=[{}]'.format(self._topic,self.value())

    def start(self):
        pass

    def stop(self):
        pass

class Proxy():
    """
    The proxy route messages beetween components. \
    The publishers send a message for a topic and a suscriber to the same topic recieve the message.
    """
    def __init__(self):
        self._suscribers={}

    def add_publisher(self, pub):
        pub._on_event = self._emit

    def add_suscriber(self, sub, topic, priority=0):
        if topic not in self._suscribers:
            self._suscribers[topic] = []
        self._suscribers[topic].append(sub)

    def _emit(self, context):
        topic = context['topic']
        if topic in self._suscribers:
            for sub in self._suscribers[topic]:
                if not sub._pull(context):
                    break


class Publisher(Base):
    """
    Publisher for a topic, typicaly a button or a sensor
    """
    def __init__(self, topic, proxy, user=None):
        super().__init__(topic, user)
        self._schedule = False
        if proxy is not None:
            proxy.add_publisher(self)

    def _push(self, event):
        """
        Push a message to the Proxy. Data is in the context defined in base class
        """
        _next = True
        self._context['topic'] = self._topic
        self._context['event'] = event
        if self._user_cb is not None:
            self._context['next'] = True
            _next = self._user_cb()
        if not self._mute and self._context['emit']:
            print(self._message())
        if _next:
            if self._schedule:
                micropython.schedule(self._on_event, self._context)
            else:
                self._on_event(self._context)

    def _on_event(self, event):
        """
        Method assigned by the proxy
        """
        pass

class Subscriber(Publisher):
    """
    Can suscribe to events.
    Can also emit scheduled events.
    """
    def __init__(self, topic, proxy=None, user=None, suscribe=None):
        super().__init__(topic, proxy, user)
        # A subscriber should schedule it's push
        self._schedule = True
        self._suscribe = suscribe
        if proxy is not None:
            proxy.add_publisher(self)
            if self._suscribe is not None:
                for topic in self._suscribe['topics']:
                    proxy.add_suscriber(self, topic)
        self._init_context()

    def _init_context(self):  
        """
        Set the global context for the user code, public methods can by called in user code with action.method().
        """
        members = dir(self)
        _actions = {}
        for m in members:
            func = getattr(self, m)
            if callable(func) and m[:1] != '_':
                _actions[m]=func
        Actions = namedtuple('Actions', sorted(_actions))
        self._context['action'] = Actions(**_actions)

    def _pull(self, context):
        """
        Recieve the message from the proxy. Data is in the context defined in base.
        The context is owned by the sender.
        We run the user code here.
        """
        if context['topic'] == self._topic:
            return True
        self._context['next'] = True
        self._context['emit'] = True
        self._context['topic'] = context['topic']
        self._context['event'] = context['event']
        _next = self._user_eval(self._suscribe['user'])
        return _next
