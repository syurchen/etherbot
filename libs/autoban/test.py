'''
import sys
from autobahn.twisted.wamp import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner
from autobahn.twisted.util import sleep
from twisted.internet.defer import inlineCallbacks
'''

from __future__ import print_function
from os import environ

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner


class component(ApplicationSession):
    def onJoin(self, details):
        print("session ready")
        print(details)
        counter = 0
        sub = yield self.subscribe(self.on_event, u'ticker')
        print("Subscribed to com.myapp.topic1 with {}".format(sub.id))  
'''
        def oncounter(count):
            print("event received: {0}", count)

        def on_event(self, i):
            print("Got event: {}".format(i))
            self.received += 1
            # self.config.extra for configuration, etc. (see [A])

        def onDisconnect(self):
            print("disconnected")
            if reactor.running:
                reactor.stop()
'''
	
#runner = ApplicationRunner(url=u"ws://localhost:8080/ws", realm=u"realm1")
#runner = ApplicationRunner(url=u"wss://api.poloniex.com", realm=u"realm1")
#runner.run(MyComponent)

if __name__ == '__main__':
    runner = ApplicationRunner(
            u"wss://api.poloniex.com",
            realm=u"realm1",
    )
    runner.run(component)

