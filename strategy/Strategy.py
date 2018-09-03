import logging


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
        #     logging.warning("Doesn't support multiple signals in a strategy now, skipped the second sign")
        #     return

        self.signals.append(s)
        logging.info('%s: Added sign %s', self.name, s.name)
        s.subscribe(self.check)
        s.start()

    def remove_signal(self, s):
        s.unsubscribe(self.check)
        self.signals.remove(s)
        logging.info('%s: Removed sign %s', self.name, s.name)

    def check(self, event):
        logging.error('%s is not handling sign %s' % (self.name, event.source.name))

    def set_name(self, name):
        self.name = 'Strategy[%s/%d]' % (name, Strategy.id)

    def log(self, msg):
        return 'Strategy[%s] ' % self.name + msg
