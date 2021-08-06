import logging
from os import getenv
from time import sleep
from typing import Union, Tuple
from re import sub
import requests
from utils.queries_sqlite import Queries
from utils.xml_parser import ParseXML

# TODO: melhorar o logging, deixar uniformizado
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)s] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO)
logger = logging.getLogger('')


def orchestrator(service: str, *args: str) -> Tuple[float, 'ParseXML']:
    """ Orchestrator to create a url+query and request it. """

    xml, sleep_ = request_(service, _get_service_endpoint(service, *args))
    return sleep_, ParseXML(xml)


# TODO: versão pública, uma maneira de identificar o endpoint sem conditions
def _get_service_endpoint(service: str, wildcard: str, query=None) -> str:
    if service == 'search':
        return getenv('OPS_SEARCH_ENDPOINT').format(wildcard) + query
    elif service == 'inpadoc':
        return getenv('OPS_PATENTFAMILY_ENDPOINT').format(wildcard)
    elif service == 'retrieval':
        return getenv('OPS_CHECKIMAGES_ENDPOINT').format(wildcard)


def request_(service: str, url: str, binary=False) -> Tuple[Union[str, bytes], float]:
    logger.info(url)
    h = {'Authorization': f'Bearer {Queries().get_access_token()}'}
    r = requests.get(url, headers=h)
    throttling = r.headers.get('X-Throttling-Control')
    if not throttling:
        _print_response(r, service, url, binary)
    else:
        if not binary:
            return r.text, _set_sleep(service, throttling)
        return r.content, _set_sleep(service, throttling)


# TODO: após testes, melhorar a função para lidar com os erros.
def _print_response(response: requests.models.Response, *args: Union[str, bool]) -> None:
    logger.error(response.text)
    logger.error(response.headers)
    logger.error(response.status_code)
    sleep(180)
    request_(*args)


def _set_sleep(service: str, throttling: str) -> float:
    service = throttling[throttling.find(service):]
    max_requests_per_minute = service[service.find(':') + 1:]
    filter_ = int(sub(r'\D', " ", max_requests_per_minute).split()[0])
    return 60 / filter_ + 1
