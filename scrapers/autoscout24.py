from scrapers.base_scraper import BaseScraper
import random

class AutoScout24Scraper(BaseScraper):
    async def scrape(self, brand, model, country, max_results):
        print(f"⚠️ AutoScout24 en desarrollo. Datos simulados...")
        vehicles = []
        for i in range(max_results):
            vehicle = {
                "search_id": 1,
                "external_id": f"AS24-{brand}-{i+1}",
                "source_portal": "autoscout24",
                "url": f"https://autoscout24.com/vehicle-{i+1}",
                "brand": brand,
                "model": model or "Model X",
                "year": random.randint(2019, 2023),
                "mileage_km": random.randint(20000, 120000),
                "fuel_type": "Diesel",
                "transmission": "Automatic",
                "power_hp": random.randint(150, 300),
                "price_original": random.randint(25000, 55000),
                "currency": "EUR",
                "vat_status": "vat_deductible",
                "country": country,
                "city": "Stuttgart",
                "seller_type": "dealer",
                "seller_name": f"AS24 Dealer {i+1}",
                "seller_phone": "+49 711 1234567",
                "seller_email": f"dealer{i+1}@example.de",
                "title": f"{brand} {model} AS24",
                "description": "From AutoScout24",
                "images_urls": []
            }
            vehicles.append(vehicle)
        return vehicles
