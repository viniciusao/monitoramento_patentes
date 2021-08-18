from sqlite3 import connect, OperationalError
from utils import datetime, environ, Logger, List, Optional, Union, Tuple


class Queries:
    def __init__(self):
        self.con = connect(f'{environ["OPS_DB_PATH"]}')
        self.cursor = self.con.cursor()
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def check_credential_existence(self) -> Optional[bool]:
        if self.cursor.execute('SELECT * from credential').fetchone():
            return True
        return None

    def insert_access_token(self, status: str, access_token: str = None) -> None:
        query = 'INSERT INTO credential (access_token, updated, status) VALUES ' \
                f'("{access_token}", "{self.timestamp}", "{status}")'
        if not access_token:
            query = query.replace('access_token, ', '').replace('"None", ', '')
        self.cursor.execute(query)
        self.con.commit()

    def update_access_token(self, status: str, access_token: str = None) -> None:
        query = f'UPDATE credential SET access_token="{access_token}", ' \
                f'updated="{self.timestamp}", status="{status}" WHERE id=1'
        if not access_token:
            query = query.replace('access_token="None", ', '')
        self.cursor.execute(query)
        self.con.commit()

    def get_access_token(self) -> str:
        return self.cursor.execute('SELECT access_token from credential').fetchone()[0]

    def store_patents_pubnum(self, patents: list, logger: Logger) -> None:
        sql_query = 'INSERT INTO patents (country, pubnum) VALUES '
        for patent in patents:
            sql_query += self._sql_query_maker(patent)
        try:
            self.cursor.execute(sql_query.rstrip(','))
            self.con.commit()
        except OperationalError:
            logger.error(sql_query)

    @staticmethod
    def _sql_query_maker(patent: dict) -> str:
        return ''.join((
            '(', f'"{patent["country"]}", ',
            f'"{patent["doc-number"]+patent["kind"]}"', '),'))

    def delete_duplicated_patents(self, infos=False) -> None:
        if not infos:
            self.cursor.execute(
                '''DELETE FROM patents WHERE rowid NOT IN (SELECT MIN(rowid) 
                FROM patents GROUP BY country, pubnum)''')
        else:
            self.cursor.execute(
                '''DELETE FROM patents_infos WHERE patent_family != 'null' AND 
                rowid NOT IN (SELECT MIN(rowid) FROM patents_infos GROUP BY patent_family)''')
        self.con.commit()

    def get_all_patents_infos(self) -> List[Tuple[str]]:
        return self.cursor.execute('''SELECT p.country, p.pubnum, pi.title, pk.keywords, pi.abstract, 
                pi.applicant, pi.patent_family, pi.image_path FROM patents_infos AS pi LEFT JOIN 
                patents_keywords AS pk ON pi.patent_id=pk.patent_id INNER JOIN 
                patents AS p ON pi.patent_id=p.id
                ''').fetchall()

    def get_patents_keywords(self) -> List[Optional[Tuple[str]]]:
        return self.cursor.execute('''SELECT p.country, p.pubnum, pi.title, pk.keywords, pi.abstract, 
                        pi.applicant, pi.patent_family, pi.image_path FROM patents_infos AS pi LEFT JOIN 
                        patents_keywords AS pk ON pi.patent_id=pk.patent_id INNER JOIN 
                        patents AS p ON pi.patent_id=p.id WHERE pk.keywords IS NOT NULL
                        ''').fetchall()

    def get_patents_statistics(self) -> Tuple[List[str], List[str]]:
        top_players_br = '''SELECT  pi.applicant, count(pi.applicant) 
                    AS c FROM patents_infos AS pi INNER JOIN patents AS p ON 
                    pi.patent_id=p.id WHERE p.country="BR" GROUP BY pi.applicant 
                    ORDER BY c DESC LIMIT 10'''
        top_players_world = '''SELECT applicant, count(applicant) AS c 
                    FROM patents_infos GROUP BY applicant ORDER BY c DESC LIMIT 10'''
        return self.cursor.execute(top_players_br).fetchall(), self.cursor.execute(top_players_world).fetchall()

    def get_patents(self, option: Optional[str] = None) -> Union[List[Tuple[int, str, str]]]:
        if option == 'intros':
            return self.cursor.execute('SELECT patent_id, title, abstract from patents_infos').fetchall()
        return self.cursor.execute('SELECT id, country, pubnum FROM patents').fetchall()

    def truncate_tables(self) -> None:
        self.cursor.execute('DELETE FROM patents')
        self.cursor.execute('DELETE FROM sqlite_sequence WHERE name="patents"')
        self.cursor.execute('DELETE FROM patents_infos')
        self.cursor.execute('DELETE FROM patents_keywords')
        self.con.commit()
