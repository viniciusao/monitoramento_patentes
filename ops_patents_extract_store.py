from datetime import datetime
import logging
from time import sleep
from typing import List, Optional, Tuple
from dotenv import load_dotenv
from utils.http_request import orchestrator
from utils.queries_sqlite import Queries
from utils.query_maker import create_query_over_2000, get_ipc_codes

load_dotenv()

# TODO: melhorar o logging, deixar uniformizado
logging.basicConfig(
            format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)s] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=logging.INFO,
            handlers=[logging.FileHandler("ops_patents_extract_store.log"),
                      logging.StreamHandler()])


class OPSExtractStorePatents:

    def __init__(self, start_date: str) -> None:
        self.start_date = start_date
        self.end_date = datetime.now().strftime('%Y')
        self.db = Queries()
        self.logger = logging.getLogger('ops_patents_extract_store')

    def main(self, default=True) -> None:
        """ Initiator of the whole process of extracting and consuming OPS API"""

        queries = get_ipc_codes(self.start_date, self.end_date)
        if not default:
            # custom end date
            # implement new method to retrieve last time the robot was executed
            pass
        for q in queries:
            self._search(q.get('query'), q.get('ipc'))
        self.db.con.close()

    def _search(self, query: str, ipc=None) -> None:
        """ OPS API search endpoint """

        self.sleep, xml_parser = orchestrator('search', '?', query)
        pages = xml_parser.extract_search_pages_quantity()
        if pages and pages > 0:
            if pages > 2000:
                for q in self._set_range_over_2000(ipc):
                    sleep(self.sleep)
                    self._search(q)
            else:
                r = self._range_maker(pages)
                sleep(self.sleep)
                if r:
                    self._search_patents(r.get('vezes'), r.get('l_range'), query)
                    sleep(self.sleep)

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

    def _search_patents(self, qntd: int, l_range: Optional[str], query: str) -> None:
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
        self.sleep, xml_parser = orchestrator('search', f'?Range={range_}&', query)
        if ps := xml_parser.extract_patents():
            self._store_patents(ps)

    def _store_patents(self, patents: list) -> None:
        from sqlite3 import OperationalError
        sql_query = 'INSERT INTO patents (country, pub_num, kind, created) VALUES '
        for patent in patents:
            sql_query += self._sql_query_maker(patent)
        try:
            self.logger.info(sql_query)
            self.db.cursor.execute(sql_query.rstrip(','))
            self.db.con.commit()
        except OperationalError:
            self.logger.error('ERRO')
            self.logger.error(sql_query)

    @staticmethod
    def _sql_query_maker(patent: dict) -> str:
        t = f'"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"'
        p = ','.join((
            f'"{patent.get("country")}"',
            f'"{patent.get("doc-number")}"',
            f'"{patent.get("kind")}"', t))
        return ''.join(('(', p, '),'))


if __name__ == '__main__':
    OPSExtractStorePatents('2019').main()
