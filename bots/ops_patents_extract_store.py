from bots import load_dotenv, datetime, environ, getLogger, sleep, Queries, Orchestrator, List, Optional, Tuple
from utils.exports import to_csv
from utils.ops_search_query_maker import create_query_over_2000, get_ipc_codes

load_dotenv()


class OPSExtractStorePatents:
    def __init__(self, start_date: str) -> None:
        self.start_date = start_date
        self.end_date = datetime.now().strftime('%Y')
        self.db = Queries()
        self.table_rows = self.db.get_all_patents_infos()
        self.logger = getLogger('ops_patents_extract_store')
        self.request = Orchestrator()

    def main(self, default=True) -> None:
        """ Initiator of the process of extracting and consuming OPS API. """

        self._check_database()
        queries = get_ipc_codes(self.start_date, self.end_date)
        if not default:
            # custom end date
            # implement new method to retrieve last time the robot was executed
            pass
        for q in queries:
            self._search(q.get('query'), q.get('ipc'))
        self.db.con.close()

    def _check_database(self) -> None:
        if tr := self.table_rows:
            to_csv(
                f'{environ["EXP_PATH"]}{self.start_date}_{self.end_date}.csv',
                write_mode='w', hdr_row=eval(environ['CSV_HEADERS']),
                body_rows=tr)
            self.db.truncate_tables()

    def _search(self, query: str, ipc=None) -> None:
        """ OPS API search endpoint. """

        xml_parser, self.sleep = self.request.get_(
            'search', self.logger, query=query, wildcard='?')

        if pages := xml_parser.extract_search_pages_quantity():
            if pages > 2000:
                for q in self._set_range_over_2000(ipc):
                    sleep(self.sleep)
                    self._search(q)
            else:
                r = self._range_maker(pages)
                sleep(self.sleep)
                self._search_patents(r.get('times'), r.get('last_range'), query)
                sleep(self.sleep)

    def _set_range_over_2000(self, ipc: str):
        return create_query_over_2000(ipc, int(self.start_date), int(self.end_date))

    def _range_maker(self, total_pages: int):
        times = total_pages // 100
        f_last_range = (times * 100)
        last_range = total_pages - f_last_range
        return self._set_range_limits(times, f_last_range, last_range, total_pages)

    @staticmethod
    def _set_range_limits(*args) -> dict:
        times, f_last_range, last_range, total_pages = args
        if last_range:
            return {'times': times, 'last_range': f'{f_last_range + 1}-{total_pages}'}
        return {'times': 1}

    def _search_patents(self, times: int, last_range: Optional[str], query: str) -> None:
        """ Patent search iteration after search results (list of patents) of a query """

        range_ = [1, 100]
        for _ in range(times):
            range_, range_to_query = self._iter_search_patents(range_)
            self._get_patents_pubnum(range_to_query, query)
            sleep(self.sleep)
        if last_range:
            self._get_patents_pubnum(last_range, query)
            sleep(self.sleep)

    @staticmethod
    def _iter_search_patents(range_: List[int]) -> Tuple[List[int], str]:
        range_formatted = '-'.join((str(range_[0]), str(range_[1])))
        range_[0] += 100
        range_[1] += 100
        return range_, range_formatted

    def _get_patents_pubnum(self, range_: str, query: str) -> None:
        xml_parser, self.sleep = self.request.get_(
            'search', self.logger, query=query, wildcard=f'?Range={range_}&')

        if p := xml_parser.extract_patents():
            self.db.store_patents_pubnum(p, self.logger)


if __name__ == '__main__':
    OPSExtractStorePatents('2019').main()