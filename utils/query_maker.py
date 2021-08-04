"""
    Creates a `query` based on a list of IPC codes to search.

    ...

    Methods
    -------
    get_ipc_codes():
        :returns a list of queries.
    _slice_ipc_list(chunks_of: int, code: str, index: int):
        :returns either a list or tuple of chunks of a entire list of
        IPC codes.
    _create_query(ipc_codes: list):
        creates a query list.
    _iter_query(codes: list, counter: int, queries: list):
        loops through a query list and adds operators to it.

"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


def get_ipc_codes(*dates: str) -> List[dict]:
    codes = [i for i in eval(os.getenv('IPC_CODES'))]
    return _create_query(codes, *dates)


def _create_query(ipcs: list, *dates: str):
    sd, ed = dates
    q = [{'ipc': None, 'query': 'ic ='}] * len(ipcs)
    for c, ipc in enumerate(ipcs):
        q[c]['ipc'] = ipc
        q[c]['query'] += f'"{ipc}" AND pd within "{sd} {ed}"'
    return q


def create_query_over_2000(ipc: str, *dates: int) -> List[str]:
    # pretty lame function, it is a dummy one just for the current purpose
    # it shall be replaced.
    sd, ed = dates
    anos = [min(dates), (ed - sd) // 2 + sd, max(dates)]
    q = []
    sd, ed = '01', '04'
    for ano in anos:
        for _ in range(3):
            q.append(f'ic ="{ipc}" AND pd within "{ano}{sd} {ano}{ed}')
            if int(sd) < 6:
                sd = '0' + str(int(sd) + 4)
            ed = '0' + str(int(ed) + 4) if int(ed) < 6 else str(int(ed) + 4)
        sd, ed = '01', '04'
    q.pop()
    return q
