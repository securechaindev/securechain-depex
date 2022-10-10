# mypy: ignore-errors
from fastapi_utils.tasks import repeat_every

from app.config import settings

from app.services.populate_service import replace_env_variables
from app.services.cve_service import (
    read_cve_by_cve_id,
    bulk_write_cve_actions
)
from app.services.populate_service import read_env_variables

from pymongo import InsertOne, ReplaceOne

from requests import get

from time import sleep

from datetime import datetime

# 24h = 216000
@repeat_every(seconds = 216000)
async def db_updater():
    env_variables = await read_env_variables()
    today = datetime.today()

    headers = {'apiKey': settings.NVD_APY_KEY}

    no_stop = True
    while no_stop:
        end_day = await get_end_day(today, env_variables['last_year_update'], env_variables['last_month_update'])

        str_month = str(env_variables['last_month_update']) if env_variables['last_month_update'] > 9 else '0' + str(env_variables['last_month_update'])
        str_begin_day = str(env_variables['last_day_update']) if env_variables['last_day_update'] > 9 else '0' + str(env_variables['last_day_update'])
        str_end_day = str(end_day) if end_day > 9 else '0' + str(end_day)

        str_begin = str(env_variables['last_year_update']) + '-' + str_month + '-' + str_begin_day + 'T00:00:00'
        str_end = str(env_variables['last_year_update']) + '-' + str_month + '-' + str_end_day + 'T23:59:59'

        params_pub = {
            'pubStartDate': str_begin,
            'pubEndDate': str_end
        }

        sleep(6)
        response = get('https://services.nvd.nist.gov/rest/json/cves/2.0?', params = params_pub, headers = headers, timeout = 25).json()

        await insert_cves(response)

        params_mod = {
            'lastModStartDate': str_begin,
            'lastModEndDate': str_end
        }

        sleep(6)
        response = get('https://services.nvd.nist.gov/rest/json/cves/2.0?', params = params_mod, headers = headers, timeout = 25).json()
        
        await update_cves(response)

        env_variables['last_month_update'] += 1
        if env_variables['last_month_update'] == 13:
            env_variables['last_month_update'] = 1
            env_variables['last_year_update'] += 1

        if env_variables['last_year_update'] == today.year and env_variables['last_month_update'] == today.month + 1:
            env_variables['last_month_update'] = today.month
            env_variables['last_day_update'] = today.day
            env_variables['last_moment_update'] = datetime.now()
            await replace_env_variables(env_variables)
            no_stop = False

async def get_end_day(today: datetime, last_year: int, last_month: int) -> int:
    if last_year != today.year or last_month != today.month:
        if last_month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        if last_month in [4, 6, 9, 11]:
            return 30
        if last_month == 2:
            if last_year%4 == 0:
                return 29
            return 28
    return today.day

async def insert_cves(raw_cves: dict) -> None:
    inserts = []
    for raw_cve in raw_cves['vulnerabilities']:
        raw_cve = raw_cve['cve']
        cve = await read_cve_by_cve_id(raw_cve['id'])
        if not cve:
            inserts.append(InsertOne(raw_cve))

    await bulk_write_cve_actions(inserts)

async def update_cves(raw_cves: dict) -> None:
    updates = []
    for raw_cve in raw_cves['vulnerabilities']:
        raw_cve = raw_cve['cve']
        cve = await read_cve_by_cve_id(raw_cve['id'])
        if not cve:
            updates.append(InsertOne(raw_cve))
        else:
            updates.append(ReplaceOne({'id': raw_cve['id']}, raw_cve))
    
    await bulk_write_cve_actions(updates)