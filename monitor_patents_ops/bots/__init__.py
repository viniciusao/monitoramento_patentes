from datetime import datetime
from logging import basicConfig, INFO, FileHandler, StreamHandler, getLogger
from os import getenv, environ, makedirs
from time import sleep
from typing import cast, Dict, List, Optional, Union, Tuple
from dotenv import load_dotenv
from monitor_patents_ops.utils.http_request import Orchestrator
from monitor_patents_ops.utils.queries_sqlite import Queries

# noinspection PyArgumentList
basicConfig(
            format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)s] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=INFO,
            handlers=[FileHandler("ops_patents_extract_store.log"),
                      StreamHandler()])
