from googleapiclient.discovery import build
import pandas as pd
import streamlit as st

KEY = "AIzaSyAN1kp6p7TdYX4Rh1S5WlD6RQ2pp2q2-4s"
DEVELOPER_KEY = KEY
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                developerKey=DEVELOPER_KEY)


def video_search(youtube , q='python 自動化' , max_results=50):
    response = youtube.search().list(
        q=q,
        part='id,snippet',
        order ='viewCount',
        type='video',
        maxResults=max_results
    ).execute()

    items_id = []
    items = response['items']

    for item in items:
        item_id = {}

        item_id['video_id'] = item['id']['videoId']
        item_id['channel_id'] = item['snippet']['channelId']

        items_id.append(item_id)

    df_video = pd.DataFrame(items_id)
    return df_video

def get_results(df_video,threshold):
    
    channel_ids = df_video['channel_id'].unique().tolist()

    # チャンネルIDと登録者数
    subscriber_list = youtube.channels().list(
        part='statistics',
        id = channel_ids,
        fields = 'items(id,statistics(subscriberCount))'
    ).execute()

    subscribers = []
    for item in subscriber_list['items']:
        subscriber = {}
        if len(item['statistics'])>0:
            subscriber['channel_id'] = item['id']
            subscriber['subscriber_count'] = int(item['statistics']['subscriberCount'])
        else:
            subscriber['channel_id'] = item['id']
        subscribers.append(subscriber)
    df_subscribers = pd.DataFrame(subscribers)

    # videoID-channelID-登録者数をマージ
    df = pd.merge(left=df_video , right=df_subscribers , on='channel_id')
    
    # 登録者数で一部のみ抽出
    df_extracted = df[df['subscriber_count']>threshold]

    # video情報
    video_ids = df_extracted['video_id'].tolist()
    videos_list = youtube.videos().list(
        part='snippet,statistics',
        id = ','.join(video_ids),
        fields = 'items(id,snippet(title),statistics(viewCount))'
    ).execute()

    videos_info = []
    for item in videos_list['items']:
        video_info = {}
        video_info['video_id'] = item['id']
        video_info['title'] = item['snippet']['title']    
        video_info['view_count'] = int(item['statistics']['viewCount'])
        videos_info.append(video_info)

    df_videos_info = pd.DataFrame(videos_info)
    
    # 取得した全データのマージ

    results = pd.merge(left=df_extracted , right=df_videos_info  , on='video_id')
    results = results.loc[:,['video_id','title','view_count','subscriber_count','channel_id']]
    
    return results

# サイドバー

st.sidebar.write('## クエリと閾値の設定')
st.sidebar.write('### クエリの入力')
query = st.sidebar.text_input('検索クエリを入力してください','Python 自動化')

st.sidebar.write('### 閾値の設定')
threshold = st.sidebar.slider('登録者の基準（--人以上）' , 100000,500000,250000)

st.sidebar.write('### 表示件数の最大値設定')
max_results = st.sidebar.slider('表示件数の最大値' , 0,100,50)

# メイン

st.title('YouTube分析アプリ')

st.write('### 選択中のパラメータ')
st.markdown(f"""
- 検索クエリ : {query}
- 登録者数の基準（--人以上）: {threshold}
- 表示件数の最大値 : {max_results}
""")

df_video = video_search(youtube , q=query , max_results=max_results)
results = get_results(df_video,threshold=threshold)

st.write('### 分析結果' , results)
st.write('### 動画再生')

video_id = st.text_input('動画IDを入力してください')
url = f'https://youtu.be/{video_id}'

video_field = st.empty()
video_field.write('こちらに動画が表示されます')

if st.button('ビデオ表示'):
    if len(video_id) > 0 :
        try:
            video_field.video(url)
        except:
           st.error('エラーが起きています。動画が表示できません') 
