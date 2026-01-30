
import time
import base64
import requests
import subprocess
import os
import uuid
from lxml import etree

def auth1(url):
    authkey = b'bcd151073c03b352e1ef2fd66c32209da9ca0afa'
    header = {
        'User-Agent': 'curl/7.52.1',
        'Accept': '*/*',
        'x-radiko-user': 'johndoe',
        'x-radiko-app': 'pc_html5',
        'x-radiko-app-version': '0.0.1',
        'x-radiko-device': 'pi'
    }
    response = requests.get('https://radiko.jp/v2/api/auth1', headers=header)

    length = int(response.headers['X-Radiko-KeyLength'])
    offset = int(response.headers['X-Radiko-KeyOffset'])
    authtoken = response.headers['X-Radiko-AUTHTOKEN']
    partialkey = base64.b64encode(authkey[offset: offset + length])

    return authtoken, partialkey


def auth2(url, authtoken, partialkey):
    header = {
        'User-Agent': 'curl/7.52.1',
        'Accept': '*/*',
        'x-radiko-user': 'johndoe',
        'X-RADIKO-AUTHTOKEN': authtoken,
        'x-radiko-partialkey': partialkey,
        'x-radiko-device': 'pi'
    }
    response = requests.get('https://radiko.jp/v2/api/auth2', headers=header)
    return (response.status_code == 200)


def download(url, authtoken, output_file, duration):
    """
    radikoストリーミングをダウンロード
    v3 API対応版（2026年仕様変更後）

    ffmpegが新しいradikoサーバーと互換性がないため、
    Pythonで直接HLSセグメントをダウンロードして結合する
    """
    header = {
        'X-Radiko-AuthToken': authtoken
    }
    try:
        # M3U8マスタープレイリストからストリーミングURLを取得
        response = requests.get(url, headers=header, timeout=10)
        response.raise_for_status()

        lines = response.content.decode().splitlines()
        streaming_url = None
        for line in lines:
            if line and not line.startswith('#'):
                streaming_url = line
                break

        if not streaming_url:
            raise Exception("Streaming URL not found in master playlist")
        # print(f'Streaming URL: {streaming_url}')

        # 出力ファイルを開く
        temp_file = output_file + '.tmp'
        with open(temp_file, 'wb') as outf:
            start_time = time.time()
            downloaded_segments = set()

            # print(f'Starting download (duration: {duration}s)...')
            while True:
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    break

                # 現在のチャンクリストを取得
                try:
                    resp = requests.get(streaming_url, headers=header, timeout=10)
                    resp.raise_for_status()
                except Exception as e:
                    print(f'Warning: Failed to get chunklist: {e}')
                    time.sleep(1)
                    continue

                # セグメントURLを抽出
                segment_lines = resp.text.splitlines()
                segment_urls = [l for l in segment_lines if l and not l.startswith('#')]

                # 新しいセグメントをダウンロード
                for segment_url in segment_urls:
                    if segment_url in downloaded_segments:
                        continue

                    try:
                        seg_resp = requests.get(segment_url, headers=header, timeout=10)
                        seg_resp.raise_for_status()
                        outf.write(seg_resp.content)
                        outf.flush()
                        downloaded_segments.add(segment_url)
                        # print(f'.', end='', flush=True)
                    except Exception as e:
                        print(f'\nWarning: Failed to download segment {segment_url}: {e}')

                # HLSは通常5秒ごとに更新されるので、少し待機
                time.sleep(2)

            print(f'\nDownload completed: {len(downloaded_segments)} segments')
        
        # ffmpegで再パッケージ
        print('Repackaging file for compatibility...')        
        try:
            # 拡張子に応じて適切な形式に変換
            # .mp3の場合はMP3に再エンコード、それ以外（.aac, .m4aなど）はコピー
            if output_file.lower().endswith('.mp3'):
                # MP3形式に変換（再エンコードが必要）
                cmd = [
                    'ffmpeg',
                    '-i', temp_file,
                    '-c:a', 'libmp3lame',  # MP3エンコーダー
                    '-b:a', '128k',  # ビットレート
                    '-y',
                    '-loglevel', 'error',
                    output_file
                ]
            else:
                cmd = [
                    'ffmpeg',
                    '-i', temp_file,
                    '-c', 'copy',
                    '-y',
                    '-loglevel', 'error',
                    output_file
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            os.remove(temp_file)
            if result.returncode == 0:
                return True
            print(f'Warning: Repackaging failed: {result.stderr}')

        except Exception as e:
            print(f'Warning: Repackaging error: {e}')
            os.remove(temp_file)

    except Exception as e:
        print(f'Download error: {e}')
        raise
    return False


def get_streaming_url_v3(station, authtoken):
    """
    v3 APIを使用してストリーミングURLを取得
    2026年のAPI仕様変更に対応

    Args:
        station: 放送局ID（例: TBS）
        authtoken: 認証トークン

    Returns:
        str: プレイリストURL
    """
    # v3 APIでストリーミングエンドポイントを取得
    stream_xml_url = f'https://radiko.jp/v3/station/stream/pc_html5/{station}.xml'

    try:
        response = requests.get(stream_xml_url, timeout=10)
        response.raise_for_status()

        # XMLをパース
        root = etree.fromstring(response.content)

        # timefree="0"（ライブストリーミング）のURLを取得
        urls = root.findall('.//url[@timefree="0"]')
        if not urls:
            raise Exception("Live streaming URL not found in XML")

        playlist_create_url = urls[0].find('playlist_create_url')
        if playlist_create_url is None:
            raise Exception("playlist_create_url not found in XML")

        base_url = playlist_create_url.text

        # ランダムなlsid（Live Stream ID）を生成
        lsid = uuid.uuid4().hex

        # プレイリストURLを構築
        # パラメータ: station_id, l (length), lsid, type (b=baseband)
        playlist_url = f"{base_url}?station_id={station}&l=15&lsid={lsid}&type=b"

        return playlist_url

    except Exception as e:
        print(f'Error getting streaming URL: {e}')
        raise


def record(filename, station, duration, start_time = '', end_time = ''):
    # ライブストリーミング
    if start_time == '':
        print(f'Record start: station={station} duration={duration}s filename={filename}')

        try:
            # ダミーURL（auth用）
            dummy_url = f'http://c-radiko.smartstream.ne.jp/{station}/_definst_/simul-stream.stream/playlist.m3u8'
            authtoken, partialkey = auth1(dummy_url)
        except Exception as e:
            print('Record error (auth1): ', e)
            raise

        if not auth2(dummy_url, authtoken, partialkey):
            print('Auth2 failed, aborting record')
            return

        try:
            # v3 APIでストリーミングURLを取得
            url = get_streaming_url_v3(station, authtoken)
            print(f'Playlist URL: {url}')
        except Exception as e:
            print('Record error (get_streaming_url): ', e)
            raise

        try:
            # Pythonで直接ダウンロード（ffmpegを使わない）
            download(url, authtoken, filename, duration)
        except Exception as e:
            print('Record error (download): ', e)
            raise

        print('Record completed')

    # タイムフリー
    else:
        # TODO: タイムフリーのv3 API対応が必要
        print('Timefree recording is not yet supported with v3 API')
        raise NotImplementedError('Timefree recording needs v3 API implementation')
