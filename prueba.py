from requests import get

pkg_name = 'urllib3'

params = {
    'virtualMatchString': 'cpe:2.3:a:*:' + pkg_name + ':*:*:*:*'
}

headers = {
    'apiKey': 'f6b65d1a-52af-4c4f-80f0-c887a72502c8',
}

response = get('https://services.nvd.nist.gov/rest/json/cves/2.0?', params = params, headers = headers, timeout = 25).json()

print(response)