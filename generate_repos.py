from requests import post

import time

file = open('pip_repos.txt', 'r')

begin = time.time()
for line in file:
    line = line.replace('\n', '').strip()
    owner, name = line.split('/')
    print(owner + ' -- ' + name)
    response = post(url = f'http://localhost:8000/graph/init?owner={owner}&name={name}&manager=PIP')
    if time.time() - begin >= 86400:
        break
print('Tiempo en generar los 100 repositorios: ' + str(time.time() - begin))
