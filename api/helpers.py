import pandas as pd

def filter_area(df, query):
    return df[df['area'].str.lower().str.contains('|'.join(query.lower().split()))]
