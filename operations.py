from requests import post

import csv

import time

file = open('mvn_repos_ids.txt', 'r')

with open('minmax.csv', 'w', newline='') as csvfile:
    fieldnames = ['min', 'min_time', 'max', 'max_time']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for line in file:
        id = line.replace('\n', '').strip()
        print(id)

        # Minimize pom xml
        min_time = time.time()
        try:
            pom_min_response = post(url='http://localhost:8000/operation/file/minimize_impact/' + id + '?agregator=mean&file_name=pom.xml&limit=1&max_level=5').json()
            pom_min_response = round(pom_min_response['result'][0]['CVSSpom.xml'], 2)
        except:
            pom_min_response = None

        if pom_min_response:
            min = pom_min_response
        else:
            min = '-'
        min_time = time.time() - min_time

        # Maximize pom xml
        max_time = time.time()
        try:
            pom_max_response = post(url='http://localhost:8000/operation/file/maximize_impact/' + id + '?agregator=mean&file_name=pom.xmln&limit=1&max_level=5').json()
            pom_max_response = round(pom_max_response['result'][0]['CVSSpom.xml'], 2)
        except:
            pom_max_response = None

        if pom_max_response:
            max = pom_max_response
        else:
            max = '-'
        max_time = time.time() - max_time

        writer.writerow(
            {
                'min': min,
                'min_time': round(min_time, 2),
                'max': max,
                'max_time' : round(max_time, 2)
            }
        )