import requests
import pandas as pd
url = "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap150list.csv"
try:
    df = pd.read_csv(url)
    print(df.head())
except Exception as e:
    print(e)
