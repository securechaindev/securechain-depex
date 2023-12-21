# import pandas as pd
# from sklearn import preprocessing
# import seaborn as sns
# import matplotlib.pyplot as plt


# le = preprocessing.LabelEncoder()

# home_data = pd.read_csv('cves.csv', usecols = ['exploit-id', 'cve-published-date', 'av-availability'])

# sns.scatterplot(data = home_data, x = 'cve-published-date', y = 'exploit-id', hue='av-availability')
# plt.show()

# file = open("pip_repos.txt", "r")
# file2 = open("pip_repos2.txt", "w")

# for line in file.readlines():
#     line = line.strip().replace("\n", "")
#     name, owner = line.split("/")
#     file2.write(owner + "/" + name + "\n")

# from requests import post

# pom_min_response = post(url='http://localhost:8000/operation/file/minimize_impact/4:890aea88-721b-4e87-a01f-1fc312de6e16:337?agregator=mean&file_name=pyproject.toml&limit=1&max_level=5', timeout=10).json()
# pom_min_response = round(pom_min_response['result'][0]['file_risk_pyproject.toml'], 2)

# if pom_min_response is not None:
#     min = pom_min_response
# else:
#     min = '-'

# print(min)

# import requests

# CONTENT_TYPES = [
#     "application/vnd.pypi.simple.v1+json"
# ]

# ACCEPT = ", ".join(CONTENT_TYPES)

# resp = requests.get("https://pypi.org/simple/about", headers={"Accept": ACCEPT})

# print(resp.json())