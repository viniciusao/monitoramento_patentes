class Queries:

    from typing import Optional

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

    def get_access_token(self) -> str:
        return self.cursor.execute('SELECT a_token from credential').fetchone()[0]

    def insert(self, token: str, stat: str) -> None:
        self.cursor.execute(
            'INSERT INTO credential (a_token, updated, status) VALUES '
            f'("{token}", "{self.timestamp}", "{stat}")')
        self.con.commit()

    def update(self, token: str, stat: str) -> None:
        self.cursor.execute(
            f'UPDATE credential SET a_token="{token}", '
            f'updated="{self.timestamp}", status="{stat}" WHERE id=1')
        self.con.commit()
