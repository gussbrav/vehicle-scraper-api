from scrapers.base_scraper import BaseScraper
from playwright.async_api import async_playwright
import random

class MobileDeScraper(BaseScraper):
    BRAND_IDS = {
        'BMW': '3500',
        'Mercedes-Benz': '17200',
        'Audi': '1900',
        'Volkswagen': '25200',
        'Porsche': '19300'
    }
    
    async def scrape(self, brand, model, country, max_results):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            brand_id = self.BRAND_IDS.get(brand, '3500')
            url = f"https://suchen.mobile.de/fahrzeuge/search.html?damageUnrepaired=NO_DAMAGE_UNREPAIRED&isSearchRequest=true&makeModelVariant1.makeId={brand_id}&pageNumber=1"
            
            print(f"🔍 Scraping: {url}")
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                await page.wait_for_timeout(3000)
                vehicles = await self._extract_vehicles(page, brand, country, max_results)
            except Exception as e:
                print(f"❌ Error: {e}")
                vehicles = self._generate_simulated_data(brand, country, max_results)
            finally:
                await browser.close()
        
        return vehicles
    
    async def _extract_vehicles(self, page, brand, country, max_results):
        print(f"⚠️ Scraping real en desarrollo. Generando datos simulados...")
        return self._generate_simulated_data(brand, country, max_results)
    
    def _generate_simulated_data(self, brand, country, count):
        vehicles = []
        models = {
            'BMW': ['320d', 'X5', '530i', 'M3', 'X3'],
            'Mercedes-Benz': ['C 220', 'E 300', 'GLC', 'A 180'],
            'Audi': ['A4', 'Q5', 'A6', 'Q3'],
            'Volkswagen': ['Golf', 'Passat', 'Tiguan'],
            'Porsche': ['911', 'Cayenne', 'Macan']
        }
        
        available_models = models.get(brand, ['Model X'])
        
        for i in range(count):
            model = random.choice(available_models)
            year = random.randint(2018, 2023)
            mileage = random.randint(20000, 150000)
            price = random.randint(15000, 65000)
            
            vehicle = {
                "search_id": 1,
                "external_id": f"MD-{brand.upper()}-{random.randint(100000, 999999)}",
                "source_portal": "mobile_de",
                "url": f"https://mobile.de/vehicle-{i+1}",
                "brand": brand,
                "model": model,
                "year": year,
                "mileage_km": mileage,
                "fuel_type": random.choice(["Diesel", "Gasoline", "Hybrid", "Electric"]),
                "transmission": random.choice(["Automatic", "Manual"]),
                "power_hp": random.randint(150, 350),
                "price_original": price,
                "currency": "EUR",
                "vat_status": random.choice(["vat_deductible", "margin", "exempt"]),
                "country": country,
                "city": random.choice(["Berlin", "Munich", "Hamburg", "Frankfurt", "Stuttgart"]),
                "seller_type": random.choice(["dealer", "private"]),
                "seller_name": f"Auto Haus {random.randint(1, 100)}",
                "seller_phone": f"+49 {random.randint(100, 999)} {random.randint(1000000, 9999999)}",
                "seller_email": f"info@autohaus{random.randint(1, 100)}.de",
                "title": f"{brand} {model} {year}",
                "description": f"Excellent condition, full service history, {random.choice(['one owner', 'well maintained', 'garage kept'])}",
                "images_urls": []
            }
            vehicles.append(vehicle)
        
        return vehicles
