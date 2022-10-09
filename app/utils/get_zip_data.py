from zipfile import ZipFile

from json import load


async def get_zip_data():
    with ZipFile('app/services/dbs/db_files/cves.zip') as zip:
        for filename in zip.namelist():  
            with zip.open(filename) as file:  
                return load(file)