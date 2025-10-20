#!/usr/bin/env python3
"""
AnalyzeTube - Versione Unica
Applicazione Flask standalone in un unico file.
Estrae trascrizioni e commenti da video YouTube.

Uso:
    python3 analyzetube.py

Poi apri: http://localhost:5001
"""

from flask import Flask, request, jsonify
import yt_dlp
import re
import requests
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR

app = Flask(__name__)

# ============================================================================
# HTML/CSS/JS INCORPORATI
# ============================================================================

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

        label {
            display: block;
            margin-bottom: 10px;
            font-weight: 600;
            color: #555;
        }

        input[type="text"] {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            transition: border-color 0.3s;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }

        button {
            width: 100%;
            padding: 15px;
            margin-top: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }

        button:hover:not(:disabled) { transform: translateY(-2px); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }

        .loading { text-align: center; padding: 40px; }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .hidden { display: none !important; }

        .error {
            background: #fee;
            border: 2px solid #fcc;
            color: #c33;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        .results { animation: fadeIn 0.5s; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .video-info {
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }

        .video-info h2 { color: #333; margin-bottom: 15px; }
        .stats { display: flex; gap: 20px; flex-wrap: wrap; }

        .stats span {
            background: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            color: #666;
        }

        .chatgpt-section {
            margin-bottom: 30px;
            padding: 25px;
            background: linear-gradient(135deg, #10a37f 0%, #0d8a6a 100%);
            border-radius: 10px;
            color: white;
        }

        .chatgpt-section h3 { margin-bottom: 10px; }
        .instruction { margin-bottom: 15px; opacity: 0.95; }

        .prompt-box textarea {
            width: 100%;
            min-height: 200px;
            padding: 15px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            resize: vertical;
            background: rgba(255, 255, 255, 0.95);
            color: #333;
        }

        .copy-btn {
            margin-top: 10px;
            background: white;
            color: #10a37f;
            padding: 12px 20px;
            width: auto;
        }

        .chatgpt-link { margin-top: 15px; text-align: center; }

        .chatgpt-button {
            display: inline-block;
            padding: 12px 30px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: background 0.3s;
        }

        .chatgpt-button:hover { background: rgba(255, 255, 255, 0.3); }

        .details-section {
            margin-bottom: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }

        summary {
            padding: 15px 20px;
            background: #f8f9fa;
            cursor: pointer;
            font-weight: 600;
            color: #555;
            user-select: none;
        }

        summary:hover { background: #e9ecef; }

        .content-box {
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.6;
            color: #555;
            white-space: pre-wrap;
        }

        footer {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
        }

        @media (max-width: 600px) {
            header h1 { font-size: 2em; }
            main { padding: 20px 15px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎥 AnalyzeTube</h1>
            <p class="subtitle">Analisi automatica di video YouTube con ChatGPT</p>
        </header>

        <main>
            <div class="input-section">
                <label for="youtube-url">URL Video YouTube:</label>
                <input type="text" id="youtube-url" placeholder="https://www.youtube.com/watch?v=..." autocomplete="off">
                <button id="analyze-btn" onclick="analyzeVideo()">Analizza Video</button>
            </div>

            <div id="loading" class="loading hidden">
                <div class="spinner"></div>
                <p id="loading-text">Estrazione in corso...</p>
            </div>

            <div id="error" class="error hidden"></div>

            <div id="results" class="results hidden">
                <div class="video-info">
                    <h2 id="video-title"></h2>
                    <div class="stats">
                        <span id="transcript-length"></span>
                        <span id="comments-count"></span>
                    </div>
                </div>

                <div class="chatgpt-section">
                    <h3>🤖 Prompt per ChatGPT</h3>
                    <p class="instruction">Copia questo testo e incollalo in ChatGPT:</p>

                    <div class="prompt-box">
                        <textarea id="chatgpt-prompt" readonly></textarea>
                        <button class="copy-btn" onclick="copyPrompt()">📋 Copia Prompt</button>
                    </div>

                    <div class="chatgpt-link">
                        <a href="https://chat.openai.com" target="_blank" class="chatgpt-button">Apri ChatGPT →</a>
                    </div>
                </div>

                <details class="details-section">
                    <summary>📝 Trascrizione Completa</summary>
                    <div id="transcript-content" class="content-box"></div>
                </details>

                <details class="details-section">
                    <summary>💬 Commenti Estratti</summary>
                    <div id="comments-content" class="content-box"></div>
                </details>
            </div>
        </main>

        <footer>
            <p>Powered by yt-dlp + youtube-comment-downloader</p>
        </footer>
    </div>

    <script>
        async function analyzeVideo() {
            const urlInput = document.getElementById('youtube-url');
            const url = urlInput.value.trim();

            if (!url) {
                showError('Inserisci un URL di YouTube valido');
                return;
            }

            hideError();
            hideResults();
            showLoading('Estrazione trascrizione e commenti...');
            disableButton(true);

            try {
                const response = await fetch('/api/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Errore durante l\\'estrazione');
                }

                displayResults(data);

            } catch (error) {
                console.error('Errore:', error);
                showError(error.message);
            } finally {
                hideLoading();
                disableButton(false);
            }
        }

        function displayResults(data) {
            document.getElementById('video-title').textContent = data.title;
            document.getElementById('transcript-length').textContent = `📝 Trascrizione: ${data.transcript.length} caratteri`;
            document.getElementById('comments-count').textContent = `💬 Commenti estratti`;

            const prompt = generatePrompt(data);
            document.getElementById('chatgpt-prompt').value = prompt;
            document.getElementById('transcript-content').textContent = data.transcript;
            document.getElementById('comments-content').textContent = data.comments;

            document.getElementById('results').classList.remove('hidden');
            document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
        }

        function generatePrompt(data) {
            return `Analizza questo video YouTube e dimmi se ciò che viene detto nel video è confermato dai commenti degli utenti.

TITOLO VIDEO: ${data.title}

TRASCRIZIONE:
${data.transcript}

COMMENTI:
${data.comments}

---

Per favore, fornisci un'analisi breve che risponda a:
1. Qual è il tema principale del video?
2. I commenti degli utenti confermano o contraddicono ciò che viene detto nel video?
3. Ci sono discrepanze significative tra il contenuto del video e le reazioni degli utenti?
4. Qual è il sentiment generale dei commenti?

Limita la risposta a 200-300 parole.`;
        }

        function copyPrompt() {
            const promptText = document.getElementById('chatgpt-prompt');
            promptText.select();
            promptText.setSelectionRange(0, 99999);

            navigator.clipboard.writeText(promptText.value).then(() => {
                showCopySuccess();
            }).catch(() => {
                document.execCommand('copy');
                showCopySuccess();
            });
        }

        function showCopySuccess() {
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = '✓ Copiato!';
            btn.style.background = '#4caf50';

            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = '';
            }, 2000);
        }

        function showLoading(text) {
            document.getElementById('loading-text').textContent = text;
            document.getElementById('loading').classList.remove('hidden');
        }

        function hideLoading() {
            document.getElementById('loading').classList.add('hidden');
        }

        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = '❌ ' + message;
            errorDiv.classList.remove('hidden');
            errorDiv.scrollIntoView({ behavior: 'smooth' });
        }

        function hideError() {
            document.getElementById('error').classList.add('hidden');
        }

        function hideResults() {
            document.getElementById('results').classList.add('hidden');
        }

        function disableButton(disabled) {
            document.getElementById('analyze-btn').disabled = disabled;
        }

        document.getElementById('youtube-url').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                analyzeVideo();
            }
        });
    </script>
</body>
</html>'''

# ============================================================================
# FUNZIONI BACKEND
# ============================================================================

def extract_video_id(url):
    """Estrae l'ID del video dall'URL YouTube"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'^([a-zA-Z0-9_-]{11})$'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

def extract_video_info(video_id):
    """Estrae informazioni video e trascrizione usando yt-dlp"""
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'it'],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            title = info.get('title', 'Titolo non disponibile')
            transcript = extract_subtitles(info)

            return {
                'title': title,
                'transcript': transcript
            }

    except Exception as e:
        return {
            'title': 'Errore',
            'transcript': f"Impossibile estrarre informazioni: {str(e)}"
        }

def extract_subtitles(info):
    """Estrae i sottotitoli dal dizionario info di yt-dlp"""
    try:
        subtitles = info.get('subtitles', {})
        auto_subs = info.get('automatic_captions', {})

        # Prova inglese, poi italiano
        for lang in ['en', 'it']:
            if lang in subtitles and subtitles[lang]:
                result = download_subtitle_content(subtitles[lang][0].get('url'))
                if result and not result.startswith('Errore'):
                    return result

        for lang in ['en', 'it']:
            if lang in auto_subs and auto_subs[lang]:
                result = download_subtitle_content(auto_subs[lang][0].get('url'))
                if result and not result.startswith('Errore'):
                    return result

        # Prova qualsiasi lingua
        if auto_subs:
            first_lang = list(auto_subs.keys())[0]
            result = download_subtitle_content(auto_subs[first_lang][0].get('url'))
            if result and not result.startswith('Errore'):
                return result

        return "⚠️ Trascrizione non disponibile per questo video"

    except Exception as e:
        return f"Errore estrazione sottotitoli: {str(e)}"

def download_subtitle_content(url):
    """Scarica e processa il contenuto dei sottotitoli"""
    try:
        import json

        response = requests.get(url, timeout=10)

        # Formato JSON (moderno)
        try:
            data = json.loads(response.text)

            texts = []
            for event in data.get('events', []):
                if 'segs' in event:
                    for seg in event['segs']:
                        if 'utf8' in seg:
                            texts.append(seg['utf8'].strip())

            if texts:
                return ' '.join(texts)

        except (json.JSONDecodeError, KeyError):
            pass

        return None

    except Exception as e:
        return f"Errore download sottotitoli: {str(e)}"

def extract_comments(video_id):
    """Estrae i commenti del video usando youtube-comment-downloader"""
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        downloader = YoutubeCommentDownloader()
        comments = downloader.get_comments_from_url(url, sort_by=SORT_BY_POPULAR)

        comments_list = []
        for comment in comments:
            comments_list.append(comment)
            if len(comments_list) >= 50:
                break

        if comments_list:
            comments_text = ""
            for i, comment in enumerate(comments_list, 1):
                author = comment.get('author', 'Utente')
                text = comment.get('text', '')
                votes = comment.get('votes', '0')

                try:
                    votes_int = int(str(votes).replace(',', '').replace('.', ''))
                except:
                    votes_int = 0

                if text and len(text) > 10:
                    comments_text += f"{i}. {author}"
                    if votes_int > 0:
                        comments_text += f" [{votes} likes]"
                    comments_text += f"\n{text}\n\n"

            return comments_text if comments_text else "Commenti non disponibili"
        else:
            return "Nessun commento disponibile"

    except Exception as e:
        return f"Errore estrazione commenti: {str(e)}"

# ============================================================================
# ROUTES FLASK
# ============================================================================

@app.route('/')
def index():
    """Serve la pagina HTML"""
    return HTML_TEMPLATE

@app.route('/api/extract', methods=['POST'])
def extract_video_data():
    """API per estrarre trascrizione e commenti"""
    data = request.get_json()
    video_url = data.get('url', '')

    video_id = extract_video_id(video_url)
    if not video_id:
        return jsonify({'error': 'URL YouTube non valido'}), 400

    try:
        video_info = extract_video_info(video_id)
        comments = extract_comments(video_id)

        return jsonify({
            'success': True,
            'title': video_info['title'],
            'transcript': video_info['transcript'],
            'comments': comments,
            'video_id': video_id
        })

    except Exception as e:
        return jsonify({
            'error': f'Errore durante l\'estrazione: {str(e)}'
        }), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("AnalyzeTube - Versione Unica")
    print("=" * 60)
    print("\n🚀 Server avviato su: http://localhost:5001")
    print("\n📝 Dipendenze richieste:")
    print("   - yt-dlp")
    print("   - youtube-comment-downloader")
    print("   - Flask")
    print("   - requests")
    print("\n💡 Per installare: pip install flask yt-dlp youtube-comment-downloader requests")
    print("\n" + "=" * 60 + "\n")

    app.run(debug=True, port=5002)
