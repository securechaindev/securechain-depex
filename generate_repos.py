from requests import post

import time

# https://djangopackages.org/categories/frameworks/

file = open('pip_repos.txt', 'r')

begin = time.time()
for line in file:
    line = line.replace('\n', '').strip()
    owner, name = line.split('/')
    print(owner + ' -- ' + name)
    response = post(url = f'http://localhost:8000/graph/init?owner={owner}&name={name}')
print('Tiempo en generar los 100 repositorios: ' + str(time.time() - begin))
