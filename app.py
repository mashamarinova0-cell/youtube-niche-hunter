# @title YouTube Niche Hunter: AI-Producer Edition
# @markdown ### 🟢 Нажмите кнопку Play (слева).
# @markdown Подождите ~45 секунд. Скопируйте IP адрес, который появится ниже, и перейдите по ссылке.

import os
import sys
import urllib.request

# --- 1. УСТАНОВКА БИБЛИОТЕК ---
print("⏳ Установка библиотек... (Подождите ~45 сек)")
os.system('pip install streamlit pandas google-api-python-client plotly wordcloud pytrends localtunnel colorthief isodate requests pillow')
print("✅ Библиотеки установлены!")

# Получение внешнего IP для туннеля (нужен для входа)
print("🔗 ВАШ ПАРОЛЬ ДЛЯ ВХОДА (IP): ", end="")
print(urllib.request.urlopen('https://ipv4.icanhazip.com').read().decode('utf8').strip("\n"))

# --- 2. СОЗДАНИЕ ФАЙЛА ПРИЛОЖЕНИЯ ---
with open("app.py", "w", encoding='utf-8') as f:
    f.write('''
import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import isodate
from colorthief import ColorThief
from io import BytesIO
import requests
import numpy as np

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="Niche Hunter GOD MODE", layout="wide", page_icon="🧿")

# --- CSS СТИЛИЗАЦИЯ ---
st.markdown("""
<style>
    /* Карточки метрик */
    .metric-container {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-label { font-size: 14px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 28px; font-weight: bold; color: #fff; margin-top: 5px; }
    
    /* Бейджи */
    .badge-hype { background-color: #ff4b4b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .badge-new { background-color: #00CC96; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .badge-money { background-color: #FFD700; color: black; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    
    /* Цветовая палитра */
    .palette-circle { width: 45px; height: 45px; border-radius: 50%; display: inline-block; margin: 5px; border: 2px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- БАЗА RPM (СТОИМОСТЬ ЗА 1000 ПРОСМОТРОВ) ---
RPM_DATA = {
    'finance': 18.0, 'crypto': 22.0, 'invest': 20.0, 'business': 15.0,
    'tech': 8.0, 'ai': 9.0, 'python': 10.0, 'tutorial': 6.0,
    'health': 5.0, 'fitness': 4.0, 'beauty': 3.5,
    'cars': 7.0, 'real estate': 12.0,
    'gaming': 1.5, 'minecraft': 1.2, 'roblox': 1.0, 'asmr': 2.5,
    'vlog': 2.0, 'comedy': 1.8, 'news': 3.0
}

# --- ФУНКЦИИ ---

def get_estimated_rpm(query):
    query_lower = query.lower()
    best_match = 2.0 # Дефолтный RPM
    for key, val in RPM_DATA.items():
        if key in query_lower:
            best_match = val
            break
    return best_match

def parse_duration_to_minutes(iso_duration):
    try:
        dur = isodate.parse_duration(iso_duration)
        return round(dur.total_seconds() / 60, 1)
    except:
        return 0.0

def get_dominant_colors(url):
    try:
        response = requests.get(url, timeout=3)
        color_thief = ColorThief(BytesIO(response.content))
        # Возвращаем топ-3 цвета
        return color_thief.get_palette(color_count=3, quality=10)
    except:
        return []

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

# --- UI И ЛОГИКА ---

st.sidebar.header("🛸 НАСТРОЙКИ ПОИСКА")
api_key = st.sidebar.text_input("🔑 Ваш API Key YouTube", type="password")
st.sidebar.divider()
query = st.sidebar.text_input("🔍 Ниша / Тема", "Заработок на нейросетях")
days = st.sidebar.slider("📅 Анализ за (дней)", 7, 90, 30)
min_viral_score = st.sidebar.slider("🔥 Мин. Виральность (x)", 1.0, 10.0, 2.0, help="Во сколько раз просмотров больше, чем подписчиков")

st.title("🧿 YouTube Niche Hunter: GOD MODE ULTRA")
st.markdown("Анализ ниши, ДНК обложек, Прогноз дохода и AI-сценарии.")

if st.sidebar.button("ЗАПУСТИТЬ СКАНЕР 🚀", type="primary"):
    if not api_key:
        st.error("❌ Ошибка: Введите API Key!")
    else:
        with st.spinner('📡 Сканируем YouTube... Анализируем цвета... Считаем деньги...'):
            try:
                youtube = build('youtube', 'v3', developerKey=api_key)
                
                # 1. ПОИСК ВИДЕО
                published_after = (datetime.now() - timedelta(days=days)).isoformat("T") + "Z"
                
                search_response = youtube.search().list(
                    q=query, part="id,snippet", maxResults=50, 
                    order="viewCount", type="video", publishedAfter=published_after
                ).execute()
                
                video_ids = [item['id']['videoId'] for item in search_response['items']]
                
                if not video_ids:
                    st.warning("⚠️ Видео не найдено. Попробуйте изменить запрос или период.")
                    st.stop()
                
                # 2. ДЕТАЛИ ВИДЕО
                vid_response = youtube.videos().list(
                    part="statistics,snippet,contentDetails", id=','.join(video_ids)
                ).execute()
                
                # 3. ДЕТАЛИ КАНАЛОВ (для расчета виральности)
                channel_ids = list(set([item['snippet']['channelId'] for item in vid_response['items']]))
                # API лимит 50 id за раз
                chan_response = youtube.channels().list(
                    part="statistics,snippet", id=','.join(channel_ids[:50])
                ).execute()
                
                channel_map = {}
                for ch in chan_response['items']:
                    subs = int(ch['statistics'].get('subscriberCount', 1))
                    created_at = ch['snippet']['publishedAt'][:10]
                    channel_map[ch['id']] = {'subs': subs, 'created': created_at}
                
                # 4. ОБРАБОТКА ДАННЫХ
                data = []
                thumbnails_for_analysis = []
                all_tags = []
                
                estimated_rpm = get_estimated_rpm(query)
                
                for item in vid_response['items']:
                    stats = item['statistics']
                    snip = item['snippet']
                    content = item['contentDetails']
                    ch_id = snip['channelId']
                    
                    # Данные канала
                    ch_info = channel_map.get(ch_id, {'subs': 1, 'created': '2000-01-01'})
                    subs = ch_info['subs'] if ch_info['subs'] > 0 else 1
                    
                    # Метрики
                    views = int(stats.get('viewCount', 0))
                    likes = int(stats.get('likeCount', 0))
                    comments = int(stats.get('commentCount', 0))
                    
                    viral_score = round(views / subs, 2)
                    engagement = round(((likes + comments) / views) * 100, 2) if views > 0 else 0
                    duration_min = parse_duration_to_minutes(content['duration'])
                    revenue = (views / 1000) * estimated_rpm
                    
                    # Возраст канала
                    chan_date = datetime.strptime(ch_info['created'], "%Y-%m-%d")
                    chan_age_days = (datetime.now() - chan_date).days
                    is_new_channel = chan_age_days < 365
                    
                    # Собираем теги
                    if 'tags' in snip:
                        all_tags.extend(snip['tags'])
                    
                    if viral_score >= min_viral_score:
                        row = {
                            'title': snip['title'],
                            'views': views,
                            'subs': subs,
                            'viral_score': viral_score,
                            'engagement': engagement,
                            'duration': duration_min,
                            'revenue': round(revenue),
                            'is_new': is_new_channel,
                            'chan_age': chan_age_days,
                            'channel_title': snip['channelTitle'],
                            'thumb': snip['thumbnails']['high']['url'],
                            'link': f"https://youtu.be/{item['id']}",
                            'date': snip['publishedAt'][:10]
                        }
                        data.append(row)
                        if len(thumbnails_for_analysis) < 5:
                            thumbnails_for_analysis.append(row['thumb'])
                
                df = pd.DataFrame(data)
                
                if df.empty:
                    st.warning("Нет данных, удовлетворяющих фильтру виральности.")
                    st.stop()
                    
                df = df.sort_values(by='viral_score', ascending=False)
                
                # --- ВИЗУАЛИЗАЦИЯ ---
                
                # 1. KPI ПАНЕЛЬ
                st.subheader("📊 Рентген Ниши")
                c1, c2, c3, c4 = st.columns(4)
                
                ideal_duration = df['duration'].median()
                avg_viral = df['viral_score'].mean()
                total_rev = df['revenue'].sum()
                
                c1.markdown(f'<div class="metric-container"><div class="metric-label">Виральность</div><div class="metric-value">{avg_viral:.1f}x</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-container"><div class="metric-label">Идеальная Длина</div><div class="metric-value">{ideal_duration} мин</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="metric-container"><div class="metric-label">Потенциал Выручки</div><div class="metric-value">${total_rev:,.0f}</div></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="metric-container"><div class="metric-label">Свежих каналов</div><div class="metric-value">{len(df[df["is_new"]==True])}</div></div>', unsafe_allow_html=True)
                
                st.divider()
                
                # 2. ЦВЕТОВОЕ ДНК
                st.subheader("🎨 ДНК Успешных Обложек")
                st.write("Скрипт проанализировал пиксели топ-5 вирусных видео. Используйте эти цвета:")
                
                cols = st.columns(10)
                col_idx = 0
                for thumb_url in thumbnails_for_analysis:
                    palette = get_dominant_colors(thumb_url)
                    for color in palette:
                        if col_idx < 10:
                            hex_c = rgb_to_hex(color)
                            cols[col_idx].markdown(f'<div class="palette-circle" style="background-color: {hex_c};" title="{hex_c}"></div>', unsafe_allow_html=True)
                            col_idx += 1
                
                st.divider()

                # 3. ВКЛАДКИ (Дэшборд и AI)
                tab1, tab2, tab3 = st.tabs(["🏆 Список Видео", "📈 Графики", "🧠 AI Продюсер (Промпт)"])
                
                with tab1:
                    for i, row in df.iterrows():
                        with st.container():
                            cc1, cc2 = st.columns([1, 3])
                            cc1.image(row['thumb'], use_column_width=True, style={"border-radius":"10px"})
                            
                            with cc2:
                                st.markdown(f"### [{row['title']}]({row['link']})")
                                
                                # Бейджи
                                badges = f"<span class='badge-hype'>🔥 {row['viral_score']}x HYPE</span> "
                                badges += f"<span class='badge-money'>💰 ${row['revenue']} est.</span> "
                                if row['is_new']:
                                    badges += f"<span class='badge-new'>👶 Новый канал ({row['chan_age']} дн)</span>"
                                st.markdown(badges, unsafe_allow_html=True)
                                
                                st.markdown(f"**Канал:** {row['channel_title']} | **Подписчиков:** {row['subs']:,} | **Просмотры:** {row['views']:,}")
                                st.caption(f"Вовлеченность: {row['engagement']}% | Длительность: {row['duration']} мин | Загружено: {row['date']}")
                            st.divider()

                with tab2:
                    c_g1, c_g2 = st.columns(2)
                    with c_g1:
                        st.markdown("**Карта Возможностей (Scatter Plot)**")
                        fig_scat = px.scatter(df, x="duration", y="views", size="viral_score", color="viral_score",
                                              hover_name="title", log_y=True, title="Длительность vs Просмотры")
                        # Линия идеальной длины
                        fig_scat.add_vline(x=ideal_duration, line_dash="dash", line_color="green", annotation_text="Идеал")
                        st.plotly_chart(fig_scat, use_container_width=True)
                    
                    with c_g2:
                        st.markdown("**Частота вирусных публикаций**")
                        df['day_name'] = pd.to_datetime(df['date']).dt.day_name()
                        day_counts = df['day_name'].value_counts()
                        fig_bar = px.bar(day_counts, x=day_counts.index, y=day_counts.values, title="В какой день недели лучше постить?")
                        st.plotly_chart(fig_bar, use_container_width=True)

                with tab3:
                    st.header("Генератор Сценария (Mega-Prompt)")
                    st.success("Скопируйте этот текст и отправьте в ChatGPT/Claude. Он содержит все найденные данные.")
                    
                    # Подготовка данных для промпта
                    top_tags_str = ", ".join(pd.Series(all_tags).value_counts().head(15).index.tolist())
                    top_titles_str = "\\n- ".join(df.head(5)['title'].tolist())
                    
                    prompt_text = f"""
ACT AS: Elite YouTube Strategist.
CONTEXT: I am creating a video for the niche "{query}".

--- 📊 REAL MARKET DATA ANALYZED ---
My analysis of the top viral videos shows:
1. PROVEN VIRAL LENGTH: {ideal_duration} minutes (This is the pacing target).
2. TOP TAGS/TOPICS: {top_tags_str}
3. COMPETITOR HITS (Model these hooks):
- {top_titles_str}

--- 📝 TASK ---
Generate 3 Viral Video Concepts based on this data. For EACH concept provide:

1. 🎯 CLICKBAIT TITLE: High CTR, under 60 chars.
2. 🖼️ THUMBNAIL SPEC: Describe the visual. Use high contrast colors.
3. 🎣 THE HOOK (0:00-0:45): Write the verbatim script. Start with a visual shock or bold statement.
4. 🧱 STRUCTURE: Outline the video segments to hit exactly {ideal_duration} minutes.
5. 🧠 WHY IT WORKS: Explain the psychology using the tags provided.

OUTPUT: Russian Language. Markdown format.
"""
                    st.text_area("👇 Ваш Промпт:", prompt_text, height=500)

            except Exception as e:
                st.error(f"Произошла ошибка: {e}. Проверьте API Key.")

''')

# --- 3. ЗАПУСК TУННЕЛЯ И ПРИЛОЖЕНИЯ ---
print("🚀 Запуск сервера... Нажмите на ссылку ниже, когда она появится.")
os.system("streamlit run app.py & npx localtunnel --port 8501")
