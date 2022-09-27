from requests import get

pkg_name = 'requests'

param = '?virtualMatchString=cpe:2.3:a:*:' + pkg_name + ':*:*:*:*'

response = get('https://services.nvd.nist.gov/rest/json/cves/2.0' + param, timeout = 25).json()

print(response)