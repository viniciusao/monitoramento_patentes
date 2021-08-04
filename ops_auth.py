import os
from dotenv import load_dotenv
import requests
from requests.exceptions import ConnectionError, Timeout


load_dotenv()


class SqliteCredentialQuery:

    from datetime import datetime
    from sqlite3 import connect

    c = connect(f'{os.getenv("OPS_DB_PATH")}')
    cur = c.cursor()
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def check_len(self) -> bool:
        r = self.cur.execute('SELECT * from credential').fetchall()
        if len(r) > 0:
            return True

    def update(self, token: str, status: str) -> None:
        self.cur.execute(
            f'UPDATE credential SET a_token="{token}", '
            f'updated="{self.t}", status="{status}" WHERE id=1')
        self.c.commit()
        self.c.close()

    def insert(self, token: str, status: str) -> None:
        self.cur.execute(
            'INSERT INTO credential (a_token, updated, status) VALUES '
            f'("{token}", "{self.t}", "{status}")')
        self.c.commit()
        self.c.close()


class OPSLogin:
    """ Stores token in `ops.db` from OAuth2 at OPS API. """

    from typing import Union, Tuple

    def __init__(self):
        self.cursor = SqliteCredentialQuery()

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
        self.cursor.c.close()

    def _req(self) -> Union[bool, str]:
        u, h = self._set_params()
        r = requests.request(
            "POST", u, headers=h, data='grant_type=client_credentials',
            timeout=15)
        return self._token(r)

    @staticmethod
    def _set_params() -> Tuple[str, dict]:
        from base64 import b64encode
        b_ops_auth = bytes(
            ':'.join((os.getenv("OPS_AUTH_CONSUMER_KEY"), os.getenv(
                "OPS_AUTH_SECRET_KEY"))), encoding='utf-8')
        h = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {b64encode(b_ops_auth).decode()}'
        }
        return os.getenv('OPS_AUTH_ENDPOINT'), h

    @staticmethod
    def _token(response: requests.models.Response):
        from contextlib import suppress
        from json import JSONDecodeError
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
        if self.cursor.check_len():
            self.cursor.update(token, status)
        else:
            self.cursor.insert(token, status)


if __name__ == '__main__':
    OPSLogin().auth()
