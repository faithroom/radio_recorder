import pandas as pd
import schedule
import time
import re
import os
import sys
import multiprocessing
from datetime import datetime, timedelta
from pathlib import Path
import radio_downloader
import google_drive as gdrive
from io import StringIO
import threading


RECORD_FOLDER = 'record'          # ローカル保存フォルダ
GDRIVE_FOLDER = 'DriveSyncFiles'  # Google Driver 保存フォルダ

DAYS_OF_WEEK = {
    "Mon": 'monday',
    "Tue": 'tuesday',
    "Wed": 'wednesday',
    "Thu": 'thursday',
    "Fri": 'friday',
    "Sat": 'saturday',
    "Sun": 'sunday',
}


# 指定局・時間の録音をし、ファイルをアップロードする
def record(title, station, duration, date_str = ''):
    try:
        if date_str == '': # 現在の放送
            filename = f'{RECORD_FOLDER}/{title}_{datetime.now().strftime("%Y%m%d")}.mp3'
            radio_downloader.record(filename, station, duration)

        else: # timefree
            start_time_obj = datetime.strptime(date_str, "%Y%m%d%H%M")
            end_time_obj = start_time_obj + timedelta(seconds = duration)
            start_time = start_time_obj.strftime("%Y%m%d%H%M%S")
            end_time = end_time_obj.strftime("%Y%m%d%H%M%S")
            filename = f'{RECORD_FOLDER}/{title}_{start_time_obj.strftime("%Y%m%d")}.mp3'
            radio_downloader.record(filename, station, duration, start_time, end_time)
    except Exception as e:
        print('Record error: ', e)
        return
    
    upload(filename)


# 録音開始トリガ
def start_recording_process(title, station, duration):
    print(f"Start scheduled recording: {title} {station} for {duration} seconds.")
    p = multiprocessing.Process(target=record, args=(title, station, duration))
    p.start()
    # p.join()


# スケジュールを設定して実行
def schedule_recordings(schedule_file):
    daily_task() # 起動時に一回実行する
    df = pd.read_csv(schedule_file)

    for _, row in df.iterrows():
        title = row["title"].strip()
        day_of_week = row["day_of_week"].strip()
        start_time = row["start_time"].strip()
        duration = row["duration"]
        station = row["station"].strip()

        schedule_func = getattr(schedule.every(), DAYS_OF_WEEK[day_of_week])
        job = schedule_func.at(start_time).do(start_recording_process, title, station, duration * 60)

        print(f'{title:12} {day_of_week:3} {start_time} {duration:3} {station}')


    # 定期的に古いファイルを削除
    schedule.every().day.at("04:45").do(daily_task)

    print('-------------------------------', flush=True)

    while True:
        # print(datetime.now())
        schedule.run_pending()
        time.sleep(1)


# Google drive にファイルをアップロードしてローカルファイルは削除
upload_lock = threading.Lock()
def upload(filename):
    with upload_lock:
        print(f'Uploading {filename}...')
        for i in range(3):
            try:
                g = gdrive.GoogleDriveControl()
                gdrive_folder_id = g.search_folder(GDRIVE_FOLDER)
                print(f'GDrive folder ID:{gdrive_folder_id}')
                url = g.upload(filename, gdrive_folder_id)
                print('Upload done. Removing local file')
                os.remove(filename)
                break

            except Exception as e:
                print('Upload error: ', e)
                print('Retry upload...')
                time.sleep(60 * i)

    print('', flush=True)


def daily_task():
    # 録音フォルダに upload 失敗したファイルが残っていたら upload しておく
    for filename in Path(RECORD_FOLDER).rglob("*.mp3"):
        upload(filename)

    # Google drive に古いファイルがあったら削除
    try:
        print("Remove old files")
        g = gdrive.GoogleDriveControl()
        gdrive_folder_id = g.search_folder(GDRIVE_FOLDER)
        list = g.get_file_list(gdrive_folder_id)

        for file_name in list:
            match = re.search(r"\d{8}", file_name)  # 8桁の数字（yyyymmdd）を抽出
            if match:
                yyyymmdd_str = match.group()
                date_obj = datetime.strptime(yyyymmdd_str, "%Y%m%d")
                if date_obj < datetime.today() - timedelta(days = 30):
                    print("Remove ", file_name)
                    g.delete(file_name, gdrive_folder_id)

    except Exception as e:
        print('Remove error', e)


if __name__ == '__main__':
    if len(sys.argv) == 2:    # Scheduler 録音
        schedule_recordings(sys.argv[1])

    elif len(sys.argv) == 5:  # Time free 単発録音
        title = sys.argv[1]               # title
        date_str = sys.argv[2]            # ex) '202503151100'Accumulated
        duration = int(sys.argv[3]) * 60  # ex) 30
        station = sys.argv[4]             # station
        record(title, station, duration, date_str)

    else:
        print("Usage:")
        print("[Scheduled recording]")
        print("python radio_recorder.py <schedule file>")
        print("ex) python radio_recorder.py schedule.csv")
        print("")
        print("[Timefree recording]")
        print("python radio_recorder.py <title> <date> <duration(min)> <station_id>")
        print("ex) python radio_recorder.py test 202503151100 30 TBS")
