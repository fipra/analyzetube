#!/usr/bin/env python3
"""
AnalyzeTube - Versione completa e universale
Compatibile con Render e altri hosting.
Gestisce automaticamente cookie, fallback e messaggi d’errore.
"""

from flask import Flask, request, jsonify
import yt_dlp
import re
import requests
import os
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR

app = Flask(__name__)

# =====================================================================
# HTML + CSS + JS ORIGINALE
# =====================================================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AnalyzeTube - Analisi Video YouTube</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .subtitle { font-size: 1.1em; opacity: 0.9; }
        main { padding: 40px 30px; }
        .input-section { margin-bottom: 30px; }
        label { display: block; margin-bottom: 10px; font-weight: 600; color: #555; }
        input[type="text"] {
            width: 100%; padding: 15px; font-size: 16px;
            border: 2px solid #e0e0e0; border-radius: 10px; transition: border-color 0.3s;
        }
        input[type="text"]:focus { outline: none; border-color: #667eea; }
        button {
            width: 100%; padding: 15px; margin-top: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 10px;
            font-size: 16px; font-weight: 600; cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover:not(:disabled) { transform: translateY(-2px); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .loading { text-align: center; padding: 40px; }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px; height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .hidden { display: none !important; }
        .error {
            background: #fee; border: 2px solid #fcc;
            color: #c33; padding: 15px;
            border-radius: 10px; margin-bottom: 20px;
        }
        .results { animation: fadeIn 0.5s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .video-info { margin-bottom: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px; }
        .video-info h2 { color: #333; margin-bottom: 15px; }
        .stats { display: flex; gap: 20px; flex-wrap: wrap; }
        .stats span {
            background: white; padding: 8px 15px;
            border-radius: 20px; font-size: 0.9em; color: #666;
        }
        footer { text-align: center; padding: 20px; background: #f8f9fa; color: #666; }
    </style>
</head>
<body>
<div class="container">
<header><h1>🎥 AnalyzeTube</h1><p class="subtitle">Analisi automatica di video YouTube</p></header>
<main>
<div class="input-section">
<label for="youtube-url">URL Video YouTube:</label>
<input type="text" id="youtube-url" placeholder="https://www.youtube.com/watch?v=..." autocomplete="off">
<button id="analyze-btn" onclick="analyzeVideo()">Analizza Video</button>
</div>
<div id="loading" class="loading hidden"><div class="spinner"></div><p id="loading-text">Estrazione in corso...</p></div>
<div id="error" class="error hidden"></div>
<div id="results" class="results hidden">
<div class="video-info"><h2 id="video-title"></h2>
<div class="stats">
<span id="transcript-length"></span><span id="comments-count"></span>
</div></div>
<details><summary>📝 Trascrizione</summary><pre id="transcript-content"></pre></details>
<details><summary>💬 Commenti</summary><pre id="comments-content"></pre></details>
</div></main>
<footer><p>Powered by yt-dlp + youtube-comment-downloader</p></footer>
</div>
<script>
async function analyzeVideo(){
 const url=document.getElementById('youtube-url').value.trim();
 if(!url)return showError('Inserisci un URL valido');
 hideError(); hideResults(); showLoading('Estrazione...');
 const r=await fetch('/api/extract',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});
 const d=await r.json(); hideLoading();
 if(d.error)return showError(d.error);
 document.getElementById('video-title').textContent=d.title;
 document.getElementById('transcript-length').textContent=`📝 ${d.transcript.length} caratteri`;
 document.getElementById('comments-count').textContent=`💬 Commenti estratti`;
 document.getElementById('transcript-content').textContent=d.transcript;
 document.getElementById('comments-content').textContent=d.comments;
 document.getElementById('results').classList.remove('hidden');
}
function showError(m){const e=document.getElementById('error');e.textContent='❌ '+m;e.classList.remove('hidden');}
function hideError(){document.getElementById('error').classList.add('hidden');}
function hideResults(){document.getElementById('results').classList.add('hidden');}
function showLoading(t){document.getElementById('loading-text').textContent=t;document.getElementById('loading').classList.remove('hidden');}
function hideLoading(){document.getElementById('loading').classList.add('hidden');}
</script>
</body></html>'''

# =====================================================================
# BACKEND
# =====================================================================

def extract_video_id(url):
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m: return m.group(1)
    return None


def extract_video_info(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    cookies_path = "cookies.txt" if os.path.exists("cookies.txt") else None

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'it'],
        'quiet': True,
        'no_warnings': True,
        'cookies': cookies_path,
        'extractor_args': {
            'youtube': {'player_skip': ['configs', 'js', 'player_response']}
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Titolo non disponibile')
            transcript = extract_subtitles(info)
            return {'title': title, 'transcript': transcript}
    except Exception as e:
        if "Sign in to confirm" in str(e):
            try:
                embed_url = f"https://www.youtube.com/embed/{video_id}"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(embed_url, download=False)
                    title = info.get('title', 'Titolo non disponibile')
                    transcript = extract_subtitles(info)
                    return {'title': title, 'transcript': transcript}
            except Exception:
                msg = "⚠️ YouTube richiede autenticazione per questo video."
                return {'title': 'Video con restrizioni', 'transcript': msg}
        return {'title': 'Errore', 'transcript': f"Impossibile estrarre informazioni: {e}"}


def extract_subtitles(info):
    try:
        subtitles = info.get('subtitles', {})
        auto_subs = info.get('automatic_captions', {})
        for lang in ['it', 'en']:
            for source in (subtitles, auto_subs):
                if lang in source and source[lang]:
                    url = source[lang][0]['url']
                    text = download_subtitle_content(url)
                    if text: return text
        if auto_subs:
            first = list(auto_subs.keys())[0]
            return download_subtitle_content(auto_subs[first][0]['url'])
        return "⚠️ Trascrizione non disponibile"
    except Exception as e:
        return f"Errore estrazione sottotitoli: {e}"


def download_subtitle_content(url):
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        texts = []
        for event in data.get('events', []):
            if 'segs' in event:
                for seg in event['segs']:
                    t = seg.get('utf8', '').strip()
                    if t: texts.append(t)
        return ' '.join(texts)
    except Exception:
        return None


def extract_comments(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        d = YoutubeCommentDownloader()
        comments = d.get_comments_from_url(url, sort_by=SORT_BY_POPULAR)
        out = []
        for i, c in enumerate(comments, 1):
            a = c.get('author', 'Utente')
            t = c.get('text', '')
            v = c.get('votes', '0')
            if len(t) > 10:
                out.append(f"{i}. {a} [{v} likes]\\n{t}\\n")
            if len(out) >= 50: break
        return "\n".join(out) if out else "Nessun commento trovato"
    except Exception as e:
        return f"Errore estrazione commenti: {e}"

# =====================================================================
# FLASK ROUTES
# =====================================================================

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/extract', methods=['POST'])
def api_extract():
    data = request.get_json()
    url = data.get('url', '')
    vid = extract_video_id(url)
    if not vid:
        return jsonify({'error': 'URL YouTube non valido'}), 400
    info = extract_video_info(vid)
    comments = extract_comments(vid)
    return jsonify({
        'title': info['title'],
        'transcript': info['transcript'],
        'comments': comments
    })

# =====================================================================
# MAIN
# =====================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port)
