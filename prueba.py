from univers.version_range import PypiVersionRange
from univers.versions import PypiVersion


versions = ['0.11',
'0.12',
'0.13',
'0.14',
'0.15',
'0.16',
'0.17',
'0.18',
'0.19',
'0.20',
'0.21',
'0.22',
'0.23',
'0.9',
'0.9.1',
'0.9.2',
'0.9.3',
'1.0',
'1.1.0',
'1.1.1',
'2.0.0',
'2.0.0a1',
'2.0.0rc1',
'2.0.0rc2',
'2.0.1',
'2.1.0', '2.1.1', '2.1.2']

range = PypiVersionRange.from_native("==2.1.1")

for version in versions:
    print(PypiVersion(version) in range)

print(PypiVersion('2.1.1') == PypiVersion('2.1.1'))