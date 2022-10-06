from setuptools import setup


with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name = 'depex',
    version = '0.1.1',
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
        'wheel==0.37.1',
        'bson==0.5.10',
        'fastapi[all]==0.85.0',
        'motor==3.0.0',
        'motor-stubs==1.7.1',
        'python-dotenv==0.21.0',
        'requests==2.28.1',
        'types-requests==2.28.11.1',
        'types-setuptools==65.4.0',
        'python-dateutil==2.8.2',
        'types-python-dateutil==2.8.19'
    ],
    tests_requires = [
        'prospector[with_everything]==1.7.7',
        'mypy==0.971'
    ]
)