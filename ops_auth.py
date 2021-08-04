import os
from dotenv import load_dotenv
import requests
from requests.exceptions import ConnectionError, Timeout


load_dotenv()


class SqliteCredentialQueries:

    from typing import Optional

    def __init__(self):
        from datetime import datetime
        from sqlite3 import connect

        self.con = connect(f'{os.getenv("OPS_DB_PATH")}')
        self.cursor = self.con.cursor()
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def check_table_length(self) -> Optional[bool]:
        if self.cursor.execute('SELECT * from credential').fetchall():
            return True

    def update(self, token: str, stat: str) -> None:
        self.cursor.execute(
            f'UPDATE credential SET a_token="{token}", '
            f'updated="{self.timestamp}", status="{stat}" WHERE id=1')
        self.con.commit()

    def insert(self, token: str, stat: str) -> None:
        self.cursor.execute(
            'INSERT INTO credential (a_token, updated, status) VALUES '
            f'("{token}", "{self.timestamp}", "{stat}")')
        self.con.commit()


class OPSLogin:
    """ Stores token in `ops.db` from OAuth2 at OPS API. """

    from typing import Union, Tuple

    def __init__(self):
        self.cursor = SqliteCredentialQueries()

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
        from base64 import b64encode
        credential = bytes(
            ':'.join((os.getenv("OPS_AUTH_CONSUMER_KEY"), os.getenv(
                "OPS_AUTH_SECRET_KEY"))), encoding='utf-8')
        h = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {b64encode(credential).decode()}'
        }
        return os.getenv('OPS_AUTH_ENDPOINT'), h

    @staticmethod
    def _token(response: requests.models.Response) -> Union[bool, str]:
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
        if self.cursor.check_table_length():
            self.cursor.update(token, status)
        else:
            self.cursor.insert(token, status)


if __name__ == '__main__':
    OPSLogin().auth()
