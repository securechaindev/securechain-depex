from requests import post, ConnectTimeout

import csv

import time

file = open('npm_repos_ids.txt', 'r')

with open('info.csv', 'w', newline='') as csvfile:
    fieldnames = ['dependencies', 'edges']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for line in file:
        id = line.replace('\n', '').strip()
        print(id)

        # Minimize pom xml
        response = post(url='http://localhost:8000/operation/file/file_info/' + id + '?agregator=mean&file_name=package.json&max_level=2').json()

        writer.writerow(
            {
                'dependencies': response['dependencies'] if response and 'dependencies' in response else 0,
                'edges': response['edges'] if response and 'edges' in response else 0
            }
        )