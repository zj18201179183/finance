import time
import jwt
from django.conf import settings


class TokenUtil:

    __EXP_INCREMENT = 86400 * 7 # token有效期
    __ALGORITHM = 'HS256'

    def __init__(self, secret):
        self.secret = secret

    def generate_token(self, payload=None):
        """ 生成token """
        if payload:
            payload.update({
                'iss': 'finance',
                'iat': int(time.time()),
                'exp': int(time.time()) + self.__EXP_INCREMENT,
            })
        return jwt.encode(payload, self.secret, self.__ALGORITHM)

    def decode_token(self, token):
        """ 解析token """
        return jwt.decode(token, self.secret, self.__ALGORITHM)

    def get_user_id_from_token(self, token):
        """ 从token内获取用户id """
        payload = jwt.decode(token, self.secret, self.__ALGORITHM)
        return payload.get('user_id', None)

    def refresh_token(self, token):
        """ 刷新token """
        payload = jwt.decode(token, self.secret, self.__ALGORITHM)
        return self.generate_token(payload)

    def validate_token(self, token, user_id):
        """ 检查token是否有效 """
        uid = self.get_user_id_from_token(token)
        return uid == user_id and not self.token_is_expired(token)

    def token_is_expired(self, token):
        """ token是否已过期 """
        curr_time_secondes = int(time.time())
        return curr_time_secondes > self._get_exp_from_token(token)

    def _get_exp_from_token(self, token):
        """ 从token中获取过期时间 """
        payload = jwt.decode(token, self.secret, self.__ALGORITHM)
        return payload['exp']


token_util = TokenUtil(settings.SECRET_KEY)