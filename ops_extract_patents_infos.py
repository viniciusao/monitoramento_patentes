from base64 import b64encode
from datetime import datetime
from os import getenv
from time import sleep
from typing import List, Union
from dotenv import load_dotenv
from utils.http_request import orchestrator, request_
from utils.queries_sqlite import Queries

load_dotenv()


class OPSExtractPatentsInfos:

    def __init__(self):
        self.db = Queries()

    def get_patent_infos(self) -> None:
        # TODO: e para futuros executed? melhorar.
        self.db.delete_duplicated_patents()
        for patent in self.db.get_patents():
            t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            id_, country, pubnum, kind = patent
            patent = ''.join((country, pubnum, kind))
            titles, ab, applicants = self._get_abstract(patent)
            oficial = self.sleep
            pf = self._get_patent_family(patent)
            imgs = self._check_for_images(patent)
            sleep(oficial)
            self._insert(id_, titles, ab, applicants, pf, imgs, t)
            self._insert(id_, titles, ab, t, to_filter=True)
        self.db.con.close()

    def _get_abstract(self, patent: str):
        self.sleep, xml_parser = orchestrator('search', '/biblio?', f'pn="{patent}"')
        return xml_parser.extract_abstract()

    def _get_patent_family(self, patent: str) -> Union[str, List[str]]:
        self.sleep, xml_parser = orchestrator('inpadoc', patent)
        if pf := xml_parser.extract_patent_family():
            return pf
        return patent

    def _check_for_images(self, patent: str) -> Union[List[bytes], str]:
        self.sleep, xml_parser = orchestrator('retrieval', patent)
        if x := xml_parser.checks_for_imgs():
            return self._get_imgs(x)
        return 'null'

    def _get_imgs(self, t_pages_and_url_piece: tuple) -> List[bytes]:
        number_of_pages, url_fragment = t_pages_and_url_piece
        imgs = []
        for n, _ in enumerate(range(number_of_pages), start=1):
            imgs.append(self._encodeb64_img(url_fragment, n))
            break   # just to get one.
            # sleep(self.sleep)
        return imgs

    def _encodeb64_img(self, *args) -> bytes:
        url_fragment, page = args
        u = ''.join((
            getenv('OPS_RESTAPI_URL'), url_fragment, f'?Range={page}'))
        r, self.sleep = request_('images', u, binary=True)
        return b64encode(r)

    def _insert(self, *args, to_filter=False) -> None:
        if not to_filter:
            args = tuple(str(i) if not isinstance(i, int) else i for i in args)
            print(f'INSERT INTO patents_infos VALUES {args}')
            self.db.cursor.execute(f'INSERT INTO patents_infos VALUES {args}')
            self.db.con.commit()
        else:
            patent_id, titles, ab, timestamp = args
            if keywords_found := self._filter(ab, titles):
                values = (patent_id, str(keywords_found), timestamp)
                print(f'INSERT INTO patents_infos_filtered VALUES {values}')
                self.db.cursor.execute(
                    f'INSERT INTO patents_infos_filtered VALUES {tuple(values)}')
                self.db.con.commit()

    @staticmethod
    def _filter(abstract: str, titles: str) -> list:
        keywords = eval(getenv('KEYWORDS_FILTER'))
        return [k for k in keywords if k in titles or k in abstract]


if __name__ == '__main__':
    OPSExtractPatentsInfos().get_patent_infos()
