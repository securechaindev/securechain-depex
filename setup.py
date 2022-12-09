from setuptools import setup


with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name = 'depex',
    version = '0.3.0',
    author = 'Antonio Germán Márquez Trujillo',
    author_email = 'amtrujillo@us.es',
    description = 'Una herramienta para el análisis de vulnerabilidades en proyectos software open-source',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/GermanMT/depex',
    classifiers = [
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
    ],
    python_requires = '>=3.10',
    install_requires = [
        'wheel==0.38.4',
        'fastapi[all]==0.88.0',
        'fastapi-utils==0.2.1',
        'motor==3.1.1',
        'python-dotenv==0.21.0',
        'requests==2.28.1',
        'python-dateutil==2.8.2',
        'flamapy-dn==1.1.2'
    ],
    tests_requires = [
        'prospector[with_everything]==1.7.7',
        'mypy==0.991',
        'motor-stubs==1.7.1',
        'types-requests==2.28.11.1',
        'types-setuptools==65.4.0',
        'types-python-dateutil==2.8.19'
    ]
)