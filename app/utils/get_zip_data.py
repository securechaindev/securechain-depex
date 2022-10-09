from zipfile import ZipFile

from json import load


async def get_zip_data():
    with ZipFile('app/services/dbs/db_files/cves.zip') as z:
        for filename in z.namelist():  
            with z.open(filename) as file:  
                return load(file)