import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import isodate
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="YouTube Pro Hunter", layout="wide", page_icon="🎯")

# --- CSS (МИНИМАЛИЗМ) ---
st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; padding: 10px; border-radius: 5px;}
    .badge {padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 5px; background: #e2e3e5; color: #383d41;}
    .big-date {font-weight: bold; color: #0068c9;}
</style>
""", unsafe_allow_html=True)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def parse_duration(iso_duration):
    """Секунды из ISO формата"""
    try:
        dur = isodate.parse_duration(iso_duration)
        return dur.total_seconds()
    except:
        return 0

def format_date_ru(date_str):
    """Перевод даты в формат '25 декабря 2025'"""
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        months = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня',
            7: 'июля', 8: 'августа', 9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        return f"{dt.day} {months[dt.month]} {dt.year}"
    except:
        return date_str

def detect_content_type(title, tags):
    """Определение типа контента"""
    text = (title + " " + " ".join(tags)).lower()
    types = []
    if any(x in text for x in ['ai', 'gpt', 'midjourney', 'runway', 'neural', 'нейросет']):
        types.append("🤖 AI")
    if any(x in text for x in ['animation', 'cartoon', 'anime', 'анимаци', 'мульт']):
        types.append("🎨 Анимация")
    if any(x in text for x in ['shorts', '#shorts']):
        types.append("📱 Shorts")
    if any(x in text for x in ['asmr', 'асмр']):
        types.append("🎧 ASMR")
    return types

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.header("⚙️ Настройки")
api_key = st.sidebar.text_input("YouTube API Key", type="password")
st.sidebar.divider()
query = st.sidebar.text_input("Ниша / Запрос", "Заработок на нейросетях")
region = st.sidebar.selectbox("Страна поиска", ["RU", "US", "GB", "DE", "KZ", "UA", "BY"], index=0)
video_type = st.sidebar.radio("Формат", ["Все", "Shorts (< 60 сек)", "Длинные (> 60 сек)"])
date_filter = st.sidebar.selectbox("Когда загружено", ["За сегодня", "За неделю", "За месяц", "За все время"])
st.sidebar.divider()
min_views = st.sidebar.number_input("Мин. просмотров", value=1000, step=1000)

# Логика даты для API
days_map = {"За сегодня": 1, "За неделю": 7, "За месяц": 30, "За все время": 365}
days_ago = days_map[date_filter]

# --- ОСНОВНОЙ ЭКРАН ---
st.title(f"🔎 Поиск: {query}")

if st.button("НАЙТИ 🚀", type="primary"):
    if not api_key:
        st.error("Введите API Key!")
    else:
        with st.spinner('Поиск данных...'):
            try:
                youtube = build('youtube', 'v3', developerKey=api_key)
                
                # 1. ЗАПРОС К API
                pub_after = (datetime.now() - timedelta(days=days_ago)).isoformat("T") + "Z"
                
                search_res = youtube.search().list(
                    q=query, part="id,snippet", maxResults=50, 
                    order="viewCount", type="video", 
                    publishedAfter=pub_after, regionCode=region
                ).execute()
                
                ids = [i['id']['videoId'] for i in search_res['items']]
                if not ids:
                    st.warning("Ничего не найдено.")
                    st.stop()

                # 2. ДЕТАЛИ ВИДЕО И КАНАЛОВ
                vid_res = youtube.videos().list(part="statistics,snippet,contentDetails", id=','.join(ids)).execute()
                
                ch_ids = list(set([v['snippet']['channelId'] for v in vid_res['items']]))
                ch_res = youtube.channels().list(part="statistics,snippet", id=','.join(ch_ids[:50])).execute()
                
                ch_data = {}
                for c in ch_res['items']:
                    ch_data[c['id']] = {
                        'subs': int(c['statistics'].get('subscriberCount', 0)),
                        'created': c['snippet']['publishedAt']
                    }

                # 3. ОБРАБОТКА
                videos = []
                channels_stats = {}

                for v in vid_res['items']:
                    snip = v['snippet']
                    stats = v['statistics']
                    ch_id = snip['channelId']
                    
                    # Фильтр просмотров
                    views = int(stats.get('viewCount', 0))
                    if views < min_views: continue

                    # Фильтр длительности
                    dur_sec = parse_duration(v['contentDetails']['duration'])
                    is_short = dur_sec <= 60
                    
                    if video_type == "Shorts (< 60 сек)" and not is_short: continue
                    if video_type == "Длинные (> 60 сек)" and is_short: continue

                    # Данные канала
                    ch_info = ch_data.get(ch_id, {'subs': 0, 'created': '2000-01-01'})
                    viral = round(views / ch_info['subs'], 2) if ch_info['subs'] > 0 else 0
                    
                    # Сбор статистики канала
                    if ch_id not in channels_stats:
                        channels_stats[ch_id] = {
                            'title': snip['channelTitle'],
                            'subs': ch_info['subs'],
                            'created_raw': ch_info['created'],
                            'video_count_in_search': 0,
                            'total_views': 0
                        }
                    channels_stats[ch_id]['video_count_in_search'] += 1
                    channels_stats[ch_id]['total_views'] += views

                    tags = snip.get('tags', [])
                    
                    videos.append({
                        'id': v['id'],
                        'title': snip['title'],
                        'thumb': snip['thumbnails']['high']['url'],
                        'views': views,
                        'likes': int(stats.get('likeCount', 0)),
                        'date_ru': format_date_ru(snip['publishedAt']),
                        'time': snip['publishedAt'][11:16],
                        'duration': "Shorts" if is_short else f"{int(dur_sec//60)}:{int(dur_sec%60):02d}",
                        'channel': snip['channelTitle'],
                        'viral': viral,
                        'tags': tags,
                        'types': detect_content_type(snip['title'], tags)
                    })

                df = pd.DataFrame(videos)
                if df.empty:
                    st.warning("Нет видео под выбранные фильтры.")
                    st.stop()
                
                df = df.sort_values(by='views', ascending=False)

                # --- ВЫВОД ---
                tab1, tab2 = st.tabs(["📹 Список Видео", "📢 Каналы"])

                with tab1:
                    st.caption(f"Найдено: {len(df)} шт.")
                    # Сетка по 2
                    for i in range(0, len(df), 2):
                        cols = st.columns(2)
                        batch = df.iloc[i:i+2]
                        for idx, row in batch.iterrows():
                            c_idx = 0 if idx == batch.index[0] else 1
                            with cols[c_idx]:
                                st.image(row['thumb'], use_container_width=True)
                                st.markdown(f"#### [{row['title']}](https://youtu.be/{row['id']})")
                                
                                # Бейджи
                                if row['types']:
                                    st.markdown(" ".join([f"<span class='badge'>{t}</span>" for t in row['types']]), unsafe_allow_html=True)
                                
                                st.markdown(f"""
                                **👀 {row['views']:,}** | 👍 {row['likes']:,} | ⏱ {row['duration']}
                                <br>📅 Дата выхода: **{row['date_ru']}**
                                <br>👤 Канал: **{row['channel']}**
                                """, unsafe_allow_html=True)
                                
                                if row['viral'] > 1.5:
                                    st.success(f"🚀 Виральность: {row['viral']}x (Выше нормы)")
                                
                                with st.expander("Теги видео"):
                                    st.write(", ".join(row['tags']) if row['tags'] else "Нет тегов")
                                st.divider()

                with tab2:
                    st.write("Авторы, попавшие в поиск:")
                    ch_df = pd.DataFrame(channels_stats.values()).sort_values(by='total_views', ascending=False)
                    
                    for _, ch in ch_df.iterrows():
                        # Дата создания канала красиво
                        created_ru = format_date_ru(ch['created_raw'])
                        
                        with st.container():
                            cc1, cc2 = st.columns([1, 4])
                            with cc2:
                                st.subheader(ch['title'])
                                st.markdown(f"""
                                📅 **Дата создания канала:** <span class='big-date'>{created_ru}</span>
                                <br>👥 Подписчиков: **{ch['subs']:,}**
                                <br>🔥 Видео в этом поиске: **{ch['video_count_in_search']}** (Просмотров: {ch['total_views']:,})
                                """, unsafe_allow_html=True)
                            st.divider()

            except Exception as e:
                st.error(f"Ошибка: {e}")
