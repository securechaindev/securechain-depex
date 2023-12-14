import pandas as pd
from sklearn import preprocessing
import seaborn as sns
import matplotlib.pyplot as plt


le = preprocessing.LabelEncoder()

home_data = pd.read_csv('cves2.csv', usecols = ['published', 'impact', 'av-attack-vector', 'av-attack-complexity'])

sns.scatterplot(data = home_data, x = 'published', y = 'impact', hue='av-attack-vector')
plt.show()