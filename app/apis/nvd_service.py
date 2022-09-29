# mypy: ignore-errors
from requests import get

from app.config import settings


def get_cves(pkg_name: str):
    headers = {'apiKey': settings.NVD_APY_KEY,}
    params = {'virtualMatchString': 'cpe:2.3:a:*:' + pkg_name + ':*:*:*:*'}
    response = get('https://services.nvd.nist.gov/rest/json/cves/2.0?', params = params, headers = headers, timeout = 25).json()
    return response