# -*- coding: utf-8 -*-
"""
Created on Fri Apr 11 19:23:42 2025

@author: peill
"""

import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
from datetime import datetime

import plotly.graph_objects as go
import plotly.express as px

root_dir = Path(__file__).resolve().parents[0]
data_dir = root_dir / 'data'
# print(f'\n{root_dir=}\n{data_dir=}\n')

#%% Import data
@st.cache_data #cache data in order not reload it everytime the page is being refreshed
def load_data(verbose=False):
    df_agg = pd.read_csv(data_dir / 'Aggregated_Metrics_By_Video.csv')
    df_agg = df_agg.iloc[1:,:] # Remove total line on top
    df_agg.columns = ['VideoID', 'VideoTitle', 'VideoPublishTime', 'CommentsAdded', 'Shares',
                      'Dislikes', 'Likes', 'SubscribersLost', 'SubscribersGained',
                      'RPM_$', 'CRM_$', 'AverageViewed_%', 'AverageViewDuration', 'Views',
                      'WatchTime_h', 'Subscribers', 'EstimatedRevenue_$', 'Impressions',
                      'ImpressionsClickThroughRate_%']
    # Transform date and times into right format
    df_agg['VideoPublishTime'] = pd.to_datetime(df_agg['VideoPublishTime'], format='%b %d, %Y')
    df_agg['AverageViewDuration'] = df_agg['AverageViewDuration'].apply(lambda x: datetime.strptime(x,"%H:%M:%S"))
    df_agg['AverageViewDuration'] = df_agg['AverageViewDuration'].apply(lambda x: x.hour*3600 + x.minute*60 + x.second)

    
    df_agg_sub = pd.read_csv(data_dir  / 'Aggregated_Metrics_By_Country_And_Subscriber_Status.csv')
    df_agg_sub.columns = ['VideoTitle', 'VideoID', 'VideoDuration', 'ThumbnailLink',
                      'CountryCode', 'IsSub', 'Views', 'Likes', 'Dislikes', 'LikesRemoved',
                      'SubscribersGained', 'SubscribersLost', 'AverageViewed_%', 'AverageWatchTime',
                      'Comments']
    
    df_comments = pd.read_csv(data_dir  / 'All_Comments_Final.csv')
    df_comments['Date'] = pd.to_datetime(df_comments['Date'])
    
    df_timeperf = pd.read_csv(data_dir  / 'Video_Performance_Over_Time.csv')
    df_timeperf['Date'] = df_timeperf['Date'].str.replace('Sept', 'Sep')
    df_timeperf['Date'] = pd.to_datetime(df_timeperf['Date'])
    
    if verbose:
        print(df_agg.dtypes)
        print(df_agg_sub.dtypes)
        print(df_comments.dtypes)
        print(df_timeperf.dtypes)
        print('\n\t--> Data correctly loaded in memory')
        
    
    return df_agg, df_agg_sub, df_comments, df_timeperf


#%% 

df_agg, df_agg_sub, df_comments, df_timeperf = load_data()

metric_cols = ['Views', 'Likes', 'Subscribers', 'Shares', 'CommentsAdded', 'RPM_$', 'AverageViewed_%', 'AverageViewDuration']
cols = ['VideoTitle', 'VideoPublishTime']
cols.extend(metric_cols)

df_agg_diff = df_agg[cols].copy()
date_12mo = df_agg_diff['VideoPublishTime'].max() - pd.DateOffset(months=12)
date_3mo  = df_agg_diff['VideoPublishTime'].max() - pd.DateOffset(months=3)

median_12mo = df_agg_diff[df_agg_diff['VideoPublishTime']>=date_12mo]
median_3mo = df_agg_diff[df_agg_diff['VideoPublishTime']>=date_3mo]

median_12mo = median_12mo[metric_cols].median()
median_3mo = median_3mo[metric_cols].median()
median_3mo = (median_3mo - median_12mo) / median_12mo
for i, x in enumerate(median_3mo.values):
    median_3mo.iloc[i] = f'{x*100:.2f}%'

df_agg_diff.loc[:,metric_cols] = (df_agg_diff.loc[:,metric_cols] - median_12mo).div(median_12mo)
df_agg_diff = df_agg_diff.sort_values(by='VideoPublishTime', ascending=False)
#%% Build dashboard

add_sidebar = st.sidebar.selectbox('Aggregate or Individual video', ['Aggregate Metrics','Individual Video Analysis'])

if add_sidebar == 'Aggregate Metrics':
    st.write('Aggregated metrics')
    st_cols = st.columns(5)
    
    for i, col in enumerate(metric_cols):
        with st_cols[i]:
            st.metric(col, median_12mo[col], delta=median_3mo[col])
        
    st.dataframe(df_agg_diff)
if add_sidebar == 'Individual Video Analysis':
    st.write('Individual Video Analysis')
