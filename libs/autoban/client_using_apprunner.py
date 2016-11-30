import txaio
txaio.use_twisted()

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.application.internet import ClientService

from autobahn.wamp.types import ComponentConfig
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner

class MyAppSession(ApplicationSession):

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self._countdown = 5

    def onConnect(self):
        self.log.info('transport connected')

        self.join(self.config.realm)

    def onChallenge(self, challenge):
        self.log.info('authentication challenge received')


    def onJoin(self, details):
        #self.log.info('session joined: {}'.format(details))
        sub = self.subscribe(self.on_event, u'ticker')

    def onLeave(self, details):
        self.log.info('session left: {}'.format(details))
        self.disconnect()

    def onDisconnect(self):
        self.log.info('transport disconnected')
        self._countdown -= 1
        if self._countdown <= 0:
            try:
                reactor.stop()
            except ReactorNotRunning:
                pass
    
    def on_event(*args):
        monitor_events = ["BTC_ZEC", "BTC_ETH", "BTC_XMR", "BTC_REP"]
        if args[1] in monitor_events:
            print( args[1] + ' = ' + args[2])

def start_ticker():
    session = MyAppSession(ComponentConfig(u'realm1', {}))
    runner = ApplicationRunner(u'wss://api.poloniex.com:443', u'realm1')
    runner.run(session, auto_reconnect=True)

start_ticker()
