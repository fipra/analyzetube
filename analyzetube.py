from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

# Crea cartelle se non esistono
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def classify_zone(row):
    """Classifica il dispositivo in una zona di sicurezza basato sui dati reali"""

    # Get relevant fields
    remote_access = str(row.get('Remote Access enabled', '')).lower()
    network_mode_1 = str(row.get('Network Mode 1', '')).lower()
    network_mode_2 = str(row.get('Network Mode 2', '')).lower()
    modality = str(row.get('Modality', ''))

    # Zone 4 - Critical/Remote (has remote access)
    if 'ja' in remote_access or 'yes' in remote_access:
        return "Zone 4 – Critical/Remote"

    # Zone 1 - Offline/Low Risk (no network connection)
    has_network = ('lan' in network_mode_1 or 'wlan' in network_mode_1 or
                   'lan' in network_mode_2 or 'wlan' in network_mode_2)
    if not has_network or network_mode_1 == 'nan':
        return "Zone 1 – Offline/Low Risk"

    # Zone 3 - Sensitive (critical medical imaging devices)
    critical_modalities = ['XA', 'CT', 'MRI', 'RF', 'EPS']
    if any(mod in modality for mod in critical_modalities):
        return "Zone 3 – Sensitive"

    # Zone 2 - Moderate (default for networked devices)
    return "Zone 2 – Moderate"

def create_detailed_report(df, output_dir, base_name):
    """Crea report dettagliati per zona con liste dispositivi e analisi"""

    # File principale con tutte le zone
    main_output = os.path.join(output_dir, f"{base_name}_zoned.xlsx")

    with pd.ExcelWriter(main_output, engine='openpyxl') as writer:
        # Sheet principale con tutti i dispositivi
        df.to_excel(writer, sheet_name='All Devices', index=False)

        # Sheet per ogni zona
        for zone in sorted(df['Zone'].unique()):
            zone_df = df[df['Zone'] == zone].copy()
            sheet_name = zone.split('–')[0].strip().replace(' ', '_')
            zone_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Sheet di analisi/raggruppamento
        analysis_df = create_analysis_summary(df)
        analysis_df.to_excel(writer, sheet_name='Grouping Analysis', index=False)

    return main_output

def create_analysis_summary(df):
    """Crea un sommario di analisi per il Zonierungskonzept"""

    analysis_data = []

    # Analisi per Zona
    for zone in sorted(df['Zone'].unique()):
        zone_df = df[df['Zone'] == zone]

        # Raggruppa per Manufacturer
        manufacturer_counts = zone_df['Manufacturer'].value_counts().head(10)

        # Raggruppa per Modality
        modality_counts = zone_df['Modality'].value_counts().head(10)

        # Raggruppa per Network Type
        network_counts = zone_df['Network Type'].value_counts().head(5)

        analysis_data.append({
            'Zone': zone,
            'Total Devices': len(zone_df),
            'Unique Manufacturers': zone_df['Manufacturer'].nunique(),
            'Top Manufacturer': manufacturer_counts.index[0] if len(manufacturer_counts) > 0 else 'N/A',
            'Top Manufacturer Count': manufacturer_counts.iloc[0] if len(manufacturer_counts) > 0 else 0,
            'Unique Modalities': zone_df['Modality'].nunique(),
            'Top Modality': modality_counts.index[0] if len(modality_counts) > 0 else 'N/A',
            'Top Modality Count': modality_counts.iloc[0] if len(modality_counts) > 0 else 0,
            'With Remote Access': (zone_df['Remote Access enabled'].str.lower() == 'ja').sum(),
            'With Network': ((zone_df['Network Mode 1'].notna()) | (zone_df['Network Mode 2'].notna())).sum()
        })

    return pd.DataFrame(analysis_data)

def process_excel(input_path, output_path, sheet_name=0):
    """Processa il file Excel e aggiunge la classificazione delle zone"""
    try:
        # Leggi il file (skip first 2 rows which are headers/instructions)
        df = pd.read_excel(input_path, sheet_name=sheet_name, skiprows=2)

        # Applica classificazione
        df["Zone"] = df.apply(classify_zone, axis=1)

        # Calcola statistiche
        summary = df["Zone"].value_counts().to_dict()

        # Crea analisi per raggruppamento
        grouping_data = create_grouping_data(df)

        # Crea dati per grafici
        chart_data = create_chart_data(df)

        # Crea report dettagliato con sheets multiple
        output_dir = os.path.dirname(output_path)
        base_name = os.path.basename(output_path).rsplit('_zoned', 1)[0]
        create_detailed_report(df, output_dir, base_name)

        return True, summary, df.columns.tolist(), grouping_data, chart_data

    except Exception as e:
        return False, str(e), [], {}, {}

def create_grouping_data(df):
    """Crea dati di raggruppamento per il Zonierungskonzept"""
    grouping = {}

    for zone in sorted(df['Zone'].unique()):
        zone_df = df[df['Zone'] == zone]
        grouping[zone] = {
            'total': len(zone_df),
            'by_manufacturer': zone_df['Manufacturer'].value_counts().head(5).to_dict(),
            'by_modality': zone_df['Modality'].value_counts().head(5).to_dict(),
            'by_network': zone_df['Network Type'].value_counts().to_dict()
        }

    return grouping

def create_chart_data(df):
    """Crea dati per i grafici visuali"""
    chart_data = {}

    # Zone distribution (for pie chart)
    zone_counts = df['Zone'].value_counts().to_dict()
    chart_data['zones'] = {
        'labels': list(zone_counts.keys()),
        'data': list(zone_counts.values()),
        'colors': ['#4ade80', '#fbbf24', '#fb923c', '#ef4444'][:len(zone_counts)]
    }

    # Top 10 Manufacturers (for bar chart)
    top_manufacturers = df['Manufacturer'].value_counts().head(10)
    chart_data['manufacturers'] = {
        'labels': top_manufacturers.index.tolist(),
        'data': top_manufacturers.tolist()
    }

    # Top 10 Modalities (for bar chart)
    top_modalities = df['Modality'].value_counts().head(10)
    chart_data['modalities'] = {
        'labels': top_modalities.index.tolist(),
        'data': top_modalities.tolist()
    }

    # Network distribution
    network_dist = df['Network Type'].value_counts().to_dict()
    chart_data['network'] = {
        'labels': list(network_dist.keys()),
        'data': list(network_dist.values())
    }

    # Remote access stats
    remote_count = int((df['Remote Access enabled'].str.lower() == 'ja').sum())
    no_remote = int(len(df) - remote_count)
    chart_data['remote_access'] = {
        'labels': ['Remote Access Enabled', 'No Remote Access'],
        'data': [remote_count, no_remote],
        'colors': ['#ef4444', '#4ade80']
    }

    # Risk matrix: Zone x Modality (heatmap data)
    risk_matrix = []
    for zone in sorted(df['Zone'].unique()):
        zone_data = df[df['Zone'] == zone]
        top_mods = zone_data['Modality'].value_counts().head(5)
        risk_matrix.append({
            'zone': zone.split('–')[0].strip(),
            'modalities': top_mods.to_dict()
        })
    chart_data['risk_matrix'] = risk_matrix

    return chart_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Nessun file selezionato', 'error')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('Nessun file selezionato', 'error')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        # Genera nome file output
        base_name = filename.rsplit('.', 1)[0]
        output_filename = f"{base_name}_zoned.xlsx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # Processa il file
        success, result, columns, grouping_data, chart_data = process_excel(input_path, output_path)

        if success:
            return render_template('result.html',
                                 summary=result,
                                 output_file=output_filename,
                                 columns=columns,
                                 grouping_data=grouping_data,
                                 chart_data=chart_data)
        else:
            flash(f'Errore durante il processo: {result}', 'error')
            return redirect(url_for('index'))
    else:
        flash('Formato file non valido. Usa .xlsx o .xls', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
