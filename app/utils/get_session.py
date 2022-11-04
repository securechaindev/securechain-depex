from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


async def get_session() -> Session:
    session = Session()
    retry = Retry(connect = 4, backoff_factor = 0.5)
    adapter = HTTPAdapter(max_retries = retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session