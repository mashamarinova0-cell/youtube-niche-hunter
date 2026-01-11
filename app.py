import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import isodate
from colorthief import ColorThief
from io import BytesIO
import requests

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="Niche Hunter GOD MODE", layout="wide", page_icon="🧿")

# --- CSS СТИЛИЗАЦИЯ ---
st.markdown("""
<style>
    .metric-container {
        background-color: #262730;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-label { font-size: 14px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 28px; font-weight: bold; color: #fff; margin-top: 5px; }
    .badge-hype { background-color: #ff4b4b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .badge-new { background-color: #00CC96; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .badge-money { background-color: #FFD700; color: black; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .palette-circle { width: 45px; height: 45px; border-radius: 50%; display: inline-block; margin: 5px; border: 2px solid #333; }
</style>
""", unsafe_allow_html=True)

# --- БАЗА RPM ---
RPM_DATA = {
    'finance': 18.0, 'crypto': 22.0, 'invest': 20.0, 'business': 15.0,
    'tech': 8.0, 'ai': 9.0, 'python': 10.0, 'tutorial': 6.0,
    'health': 5.0, 'fitness': 4.0, 'beauty': 3.5,
    'cars': 7.0, 'real estate': 12.0,
    'gaming': 1.5, 'minecraft': 1.2, 'roblox': 1.0, 'asmr': 2.5,
    'vlog': 2.0, 'comedy': 1.8, 'news': 3.0
}

def get_estimated_rpm(query):
    query_lower = query.lower()
    best_match = 2.0 
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
        return color_thief.get_palette(color_count=3, quality=10)
    except:
        return []

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

# --- UI ---
st.sidebar.header("🛸 НАСТРОЙКИ ПОИСКА")
api_key = st.sidebar.text_input("🔑 Ваш API Key YouTube", type="password")
st.sidebar.divider()
query = st.sidebar.text_input("🔍 Ниша / Тема", "Заработок на нейросетях")
days = st.sidebar.slider("📅 Анализ за (дней)", 7, 90, 30)
min_viral_score = st.sidebar.slider("🔥 Мин. Виральность (x)", 1.0, 10.0, 2.0)

st.title("🧿 YouTube Niche Hunter: GOD MODE ULTRA")
st.markdown("Анализ ниши, ДНК обложек, Прогноз дохода и AI-сценарии.")

if st.sidebar.button("ЗАПУСТИТЬ СКАНЕР 🚀", type="primary"):
    if not api_key:
        st.error("❌ Ошибка: Введите API Key!")
    else:
        with st.spinner('📡 Сканируем YouTube... Анализируем цвета... Считаем деньги...'):
            try:
                youtube = build('youtube', 'v3', developerKey=api_key)
                
                published_after = (datetime.now() - timedelta(days=days)).isoformat("T") + "Z"
                
                search_response = youtube.search().list(
                    q=query, part="id,snippet", maxResults=50, 
                    order="viewCount", type="video", publishedAfter=published_after
                ).execute()
                
                video_ids = [item['id']['videoId'] for item in search_response['items']]
                
                if not video_ids:
                    st.warning("⚠️ Видео не найдено. Попробуйте изменить запрос.")
                    st.stop()
                
                vid_response = youtube.videos().list(
                    part="statistics,snippet,contentDetails", id=','.join(video_ids)
                ).execute()
                
                channel_ids = list(set([item['snippet']['channelId'] for item in vid_response['items']]))
                chan_response = youtube.channels().list(
                    part="statistics,snippet", id=','.join(channel_ids[:50])
                ).execute()
                
                channel_map = {}
                for ch in chan_response['items']:
                    subs = int(ch['statistics'].get('subscriberCount', 1))
                    created_at = ch['snippet']['publishedAt'][:10]
                    channel_map[ch['id']] = {'subs': subs, 'created': created_at}
                
                data = []
                thumbnails_for_analysis = []
                all_tags = []
                estimated_rpm = get_estimated_rpm(query)
                
                for item in vid_response['items']:
                    stats = item['statistics']
                    snip = item['snippet']
                    content = item['contentDetails']
                    ch_id = snip['channelId']
                    
                    ch_info = channel_map.get(ch_id, {'subs': 1, 'created': '2000-01-01'})
                    subs = ch_info['subs'] if ch_info['subs'] > 0 else 1
                    
                    views = int(stats.get('viewCount', 0))
                    likes = int(stats.get('likeCount', 0))
                    comments = int(stats.get('commentCount', 0))
                    
                    viral_score = round(views / subs, 2)
                    engagement = round(((likes + comments) / views) * 100, 2) if views > 0 else 0
                    duration_min = parse_duration_to_minutes(content['duration'])
                    revenue = (views / 1000) * estimated_rpm
                    
                    chan_date = datetime.strptime(ch_info['created'], "%Y-%m-%d")
                    chan_age_days = (datetime.now() - chan_date).days
                    is_new_channel = chan_age_days < 365
                    
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
                    st.warning("Нет данных.")
                    st.stop()
                    
                df = df.sort_values(by='viral_score', ascending=False)
                
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
                
                st.subheader("🎨 ДНК Успешных Обложек")
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

                tab1, tab2, tab3 = st.tabs(["🏆 Список Видео", "📈 Графики", "🧠 AI Продюсер"])
                
                with tab1:
                    for i, row in df.iterrows():
                        with st.container():
                            cc1, cc2 = st.columns([1, 3])
                            # ИСПРАВЛЕННАЯ СТРОКА НИЖЕ
                            cc1.image(row['thumb'], use_column_width=True)
                            with cc2:
                                st.markdown(f"### [{row['title']}]({row['link']})")
                                badges = f"<span class='badge-hype'>🔥 {row['viral_score']}x HYPE</span> <span class='badge-money'>💰 ${row['revenue']} est.</span> "
                                if row['is_new']: badges += f"<span class='badge-new'>👶 Новый ({row['chan_age']} дн)</span>"
                                st.markdown(badges, unsafe_allow_html=True)
                                st.markdown(f"**Канал:** {row['channel_title']} | **Подп:** {row['subs']:,} | **Прос:** {row['views']:,}")
                                st.caption(f"Вовлеченность: {row['engagement']}% | Длит: {row['duration']} мин | Дата: {row['date']}")
                            st.divider()

                with tab2:
                    c_g1, c_g2 = st.columns(2)
                    with c_g1:
                        fig_scat = px.scatter(df, x="duration", y="views", size="viral_score", color="viral_score", log_y=True, title="Длительность vs Просмотры")
                        fig_scat.add_vline(x=ideal_duration, line_dash="dash", line_color="green", annotation_text="Идеал")
                        st.plotly_chart(fig_scat, use_container_width=True)
                    with c_g2:
                        df['day_name'] = pd.to_datetime(df['date']).dt.day_name()
                        day_counts = df['day_name'].value_counts()
                        fig_bar = px.bar(day_counts, x=day_counts.index, y=day_counts.values, title="Дни недели")
                        st.plotly_chart(fig_bar, use_container_width=True)

                with tab3:
                    st.header("Генератор Сценария (Mega-Prompt)")
                    top_tags_str = ", ".join(pd.Series(all_tags).value_counts().head(15).index.tolist())
                    top_titles_str = "\\n- ".join(df.head(5)['title'].tolist())
                    prompt_text = f"""ACT AS: YouTube Strategist.\nCONTEXT: Niche "{query}".\nDATA:\n1. VIRAL LENGTH: {ideal_duration} min.\n2. TOP TAGS: {top_tags_str}\n3. MODEL HOOKS:\n- {top_titles_str}\n\nTASK: Generate 3 Viral Concepts (Title, Thumbnail, Hook Script, Structure). OUTPUT: Russian."""
                    st.text_area("Скопируй в ChatGPT:", prompt_text, height=300)

            except Exception as e:
                st.error(f"Ошибка: {e}")
