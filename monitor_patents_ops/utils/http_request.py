from time import sleep
from re import sub
from requests import get, models
from monitor_patents_ops.utils import environ, Logger, cast, Optional, Union, Tuple
from monitor_patents_ops.utils.queries_sqlite import Queries
from monitor_patents_ops.utils.xml_parser import ParseXML


class Orchestrator:
    """ Orchestrator to create a url+query and request it. """

    def get_(self, *args: Union[str, Logger], wildcard: str , query: Optional[str] = None) -> Optional[Tuple['ParseXML', Union[float, int]]]:
        service, logger = cast(str, args[0]), cast(Logger, args[1])
        url = self._get_service_endpoint(service, wildcard, query)
        if url:
            response, sleep_ = self.request_(service, url, logger=logger)
            return ParseXML(response), sleep_
        return None

    @staticmethod
    def _get_service_endpoint(service: str, wildcard: str, query=None) -> Optional[str]:
        if service == 'search':
            return environ['OPS_SEARCH_ENDPOINT'].format(wildcard) + query
        elif service == 'inpadoc':
            return environ['OPS_PATENTFAMILY_ENDPOINT'].format(wildcard)
        elif service == 'retrieval':
            return environ['OPS_CHECKIMAGES_ENDPOINT'].format(wildcard)
        return None


    def request_(self, *args: Union[str], logger: Logger, binary=False) -> Tuple[Union[str, bytes], float]:
        service, url = args
        logger.info(url)
        r = get(url, headers={'Authorization': f'Bearer {Queries().get_access_token()}'})
        throttling = r.headers.get('X-Throttling-Control')
        if not throttling:
            self._log_response(r, logger)
            return self.request_(*args, logger=logger, binary=binary)
        if not binary:
            return r.text, self._set_sleep(service, throttling)
        return r.content, self._set_sleep(service, throttling)

    @staticmethod
    def _log_response(response: models.Response, logger: Logger) -> None:
        logger.error(response.url)
        logger.error(response.text)
        logger.error(response.headers)
        logger.error(response.status_code)
        sleep(360)

    @staticmethod
    def _set_sleep(service: str, throttling: str) -> Union[float, int]:
        service = throttling[throttling.find(service):]
        max_requests_per_minute = service[service.find(':') + 1:]
        filter_ = int(sub(r'\D', " ", max_requests_per_minute).split()[0])
        if filter_ != 0:
            return 60 / filter_ + 1
        return 61
