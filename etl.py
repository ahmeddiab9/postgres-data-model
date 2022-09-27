import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
     """_summary_
        process_song_file 
        1 - extract Song Information (song_id,title,artist_id,year,duration) To Load to Song Table
        2 - extract artist Information (artist_id,artist_name,artist_location,artist_latitude,artist_longitude)
            To Load to artist Table

        Args:
            cur (object): psycopg2.cursor Object to execute Query
            filepath (String): Songs Dataset File Path
    """
    # open song file
    df = pd.read_json(filepath, lines=True)

    # insert song record
    for index,row in df.iterrows():
         song_data = (row.song_id, row.title,row.artist_id, row.year, row.duration)
    cur.execute(song_table_insert, song_data)

    # insert artist record
    artist_data = (row.artist_id, row.artist_name, row.artist_location, row.artist_latitude, row.artist_longitude)
    cur.execute(artist_table_insert, artist_data)


def process_log_file(cur, filepath):
     """_summary_
        1 - Convert timestamp column to datetime
        2 -Extract time information (timestamp,hour, day, week,month,year, day name) to load to time table
        3 - extract user Information ('userId','firstName','lastName','gender','level')
            To Load to User Table
        Args:
            cur (object): psycopg2.cursor Object to execute Query
            filepath (String): Songs Dataset File Path
    """
    # open log file
    df =pd.read_json(filepath,lines=True)

    # filter by NextSong action
    df =df[df['page'] == 'NextSong']

    # convert timestamp column to datetime
    t =pd.to_datetime(df['ts'],unit='ms')

    # insert time data records
    time_data = []
    for i in t:
        time_data.append([i, i.hour, i.day, i.week, i.month, i.year, i.day_name()])
    column_labels = ('timestamp', 'hour', 'day', 'week', 'month', 'year', 'weekday')
    time_df =pd.DataFrame(data=time_data,columns=column_labels)

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df =df[['userId','firstName','lastName','gender','level']]

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    for index, row in df.iterrows():

        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()

        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        songplay_data = (pd.to_datetime(row.ts,unit='ms'), row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent)
        cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
      """_summary_
        get all files matching extension from directory
        get total number of files found
        iterate over files and process
        Args:
            cur (object): psycopg2.cursor Object to execute Query
            conn (object): psycopg2.cursor Object Connection To database
            filepath (String): Songs Dataset File Path
            func (function): function to each file
      """
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root, '*.json'))
        for f in files:
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()
