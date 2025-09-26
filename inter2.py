import pandas as pd
import numpy as np
import plotly.express as px
from pyMyriad import *
from importlib import reload
import pyMyriad.plots

df = pd.DataFrame({
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
age_cut = lambda df: df.Age > 40

atree = AnalysisTree()\
  .split_by("df.Gender")\
  .split_by(label = "Benin", b = benin_fun)\
  .split_at_by(path = [], label = "aaaaaaAge > 40", expr = age_cut)\
  .analyze_by(m = mfun, n = nfun)\
  .analyze_by_at(path = [], label = "aaaaroot analysis", m = mfun, n = nfun)

print(atree)

res = atree.run(df)
ff = forest_plot(res, x = "m", x_err = "n")


