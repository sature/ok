import os
import ccxt
import logging
from configparser import ConfigParser
from WechatHandler import WechatHandler
from flask import Flask, send_from_directory

logger = logging.getLogger('rich')


class Application:

    config = None
    exchange = dict()
    webapp = Flask('Rich')

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

        web_dir = os.path.split(os.path.realpath(__file__))[0] + '/../web/'

        @Application.webapp.route('/', methods=['GET'])
        def get_homepage():
            logger.info('get %s' % web_dir + 'index.html')
            return send_from_directory(web_dir, 'index.html')

        @Application.webapp.route('/js/<filename>', methods=['GET'])
        def get_js(filename):
            logger.info('get %s' % web_dir + 'js/' + filename)
            return send_from_directory(web_dir + 'js', filename)

        @Application.webapp.route('/css/<filename>', methods=['GET'])
        def get_css(filename):
            logger.info('get %s' % web_dir + 'css/' + filename)
            return send_from_directory(web_dir + 'css', filename)

        @Application.webapp.route('/fonts/<filename>', methods=['GET'])
        def get_fonts(filename):
            logger.info('get %s' % web_dir + 'fonts/' + filename)
            return send_from_directory(web_dir + 'fonts', filename)

        @Application.webapp.route('/asset/<path>/<filename>', methods=['GET'])
        def get_asset(path, filename):
            logger.info('get %s' % web_dir + 'asset/' + path + '/' + filename)
            return send_from_directory(web_dir + 'asset/' + path, filename)

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
    def start():
        Application.webapp.run(host='0.0.0.0', port=Application.config.get('WEB', 'PORT'))
