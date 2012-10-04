import optparse
import re
from twisted.internet import protocol
from twisted.words.protocols.irc import IRCClient
from twisted.internet.defer import Deferred

class IRCBot(IRCClient):
    """
    An instance of this class will connect to a single IRC channel
        and propagate output (watchword alerts, etc) up to the reactor
        via its IRCBotFactory instance.
    """
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)
    
    def signedOn(self):
        self.join(self.factory.channel)
        self.factory.defer_message('{} signed on as {}'.format(self.nickname, self.factory.channel))
        
    def joined(self, channel):
        self.factory.defer_message('{} joined channel {}.'.format(self.nickname, self.factory.channel))
    
    def privmsg(self, user, channel, msg):
        if re.search(self.factory.watchword, msg, flags=re.IGNORECASE):
            self.factory.defer_message('Saw the watchword!')
        
        self.factory.defer_message('[Message from {} in {}]: {}'.format(user, channel, msg))
    
    def left(self, channel):
        self.factory.defer_message('Left channel {}.'.format(channel))
    
class IRCBotFactory(protocol.ClientFactory):
    def __init__(self, defer_message, channel, watchword, nickname='MyTestBot'):
        self.defer_message = defer_message
        self.channel = channel
        self.nickname = nickname
        self.watchword = watchword
    
    protocol = IRCBot
    
    def clientConnectionFailed(self, connector, reason):
        self.defer_message('IRC Client: Client connection failed because: {}'.format(reason))
        connector.connect()
    
    def clientConnectionLost(self, connector, reason):
        self.defer_message('IRC Client: Client connection lost because: {}'.format(reason))

def parse_args():
    usage_text = """usage: %prog [IRC channels to join]
    IRC bot that joins several channels and uses an event loop to 
        detect and print(incoming messages.
    
    Todo: Figure out whether IRCBotFactory can be a singleton, and
        whether or not that would be meaningful, helpful or good.
    
    """
    
    parser = optparse.OptionParser(usage_text)
    
    parser.add_option('--hostname', type='string', default='localhost')
    parser.add_option('--watchword', type='string', default='lunch')
    
    options, args = parser.parse_args()
    
    if len(args) < 1:
        raise Exception('Please provide at least one channel name.')
    return args, options.hostname, options.watchword

class Monitor():
    """
    Class instances print incoming IRC messages to the console.
    Incoming messages are printed by the event loop.
    """
    def __init__(self, channels, hostname, watchword):
        # Change reactor implementation here
        # See http://krondo.com/?p=1333
        
        from twisted.internet import reactor
        self.reactor = reactor
        for channel in channels:
            reactor.connectTCP(hostname, 6667, \
                IRCBotFactory(self.defer_message, channel, watchword.lower()))
            self.defer_message('Twisted: Reactor listening on channel {}'.format(channel))
        
        reactor.run()
    
    def defer_message(self, message):
        self.reactor.callWhenRunning(self._print_message, message)

    def _print_message(self, message):
        print(message)

if __name__ == '__main__':
    # If this module is the main program
    #   the Python interpreter assigns the value __main__
    #   to the __name__ variable.
    channels, hostname, watchword = parse_args()
    
    if not hostname:
        raise Exception('Please provide a fully-qualified hostname.')
    
    myMonitor = Monitor(channels, hostname, watchword)