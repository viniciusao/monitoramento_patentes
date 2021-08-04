import logging
from time import sleep
from typing import Union, Tuple
from re import sub
import requests
from utils.queries_sqlite import Queries

logger = logging.getLogger('ops_patents_extract_store')


def req(node_service: str, url: str, binary=False) -> Tuple[Union[str, bytes], float]:
    logger.info(url)
    h = {'Authorization': f'Bearer {Queries().get_access_token()}'}
    r = requests.get(url, headers=h)
    h_throttling = r.headers.get('X-Throttling-Control')
    if not h_throttling:
        _print_response(r, node_service, url, binary)
    else:
        if not binary:
            return r.text, _set_sleep(node_service, h_throttling)
        return r.content, _set_sleep(node_service, h_throttling)


def _print_response(response: requests.models.Response, *args: Union[str, bool]) -> None:
    logger.error(response.text)
    logger.error(response.headers)
    logger.error(response.status_code)
    sleep(180)
    req(*args)


def _set_sleep(node_service: str, throttling_header: str) -> float:
    get_node = throttling_header[throttling_header.find(node_service):]
    node_reqmax_perminute = get_node[get_node.find(':') + 1:]
    filter_ = int(sub(r'\D', " ", node_reqmax_perminute).split()[0])
    return 60 / filter_ + 1
