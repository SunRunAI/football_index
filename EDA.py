# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 13:13:43 2020

@author: MikeyJW
"""

''' EDA '''

#TODO: Remove short smaples from the mkt beta calculations (or do the top 100 format)
#TODO: Compare returns to SPY
#TODO: Think of more classic stock market stuff
#TODO: Make top 200 mask dynamic

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# import yfinance as yf [to get spy numbers] [change environment???]

# Import and organise dataframe
df = pd.read_csv('Q32019_Q22020.csv')
df['Date'] = pd.to_datetime(df['Date'])
df.set_index(['Date', 'PlayerName'], inplace=True)
df.sort_index(level=0, inplace=True)

df['daily_log_returns'] = df['EndofDayPrice'].apply(np.log).groupby(level=1).diff(1)
df['daily_mkt_log_returns'] = df['ave_mkt_price'].apply(np.log).groupby(level=1).diff(1) 

first_day = df.loc[('2019-07-01', slice(None)), :]
top200_mask = first_day.nlargest(200, 'EndofDayPrice').index.droplevel(0).values
top200 = df.loc[(slice(None), top200_mask), :]


# Gen informative plots

# Extract index price
index_price = df.groupby(level=0)['ave_mkt_price'].head(1).values
# Benchmark (holding roughly the same amount of all players TODO: THIS NEEDS REFINING [if we can't hold equal values of all players???])
mkt_log_returns = df['daily_mkt_log_returns'].groupby(level=0).head(1).droplevel(1)
mkt_log_returns.cumsum().apply(np.exp).plot(title='Benchmark')

# PLOT: Market aggregates
# TODO: put epl start/end dates in for reference.
mkt_returns = mkt_log_returns.apply(np.exp)
mkt_returns.plot(title='Daily market returns')
plt.plot(index_price) # Compare this to the money in circulation stats from FIE
sns.kdeplot(mkt_returns) # Comp to norm dist/SPY
plt.boxplot(mkt_returns.dropna())


# Gen cov matrix and slice off the useful values
cov = df.groupby(level=1)[['daily_returns', 'daily_mkt_returns']].cov()
cov = cov.loc[(slice(None), 'daily_mkt_returns'), 'daily_returns']

cov.index = cov.index.droplevel(1)
mkt_beta = cov / (df.groupby(level=1)['daily_returns'].std() ** 2)

# PLOT: Market beta dispersion
sns.kdeplot(mkt_beta.dropna())


# Business day effects
df['dayofweek'] = df.index.get_level_values(0)
df['dayofweek'] = df['dayofweek'].dt.weekday

# Extract day of week from index
mkt_returns = df.groupby(level=0)[['daily_mkt_returns', 'dayofweek']].head(1)
mkt_returns.index = mkt_returns.index.droplevel(level=1)

# PLOT: Day of week trends
mkt_returns.groupby('dayofweek').mean()
sns.boxplot(x="dayofweek", y='daily_mkt_returns', data=mkt_returns)
sns.violinplot(x="dayofweek", y='daily_mkt_returns', data=mkt_returns)





####################################################################





# Begin scouting basic quant strategy:
from strategies_and_optimisation import custom_grid_search, momentum_strat, mean_reversion, post_div_drift, SMAC

# STRATEGY 1: Price momentum
data = top200
strategy = momentum_strat
param_grid = {'lookback_window': [3, 7, 14, 21],
              'holding_period': [3, 7, 14, 21]}

results = custom_grid_search(data, strategy, param_grid)
print(results)

optimal_params =  {'holding_period': 7,
                   'lookback_window': 7}

results = momentum_strat(data, param_dict=optimal_params)
results.plot(title='Momentum strategy cumulative returns')
# TODO: Check Sharpe ratio?



# STRATEGY 2: Mean reversion
# Find biggest losers in past x period, and long them. # This is a bad strat but holding periods tell us something???
data = top200
strategy = mean_reversion
param_grid = {'lookback_window': [3, 7, 14, 21],
              'holding_period': [3, 7, 14, 21]}

results = custom_grid_search(data, strategy, param_grid)
print(results)

optimal_params =  {'holding_period': 7,
                   'lookback_window': 21}

results = mean_reversion(data, param_dict=optimal_params)
results.plot(title='Mean reversion cumulative returns')



# STRATEGY 3: Post div. drift
data = top200
strategy = post_div_drift
param_grid = {'holding_period': [3, 6, 13, 20]}

results = custom_grid_search(data, strategy, param_grid)
print(results)

optimal_params =  {'holding_period': 20}

results = post_div_drift(data, param_dict=optimal_params)
results.plot(title='Mean reversion cumulative returns')



# STRATEGY 5.1: SMAC (single player)
data = top200.loc[(slice(None),'Mohamed Salah'), 'EndofDayPrice'].unstack()
strategy = SMAC
param_grid = {'duration_MA1': [5, 22],
              'duration_MA2': [5, 22]}

results = custom_grid_search(data, strategy, param_grid)
print(results)

optimal_params =  {'duration_MA1': 5, 'duration_MA2': 22}

results = SMAC(data, param_dict=optimal_params)
results.plot(title='Mean reversion cumulative returns')



# STRATEGY 5.2: EMAC (aggregate market)
data = top200.loc[(slice(None),'Mohamed Salah'), 'EndofDayPrice'].unstack()
strategy = EMAC
param_grid = {'duration_MA1': [5, 22],
              'duration_MA2': [5, 22]}

results = custom_grid_search(data, strategy, param_grid)
print(results)

optimal_params =  {'duration_MA1': 5, 'duration_MA2': 22}

results = EMAC(data, param_dict=optimal_params)
results.plot(title='Mean reversion cumulative returns')



# STRATEGY 6: ALWAYS BUY/SELL IPO (extension: given conditions) (or just general analysis)