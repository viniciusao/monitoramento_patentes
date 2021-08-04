import os
from time import sleep
import sqlite3
from typing import List, Union, Tuple
from dotenv import load_dotenv
import requests
from utils.query_maker import create_query_over_2000, get_ipc_codes
from utils.xml_parser import ParseXML

load_dotenv()


class QueryOPS:

    def __init__(self, start_date: str) -> None:
        import logging
        from datetime import datetime

        self.start_date = start_date
        self.end_date = datetime.now().strftime('%Y')
        self.con = sqlite3.connect(os.getenv('OPS_DB_PATH'))
        self.cur = self.con.cursor()
        logging.basicConfig(
            format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)s] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=logging.INFO,
            handlers=[logging.FileHandler("ops_query.log"),
                      logging.StreamHandler()])
        self.logger = logging.getLogger('ops_query')
        self.sleep = 0

    def main(self, default=True) -> None:
        """ Initiator of the whole process of extracting and consuming OPS API"""

        queries = get_ipc_codes(self.start_date, self.end_date)
        if not default:
            # implement new method to retrieve last time the robot was executed
            pass
        for q in queries:
            self._search(q.get('query'), q.get('ipc'))
        self.con.close()

    def _search(self, query: str, ipc=None) -> None:
        """ OPS API search endpoint """

        p = self._orch('search', '?', query).extract_qntd_pages()
        if p > 2000:
            for q in self._set_range_over_2000(ipc):
                self._search(q)
        r = self._range_maker(p)
        sleep(self.sleep)
        if r:
            self._search_patents(r.get('vezes'), r.get('l_range'), query)

    def _orch(self, node_service: str, any_: str, query: str) -> 'ParseXML':
        """ Orchestrator to create a url+query and request it. """

        u = self._url_maker(node_service, any_, query)
        r = self._req(node_service, u)
        return ParseXML(r)

    @staticmethod
    def _url_maker(node_service: str, any_: str, query=None) -> str:
        if node_service == 'search':
            return os.getenv('OPS_SEARCH_ENDPOINT').format(any_) + query
        elif node_service == 'inpadoc':
            return os.getenv('OPS_PATENTFAMILY_ENDPOINT').format(any_)
        elif node_service == 'images':
            return os.getenv('OPS_CHECKIMAGES_ENDPOINT').format(any_)

    def _req(self, node_service: str, url: str, binary=False) -> Union[str, bytes]:
        self.logger.info(url)
        h = {'Authorization': f'Bearer {self._get_a_token()}'}
        r = requests.get(url, headers=h)
        self._set_sleep(node_service, r.headers.get('X-Throttling-Control'))
        if not binary:
            return r.text
        return r.content

    def _get_a_token(self) -> str:
        return self.cur.execute('SELECT a_token from credential').fetchone()[0]

    def _set_sleep(self, node_service: str, response_headers: str) -> None:
        from re import sub
        get_node = response_headers[response_headers.find(node_service):]
        node_reqmax_perminute = get_node[get_node.find(':') + 1:]
        filter_ = int(sub(r'\D', " ", node_reqmax_perminute).split()[0])
        self.sleep = 60 / filter_ + 1

    def _set_range_over_2000(self, ipc: str):
        return create_query_over_2000(ipc, int(self.start_date), int(self.end_date))

    def _range_maker(self, total_pages: int):
        c = total_pages // 100
        l_range_begin = (c * 100)
        range_lim_check = total_pages - l_range_begin
        return self._set_range_limits(c, l_range_begin, range_lim_check, total_pages)

    @staticmethod
    def _set_range_limits(*args) -> dict:
        qntd, l_r_begin, r_lim_check, t_pages = args
        if 100 >= t_pages > 0:
            return {'vezes': 1}
        if r_lim_check:
            return {'vezes': qntd, 'l_range': f'{l_r_begin + 1}-{t_pages}'}

    def _search_patents(self, qntd: int, l_range: str, query: str) -> None:
        """ Patent search iteration after search results (list of patents) of a query """

        range_ = [1, 100]
        for _ in range(qntd):
            range_, range_to_query = self._iter_search_patents(range_)
            self._get_patents_pubnum(range_to_query, query)
            sleep(self.sleep)
        if l_range:
            self._get_patents_pubnum(l_range, query)
            sleep(self.sleep)

    @staticmethod
    def _iter_search_patents(c_r: List[int]) -> Tuple[List[int], str]:
        r_fmt = '-'.join((str(c_r[0]), str(c_r[1])))
        c_r[0] += 100
        c_r[1] += 100
        return c_r, r_fmt

    def _get_patents_pubnum(self, range_: str, query: str) -> None:
        r = self._orch('search', f'?Range={range_}&', query)
        self._store_patents(r.extract_pubnums())

    def _store_patents(self, patents: list) -> None:
        sql_query = 'INSERT INTO total_patents (country, pub_num, kind, created) VALUES '
        for patent in patents:
            sql_query += self._sql_query_maker(patent)
        self.cur.execute(sql_query.rstrip(','))
        self.con.commit()

    @staticmethod
    def _sql_query_maker(patent: dict) -> str:
        from datetime import datetime
        t = f'"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"'
        p = ','.join((
            f'"{patent.get("country")}"',
            f'"{patent.get("doc-number")}"',
            f'"{patent.get("kind")}"', t))
        return ''.join(('(', p, '),'))

    # def _patent_infos(self, patents_pubnum: list) -> None:
    #     for ppn in patents_pubnum:
    #         titles, a = self._get_abstract(ppn)
    #         pf = self._get_patent_family(ppn)
    #         imgs = self._check_for_images(ppn)
    #         print('Patente, Título, Abstract, Imgs =>',
    #               [ppn, titles, a, pf, imgs])
    #         sleep(4)
    #
    # def _get_abstract(self, pubnum: str):
    #     g = self._orch(*['search', '/biblio?', f'pn="{pubnum}"'])
    #     titles, a = g.extract_abstract()
    #     return titles, a

    # def _get_patent_family(self, pubnum: str):
    #     pf = self._orch(*['patent_family', pubnum]).extract_patent_family()
    #     if not pf:
    #         return pubnum
    #     return pf
    #
    # def _check_for_images(self, pubnum: str):
    #     if c := self._orch(*['check_for_imgs', pubnum]).checks_for_imgs():
    #         return self._get_imgs(c)
    #     return 'null'
    #
    # def _get_imgs(self, t_pages_and_url_piece: tuple):
    #     number_of_pages, url_fragment = t_pages_and_url_piece
    #     imgs = []
    #     for n, _ in enumerate(range(number_of_pages), start=1):
    #         imgs.append(self._encodeb64_img(url_fragment, n))
    #         sleep(1)
    #     return imgs

    # def _encodeb64_img(self, *args) -> bytes:
    #     from base64 import b64encode
    #
    #     url_fragment, page = args
    #     u = ''.join((
    #         os.getenv('OPS_RESTAPI_URL'), url_fragment, f'?Range={page}'))
    #     r = self._req(u, binary=True)
    #     return b64encode(r)


if __name__ == '__main__':
    QueryOPS('2019').main()
