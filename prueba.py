# import pandas as pd
# from sklearn import preprocessing
# import seaborn as sns
# import matplotlib.pyplot as plt


# le = preprocessing.LabelEncoder()

# home_data = pd.read_csv('cves.csv', usecols = ['exploit-id', 'cve-published-date', 'av-availability'])

# sns.scatterplot(data = home_data, x = 'cve-published-date', y = 'exploit-id', hue='av-availability')
# plt.show()

file = open("pip_repos.txt", "r")
file2 = open("pip_repos2.txt", "w")

for line in file.readlines():
    line = line.strip().replace("\n", "")
    name, owner = line.split("/")
    file2.write(owner + "/" + name + "\n")