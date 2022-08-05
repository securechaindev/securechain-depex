from setuptools import setup


with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='depex',
    version='0.0.2',
    author='Antonio Germán Márquez Trujillo',
    author_email='amtrujillo@us.es',
    description='Una herramienta para el análisis de vulnerabilidades en proyectos software open-source',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/GermanMT/depex',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    install_requires=[
        'wheel==0.37.1',
        'uvicorn==0.18.2',
        'fastapi==0.79.0',
        'pymongo==4.2.0',
        'motor==3.0.0',
        'python-dotenv==0.20.0',
        'requests==2.28.1'
    ]
)