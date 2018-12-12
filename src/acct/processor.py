import os
import datetime
import subprocess
# 第三方库
from decouple import config
from gevent.server import DatagramServer
from pyrad.dictionary import Dictionary
from pyrad.packet import AcctPacket
# 自己的库
from utils import get_dictionaries
from settings import log, DICTIONARY_DIR, SECRET
from child_pyrad.packet import CODE_ACCOUNT_RESPONSE
from auth.models import User
from acct.models import AcctUser


class EchoServer(DatagramServer):
    dictionary: Dictionary = None

    def __init__(self, dictionary, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.dictionary = dictionary

    def handle(self, data, address):
        ip, port = address
        # print('from %s, data: %r' % (ip, data))

        # 解析报文
        request = AcctPacket(dict=self.dictionary, secret=SECRET, packet=data)
        # log.d('recv request: {}'.format(request))

        # 验证用户
        acct_user = verify(request)

        # 接受或断开链接
        if acct_user.is_valid:
            pass
        else:
            # 断开链接
            disconnect(mac_address=acct_user.mac_address)

        # 返回
        reply = acct_res(request)
        self.socket.sendto(reply.ReplyPacket(), address)


def verify(request):
    acct_user = AcctUser()

    # 提取报文
    # Acct-Status-Type:  Start-1; Stop-2; Interim-Update-3; Accounting-On-7; Accounting-Off-8;
    acct_user.acct_status_type = request["Acct-Status-Type"][0]
    acct_user.username = request['User-Name'][0]
    acct_user.mac_address = request['Calling-Station-Id'][0]
    log.d('IN: {iut}|{username}|{mac_address}'.format(
        iut=acct_user.acct_status_type, username=acct_user.username, mac_address=acct_user.mac_address)
    )

    now = datetime.datetime.now()
    user = User.select().where((User.username == acct_user.username) & (User.expired_at >= now)).first()
    if not user:
        acct_user.is_valid = False

    return acct_user


def disconnect(mac_address):
    log.i(f'disconnect session. mac_address: {mac_address}')

    command = f"ps -ef | grep -v grep | grep pppoe_sess | grep -i :{mac_address} | awk '{{print $2}}' | xargs kill"
    ret = subprocess.getoutput(command)

    log.d(f'ret: {ret}, command: {command}')
    if ret.find('error') > -1:
        log.e(f'session disconnect error! ret: {ret}')


def acct_res(request):
    reply = request.CreateReply()
    reply.code = CODE_ACCOUNT_RESPONSE
    return reply


def main():
    dictionary = Dictionary(*get_dictionaries(DICTIONARY_DIR))
    print('listening on :1813')
    server = EchoServer(dictionary, ':1813')
    server.serve_forever()


main()
