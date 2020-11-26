# 第三方库
from child_pyrad.packet import AuthRequest, AuthResponse
# 自己的库
from loguru import logger as log
from controls.user import AuthUser


class AccessReject(Exception):
    pass


class Flow(object):

    @classmethod
    def access_reject(cls, request: AuthRequest, auth_user: AuthUser):
        log.info(f'reject. user: {auth_user.outer_username}, mac: {auth_user.mac_address}')
        reply = AuthResponse.create_access_reject(request=request)
        return request.reply_to(reply)
