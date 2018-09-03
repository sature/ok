import logging

logger = logging.getLogger('rich')


class Strategy:

    k = None
    id = 0

    def __init__(self):
        self.signals = []
        self.name = 'Strategy[-]'
        self.contract = None
        Strategy.id += 1

    def add_signal(self, s):

        # if len[self.signals] > 0:
        #     logger.warning("Doesn't support multiple signals in a strategy now, skipped the second sign")
        #     return

        self.signals.append(s)
        logger.info('%s: Added sign %s', self.name, s.name)
        s.subscribe(self.check)
        s.start()

    def remove_signal(self, s):
        s.unsubscribe(self.check)
        self.signals.remove(s)
        logger.info('%s: Removed sign %s', self.name, s.name)

    def check(self, event):
        logger.error('%s is not handling sign %s' % (self.name, event.source.name))

    def set_name(self, name):
        self.name = 'Strategy[%s/%d]' % (name, Strategy.id)

    def log(self, msg):
        return 'Strategy[%s] ' % self.name + msg
