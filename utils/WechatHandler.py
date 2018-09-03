import logging
import itchat


class WechatHandler(logging.Handler):

    chat = None
    username = None

    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        try:
            itchat.auto_login(hotReload=True, enableCmdQR=2)
        except Exception as e:
            print(str(e))

        if WechatHandler.chat is None:
            WechatHandler.chat = itchat
        if WechatHandler.username is None:
            WechatHandler.username = WechatHandler.chat.search_friends(name='杨硕')[0]['UserName']

    def emit(self, record):
        self.chat.send(self.format(record), toUserName=WechatHandler.username)


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('rich')

    wechat = WechatHandler()
    wechat.setLevel(logging.WARNING)
    logger.addHandler(wechat)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    logger.warning("I'm a warning")
    logger.info("I'm an info")
    logger.debug("I'm a debug")
