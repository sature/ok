import ccxt
import logging
from configparser import ConfigParser
from WechatHandler import WechatHandler
from flask import Flask
from flask_restful import Api
import threading
from K import K


logger = logging.getLogger('rich')


class Application:

    config = None
    exchange = dict()
    webapp = None

    @staticmethod
    def read_config(f):
        Application.config = ConfigParser()
        Application.config.read(f)

        # logging
        logging.basicConfig(level=logging.INFO)
        loggers = Application.config.get('LOGGING', 'LOGGER').split()
        logging.getLogger('rich').info('loggers: %s' % str(loggers))
        if 'wechat' in loggers:
            wechat = WechatHandler()
            wechat.setLevel(logging.WARNING)
            logger.addHandler(wechat)
            logger.warning(u'微信登录成功!')

        # web
        Application.webapp = Flask(__name__)
        api = Api(Application.webapp)
        K.register_rest_api(api)

        threading.Thread(target=Application._start_web_app).start()

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

    @staticmethod
    def _start_web_app():
        Application.webapp.run(host='0.0.0.0', port=Application.config.get('WEB', 'PORT'))
