import logging


class S:

    k = None
    id = 0

    def __init__(self):
        self.signals = []
        self.name = 'Strategy[-]'
        self.contract = None
        S.id += 1

    def add_signal(self, s):

        # if len[self.signals] > 0:
        #     logging.warning("Doesn't support multiple signals in a strategy now, skipped the second signal")
        #     return

        self.signals.append(s)
        logging.info('%s: Added signal %s', self.name, s.name)
        s.subscribe(self.check)
        s.start()

    def remove_signal(self, s):
        s.unsubscribe(self.check)
        self.signals.remove(s)
        logging.info('%s: Removed signal %s', self.name, s.name)

    def check(self, event):
        logging.error('%s is not handling signal %s' % (self.name, event.source.name))

    def set_name(self, name):
        self.name = 'Strategy[%s/%d]' % (name, S.id)

    def log(self, msg):
        return 'Strategy[%s] ' % self.name + msg
