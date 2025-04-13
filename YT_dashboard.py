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

def style_df(x, props:list):
    try:
        return props[0] if x>0 else props[1]
    except:
        pass
    
def style_percentage(x):
    try:
        return f'{x:.2%}' if isinstance(x, float) else x
    except:
        pass
    
def audience(country):
    if country == 'US':
        return 'USA'
    elif country == 'ID':
        return 'India'
    else:
        return 'Other'
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

df_time_diff = pd.merge(df_timeperf, df_agg.loc[:,['VideoID','VideoPublishTime']], left_on='External Video ID', right_on='VideoID')
df_time_diff['days_published'] = (df_time_diff['Date'] - df_time_diff['VideoPublishTime']).dt.days

date_12mo = df_agg['VideoPublishTime'].max() - pd.DateOffset(months=12)
df_time_diff_yr = df_time_diff[df_time_diff['VideoPublishTime']>=date_12mo]

views_days = pd.pivot_table(df_time_diff_yr, index='days_published', values='Views', aggfunc=[np.mean, np.median, lambda x: np.percentile(x, 80), lambda x: np.percentile(x, 20)]).reset_index()
views_days.columns = ['days_published','mean_views','median_views','80pct_views','20pct_views']
views_days = views_days[views_days['days_published'].between(0,30)]
views_cumulative = views_days.loc[:,['days_published','median_views','80pct_views','20pct_views']]
views_cumulative.loc[:,['median_views','80pct_views','20pct_views']] = views_cumulative.loc[:,['median_views','80pct_views','20pct_views']].cumsum()



#%% Build dashboard

add_sidebar = st.sidebar.selectbox('Aggregate or Individual video', ['Aggregate Metrics','Individual Video Analysis'])

if add_sidebar == 'Aggregate Metrics':
    st.header('Overall metrics')
    
    n_cols = 4
    st_cols1 = st.columns(n_cols)
    st_cols2 = st.columns(n_cols)
    
    for i, col in enumerate(metric_cols):
        if i < n_cols:
            with st_cols1[i]:
                st.metric(col, median_12mo[col], delta=median_3mo[col])
        else:
            with st_cols2[i-n_cols]:
                st.metric(col, median_12mo[col], delta=median_3mo[col])
    
    df_agg_diff['VideoPublishTime'] = df_agg_diff['VideoPublishTime'].apply(lambda x: x.date())
    
    st.dataframe(df_agg_diff.style.applymap(style_df, props=['color:lime','color:red']).format(style_percentage))
    
    
    
if add_sidebar == 'Individual Video Analysis':
    st.header('Individual Video Analysis')
    
    # Fisrt chart
    videos = tuple(df_agg['VideoTitle'])
    video_select = st.selectbox('Pick a video to analyze:', videos)

    agg_filtered = df_agg[df_agg['VideoTitle']==video_select]
    agg_sub_filtered = df_agg_sub[df_agg_sub['VideoTitle']==video_select]
    agg_sub_filtered['Country'] = agg_sub_filtered['CountryCode'].apply(audience)
    agg_sub_filtered.sort_values('IsSub', inplace=True)
    
    fig1 = px.bar(agg_sub_filtered, x='Views', y='IsSub', color='Country', orientation='h')
    st.plotly_chart(fig1)
    
    # Second chart
    agg_time_filtered = df_time_diff[df_time_diff['Video Title']==video_select]
    first30 = agg_time_filtered[agg_time_filtered['days_published'].between(0,30)]
    first30 = first30.sort_values('days_published')

    st.subheader('30 days launch comparison')
    fig2 = go.Figure() 
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['80pct_views'], mode='lines', name='80%', line=dict(color='purple', dash='dot')))
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['median_views'], mode='lines', name='50%', line=dict(color='royalblue', dash='dash')))
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['20pct_views'], mode='lines', name='20%', line=dict(color='purple', dash='dot')))
    fig2.add_trace(go.Scatter(x=first30['days_published'], y=first30['Views'].cumsum(), mode='lines', name='Current Video', line=dict(color='firebrick', width=3)))
    fig2.update_layout(xaxis_title='Days', yaxis_title='Views')
    
    st.plotly_chart(fig2)
    
    
    