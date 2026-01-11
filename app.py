import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import isodate
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="YouTube Pro Hunter", layout="wide", page_icon="🚀")

# --- CSS (PRO STYLE) ---
st.markdown("""
<style>
    /* Стиль для метрик */
    .metric-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 8px 12px;
        text-align: center;
        font-size: 14px;
        color: #212529;
        margin-right: 5px;
        display: inline-block;
    }
    .metric-label { font-size: 10px; color: #6c757d; text-transform: uppercase; }
    .metric-val { font-weight: bold; font-size: 15px; }
    
    /* Ссылки */
    a { text-decoration: none; color: #0366d6; font-weight: 600; }
    a:hover { text-decoration: underline; }

    /* Аватар канала */
    .ch-avatar {
        border-radius: 50%;
        width: 40px;
        height: 40px;
        vertical-align: middle;
        margin-right: 10px;
        border: 1px solid #ddd;
    }
    
    /* Бейджи */
    .badge-viral { background: #d4edda; color: #155724; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: bold; border: 1px solid #c3e6cb; }
    .badge-date { color: #666; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# --- ФУНКЦИИ ---
def parse_duration(iso_duration):
    try:
        dur = isodate.parse_duration(iso_duration)
        return dur.total_seconds()
    except:
        return 0

def format_date_ru(date_str):
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        months = {1: 'янв', 2: 'фев', 3: 'мар', 4: 'апр', 5: 'мая', 6: 'июн', 7: 'июл', 8: 'авг', 9: 'сен', 10: 'окт', 11: 'ноя', 12: 'дек'}
        return f"{dt.day} {months[dt.month]} {dt.year}"
    except:
        return date_str

def format_number(num):
    if num >= 1_000_000: return f"{num/1_000_000:.1f}M"
    if num >= 1_000: return f"{num/1_000:.1f}K"
    return str(num)

# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("🚀 PRO Настройки")
    api_key = st.text_input("YouTube API Key", type="password")
    
    st.subheader("🔍 Поиск")
    query = st.text_input("Ниша", "Минимализм")
    region = st.selectbox("🌍 Страна поиска", ["RU", "US", "GB", "KZ", "UA", "BY", "DE"], index=0)
    
    st.subheader("⚙️ Фильтры")
    video_type = st.radio("Формат", ["Все", "Длинные (> 1 мин)", "Shorts (< 1 мин)"])
    date_filter = st.selectbox("Дата загрузки", ["За месяц", "За неделю", "За сегодня", "За все время"])
    min_views = st.number_input("Мин. просмотров", 1000, step=5000)
    
    st.info("💡 Совет: Для поиска вирусных видео выбирайте 'За месяц'.")

days_map = {"За сегодня": 1, "За неделю": 7, "За месяц": 30, "За все время": 365}
days_ago = days_map[date_filter]

# --- ГЛАВНЫЙ ЭКРАН ---
st.title(f"Анализ ниши: {query}")

if st.button("ЗАПУСТИТЬ СКАНЕР 🔥", type="primary"):
    if not api_key:
        st.error("❌ Введите API Key")
    else:
        with st.spinner('Сбор данных... Анализ каналов...'):
            try:
                youtube = build('youtube', 'v3', developerKey=api_key)
                
                # 1. ПОИСК
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

                # 2. ДЕТАЛИ ВИДЕО
                vid_res = youtube.videos().list(part="statistics,snippet,contentDetails", id=','.join(ids)).execute()
                
                # 3. ДЕТАЛИ КАНАЛОВ (Аватарки + Дата создания)
                ch_ids = list(set([v['snippet']['channelId'] for v in vid_res['items']]))
                ch_res = youtube.channels().list(part="statistics,snippet", id=','.join(ch_ids[:50])).execute()
                
                ch_data = {}
                for c in ch_res['items']:
                    ch_data[c['id']] = {
                        'subs': int(c['statistics'].get('subscriberCount', 0)),
                        'created': c['snippet']['publishedAt'],
                        'avatar': c['snippet']['thumbnails']['default']['url'],
                        'customUrl': c['snippet'].get('customUrl', f"channel/{c['id']}")
                    }

                # 4. ОБРАБОТКА ДАННЫХ
                data = []
                for v in vid_res['items']:
                    snip = v['snippet']
                    stats = v['statistics']
                    ch_id = snip['channelId']
                    
                    # Фильтры
                    views = int(stats.get('viewCount', 0))
                    if views < min_views: continue
                    
                    dur_sec = parse_duration(v['contentDetails']['duration'])
                    is_short = dur_sec <= 60
                    
                    if video_type == "Длинные (> 1 мин)" and is_short: continue
                    if video_type == "Shorts (< 1 мин)" and not is_short: continue

                    # Данные канала
                    ch_info = ch_data.get(ch_id, {'subs': 1, 'created': '2000-01-01', 'avatar': '', 'customUrl': ''})
                    
                    # Виральность
                    viral = round(views / ch_info['subs'], 1) if ch_info['subs'] > 0 else 0
                    
                    # Правильная картинка (Max resolution для длинных)
                    thumb = snip['thumbnails'].get('maxres', snip['thumbnails'].get('high', snip['thumbnails']['medium']))['url']
                    
                    data.append({
                        'title': snip['title'],
                        'thumb': thumb,
                        'views': views,
                        'likes': int(stats.get('likeCount', 0)),
                        'date_video': format_date_ru(snip['publishedAt']),
                        'duration': "Shorts" if is_short else f"{int(dur_sec//60)}:{int(dur_sec%60):02d}",
                        'viral': viral,
                        'link_video': f"https://youtu.be/{v['id']}",
                        # Данные канала
                        'ch_name': snip['channelTitle'],
                        'ch_avatar': ch_info['avatar'],
                        'ch_subs': ch_info['subs'],
                        'ch_created': format_date_ru(ch_info['created']),
                        'ch_link': f"https://www.youtube.com/{ch_info['customUrl']}" if '@' in ch_info['customUrl'] else f"https://www.youtube.com/channel/{ch_id}"
                    })

                # --- ВЫВОД В СТИЛЕ СПИСКА (PRO LIST) ---
                st.markdown(f"### Результаты ({len(data)} шт.)")
                
                for row in data:
                    with st.container():
                        # Разметка: Картинка (1 часть) | Инфо (3 части)
                        c1, c2 = st.columns([1, 2])
                        
                        with c1:
                            # Обложка видео
                            st.image(row['thumb'], use_container_width=True)
                            
                        with c2:
                            # Заголовок
                            st.markdown(f"#### [{row['title']}]({row['link_video']})")
                            
                            # Метрики (Блоки)
                            st.markdown(f"""
                            <div class="metric-box"><div class="metric-label">Просмотры</div><div class="metric-val">{format_number(row['views'])}</div></div>
                            <div class="metric-box"><div class="metric-label">Виральность</div><div class="metric-val" style="color: {'green' if row['viral']>1 else 'black'}">{row['viral']}x</div></div>
                            <div class="metric-box"><div class="metric-label">Длительность</div><div class="metric-val">{row['duration']}</div></div>
                            <div class="metric-box"><div class="metric-label">Дата выхода</div><div class="metric-val">{row['date_video']}</div></div>
                            """, unsafe_allow_html=True)
                            
                            st.write("") # Отступ
                            
                            # Блок Канала (Аватар + Имя + Дата)
                            st.markdown(f"""
                            <img src="{row['ch_avatar']}" class="ch-avatar">
                            <a href="{row['ch_link']}" target="_blank">{row['ch_name']}</a> 
                            <span style="color: #666; font-size: 14px;"> • {format_number(row['ch_subs'])} подп.</span>
                            <br><span class="badge-date" style="margin-left: 54px;">📅 Канал создан: {row['ch_created']}</span>
                            """, unsafe_allow_html=True)
                        
                        st.divider()

            except Exception as e:
                st.error(f"Ошибка: {e}")
