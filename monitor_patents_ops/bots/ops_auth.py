from base64 import b64encode
from contextlib import suppress
from json import JSONDecodeError
from requests import exceptions, models, request
from monitor_patents_ops.bots import load_dotenv, environ, Queries, Dict, Optional, Union, Tuple


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
            r = request(
                "POST", u, headers=h,
                data='grant_type=client_credentials', timeout=15)
        except (exceptions.ConnectionError, exceptions.Timeout) as e:
            self._errors(e)
        else:
            return self._token(r)

    @staticmethod
    def _set_params() -> Tuple[Optional[str], Dict[str, str]]:
        credential = bytes(
            ':'.join((environ["OPS_AUTH_CONSUMER_KEY"], environ[
                "OPS_AUTH_SECRET_KEY"])), encoding='utf-8')
        h = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {b64encode(credential).decode()}'}
        return environ['OPS_AUTH_ENDPOINT'], h

    def _errors(self, e: Union[exceptions.ConnectionError, exceptions.Timeout]) -> None:
        if isinstance(e, exceptions.ConnectionError):
            self._store('Failed to connect.')
        elif isinstance(e, exceptions.Timeout):
            self._store('Connection Timedout.')
        else:
            self._store('Unknown error.')

    def _store(self, status: str, access_token: str = None) -> None:
        if self.cursor.check_credential_existence():
            self.cursor.update_access_token(status, access_token)
        else:
            self.cursor.insert_access_token(status, access_token)

    def _token(self, response: models.Response) -> Optional[str]:
        with suppress(JSONDecodeError):
            return response.json().get('access_token')
        self._store('Weird response, check the OPS Auth endpoint.')
        return None

if __name__ == '__main__':
    OPSLogin().auth()
