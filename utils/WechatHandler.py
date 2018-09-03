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
        if WechatHandler.userName is None:
            WechatHandler.userName = WechatHandler.chat.search_friends(name='杨硕')[0]['UserName']

    def emit(self, record):
        self.chat.send(self.format(record), toUserName=self.userName)

        pass


if __name__ == '__main__':

    handler = WechatHandler()
    logger = logging.getLogger('test')
    logger.addHandler(handler)

    logger.warning("gaga")
