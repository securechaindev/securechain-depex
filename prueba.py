import pandas as pd
from sklearn import preprocessing
import seaborn as sns
import matplotlib.pyplot as plt


le = preprocessing.LabelEncoder()

home_data = pd.read_csv('cves.csv', usecols = ['exploit-id', 'cve-published-date', 'av-availability'])

sns.scatterplot(data = home_data, x = 'cve-published-date', y = 'exploit-id', hue='av-availability')
plt.show()