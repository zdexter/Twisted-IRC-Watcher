import optparse
from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ClientFactory
from twisted.words.protocols.irc import IRCClient
from twisted.internet.defer import Deferred

class IRCBot(IRCClient):
    def __init__(self):
        self.d = Deferred()
    
    def _printMessage(message):
        print message
    
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)
    
    def signedOn(self):
        self.join(self.factory.channel)
        print('{} signed on as {}'.format(self.nickname, self.factory.channel))
    
    def joined(self, channel):
        print('{} joined channel {}.'.format(self.nickname, self.factory.channel))
    
    def privmsg(self, user, channel, msg):
        watchwords = [
            self.factory.watchword,
            self.factory.watchword.lower(),
            self.factory.watchword.upper()
        ]
        
        if len(filter(lambda substring: (substring in watchwords), msg.split(' '))) > 0:
            # The above filter() adds a substring to
            #    the return list IFF the lambda function returns true.
            print 'Saw the watchword!'
        
        print('[Message from {} in {}]: {}'.format(user, channel, msg))
    
    def left(self, channel):
        print('Left channel {}.'.format(channel))
    
class IRCBotFactory(ClientFactory):
    def __init__(self, channel, watchword, nickname='MyTestBot'):
        self.channel = channel
        self.nickname = nickname
        self.watchword = watchword
    
    protocol = IRCBot
    
    def clientConnectionFailed(self, connector, reason):
        print('IRC Client: Client connection failed because: {}'.format(reason))
        connector.connect()
    
    def clientConnectionLost(self, connector, reason):
        print('IRC Client: Client connection lost because: {}'.format(reason))

def parse_args():
    usage_text = """usage: %prog [IRC channels to join]
    IRC bot that joins several channels and uses an event loop to 
        detect and print(incoming messages.
    
    Todo: be more true to the claim that the event loop is async 
        with respect to input and output by deferring prints.
    
    Todo: Alert user of any messages containing a specified keyword, 
        and allow user to respond to those messages.
    
    """
    # Unpack returned tuple
    parser = optparse.OptionParser(usage_text)
    
    parser.add_option('--hostname', type='string', default='localhost')
    parser.add_option('--watchword', type='string', default='lunch')
    
    options, args = parser.parse_args()
    
    if len(args) < 1:
        raise Exception('Please provide at least one channel name.')
    return args, options.hostname, options.watchword
    
class Monitor:
    """
    Class instances print(incoming IRC messages to the console.
    Incoming messages are printed by the event loop.
    """
    def __init__(self, channels, hostname, watchword):
        from twisted.internet import reactor
        for channel in channels:
            print('Twisted: Reactor listening on channel {}'.format(channel))
            reactor.connectTCP(hostname, 6667, IRCBotFactory(channel, watchword))
        reactor.run()

if __name__ == '__main__':
    hostname = None
    channels, hostname, watchword = parse_args()
    
    if not hostname:
        raise Exception('Please provide a fully-qualified hostname.')
    
    myMonitor = Monitor(channels, hostname, watchword)