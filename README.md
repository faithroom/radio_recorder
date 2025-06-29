# radio_recorder

## 概要

作成したスケジュールに基づいて radiko 放送をダウンロードし、mp3 で Google Drive に保存します。(個人用)

## 事前準備

### python

python の実行環境を準備し、必要なモジュールをインストールしてください。
```
pip install -r requirements.txt
```

### Google Drive アクセス設定

Google アカウントを使用して Google drive 認証用の以下 2 ファイルを作成し、radio_recorder フォルダに置いてください。
詳しくは PyDrive2 や Google のアプリ認証についてのページを参考にしてください。

* client_secret.json
* saved_credentials.json

### 録音スケジュール編集

schedule_sample.csv をカスタマイズして録音したい時間と station を指定します。利用できる放送局はご利用の地域によって変わります。

## アプリの実行

以下の機能があります

### スケジュールファイルに基づいた自動録音

アプリを起動しておけばスケジュールに従って自動で録音されます。
```
python radio_recorder.py <schedule file>
```

### タイムフリー単発録音
現在視聴可能な番組を直接指定して録音します。
```
python radio_recorder.py <title> <date> <duration[min]> <station_id>

ex) python radio_recorder.py test 202503151100 30 TBS
```

### 番組表表示
指定した日付の番組情報を表示します。サンプルは東京の設定なので、利用する地域に応じて radio_program.py を編集してください。

```
python radio_program.py <date> [station_id]

ex) python radio_program.py 20250315 TBS
```

### 参考: 東京向け station_id (初期実装)

| station_id     | 局               |
| ---            | ---              |
| TBS            | TBSラジオ        |
| QRR            | 文化放送         |
| LFR            | ニッポン放送     |
| RN1            | ラジオNIKKEI第一 |
| RN2            | ラジオNIKKEI第二 |
| INT            | InterFM897       |
| FMT            | TOKYO FM         |
| FMJ            | J-WAVE           |
| JORF           | ラジオ日本       |
| bayfm78        | bayfm78          |
| NACK5          | NACK5            |
| YFM            | FMヨコハマ       |
| HOUSOU-DAIGAKU | 放送大学         |
| JOAK           | NHKラジオ第1     |
| JOAB           | NHKラジオ第2     |
| JPAK-FM        | NHK-FM           |
