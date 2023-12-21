from requests import post, ConnectTimeout

import csv

import time

file = open('mvn_repos_ids.txt', 'r')

with open('minmax.csv', 'a', newline='') as csvfile:
    fieldnames = ['min', 'min_time', 'max', 'max_time']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for line in file:
        id = line.replace('\n', '').strip()
        print(id)

        # Minimize pom xml
        min_time = time.time()
        try:
            min_response = post(url='http://localhost:8000/operation/file/minimize_impact/' + id + '?agregator=mean&file_name=pom.xml&limit=1&max_level=2', timeout=10).json()
            min_response = round(min_response['result'][0]['file_risk_pom.xml'], 2)
            min_time = round(time.time() - min_time, 2)
        except Exception as e:
            min_response = '-'
            if type(e) == ConnectTimeout:
                min_time = '+10'
            else:
                min_time = round(time.time() - min_time, 2)

        # Maximize pom xml
        max_time = time.time()
        try:
            max_response = post(url='http://localhost:8000/operation/file/maximize_impact/' + id + '?agregator=mean&file_name=pom.xml&limit=1&max_level=2', timeout=10).json()
            max_response = round(max_response['result'][0]['file_risk_pom.xml'], 2)
            max_time = round(time.time() - max_time, 2)
        except Exception as e:
            max_response = '-'
            if type(e) == ConnectTimeout:
                max_time = '+10'
            else:
                max_time = round(time.time() - max_time, 2)

        writer.writerow(
            {
                'min': min_response,
                'min_time': min_time,
                'max': max_response,
                'max_time' : max_time
            }
        )