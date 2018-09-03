import ccxt
import logging
from configparser import ConfigParser
from WechatHandler import WechatHandler

logger = logging.getLogger('rich')


class Application:

    config = None
    exchange = dict()

    @staticmethod
    def read_config(f):
        Application.config = ConfigParser()
        Application.config.read(f)

        logging.basicConfig(level=logging.INFO)

        loggers = Application.config.get('LOGGING', 'LOGGER').split()

        logging.getLogger('rich').info('loggers: %s' % str(loggers))

        if 'wechat' in loggers:
            wechat = WechatHandler()
            wechat.setLevel(logging.WARNING)
            logger.addHandler(wechat)
            logger.warning(u'微信登录成功!')

    @staticmethod
    def get_exchange(contract_type='quarter'):

        if Application.config is None:
            return None

        if contract_type not in Application.exchange.keys():
            e = ccxt.okex({'API_KEY': Application.config.get('OKEX', 'API_KEY'), 
                           'SECRET': Application.config.get('OKEX', 'SECRET')})
            e.load_markets()
            e.options['defaultContractType'] = contract_type
            Application.exchange[contract_type] = e

        return Application.exchange[contract_type]

