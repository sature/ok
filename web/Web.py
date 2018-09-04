from flask import Flask
from flask_restful import Api
import logging
import threading

logger = logging.getLogger('rich')


class Web:

    app = None

    @staticmethod
    def start(resources):
        Web.app = Flask(__name__)
        api = Api(app)

        for r in resource:
            r.register_rest_api(api)

        threading.Thread(target=Web.run).start()

    def run():
        Web.app.run(port='8080')
        logger.warning('web server started on port 8080')

