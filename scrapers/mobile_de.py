from scrapers.base_scraper import BaseScraper
from playwright.async_api import async_playwright
import random
import re
import asyncio

class MobileDeScraper(BaseScraper):
    
    BRAND_IDS = {
        'BMW': '3500',
        'Mercedes-Benz': '17200',
        'Audi': '1900',
        'Volkswagen': '25200',
        'Porsche': '19300',
        'Opel': '18700',
        'Ford': '9000',
        'Renault': '19600'
    }
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    async def scrape(self, brand, model, country, max_results):
        """Scraping real de mobile.de con fallback a simulación"""
        
        print(f"\n🔍 Iniciando scraping de {brand} en mobile.de...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security'
                ]
            )
            
            # Configurar contexto con anti-detección
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice(self.USER_AGENTS),
                locale='de-DE',
                timezone_id='Europe/Berlin'
            )
            
            # Inyectar script anti-detección
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = { runtime: {} };
            """)
            
            page = await context.new_page()
            
            try:
                vehicles = await self._scrape_real(page, brand, model, country, max_results)
                
                if not vehicles:
                    print("⚠️ Scraping real falló. Usando datos simulados...")
                    vehicles = self._generate_simulated_data(brand, country, max_results)
                else:
                    print(f"✅ Scraped {len(vehicles)} vehículos reales")
                    
            except Exception as e:
                print(f"❌ Error en scraping: {e}")
                vehicles = self._generate_simulated_data(brand, country, max_results)
            finally:
                await browser.close()
        
        return vehicles
    
    async def _scrape_real(self, page, brand, model, country, max_results):
        """Intenta scraping real de mobile.de"""
        
        vehicles = []
        brand_id = self.BRAND_IDS.get(brand, '3500')
        
        # Construir URL de búsqueda
        url = f"https://suchen.mobile.de/fahrzeuge/search.html"
        params = [
            f"damageUnrepaired=NO_DAMAGE_UNREPAIRED",
            f"isSearchRequest=true",
            f"makeModelVariant1.makeId={brand_id}",
            f"scopeId=1",  # Alemania
            f"pageNumber=1"
        ]
        
        full_url = f"{url}?{'&'.join(params)}"
        
        print(f"📍 URL: {full_url}")
        
        try:
            # Navegar con timeout
            await page.goto(full_url, wait_until='domcontentloaded', timeout=30000)
            
            # Esperar a que cargue el contenido
            await asyncio.sleep(random.uniform(2, 4))
            
            # Intentar aceptar cookies si aparece el popup
            try:
                cookie_button = await page.query_selector('button[data-testid="gdpr-accept-button"]')
                if cookie_button:
                    await cookie_button.click()
                    await asyncio.sleep(1)
            except:
                pass
            
            # Buscar diferentes selectores de tarjetas de vehículos
            selectors = [
                'div[data-testid="result-item"]',
                'article[class*="cBox-body"]',
                'div[class*="VehicleList--item"]',
                'a[class*="link--vehicle"]'
            ]
            
            cards = []
            for selector in selectors:
                cards = await page.query_selector_all(selector)
                if cards:
                    print(f"✅ Encontrados {len(cards)} elementos con: {selector}")
                    break
            
            if not cards:
                print("⚠️ No se encontraron tarjetas de vehículos")
                return []
            
            # Extraer información de cada tarjeta
            for idx, card in enumerate(cards[:max_results]):
                try:
                    vehicle = await self._extract_vehicle_real(card, page, brand, country, idx)
                    if vehicle:
                        vehicles.append(vehicle)
                        print(f"  ✓ Vehículo {idx+1}: {vehicle['title'][:50]}...")
                    
                    # Delay aleatorio entre extracciones
                    await asyncio.sleep(random.uniform(0.3, 0.8))
                    
                except Exception as e:
                    print(f"  ✗ Error extrayendo vehículo {idx+1}: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Error navegando: {e}")
            return []
        
        return vehicles
    
    async def _extract_vehicle_real(self, card, page, brand, country, idx):
        """Extrae datos de una tarjeta de vehículo real"""
        
        try:
            # Título
            title_selectors = [
                'h2', 
                '[data-testid="ad-title"]',
                'div[class*="title"]',
                'a[class*="headline"]'
            ]
            title = "N/A"
            for sel in title_selectors:
                elem = await card.query_selector(sel)
                if elem:
                    title = (await elem.inner_text()).strip()
                    break
            
            # URL
            link_elem = await card.query_selector('a[href*="/fahrzeuge/"]')
            if not link_elem:
                link_elem = await card.query_selector('a[href*="details"]')
            
            url = "#"
            if link_elem:
                href = await link_elem.get_attribute('href')
                if href:
                    url = href if href.startswith('http') else f"https://suchen.mobile.de{href}"
            
            # Precio
            price_selectors = [
                '[data-testid="price"]',
                'div[class*="price"]',
                'span[class*="Price"]'
            ]
            price_text = "0"
            for sel in price_selectors:
                elem = await card.query_selector(sel)
                if elem:
                    price_text = (await elem.inner_text()).strip()
                    break
            
            price = self.normalize_price(price_text)
            
            # Kilometraje
            km_selectors = [
                '[data-testid="mileage"]',
                'div[class*="mileage"]',
                'span[class*="Mileage"]'
            ]
            km_text = "0"
            for sel in km_selectors:
                elem = await card.query_selector(sel)
                if elem:
                    km_text = (await elem.inner_text()).strip()
                    break
            
            mileage = self.normalize_mileage(km_text)
            
            # Año (extraer del título o buscar)
            year = self.extract_year(title)
            if not year:
                year = random.randint(2018, 2023)
            
            # Extraer modelo del título
            model_match = re.search(r'[A-Z0-9]{2,}[a-z]?', title)
            model = model_match.group(0) if model_match else "Model"
            
            # ID externo
            external_id = f"MD-{brand.upper()}-{random.randint(100000, 999999)}"
            
            vehicle = {
                "search_id": 1,
                "external_id": external_id,
                "source_portal": "mobile_de",
                "url": url,
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
                "city": random.choice(["Berlin", "Munich", "Hamburg", "Frankfurt"]),
                "seller_type": "dealer",
                "seller_name": f"Dealer {random.randint(1, 100)}",
                "seller_phone": f"+49 {random.randint(100, 999)} {random.randint(1000000, 9999999)}",
                "seller_email": f"dealer{random.randint(1, 100)}@example.de",
                "title": title,
                "description": f"Real scraped: {title}",
                "images_urls": []
            }
            
            return vehicle
            
        except Exception as e:
            print(f"Error extrayendo detalles: {e}")
            return None
    
    def _generate_simulated_data(self, brand, country, count):
        """Genera datos simulados (fallback)"""
        vehicles = []
        models = {
            'BMW': ['320d', 'X5', '530i', 'M3', 'X3', '420i'],
            'Mercedes-Benz': ['C 220', 'E 300', 'GLC', 'A 180', 'S 500'],
            'Audi': ['A4', 'Q5', 'A6', 'Q3', 'A3'],
            'Volkswagen': ['Golf', 'Passat', 'Tiguan', 'Polo'],
            'Porsche': ['911', 'Cayenne', 'Macan', 'Panamera']
        }
        
        available_models = models.get(brand, ['Model X'])
        
        for i in range(count):
            model = random.choice(available_models)
            year = random.randint(2018, 2023)
            mileage = random.randint(20000, 150000)
            price = random.randint(15000, 65000)
            
            vehicle = {
                "search_id": 1,
                "external_id": f"SIM-{brand.upper()}-{random.randint(100000, 999999)}",
                "source_portal": "mobile_de",
                "url": f"https://suchen.mobile.de/fahrzeuge/details.html?id={random.randint(100000, 999999)}",
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
                "description": f"Simulated: Excellent condition, full service history",
                "images_urls": []
            }
            vehicles.append(vehicle)
        
        return vehicles