import logging
from utils import App
from flask import jsonify

logger = logging.getLogger('rich')


class Strategy:

    k = None
    id = 0
    strategies = []

    def __init__(self, k, amount = 1):
        self.k = k
        self.amount = amount
        self.signals = []
        self.name = 'Strategy[-]'
        self.contract = None
        self.id = Strategy.id
        Strategy.id += 1
        Strategy.strategies.append(self)

    def add_signal(self, s):

        self.signals.append(s)
        logger.info('%s: Added signal %s', self.name, s.name)
        s.subscribe(self.check)
        s.start(self.k)

    def remove_signal(self, s):
        s.stop()
        s.unsubscribe(self.check)
        self.signals.remove(s)
        logger.info('%s: Removed signal %s', self.name, s.name)

    def get_signals(self):
        return self.signals

    def check(self, event):
        logger.error('%s is not handling sign %s' % (self.name, event.source.name))

    def set_name(self, name):
        self.name = name

    def log(self, msg):
        return '%s: %s' % (self.name, msg)

    def get_id(self):
        return self.id

    # @staticmethod
    # def get_strategy(strategy_id):
    #     for s in Strategy.strategies:
    #         if s.id == strategy_id:
    #             return s
    #     else:
    #         return None
    #
    @staticmethod
    def get_strategy_dict(sid):
        for s in Strategy.strategies:
            if s.id == sid:
                return dict({
                    'id': sid,
                    'name': s.name,
                    'amount': s.amount,
                    'k': {
                        'exchange': s.k.exchange.name,
                        'symbol': s.k.symbol,
                        'period': s.k.period,
                        'type': s.k.exchange.options['defaultContractType']
                    },
                    'signals': [signal.get_dict() for signal in s.get_signals()]
                })
        else:
            return dict({})

    @staticmethod
    @App.webapp.route('/strategy', methods=['GET'])
    def rest_get_strategies():
        logger.info('[REST] Get all %d/%d strategies.' % (len(Strategy.strategies), len(Strategy.strategies)))
        return jsonify([Strategy.get_strategy_dict(s.id) for s in Strategy.strategies])

    @staticmethod
    @App.webapp.route('/strategy/<sid>', methods=['GET'])
    def rest_get_strategy(sid):
        logger.info('[REST] Get strategy id=%d' % int(sid))
        return jsonify(Strategy.get_strategy_dict(int(sid)))
