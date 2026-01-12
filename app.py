import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import isodate
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="Vidx Hunter Clone", layout="wide", page_icon="⚡")

# --- CSS (CLEAN VIDX STYLE) ---
st.markdown("""
<style>
    /* Фон */
    .stApp { background-color: #f8fafc; }
    
    /* Карточка */
    .vidx-card {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        transition: transform 0.2s;
    }
    .vidx-card:hover { border-color: #cbd5e1; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }

    /* Контейнер карточки */
    .card-flex { display: flex; flex-wrap: wrap; }
    
    /* Левая часть (Превью) */
    .card-thumb {
        width: 360px;
        min-width: 360px;
        height: 202px; /* 16:9 aspect ratio fix */
        position: relative;
    }
    .card-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-top-left-radius: 12px;
        border-bottom-left-radius: 12px;
    }
    
    /* Длительность на превью */
    .dur-badge {
        position: absolute;
        bottom: 8px;
        right: 8px;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
    }

    /* Правая часть (Инфо) */
    .card-info {
        padding: 16px 20px;
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    /* Заголовок */
    .vid-title a {
        font-size: 18px;
        font-weight: 700;
        color: #1e293b;
        text-decoration: none;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .vid-title a:hover { color: #3b82f6; }

    /* Метрики (Pills) */
    .meta-row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
    .pill {
        background: #f1f5f9;
        color: #475569;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .pill.green { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .pill.blue { background: #dbeafe; color: #1e40af; }

    /* Канал */
    .channel-row {
        display: flex;
        align-items: center;
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid #f1f5f9;
    }
    .ch-avatar { width: 40px; height: 40px; border-radius: 50%; margin-right: 12px; border: 1px solid #e2e8f0;}
    .ch-name { font-weight: 700; color: #334155; font-size: 14px; }
    .ch-stats { font-size: 12px; color: #64748b; margin-top: 2px; }

    @media (max-width: 768px) {
        .card-thumb { width: 100%; min-width: 100%; height: auto; }
        .card-img { border-radius: 12px 12px 0 0; aspect-ratio: 16/9; }
    }
</style>
""", unsafe_allow_html=True)

# --- ФУНКЦИИ ---
def parse_duration_sec(iso_duration):
    try:
        dur = isodate.parse_duration(iso_duration)
        return int(dur.total_seconds())
    except:
        return 0

def format_duration(sec):
    m = sec // 60
    s = sec % 60
    return f"{m}:{s:02d}"

def format_num(num):
    if num >= 1_000_000: return f"{num/1_000_000:.1f}M"
    if num >= 1_000: return f"{num/1_000:.1f}K"
    return str(num)

def time_ago(date_str):
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        delta = datetime.now() - dt
        if delta.days == 0: return "Сегодня"
        if delta.days == 1: return "Вчера"
        if delta.days < 30: return f"{delta.days} дн. назад"
        return f"{delta.days // 30} мес. назад"
    except:
        return date_str

# --- SIDEBAR (ФИЛЬТРЫ КАК В VIDX) ---
with st.sidebar:
    st.header("⚡ Vidx Filters")
    api_key = st.text_input("YouTube API Key", type="password")
    
    st.subheader("1. Поиск")
    query_raw = st.text_input("Ключевое слово", "Minecraft")
    
    # ПРЕСЕТЫ FACELESS
    niche_preset = st.selectbox("Тип ниши (Presets)", 
        ["🌐 Любая", "👤 Faceless (Без лица)", "🎮 Гейминг", "🧘 Медитация/ASMR", "🤖 AI Content"])
    
    # Логика пресетов (добавляем слова в поиск)
    query = query_raw
    if niche_preset == "👤 Faceless (Без лица)":
        query += " (tutorial|animation|compilation|no talking|satisfying)"
    elif niche_preset == "🧘 Медитация/ASMR":
        query += " (asmr|relaxing|meditation|sleep)"
    elif niche_preset == "🤖 AI Content":
        query += " (ai|chatgpt|midjourney|neural)"

    region_ui = st.selectbox("Регион", ["🌍 Global", "🇺🇸 USA", "🇷🇺 Russia", "🇩🇪 Germany"])
    
    st.subheader("2. Метрики (Sliders)")
    # Ползунки как в Vidx
    min_views = st.slider("Мин. Просмотров", 1000, 500_000, 10_000, step=1000)
    
    # Диапазон подписчиков (эмуляция, фильтруем после запроса)
    subs_range = st.slider("Подписчики канала (Range)", 0, 10_000_000, (1000, 500_000))
    
    # Длительность
    dur_range = st.slider("Длительность (мин)", 0, 60, (2, 20))
    
    # Дата
    date_filter = st.selectbox("Дата загрузки", ["За 30 дней", "За 7 дней", "За 24 часа", "За год"])

# Логика даты
days_map = {"За 24 часа": 1, "За 7 дней": 7, "За 30 дней": 30, "За год": 365}
days_ago = days_map[date_filter]
if "Global" in region_ui: region_code = None
else: region_code = region_ui.split(" ")[1]

# --- MAIN ---
st.title(f"Результаты: {query_raw} {'(Faceless Mode)' if 'Faceless' in niche_preset else ''}")

if st.button("Найти Аномалии (Outliers) 🔎", type="primary"):
    if not api_key:
        st.error("Введите API Key")
    else:
        with st.spinner('Сканируем базу... Применяем Faceless фильтры...'):
            try:
                youtube = build('youtube', 'v3', developerKey=api_key)
                
                # 1. SEARCH
                pub_after = (datetime.now() - timedelta(days=days_ago)).isoformat("T") + "Z"
                
                search_params = {
                    'q': query,
                    'part': "id,snippet",
                    'maxResults': 50,
                    'order': "viewCount",
                    'type': "video",
                    'publishedAfter': pub_after
                }
                if region_code: search_params['regionCode'] = region_code
                
                search_res = youtube.search().list(**search_params).execute()
                ids = [i['id']['videoId'] for i in search_res['items']]
                
                if not ids:
                    st.warning("Ничего не найдено.")
                    st.stop()

                # 2. DETAILS
                vid_res = youtube.videos().list(part="statistics,snippet,contentDetails", id=','.join(ids)).execute()
                
                ch_ids = list(set([v['snippet']['channelId'] for v in vid_res['items']]))
                ch_res = youtube.channels().list(part="statistics,snippet", id=','.join(ch_ids[:50])).execute()
                
                ch_data = {}
                for c in ch_res['items']:
                    ch_data[c['id']] = {
                        'subs': int(c['statistics'].get('subscriberCount', 0)),
                        'avatar': c['snippet']['thumbnails']['default']['url'],
                        'created': c['snippet']['publishedAt'][:10]
                    }

                # 3. FILTERING & LOGIC
                data = []
                for v in vid_res['items']:
                    stats = v['statistics']
                    snip = v['snippet']
                    ch_id = snip['channelId']
                    
                    # Фильтр просмотров
                    views = int(stats.get('viewCount', 0))
                    if views < min_views: continue
                    
                    # Фильтр длительности
                    sec = parse_duration_sec(v['contentDetails']['duration'])
                    mins = sec / 60
                    if mins < dur_range[0] or mins > dur_range[1]: continue
                    
                    # Данные канала
                    ch_info = ch_data.get(ch_id, {'subs': 0, 'avatar': '', 'created': ''})
                    subs = ch_info['subs']
                    
                    # Фильтр подписчиков (ВАЖНО ДЛЯ VIDX)
                    if subs < subs_range[0] or subs > subs_range[1]: continue
                    
                    # Outlier Score
                    outlier = round(views / subs, 1) if subs > 0 else 0
                    
                    thumb = snip['thumbnails'].get('maxres', snip['thumbnails'].get('high'))['url']
                    
                    data.append({
                        'id': v['id'],
                        'title': snip['title'],
                        'thumb': thumb,
                        'duration': format_duration(sec),
                        'views': views,
                        'ago': time_ago(snip['publishedAt']),
                        'outlier': outlier,
                        'ch_name': snip['channelTitle'],
                        'ch_avatar': ch_info['avatar'],
                        'ch_subs': subs,
                        'ch_created': ch_info['created']
                    })
                
                # Сортировка: сначала самые аномальные (высокий Outlier Score)
                data.sort(key=lambda x: x['outlier'], reverse=True)
                
                if not data:
                    st.warning("Нет видео под эти фильтры. Попробуйте расширить диапазон подписчиков или длительности.")
                    st.stop()

                st.success(f"Найдено {len(data)} видео (Отсортировано по Outlier Score)")

                # --- ОТРИСОВКА КАРТОЧЕК ---
                for row in data:
                    # Стиль бейджа
                    outlier_style = "green" if row['outlier'] >= 2.0 else "blue"
                    outlier_icon = "🔥" if row['outlier'] >= 5.0 else "📈"
                    
                    st.markdown(f"""
                    <div class="vidx-card">
                        <div class="card-flex">
                            <div class="card-thumb">
                                <img src="{row['thumb']}" class="card-img">
                                <div class="dur-badge">{row['duration']}</div>
                            </div>
                            <div class="card-info">
                                <div class="vid-title">
                                    <a href="https://youtu.be/{row['id']}" target="_blank">{row['title']}</a>
                                </div>
                                
                                <div class="meta-row">
                                    <span class="pill">👀 {format_num(row['views'])}</span>
                                    <span class="pill">⏱ {row['ago']}</span>
                                    <span class="pill {outlier_style}">{outlier_icon} Score: {row['outlier']}x</span>
                                </div>
                                
                                <div class="channel-row">
                                    <img src="{row['ch_avatar']}" class="ch-avatar">
                                    <div>
                                        <div class="ch-name">{row['ch_name']}</div>
                                        <div class="ch-stats">
                                            👥 {format_num(row['ch_subs'])} • Создан: {row['ch_created']}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Ошибка API: {e}")
