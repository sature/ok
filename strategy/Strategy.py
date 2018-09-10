import logging
from utils import App
from flask import jsonify

logger = logging.getLogger('rich')


class Strategy:

    k = None
    id = 0
    strategies = []

    def __init__(self):
        self.signals = []
        self.name = 'Strategy[-]'
        self.contract = None
        self.id = Strategy.id
        Strategy.id += 1
        Strategy.strategies.append(self)

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

    def get_signals(self):
        return self.signals

    def check(self, event):
        logger.error('%s is not handling sign %s' % (self.name, event.source.name))

    def set_name(self, name):
        self.name = 'Strategy[%s-%d]' % (name, self.id)

    def log(self, msg):
        return '%s: %s' % (self.name, msg)

    def get_id(self):
        return self.id

    @staticmethod
    def get_strategy(strategy_id):
        for s in Strategy.strategies:
            if s.id == strategy_id:
                return s
        else:
            return None

    @staticmethod
    @App.webapp.route('/strategy', methods=['GET'])
    def rest_get_strategies():
        logger.info('web getting strategies')
        return jsonify({
            'strategy': [{
                'id': strategy.get_id(),
                'name': strategy.name,
                'signals': [signal.get_dict() for signal in strategy.get_signals()]
            } for strategy in Strategy.strategies]
        })

    @staticmethod
    @App.webapp.route('/strategy/<strategy_id>', methods=['GET'])
    def rest_get_strategy(strategy_id):
        logger.info('[REST] Get strategy id=%d' % int(strategy_id))
        s = Strategy.get_strategy(int(strategy_id))
        return jsonify({}) if s is None else jsonify({
            'id': s.id,
            'name': s.name,
            'signals': [signal.get_dict() for signal in s.get_signals()]
        })
