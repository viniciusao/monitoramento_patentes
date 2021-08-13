from base64 import b64encode
from json import JSONDecodeError
from os import getenv
from typing import Optional, Union, Tuple
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
            r = self._req()
            if r:
                self._store('Ok', r)
                break
        self.cursor.con.close()

    def _req(self):
        u, h = self._set_params()
        try:
            r = requests.request(
                "POST", u, headers=h,
                data='grant_type=client_credentials', timeout=15)
        except (ConnectionError, Timeout) as e:
            self._errors(e)
        else:
            return self._token(r)

    @staticmethod
    def _set_params() -> Tuple[str, dict]:
        credential = bytes(
            ':'.join((getenv("OPS_AUTH_CONSUMER_KEY"), getenv(
                "OPS_AUTH_SECRET_KEY"))), encoding='utf-8')
        h = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {b64encode(credential).decode()}'}
        return getenv('OPS_AUTH_ENDPOINT'), h

    def _errors(self, e: Union[ConnectionError, Timeout]) -> None:
        if isinstance(e, ConnectionError):
            self._store('Failed to connect.')
        elif isinstance(e, Timeout):
            self._store('Connection Timedout.')
        else:
            self._store('Unknown error.')

    def _store(self, status: str, access_token=None) -> None:
        if self.cursor.check_credential_existence():
            self.cursor.update_access_token(status, access_token)
        else:
            self.cursor.insert_access_token(status, access_token)

    def _token(self, response: requests.models.Response) -> Optional[str]:
        try:
            return response.json().get('access_token')
        except JSONDecodeError:
            self._store('Weird response, check the OPS Auth endpoint.')


if __name__ == '__main__':
    OPSLogin().auth()
