from base64 import b64encode
from contextlib import suppress
from json import JSONDecodeError
from os import getenv
from typing import Union, Tuple
from dotenv import load_dotenv
import requests
from requests.exceptions import ConnectionError, Timeout
from utils.queries_sqlite import Queries


load_dotenv()


class OPSLogin:
    """ Stores token in `ops.db` from OAuth2 at OPS API. """

    def __init__(self):
        self.cursor = Queries()

    def auth(self) -> None:
        # try 3 times to authenticate
        for _ in range(3):
            try:
                r = self._req()
            except (ConnectionError, Timeout) as e:
                self._erros(e)
            else:
                if r:
                    self._store(r, 'Ok')
                    break
                self._store(
                    'Null', 'Request Error, check auth endpoint response.')
        self.cursor.con.close()

    def _req(self):
        u, h = self._set_params()
        r = requests.request(
            "POST", u, headers=h, data='grant_type=client_credentials',
            timeout=15)
        return self._token(r)

    @staticmethod
    def _set_params() -> Tuple[str, dict]:
        credential = bytes(
            ':'.join((getenv("OPS_AUTH_CONSUMER_KEY"), getenv(
                "OPS_AUTH_SECRET_KEY"))), encoding='utf-8')
        h = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {b64encode(credential).decode()}'
        }
        return getenv('OPS_AUTH_ENDPOINT'), h

    @staticmethod
    def _token(response: requests.models.Response) -> Union[bool, str]:
        with suppress(JSONDecodeError):
            return response.json().get('access_token')

    def _erros(self, e: Union[ConnectionError, Timeout]) -> None:
        if isinstance(e, ConnectionError):
            self._store('Null', 'Failed to connect.')
        elif isinstance(e, Timeout):
            self._store('Null', 'Connection Timedout.')
        self._store('Null', 'Unknown error.')

    def _store(self, token: str, status: str) -> None:
        # condition if it is the first run of this bot.
        if self.cursor.check_table_length():
            self.cursor.update(token, status)
        else:
            self.cursor.insert(token, status)


if __name__ == '__main__':
    OPSLogin().auth()
