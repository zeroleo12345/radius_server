import traceback
import datetime
# 第三方库
from gevent.server import DatagramServer
from pyrad.dictionary import Dictionary
# 自己的库
from child_pyrad.dictionary import get_dictionaries
from child_pyrad.request import AuthRequest
from auth.chap_flow import ChapFlow
from auth.eap_peap_flow import EapPeapFlow
from settings import log, RADIUS_DICTIONARY_DIR, RADIUS_SECRET
from controls.auth_user import AuthUser
from models import Session
from models.auth import User
from utils.signal import Signal
Signal.register()


class EchoServer(DatagramServer):
    dictionary: Dictionary = None

    def __init__(self, dictionary, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.dictionary = dictionary

    @classmethod
    def handle_signal(cls):
        if Signal.is_usr1:
            log.flush()
            Signal.is_usr1 = False
            return
        if Signal.is_usr2:
            log.flush()
            Signal.is_usr2 = False
            return

    def handle(self, data, address):
        try:
            self.handle_signal()
            # ip, port = address
            # print('from %s, data: %r' % (ip, data))

            # 解析报文
            request = AuthRequest(dict=self.dictionary, secret=RADIUS_SECRET, packet=data, socket=self.socket, address=address)

            # 验证用户
            verify(request)
        except Exception:
            log.e(traceback.format_exc())


def verify(request: AuthRequest):
    auth_user = AuthUser(request)

    # 查找用户明文密码
    now = datetime.datetime.now()
    session = Session()
    user = session.query(User).filter(User.username == auth_user.outer_username, User.expired_at >= now).first()
    if not user:
        log.e(f'user: {auth_user.outer_username} not exist')
        return

    # 保存用户密码
    auth_user.set_user_password(user.password)

    # 根据报文内容, 选择认证方式
    if 'CHAP-Password' in request:
        return ChapFlow.authenticate(request=request, auth_user=auth_user)
    elif 'EAP-Message' in request:
        return EapPeapFlow.authenticate(request=request, auth_user=auth_user)

    raise Exception('can not choose auth method!')


def main():
    dictionary = Dictionary(*get_dictionaries(RADIUS_DICTIONARY_DIR))
    print('listening on 0.0.0.0:1812')
    server = EchoServer(dictionary, '0.0.0.0:1812')
    server.serve_forever()


main()
