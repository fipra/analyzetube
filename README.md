# AnalyzeTube - Versione Unica

**Applicazione Flask standalone in un singolo file Python.**

Tutto incluso: HTML, CSS, JavaScript e backend Python in un unico file da ~500 righe.

## Caratteristiche

✅ **Un solo file** - `analyzetube.py` contiene tutto
✅ **Nessuna configurazione** - Niente cartelle templates/static
✅ **Facile da condividere** - Basta inviare un file
✅ **Stesse funzionalità** - Come la versione completa
✅ **Portable** - Funziona ovunque ci sia Python

## Installazione Rapida

```bash
# Installa dipendenze
pip install flask yt-dlp youtube-comment-downloader requests

# Avvia l'app
python3 analyzetube.py
```

Oppure rendilo eseguibile:

```bash
chmod +x analyzetube.py
./analyzetube.py
```

Poi apri: **http://localhost:5001**

## Come Funziona

Tutto è contenuto in un unico file:

- **HTML/CSS/JS**: Incorporati come stringa Python
- **Backend**: Funzioni Flask per estrazione dati
- **API**: Endpoint `/api/extract` per processare video

### Struttura del file:

```python
analyzetube.py
├── HTML_TEMPLATE (linea ~28)        # Frontend completo
│   ├── CSS incorporato              # Stili inline
│   └── JavaScript incorporato       # Logica frontend
├── Funzioni Backend (linea ~380)
│   ├── extract_video_id()
│   ├── extract_video_info()
│   ├── extract_subtitles()
│   ├── download_subtitle_content()
│   └── extract_comments()
└── Routes Flask (linea ~460)
    ├── @app.route('/')              # Serve HTML
    └── @app.route('/api/extract')   # API estrazione
```

## Utilizzo

1. Avvia: `python3 analyzetube.py`
2. Apri: http://localhost:5001
3. Incolla URL video YouTube
4. Clicca "Analizza Video"
5. Copia il prompt per ChatGPT

## Vantaggi vs Versione Multi-File

| Caratteristica | Versione Unica | Versione Multi-File |
|----------------|----------------|---------------------|
| **File count** | 1 file | 5+ file |
| **Setup** | Velocissimo | Normale |
| **Condivisione** | Facilissima | Richiede zip |
| **Manutenzione** | Più difficile | Più facile |
| **Funzionalità** | Identiche | Identiche |

## Quando Usare

### Usa la versione unica se:
- ✅ Vuoi qualcosa di veloce e portable
- ✅ Devi condividere l'app facilmente
- ✅ Non hai bisogno di modifiche frequenti
- ✅ Preferisci la semplicità

### Usa la versione multi-file se:
- ✅ Vuoi modificare spesso HTML/CSS/JS
- ✅ Hai un team che lavora sul progetto
- ✅ Preferisci separazione delle responsabilità
- ✅ Vuoi usare un editor con syntax highlighting migliore

## Modifiche

### Cambiare la porta:

Modifica l'ultima riga:

```python
app.run(debug=True, port=5001)  # Cambia 5001 con la porta desiderata
```

### Personalizzare il prompt:

Cerca la funzione `generatePrompt()` nell'HTML (circa linea 320):

```javascript
function generatePrompt(data) {
    return `Il tuo prompt personalizzato...`;
}
```

### Modificare lo stile:

Cerca `<style>` nell'HTML (circa linea 32) e modifica il CSS.

## Dipendenze

```bash
pip install flask yt-dlp youtube-comment-downloader requests
```

Oppure con requirements:

```txt
Flask>=3.0.0
yt-dlp>=2024.10.0
youtube-comment-downloader>=0.1.78
requests>=2.31.0
```

## Risoluzione Problemi

### Porta già in uso
```bash
python3 analyzetube.py
# Se errore, modifica la porta nell'ultima riga del file
```

### Dipendenze mancanti
```bash
pip install --upgrade flask yt-dlp youtube-comment-downloader requests
```

### Trascrizioni non funzionano
- Il video deve avere sottotitoli
- Prova con un altro video
- Aggiorna yt-dlp: `pip install --upgrade yt-dlp`

## Performance

Dimensione file: **~30 KB**
Tempo caricamento: **< 1s**
RAM utilizzata: **~50 MB**
Dipendenze: **4 package pip**

## Licenza

Stesso progetto AnalyzeTube, versione compatta.

## Tips

💡 **Backup**: Fai una copia prima di modificare
💡 **Testing**: Usa `debug=True` durante lo sviluppo
💡 **Deploy**: Cambia `debug=False` in produzione
💡 **Sicurezza**: Non esporre pubblicamente senza autenticazione
