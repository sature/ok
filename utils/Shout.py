import itchat
import datetime


class Shout():

    chat = None
    userName = None

    @staticmethod
    def login():

        # try:
        #     itchat.auto_login(hotReload=True, enableCmdQR=2)
        # except Exception as e:
        #     print(e)
        #
        # if Shout.chat is None:
        #     Shout.chat = itchat
        # if Shout.userName is None:
        #     Shout.userName = Shout.chat.search_friends(name='杨硕')[0]['UserName']

        pass

    @staticmethod
    def send(message):
        timestamp = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
        # Shout.chat.send(timestamp+"\n"+message, toUserName=Shout.userName)
        print(timestamp+"\n"+message)

