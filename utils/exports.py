from csv import writer
from . import makedirs, List, Tuple


def to_csv(fname: str, write_mode: str, hdr_row: Tuple[Tuple[str]], body_rows: List[Tuple[str]]) -> None:
    ps = fname.split('/')
    ps.pop()
    makedirs('/'.join(ps), exist_ok=True)
    with open(fname, write_mode) as f:
        w = writer(f)
        w.writerows(hdr_row)
        w.writerows(body_rows)
