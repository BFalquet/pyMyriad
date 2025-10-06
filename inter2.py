import pandas as pd

import numpy as np
import plotly.express as px
from pyMyriad import *
from importlib import reload
import pyMyriad.plots

df = pd.DataFrame({
  "id": np.arange(1000),
  "Gender": np.random.choice(["M", "F"], 1000),
  "Age": np.random.randint(18, 70, 1000),
  "Income": np.random.normal(50000, 15000, 1000),
  "Country": np.random.choice(["Benin", "Albania"], 1000),
  "A": np.random.normal(0, 1, 1000),
  "B": np.random.normal(0, 10, 1000)
})

mfun = lambda df: np.mean(df.Income)
nfun = lambda df: np.std(df.Income)
benin_fun =  lambda df: df.Country == 'Benin'
age_40 = lambda df: df.Age > 40
age_60 = lambda df: df.Age > 60

atree = AnalysisTree()\
  .split_by("df.Gender")\
  .summarize_by(label = "something", m = mfun, n = nfun)\
  .split_by(label = "Benin Y/N", expr = benin_fun)\
  .split_by(label = "Age Group", age40 = age_40, age60 = age_60)\
  .analyze_by(m = mfun, n = nfun)

dtree = atree.run(df)
col = "df.Gender"
from pyMyriad.tabular import flatten

forest_plot(dtree, "m", "n", col = "Age Group")