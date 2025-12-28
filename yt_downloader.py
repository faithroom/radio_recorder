import sys
import time
import subprocess
from datetime import datetime, timedelta
import radio_recorder
import config


# Youtube download
def download(filename, url):
    cmd = f'yt-dlp -x --audio-format mp3 -o {filename} {url}'
    process = subprocess.Popen(cmd.split(' '))

    print('downloading...')

    start_time = time.time()
    while (True):
        if process.poll() is not None:
            break
        time.sleep(1)
        if time.time() - start_time > 600:  # 10分 timeout
            print('timeout')
            process.terminate()
            return False

    process = None
    print('done')
    return True


# Youtube download
def yt_download(title, url):
    filename = f'{config.RECORD_FOLDER}/{title}_{datetime.now().strftime("%Y%m%d")}.mp3'
    download(filename, url)
    radio_recorder.upload(filename)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        title = sys.argv[1]
        url = sys.argv[2]
        yt_download(title, url)
    else:
        print('Usage: python yt_download.py [title] [url]')



