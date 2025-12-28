from flask import Flask, request, render_template, redirect, url_for
import os
import threading
import config

APP_ROOT = os.path.dirname(__file__)

app = Flask(__name__)
yt_callback = None


def set_callback_yt_request(callback):
    global yt_callback
    yt_callback = callback


@app.route('/', methods=['GET', 'POST'])
def index():
    global yt_callback
    message = ''
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        url = request.form.get('url', '').strip()
        if title and url and yt_callback:
            yt_callback(title, url)
            message = f'Request submitted for "{title}".'

    return render_template('index.html', default_title='sunday', message=message)


def start_server_thread():
    # Start web server in a background thread
    web_thread = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=config.WEB_PORT, debug=False), daemon=True)
    web_thread.start()
    print(f'Web server started on http://127.0.0.1:{config.WEB_PORT}', flush=True)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=config.WEB_PORT, debug=True)
