from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from scrapers.mobile_de import MobileDeScraper
from scrapers.autoscout24 import AutoScout24Scraper
import os
import requests

app = Flask(__name__)
CORS(app)

N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL', 'https://doctormuelita-n8n.luxmju.easypanel.host/webhook/import-vehicle')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "Vehicle Scraper API"}), 200

@app.route('/api/scrape', methods=['POST'])
def scrape_vehicles():
    try:
        data = request.get_json()
        
        portal = data.get('portal', 'mobile_de')
        brand = data.get('brand', 'BMW')
        model = data.get('model', '')
        country = data.get('country', 'DE')
        max_results = min(data.get('max_results', 20), 50)
        send_to_n8n = data.get('send_to_n8n', False)
        
        if portal == 'mobile_de':
            scraper = MobileDeScraper()
        elif portal == 'autoscout24':
            scraper = AutoScout24Scraper()
        else:
            return jsonify({"error": "Portal no soportado"}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        vehicles = loop.run_until_complete(
            scraper.scrape(brand=brand, model=model, country=country, max_results=max_results)
        )
        loop.close()
        
        sent_count = 0
        if send_to_n8n:
            for vehicle in vehicles:
                try:
                    response = requests.post(N8N_WEBHOOK_URL, json=vehicle, timeout=10)
                    if response.status_code == 200:
                        sent_count += 1
                except Exception as e:
                    print(f"Error enviando a n8n: {e}")
        
        return jsonify({
            "success": True,
            "portal": portal,
            "brand": brand,
            "model": model,
            "total_found": len(vehicles),
            "sent_to_n8n": sent_count,
            "vehicles": vehicles[:5] if not send_to_n8n else []
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portals', methods=['GET'])
def get_portals():
    return jsonify({
        "portals": [
            {"id": "mobile_de", "name": "Mobile.de", "countries": ["DE", "AT", "NL", "BE"], "status": "active"},
            {"id": "autoscout24", "name": "AutoScout24", "countries": ["DE", "AT", "NL", "BE", "IT", "ES", "FR"], "status": "active"}
        ]
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
