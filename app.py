from flask import Flask, jsonify
from flask_cors import CORS
import urllib.request
import csv
import io
import json

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "COT + OI Signal API — OK"

@app.route('/price')
def get_price():
    try:
        url = 'https://query1.finance.yahoo.com/v8/finance/chart/ES%3DF?interval=1d&range=5d'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        closes = [v for v in data['chart']['result'][0]['indicators']['quote'][0]['close'] if v]
        prev = closes[-2]
        last = closes[-1]
        diff = last - prev
        thr  = prev * 0.001
        direction = 'sideways' if abs(diff) <= thr else ('up' if diff > 0 else 'down')
        return jsonify({'prev': round(prev,2), 'last': round(last,2), 'diff': round(diff,2), 'pct': round(diff/prev*100,2), 'direction': direction})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cot')
def get_cot():
    try:
        url = 'https://www.cftc.gov/dea/newcot/FinFutWk.txt'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode('utf-8', errors='ignore')
        rows = list(csv.reader(io.StringIO(raw)))
        sp500 = [r for r in rows if len(r) > 10 and 'S&P 500' in r[0].upper()]
        if not sp500:
            return jsonify({'error': 'S&P 500 not found'}), 404
        nets = []
        for row in sp500[:52]:
            try:
                nets.append(float(row[9].replace(',','')) - float(row[10].replace(',','')))
            except: pass
        latest = sp500[0]
        lL = float(latest[9].replace(',',''))
        lS = float(latest[10].replace(',',''))
        net = lL - lS
        hi, lo = max(nets), min(nets)
        pct = round((net - lo) / (hi - lo) * 100, 1) if hi != lo else 50.0
        pct = max(0, min(100, pct))
        return jsonify({'date': latest[2].strip(), 'long': int(lL), 'short': int(lS), 'net': int(net), 'pct': pct, 'direction': 'bull' if pct >= 50 else 'bear'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
