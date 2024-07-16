from googleapiclient.discovery import build
import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px
from streamlit_option_menu import option_menu

# API connection
def api_connect():
    api_key = 'AIzaSyDD0PFs1Ywj2ZDhUeJkxlfiPvVNrLgigs0'
    api_service_name = "youtube"
    api_version = "v3"
    youtube = build(api_service_name, api_version, developerKey=api_key)
    return youtube

youtube = api_connect()

# Get channel information
def Get_Channel_Info(channel_id):
    request = youtube.channels().list(
        part='snippet,contentDetails,statistics',
        id=channel_id)
    response = request.execute()
    for i in response['items']:
        data = dict(Channel_Name=i['snippet']['title'],
                    Channel_Id=i["id"],
                    Subscribers=i['statistics'].get('subscriberCount'),
                    Views=i["statistics"].get('viewCount'),
                    Total_Videos=i['statistics'].get('videoCount'),
                    Channel_Description=i["snippet"]["description"],
                    Playlist_Id=i["contentDetails"]["relatedPlaylists"]["uploads"])
        return data

# Get video IDs
def Get_Videos_Ids(channel_id):
    video_ids = []
    response = youtube.channels().list(id=channel_id,
                                       part='contentDetails').execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None
    while True:
        response1 = youtube.playlistItems().list(part='snippet',
                                                 playlistId=playlist_id,
                                                 maxResults=50,
                                                 pageToken=next_page_token).execute()
        for i in range(len(response1['items'])):
            video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = response1.get('nextPageToken')
        if next_page_token is None:
            break
    return video_ids


# Get video information
def Get_Video_Info(video_ids):
    video_data = []
    for video_id in video_ids:
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        response = request.execute()
        for item in response["items"]:
            data = dict(Channel_Name=item['snippet']['channelTitle'],
                        Channel_Id=item['snippet']['channelId'],
                        Video_Id=item['id'],
                        Title=item['snippet']['title'],
                        Tags=item['snippet'].get('tags'),
                        Thumbnail=item['snippet']['thumbnails']['default']['url'],
                        Description=item['snippet'].get('description'),
                        Published_Date=pd.to_datetime(item["snippet"]["publishedAt"]),
                        Duration=item['contentDetails']['duration'],
                        Views=item['statistics'].get('viewCount'),
                        Comments=item['statistics'].get('commentCount'),
                        Likes=item['statistics'].get('likeCount'),
                        DisLikes=item['statistics'].get('dislikeCount'),
                        Favorite_Count=item['statistics'].get('favoriteCount'),
                        Definition=item['contentDetails']['definition'],
                        Caption_Status=item['contentDetails']['definition'],
                        )
            video_data.append(data)
    return video_data

# Get comment information
def Get_Comment_Info(video_ids):
    comment_data = []
    try:
        for video_id in video_ids:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=50
            )
            response = request.execute()
            for item in response['items']:
                data = dict(Comment_Id=item['snippet']['topLevelComment']['id'],
                            Video_Id=item['snippet']['topLevelComment']['snippet']['videoId'],
                            Channel_Id=item['snippet']['channelId'],
                            Comment_Text=item['snippet']['topLevelComment']['snippet'].get('textDisplay'),
                            Comment_Author=item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            Comment_Publisment=item['snippet']['topLevelComment']['snippet']['publishedAt'])
                comment_data.append(data)
    except:
        pass
    return comment_data

# Get playlist details
def Get_Playlist_Details(channel_id):
    next_page_token = None
    All_data = []
    while True:
        request = youtube.playlists().list(
            part='snippet,contentDetails',
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        for item in response['items']:
            data = dict(Playlist_Id=item['id'],
                        Title=item['snippet']['title'],
                        Channel_Id=item['snippet']['channelId'],
                        Channel_Name=item['snippet']['channelTitle'],
                        Published_At=pd.to_datetime(item["snippet"]["publishedAt"]),
                        Video_Count=item['contentDetails']['itemCount'])
            All_data.append(data)
        next_page_token = response.get('nextPageToken')
        if next_page_token is None:
            break
    return All_data

# SQLite3 database connection
connection = sqlite3.connect('YouTube_Data_Base.db')
cur = connection.cursor()

# Create tables
cur.execute('''CREATE TABLE IF NOT EXISTS Channels
             (Channel_Name TEXT, Channel_Id TEXT PRIMARY KEY, Subscribers INTEGER,
              Views INTEGER, Total_Videos INTEGER, Channel_Description TEXT, Playlist_Id TEXT)''')

cur.execute('''CREATE TABLE IF NOT EXISTS Playlists
             (Playlist_Id TEXT PRIMARY KEY, Title TEXT, Channel_Id TEXT, Channel_Name TEXT,
              Published_At TEXT, Video_Count INTEGER)''')

cur.execute('''CREATE TABLE IF NOT EXISTS Videos
             (Channel_Name TEXT, Channel_Id TEXT, Video_Id TEXT PRIMARY KEY, Title TEXT,
              Tags TEXT, Thumbnail TEXT, Description TEXT, Published_Date TEXT, Duration TEXT,
              Views INTEGER, Comments INTEGER, Likes INTEGER, DisLikes INTEGER, Favorite_Count INTEGER,
              Definition TEXT, Caption_Status TEXT)''')

cur.execute('''CREATE TABLE IF NOT EXISTS Comments
             (Comment_Id TEXT PRIMARY KEY, Video_Id TEXT, Channel_Id TEXT, Comment_Text TEXT,
              Comment_Author TEXT, Comment_Publisment TEXT)''')
connection.commit()

# Function to convert DataFrame columns to match SQLite table data types
def convert_df_to_sql_dtypes(df, table_name):

    channel_info_dtype = {
        'Subscribers': int,
        'Views': int,
        'Total_Videos': int,
        'Playlist_Id': str,
        'Channel_Description': str if 'Channel_Description' in df.columns else object
    }

    video_data_dtype = {
        'Views': int,
        'Published_Date': str,
        'Comments': int,
        'Likes': int,
        'DisLikes': int,
        'Favorite_count': int,
        'Definition': str if 'Definition' in df.columns else object,
        'Caption_Status': str if 'Caption_Status' in df.columns else object,
        'Channel_Name': str,
        'Tags': str,
        'Thumbnail': str,
        'Description': str,
        'Duration': str,
        'Channel_Id': str,
        'Title': str
    }

    comments_dtype = {
        'Comment_Text': str,
        'Comment_Author': str,
        'Comment_Publishment': str if 'Comment_Publishment' in df.columns else object,
        'Video_Id': str
    }

    playlist_details_dtype = {
        'Title': str,
        'Channel_Name': str,
        'Published_At': str if 'Published_At' in df.columns else object,
        'Video_Count': int,
        'Channel_Id': str
    }

    # Choose the appropriate dtype mapping based on table_name
    if table_name == 'Channels':
        dtype_mapping = channel_info_dtype
    elif table_name == 'Videos':
        dtype_mapping = video_data_dtype
    elif table_name == 'Comments':
        dtype_mapping = comments_dtype
    elif table_name == 'Playlists':
        dtype_mapping = playlist_details_dtype
    else:
        raise ValueError(f"Unsupported Table Name: {table_name}")

    # Convert each column in the DataFrame to match SQLite data types
    for col, dtype in dtype_mapping.items():
        if col in df.columns:
            if dtype == int:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            elif dtype == float:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)
            elif dtype == str:
                df[col] = df[col].astype(str).fillna('')
            elif dtype == object:
                pass
            elif dtype == pd.Timestamp:
                df[col] = pd.to_datetime(df[col], errors='coerce').fillna(pd.Timestamp('1900-01-01'))

    return df

def channel_details(channel_id):
    channel_detail = Get_Channel_Info(channel_id)
    playlist_details = Get_Playlist_Details(channel_id)
    video_ids = Get_Videos_Ids(channel_id)
    video_details = Get_Video_Info(video_ids)
    comment_details = Get_Comment_Info(video_ids)

    # Convert to DataFrame
    Channel_df = pd.DataFrame([channel_detail])
    Video_df = pd.DataFrame(video_details)
    Comments_df = pd.DataFrame(comment_details)
    Playlist_df = pd.DataFrame(playlist_details)

    # Convert each DataFrame to match SQLite table data types
    cha_details = convert_df_to_sql_dtypes(Channel_df, 'Channels')
    vid_details = convert_df_to_sql_dtypes(Video_df, 'Videos')
    comt_details = convert_df_to_sql_dtypes(Comments_df, 'Comments')
    ply_details = convert_df_to_sql_dtypes(Playlist_df, 'Playlists')

    for _, cha in cha_details.iterrows():
        cur.execute("INSERT INTO Channels VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (cha['Channel_Name'], cha['Channel_Id'], cha['Subscribers'], cha['Views'],
                  cha['Total_Videos'], cha['Channel_Description'], cha['Playlist_Id']))

    for _, ply in ply_details.iterrows():
        cur.execute("INSERT INTO Playlists VALUES (?, ?, ?, ?, ?, ?)",
                  (ply['Playlist_Id'], ply['Title'], ply['Channel_Id'], ply['Channel_Name'],
                   ply['Published_At'], ply['Video_Count']))

    for _, vid in vid_details.iterrows():
        cur.execute("INSERT INTO Videos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (vid['Channel_Name'], vid['Channel_Id'], vid['Video_Id'], vid['Title'], vid['Tags'],
                   vid['Thumbnail'], vid['Description'], vid['Published_Date'], vid['Duration'], vid['Views'] or 0,
                   vid['Comments'] or 0, vid['Likes'] or 0, vid['DisLikes'] or 0, vid['Favorite_Count'] or 0, vid['Definition'] or '',
                   vid['Caption_Status'] or ''))

    for _, comt in comt_details.iterrows():
        cur.execute("INSERT INTO Comments VALUES (?, ?, ?, ?, ?, ?)",
                  (comt['Comment_Id'], comt['Video_Id'], comt['Channel_Id'], comt['Comment_Text'], comt['Comment_Author'],
                   comt['Comment_Publisment']))

    connection.commit()
    return "Upload Completed Successfully"

def all_functions(channel_id): #main function
  cur.execute("SELECT 1 FROM Channels WHERE Channel_Id = ?", (channel_id,))
  result = cur.fetchone()

  if result:
    message="Data for this Channel ID is already stored."
  else:
    all_data_collection = channel_details(channel_id)
    if all_data_collection == "Upload Completed Successfully":
      message = "Successfully Stored"
    else:
      message = "Data Storing Faild"
  return message


from isodate import parse_duration
def dur(duration_str): #function to avoid time formate problem in video duration
    duration_seconds = parse_duration(duration_str).total_seconds()
    return duration_seconds

# SQL queries to retrieve data from SQLite database
ch=pd.read_sql_query('''SELECT Channel_Name as 'CHANNEL NAME',Subscribers as 'SUBSCRIPTION COUNT', Channel_Description as 'CHANNEL DESCRIPTION' from Channels''',connection)
vid=pd.read_sql_query('''SELECT Channel_Name as 'CHANNEL NAME',Title as 'VIDEO NAME', Views as 'VIEW COUNT'  from Videos''',connection)
com=pd.read_sql_query('''SELECT Comment_Text as 'COMMENT TEXT',Comment_Author as 'COMMENT AUTHOR' from Comments''',connection)
ply=pd.read_sql_query('''SELECT Title as 'PLAYLIST NAME',Channel_Name as 'CHANNEL NAME' , Video_Count as 'VIDEO COUNT' from Playlists''',connection)
cha = ch.drop_duplicates()


#"1.What are the names of all the videos and their corresponding channels?"
question1=pd.read_sql_query('''SELECT Channel_Name as "CHANNEL NAME",Title as "VIDEOS NAME" from Videos''',connection)
#"2.Which channels have the most number of videos and how many videos do they have?",
question2=pd.read_sql_query('''select Channel_Name as "CHANNEL NAME", count(*) as "NUMBER OF VIDEOS" from Videos GROUP BY Channel_Name ORDER BY count(*) desc''',connection)
#"3.What are the top 10 most viewed videos and their respective channels?"
question3=pd.read_sql_query('''SELECT Channel_Name as "CHANNEL NAME",Title as "VIDEO NAME",Views as "No.of VIEWS" from Videos ORDER BY Views desc LIMIT 10''',connection)
#"4.How many comments were made on each video, and what are their corresponding video names?"
question4=pd.read_sql_query('''SELECT Title as "VIDEOS NAME",Comments as "No.of COMMENTS" from Videos ORDER BY Comments DESC ''',connection)
#"5.Which videos have the highest number of likes, and what are their corresponding channel names?"
question5=pd.read_sql_query('''SELECT Channel_Name as "CHANNEL NAME",Title as "VIDEOS NAME",Likes as "No.of LIKES" from Videos ORDER BY Likes desc''',connection)
#"6.What is the total number of likes for each video and what are their corresponding video names?"
question6=pd.read_sql_query('''SELECT Title as "VIDEOS NAME", Channel_Name as "CHANNEL NAME",Likes as "No.of LIKES", DisLikes as "No.of DISLIKES"  from Videos ORDER BY Likes desc''',connection)
#"7.What is the total number of views for each channel, and what are their corresponding channel names?",
question7=pd.read_sql_query('''SELECT Channel_Name as "CHANNEL NAME",Views as "No.of VIEWS" from Channels ORDER BY Views desc''',connection)
#"8.What are the names of all the channels that have published videos in the year 2022?"
question8=pd.read_sql_query('''SELECT Channel_Name as "CHANNEL NAME",Title as "VIDEO NAME",Published_Date as "Published_Date" from Videos WHERE strftime('%Y',Published_Date) = '2022' ''',connection)
#"9.What is the average duration of all videos in each channel, and what are their corresponding channel names?"
question9=pd.read_sql_query('''SELECT Channel_Name as "CHANNEL NAME",Duration as "DURATION" from Videos''',connection)
question9["dur_alter"]=question9["DURATION"].apply(dur)
question9= question9.drop('DURATION', axis=1)
question9= question9.rename(columns={'dur_alter': 'DURATION in sec'})
q90 = question9.groupby('CHANNEL NAME').mean()
#"10.Which videos have the highest number of comments, and what are their corresponding channel names?"
question10=pd.read_sql_query('''select Channel_Name as "CHANNEL NAME",Title as "VIDEO NAME",Comments as "No.of COMMENTS " from Videos WHERE Comments is not null ORDER BY Comments desc''',connection)

def show_channel_table(unique_channel):
    channel_id = unique_channel
    df = pd.read_sql_query(f"SELECT * FROM Channels WHERE Channel_Id = '{channel_id}'", connection)
    st.dataframe(df)
    return df

def show_playlist_table(unique_channel):
    channel_id = unique_channel
    df1 = pd.read_sql_query(f"SELECT * FROM Playlists WHERE Channel_Id = '{channel_id}'", connection)
    st.dataframe(df1)
    return df1

def show_videos_table(unique_channel):
    channel_id = unique_channel
    df2 = pd.read_sql_query(f"SELECT * FROM Videos WHERE Channel_Id = '{channel_id}'", connection)
    st.dataframe(df2)
    return df2

def show_comments_table(unique_channel):
    channel_id = unique_channel
    df3 = pd.read_sql_query(f"SELECT * FROM Comments WHERE Channel_Id = '{channel_id}'", connection)
    st.dataframe(df3)
    return df3

#code for Streamlit Application

st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")

with st.sidebar:
  st.header("Skill Take Away")
  st.caption("Python Scripting")
  st.caption("Data Collection from YouTube")
  st.caption("Data Management Using SQLite3")
  st.caption("API Integration")
  selected = option_menu("MAIN MENU", ["HOME","VIEW", "QUERY"],
      icons=['house', 'search'], menu_icon="cast", default_index=0)

if selected == "HOME":
    st.title("Home Page")
    channel_id = st.text_input("Enter the Youtube Channel Id")
    if st.button(":green[Collect and store in SQL]"):
        ch_ids = []
        cursor = cur.execute("SELECT Channel_Id FROM Channels")
        for row in cursor:
            ch_ids.append(row[0])

        if channel_id in ch_ids:
            st.success("Channel Details Of The Given Channel Id Already Exists")
        else:
            insert = all_functions(channel_id)
            st.success(insert)
    with st.expander("CHANNELS"):
        st.write(cha)
    with st.expander("VIDEOS"):
        st.write(vid)
    with st.expander("PLAYLISTS"):
        st.write(ply)
    with st.expander("COMMENTS"):
        st.write(com)

elif selected == "VIEW":
    st.title("View Data")
    all_channels = []
    cursor = cur.execute("SELECT Channel_Name FROM Channels")
    for row in cursor:
        all_channels.append(row[0])

    unique_channel_name = st.selectbox("Select the channel", all_channels)
    unique_channel_1 = pd.read_sql_query(f"SELECT Channel_Id FROM Playlists WHERE Channel_Name = '{unique_channel_name}'", connection)
    unique_channel = unique_channel_1["Channel_Id"][0]

    show_table = st.radio("SELECT THE TABLE FOR VIEW", ("CHANNELS", "PLAYLISTS", "VIDEOS", "COMMENTS"))

    if show_table == "CHANNELS":
        show_channel_table(unique_channel)
    elif show_table == "PLAYLISTS":
        show_playlist_table(unique_channel)
    elif show_table == "VIDEOS":
        show_videos_table(unique_channel)
    elif show_table == "COMMENTS":
        show_comments_table(unique_channel)

elif selected == "QUERY":
    st.title("Query Data")
    question = st.sidebar.selectbox("Select Questions",
                                    ("1.What are the names of all the videos and their corresponding channels?",
                                     "2.Which channels have the most number of videos and how many videos do they have?",
                                     "3.What are the top 10 most viewed videos and their respective channels?",
                                     "4.How many comments were made on each video, and what are their corresponding video names?",
                                     "5.Which videos have the highest number of likes, and what are their corresponding channel names?",
                                     "6.What is the total number of likes for each video, and what are their corresponding video names?",
                                     "7.What is the total number of views for each channel, and what are their corresponding channel names?",
                                     "8.What are the names of all the channels that have published videos in the year 2022?",
                                     "9.What is the average duration of all videos in each channel, and what are their corresponding channel names?",
                                     "10.Which videos have the highest number of comments, and what are their corresponding channel names?"))

    if question == "1.What are the names of all the videos and their corresponding channels?":
        q1 = pd.DataFrame(question1)
        st.write(q1)
        q1_agg = q1.groupby("CHANNEL NAME").size().reset_index(name='TOTAL VIDEOS')
        fig = px.bar(q1_agg, x="CHANNEL NAME", y="TOTAL VIDEOS", title="Total Videos by Channel")
        st.plotly_chart(fig)
    elif question == "2.Which channels have the most number of videos and how many videos do they have?":
        q2 = pd.DataFrame(question2)
        st.write(q2)
        fig = px.bar(q2, x="CHANNEL NAME", y="NUMBER OF VIDEOS", title="Number of Videos by Channel")
        st.plotly_chart(fig)
    elif question == "3.What are the top 10 most viewed videos and their respective channels?":
        q3 = pd.DataFrame(question3)
        st.write(q3)
        fig = px.bar(q3, x="VIDEO NAME", y="No.of VIEWS", color="CHANNEL NAME", title="Top 10 Most Viewed Videos by Channel")
        st.plotly_chart(fig)
    elif question == "4.How many comments were made on each video, and what are their corresponding video names?":
        q4 = pd.DataFrame(question4)
        q4_sorted = q4.sort_values(by='No.of COMMENTS', ascending=False)
        q4_top3 = q4_sorted.head(3).reset_index(drop=True)
        st.write(q4)
        fig = px.bar(q4_top3, x="VIDEOS NAME", y="No.of COMMENTS",
                    title="Top 3 Videos with Highest Number of Comments")
        st.plotly_chart(fig)
    elif question == "5.Which videos have the highest number of likes, and what are their corresponding channel names?":
        q5 = pd.DataFrame(question5)
        q5_sorted = q5.sort_values(by='No.of LIKES', ascending=False)
        q5_top3 = q5_sorted.groupby('CHANNEL NAME').head(3).reset_index(drop=True)
        st.write(q5)
        fig = px.bar(q5_top3, x="VIDEOS NAME", y="No.of LIKES", color="CHANNEL NAME", title="Top 3 Videos with Highest Number of Likes by Channel")
        st.plotly_chart(fig)
    elif question == "6.What is the total number of likes for each video, and what are their corresponding video names?":
        q6 = pd.DataFrame(question6)
        q6_sorted = q6.sort_values(by='No.of LIKES', ascending=False)
        q6_top3 = q6_sorted.groupby('CHANNEL NAME').head(3).reset_index(drop=True)
        st.write(q6)
        fig = px.bar(q6_top3, x="VIDEOS NAME", y="No.of LIKES", color="CHANNEL NAME", title="Top 3 Videos with Highest Number of Likes by Channel")
        st.plotly_chart(fig)
    elif question == "7.What is the total number of views for each channel, and what are their corresponding channel names?":
        q7 = pd.DataFrame(question7)
        st.write(q7)
        fig = px.bar(q7, x="CHANNEL NAME", y="No.of VIEWS", title="Total Number of Views by Channel")
        st.plotly_chart(fig)
    elif question == "8.What are the names of all the channels that have published videos in the year 2022?":
        q8 = pd.DataFrame(question8)
        st.write(q8)
        fig = px.bar(q8, x="CHANNEL NAME", y="VIDEO NAME", title="Channels Published Videos in 2022")
        st.plotly_chart(fig)
    elif question == "9.What is the average duration of all videos in each channel, and what are their corresponding channel names?":
        q9 = pd.DataFrame(q90)
        st.write(q9)
        fig = px.bar(q9, x=q9.index, y="DURATION in sec", title="Average Video Duration by Channel")
        st.plotly_chart(fig)
    elif question == "10.Which videos have the highest number of comments, and what are their corresponding channel names?":
        q10 = pd.DataFrame(question10)
        q10_sorted = q10.sort_values(by='No.of COMMENTS ', ascending=False)
        q10_top3 = q10_sorted.groupby('CHANNEL NAME').head(3).reset_index(drop=True)
        st.write(q10)
        fig = px.bar(q10_top3, x="VIDEO NAME", y="No.of COMMENTS ", color="CHANNEL NAME", title="Top 3 Videos with Highest Number of Comments by Channel")
        st.plotly_chart(fig)