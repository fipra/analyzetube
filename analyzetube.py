#!/usr/bin/env python3
"""
AnalyzeTube - Versione universale
Applicazione Flask standalone in un unico file.
Estrae trascrizioni e commenti da video YouTube.
Funziona anche su hosting come Render, senza cookie.
"""

from flask import Flask, request, jsonify
import yt_dlp
import re
import requests
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
import os

app = Flask(__name__)

# =====================================================================
# HTML INTERFACCIA (ridotto per chiarezza — puoi tenere il tuo completo)
# =====================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head><meta charset="UTF-8"><title>AnalyzeTube</title></head>
<body style="font-family:sans-serif;margin:40px;">
<h1>🎥 AnalyzeTube</h1>
<p>Analisi automatica video YouTube</p>
<form onsubmit="event.preventDefault(); analyze();">
<input id='url' style='width:400px' placeholder='https://www.youtube.com/watch?v=...'>
<button>Analizza</button>
</form>
<pre id='out'></pre>
<script>
async function analyze(){
 const url=document.getElementById('url').value.trim();
 if(!url)return;
 document.getElementById('out').textContent='⏳ Analisi in corso...';
 const r=await fetch('/api/extract',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});
 const d=await r.json();
 document.getElementById('out').textContent=JSON.stringify(d,null,2);
}
</script>
</body></html>
"""

# =====================================================================
# FUNZIONI BACKEND
# =====================================================================

def extract_video_id(url):
    """Estrae l'ID del video dall'URL YouTube"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_video_info(video_id):
    """Estrae info e trascrizione, con fallback universale"""
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'it'],
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_skip': ['configs', 'js', 'player_response']
            }
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
            # Retry con URL "embed"
            try:
                embed_url = f"https://www.youtube.com/embed/{video_id}"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(embed_url, download=False)
                    title = info.get('title', 'Titolo non disponibile')
                    transcript = extract_subtitles(info)
                    return {'title': title, 'transcript': transcript}
            except Exception:
                return {
                    'title': 'Video con restrizioni',
                    'transcript': "⚠️ YouTube richiede autenticazione per questo video. "
                                  "Prova con un altro video pubblico."
                }
        return {'title': 'Errore', 'transcript': f"Impossibile estrarre informazioni: {str(e)}"}


def extract_subtitles(info):
    """Estrae sottotitoli dai dati yt-dlp"""
    try:
        subtitles = info.get('subtitles', {})
        auto_subs = info.get('automatic_captions', {})
        for lang in ['it', 'en']:
            for source in (subtitles, auto_subs):
                if lang in source and source[lang]:
                    url = source[lang][0].get('url')
                    text = download_subtitle_content(url)
                    if text:
                        return text
        # fallback qualsiasi lingua
        if auto_subs:
            first_lang = list(auto_subs.keys())[0]
            return download_subtitle_content(auto_subs[first_lang][0].get('url'))
        return "⚠️ Trascrizione non disponibile per questo video"
    except Exception as e:
        return f"Errore estrazione sottotitoli: {e}"


def download_subtitle_content(url):
    """Scarica sottotitoli JSON"""
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        texts = []
        for event in data.get('events', []):
            if 'segs' in event:
                for seg in event['segs']:
                    t = seg.get('utf8', '').strip()
                    if t:
                        texts.append(t)
        return ' '.join(texts) if texts else None
    except Exception:
        return None


def extract_comments(video_id):
    """Estrae fino a 50 commenti"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        downloader = YoutubeCommentDownloader()
        comments = downloader.get_comments_from_url(url, sort_by=SORT_BY_POPULAR)
        out = []
        for i, c in enumerate(comments, 1):
            author = c.get('author', 'Utente')
            text = c.get('text', '')
            votes = c.get('votes', '0')
            if len(text) > 10:
                out.append(f"{i}. {author} [{votes} likes]\n{text}\n")
            if len(out) >= 50:
                break
        return "\n".join(out) if out else "Nessun commento trovato"
    except Exception as e:
        return f"Errore estrazione commenti: {e}"

# =====================================================================
# ROUTES FLASK
# =====================================================================

@app.route('/')
def index():
    return HTML_TEMPLATE


@app.route('/api/extract', methods=['POST'])
def extract_video_data():
    data = request.get_json()
    video_url = data.get('url', '')
    video_id = extract_video_id(video_url)
    if not video_id:
        return jsonify({'error': 'URL YouTube non valido'}), 400

    info = extract_video_info(video_id)
    comments = extract_comments(video_id)

    return jsonify({
        'success': True,
        'title': info['title'],
        'transcript': info['transcript'],
        'comments': comments,
        'video_id': video_id
    })

# =====================================================================
# MAIN
# =====================================================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port)
