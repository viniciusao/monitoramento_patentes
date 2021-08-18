from bots import load_dotenv, getLogger, environ, Queries, Orchestrator, sleep, makedirs, List, Union

load_dotenv()


class OPSExtractPatentsInfos:

    def __init__(self):
        self.logger = getLogger('ops_extract_patents_infos')
        self.db = Queries()
        self.do = Orchestrator()

    def get_patent_infos(self) -> None:
        self.db.delete_duplicated_patents()
        for patent in self.db.get_patents():
            id_, country, pubnum = patent
            patent = country+pubnum
            title, ab, applicant = self._get_abstract(patent)
            pf = self._get_patent_family(patent)
            img = self._check_for_img(patent)
            sleep(self.sleep)
            self._store(id_, title, ab, applicant, pf, img)
        self.db.delete_duplicated_patents(infos=True)
        for patent_id, title, abstract in self.db.get_patents(option='intros'):
            self._store(patent_id, title, abstract, filter_=True)
        self.db.con.close()

    def _get_abstract(self, patent: str):
        xml_parser, self.sleep = self.do.get_(
            'search', self.logger, wildcard='/biblio?', query=f'pn="{patent}"')
        return xml_parser.extract_abstract()

    def _get_patent_family(self, patent: str) -> Union[str, List[str]]:
        xml_parser, _ = self.do.get_('inpadoc', self.logger, wildcard=patent)
        if pf := xml_parser.extract_patent_family():
            return pf
        return 'null'

    def _check_for_img(self, patent: str) -> str:
        xml_parser, _ = self.do.get_('retrieval', self.logger, wildcard=patent)
        if x := xml_parser.checks_for_img():
            return self._get_img(patent, x)
        return 'null'

    def _get_img(self, patent: str, url_fragment: str) -> str:
        u = ''.join((environ['OPS_RESTAPI_URL'], url_fragment, f'?Range=1'))
        r, _ = self.do.request_('images', u, logger=self.logger, binary=True)
        makedirs('files/patents_imgs/', exist_ok=True)
        f_name = f'files/patents_imgs/{patent}.pdf'
        with open(f_name, 'wb') as f:
            f.write(r)
        return f_name

    def _store(self, *args, filter_=False) -> None:
        if not filter_:
            args = tuple(str(i) if not isinstance(i, int) else i for i in args)
            self.db.cursor.execute(f'INSERT INTO patents_infos VALUES {args}')
        else:
            patent_id, title, abstract = args
            if keywords_found := self._filter(title, abstract):
                values = (patent_id, str(keywords_found))
                self.db.cursor.execute(
                    f'INSERT INTO patents_keywords VALUES {values}')
        self.db.con.commit()

    @staticmethod
    def _filter(title: str, abstract: str) -> list:
        keywords = eval(environ['KEYWORDS_FILTER'])
        return [k for k in keywords if k in title or k in abstract]


if __name__ == '__main__':
    OPSExtractPatentsInfos().get_patent_infos()
