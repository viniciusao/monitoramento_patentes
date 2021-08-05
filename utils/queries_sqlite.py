class Queries:

    from typing import Optional, List

    def __init__(self):
        from os import getenv
        from datetime import datetime
        from sqlite3 import connect

        self.con = connect(f'{getenv("OPS_DB_PATH")}')
        self.cursor = self.con.cursor()
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def check_table_length(self) -> Optional[bool]:
        if self.cursor.execute('SELECT * from credential').fetchall():
            return True

    def delete_duplicated_patents(self) -> None:
        self.cursor.execute(
            '''DELETE FROM patents WHERE rowid NOT IN (SELECT MIN(rowid) 
            FROM patents GROUP BY country, pub_num, kind)''')
        self.con.commit()

    def get_access_token(self) -> str:
        return self.cursor.execute('SELECT a_token from credential').fetchone()[0]

    def get_patents(self) -> List[str]:
        return self.cursor.execute('SELECT * FROM patents').fetchall()

    def insert(self, a_token: str, status: str) -> None:
        self.cursor.execute(
            'INSERT INTO credential (a_token, updated, status) VALUES '
            f'("{a_token}", "{self.timestamp}", "{status}")')
        self.con.commit()

    def update(self, a_token: str, status: str) -> None:
        self.cursor.execute(
            f'UPDATE credential SET a_token="{a_token}", '
            f'updated="{self.timestamp}", status="{status}" WHERE id=1')
        self.con.commit()
