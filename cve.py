from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
import csv
import asyncio
import time

client = AsyncIOMotorClient('mongodb://mongoDepex:mongoDepex@localhost:27017/admin')

nvd_db = client.nvd
cves_collection = nvd_db.get_collection('cves')

HEADERS = {
    'apiKey': 'f6b65d1a-52af-4c4f-80f0-c887a72502c8'
}

async def read_cve_by_id(cve_id: str) -> dict[str, Any]:
    return await cves_collection.find_one({'id': cve_id})

async def satinize_attack_vector(attack_vector: str) -> list[str]:
    attack_vector_template: dict[str, str] = {
        'AV': 'Null',
        'AC': 'Null',
        'PR': 'Null',
        'UI': 'Null',
        'S': 'Null',
        'C': 'Null',
        'I': 'Null',
        'A': 'Null'
    }
    attack_vector = attack_vector.replace('CVSS:3.0/', '').replace('CVSS:3.1/', '')
    for part in attack_vector.split('/'):
        metric, value = part.split(':')
        if metric in attack_vector_template:
            attack_vector_template[metric] = value
    return attack_vector_template.values()

async def get_csv():
    begin = time.time()
    with open('cves.csv', 'a') as file:
        writer = csv.writer(file)
        head = [
            'published',
            'impact',
            'av-attack-vector',
            'av-attack-complexity',
            'av-privileges-required',
            'av-user-interaction',
            'av-scope',
            'av-confidentiality',
            'av-integrity',
            'av-availability'
        ]
        writer.writerow(head)

        file = open('cves.txt', 'r')
        for cve_id in file.readlines():
            cve_id = cve_id.strip()
            cve = await read_cve_by_id(cve_id)
            print(cve_id)

            # Impact
            if 'cvssMetricV31' in cve['metrics']:
                impact = cve['metrics']['cvssMetricV31'][0]['impactScore']
            elif 'cvssMetricV30' in cve['metrics']:
                impact = cve['metrics']['cvssMetricV30'][0]['impactScore']
            elif 'cvssMetricV2' in cve['metrics']:
                impact = cve['metrics']['cvssMetricV2'][0]['impactScore']

            # Attack vector
            if 'cvssMetricV31' in cve['metrics']:
                attack_vector = cve['metrics']['cvssMetricV31'][0]['cvssData']['vectorString']
            elif 'cvssMetricV30' in cve['metrics']:
                attack_vector = cve['metrics']['cvssMetricV30'][0]['cvssData']['vectorString']
            elif 'cvssMetricV2' in cve['metrics']:
                attack_vector = cve['metrics']['cvssMetricV2'][0]['cvssData']['vectorString']

            av, ac, pr, ui, s, c, i , a = await satinize_attack_vector(attack_vector)
            published = cve['published']

            # CSV generation
            data: list[list[str]] = []
            data.append([
                published,
                impact,
                av,
                ac,
                pr,
                ui,
                s,
                c,
                i,
                a
            ])
            writer.writerows(data)
    print('Tiempo tardado en generar el CSV: ' + str(time.time() - begin))

asyncio.run(get_csv())