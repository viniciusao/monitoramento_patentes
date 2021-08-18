from monitor_patents_ops.utils import environ, List


def get_ipc_codes(*args: str):
    codes = [i for i in eval(environ['IPC_CODES'])]
    return _create_query(codes, *args)


def _create_query(ipcs: list, *dates: str) -> List[dict]:
    sd, ed = dates
    return [
        {'ipc': ipc, 'query': f'ic="{ipc}" AND pd within "{sd} {ed}"'}
        for ipc in ipcs]


# TODO: improve.
def create_query_over_2000(ipc: str, *dates: int) -> List[str]:
    """
    when a query search returns more than 2000 pages,
    this method :returns subqueries with different ranges.
    """

    # pretty lame function, it is a dummy one just for the current purpose
    # it shall be replaced.
    sd, ed = dates
    anos = [min(dates), (ed - sd) // 2 + sd, max(dates)]
    q = []
    sd_, ed_ = '01', '04'
    for ano in anos:
        for _ in range(3):
            q.append(f'ic="{ipc}" AND pd within "{ano}{sd_} {ano}{ed_}"')
            if int(sd_) < 6:
                sd_ = '0' + str(int(sd_) + 4)
            ed_ = '0' + str(int(ed_) + 4) if int(ed_) < 6 else str(int(ed_) + 4)
        sd_, ed_ = '01', '04'
    q.pop()
    return q
