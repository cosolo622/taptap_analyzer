# -*- coding: utf-8 -*-
"""
TapTap舆情监控 - Streamlit前端
v1.1版本 - 直接读取Excel数据展示
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime, timedelta
from collections import Counter
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False

st.set_page_config(
    page_title="TapTap舆情监控",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("📊 TapTap舆情监控")
st.sidebar.markdown("---")

data_files = [
    "鹅鸭杀_GLM分析_v1.1.xlsx",
    "鹅鸭杀_GLM分析_v1.1_合并子类.xlsx",
]
data_file = st.sidebar.selectbox("选择数据文件", data_files)

@st.cache_data
def load_data(file_name):
    file_path = f"./output/{file_name}"
    if not os.path.exists(file_path):
        st.error(f"文件不存在: {file_path}")
        return None, None, None, None, None
    
    df_detail = pd.read_excel(file_path, sheet_name='评价明细')
    df_sentiment = pd.read_excel(file_path, sheet_name='情感分布-总体')
    df_daily = pd.read_excel(file_path, sheet_name='情感分布-按天')
    df_weekly = pd.read_excel(file_path, sheet_name='情感分布-按周')
    
    try:
        df_main_cat = pd.read_excel(file_path, sheet_name='问题分类-大类')
    except:
        df_main_cat = None
    
    return df_detail, df_sentiment, df_daily, df_weekly, df_main_cat

df_detail, df_sentiment, df_daily, df_weekly, df_main_cat = load_data(data_file)

if df_detail is None:
    st.stop()

st.title("📊 TapTap舆情监控仪表盘")
st.markdown(f"**数据文件**: {data_file} | **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("总评价数", len(df_detail))
with col2:
    avg_rating = df_detail['星级'].mean() if '星级' in df_detail.columns else 0
    st.metric("平均星级", f"{avg_rating:.2f}")
with col3:
    positive_count = len(df_detail[df_detail['情感'] == '正向']) if '情感' in df_detail.columns else 0
    st.metric("正向评价", f"{positive_count}条", f"{positive_count/len(df_detail)*100:.1f}%")
with col4:
    negative_count = len(df_detail[df_detail['情感'] == '负向']) if '情感' in df_detail.columns else 0
    st.metric("负向评价", f"{negative_count}条", f"{negative_count/len(df_detail)*100:.1f}%")

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 情感分析", "📋 问题分类", "☁️ 词云分析", "📊 趋势分析", "📝 评价明细"])

with tab1:
    st.subheader("情感分布")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        fig_pie = px.pie(df_sentiment, values='数量', names='情感', 
                         title='情感分布',
                         color_discrete_sequence=['#4CAF50', '#FFC107', '#FF5722', '#9E9E9E'])
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        fig_bar = px.bar(df_sentiment, x='情感', y='数量', 
                         title='情感分布条形图',
                         color='情感',
                         color_discrete_sequence=['#4CAF50', '#FFC107', '#FF5722', '#9E9E9E'])
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.subheader("情感趋势")
    
    df_daily['日期'] = pd.to_datetime(df_daily['日期'])
    df_daily = df_daily.sort_values('日期')
    
    fig_trend = go.Figure()
    for col in ['正向', '负向', '中性', '中性偏负']:
        if col in df_daily.columns:
            fig_trend.add_trace(go.Scatter(
                x=df_daily['日期'],
                y=df_daily[col],
                mode='lines+markers',
                name=col
            ))
    fig_trend.update_layout(title='情感分天趋势', xaxis_title='日期', yaxis_title='评价条数')
    st.plotly_chart(fig_trend, use_container_width=True)

with tab2:
    st.subheader("问题分类统计")
    
    if df_main_cat is not None:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig_cat = px.bar(df_main_cat.head(10), x='出现次数', y='大类',
                            orientation='h',
                            title='问题大类TOP10')
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            fig_cat_pie = px.pie(df_main_cat.head(10), values='出现次数', names='大类',
                                title='问题大类分布')
            st.plotly_chart(fig_cat_pie, use_container_width=True)
    else:
        st.info("暂无问题分类数据")

with tab3:
    st.subheader("词云分析")
    
    stopwords = set(['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                     '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
                     '自己', '这', '那', '他', '她', '它', '们', '这个', '那个', '什么', '怎么',
                     '可以', '因为', '所以', '但是', '如果', '还是', '或者', '而且', '然后',
                     '比较', '真的', '非常', '特别', '还是', '已经', '一直', '一下', '一些',
                     '觉得', '感觉', '可能', '应该', '需要', '希望', '建议', '游戏', '玩家',
                     '鹅鸭杀', '鹅', '鸭', '杀', '玩', '好玩', '有趣', '不错', '挺好', '太'])
    
    all_text = ' '.join(df_detail['评价内容'].dropna().astype(str))
    words = jieba.cut(all_text)
    word_list = [w for w in words if len(w) >= 2 and w not in stopwords]
    word_counter = Counter(word_list)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if word_counter:
            wc = WordCloud(
                font_path='C:/Windows/Fonts/simhei.ttf',
                width=800,
                height=400,
                background_color='white',
                max_words=100
            )
            wc.generate_from_frequencies(word_counter)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
    
    with col2:
        st.subheader("高频词TOP20")
        word_df = pd.DataFrame(word_counter.most_common(20), columns=['词语', '频次'])
        st.dataframe(word_df, use_container_width=True)

with tab4:
    st.subheader("评价数量趋势")
    
    daily_count = df_detail.groupby('日期').size().reset_index(name='评价数')
    daily_count['日期'] = pd.to_datetime(daily_count['日期'])
    daily_count = daily_count.sort_values('日期')
    
    fig_daily = px.line(daily_count, x='日期', y='评价数', 
                        title='评价数量分天趋势',
                        markers=True)
    st.plotly_chart(fig_daily, use_container_width=True)
    
    st.subheader("评价数量分周统计")
    st.dataframe(df_weekly, use_container_width=True)

with tab5:
    st.subheader("评价明细")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        sentiment_filter = st.multiselect("情感筛选", df_detail['情感'].unique().tolist(), default=df_detail['情感'].unique().tolist())
    with col2:
        rating_filter = st.multiselect("星级筛选", sorted(df_detail['星级'].unique().tolist()), default=sorted(df_detail['星级'].unique().tolist()))
    with col3:
        search_text = st.text_input("关键词搜索", "")
    
    df_filtered = df_detail[df_detail['情感'].isin(sentiment_filter)]
    df_filtered = df_filtered[df_filtered['星级'].isin(rating_filter)]
    if search_text:
        df_filtered = df_filtered[df_filtered['评价内容'].str.contains(search_text, na=False)]
    
    st.markdown(f"**筛选结果**: {len(df_filtered)} 条")
    
    display_cols = ['日期', '用户名', '星级', '情感', '问题分类', '一句话摘要']
    display_cols = [c for c in display_cols if c in df_filtered.columns]
    st.dataframe(df_filtered[display_cols], use_container_width=True, height=400)
    
    csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
    st.download_button("导出CSV", csv, f"舆情数据_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

st.markdown("---")
st.markdown("💡 **提示**: 这是一个MVP版本，后续将支持更多平台和功能")
