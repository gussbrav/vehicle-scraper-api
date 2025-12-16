from abc import ABC, abstractmethod
import re

class BaseScraper(ABC):
    def __init__(self):
        self.results = []
    
    @abstractmethod
    async def scrape(self, brand, model, country, max_results):
        pass
    
    def normalize_price(self, price_text):
        numbers = re.sub(r'[^\d]', '', price_text)
        return int(numbers) if numbers else 0
    
    def normalize_mileage(self, km_text):
        numbers = re.sub(r'[^\d]', '', km_text)
        return int(numbers) if numbers else 0
    
    def extract_year(self, text):
        year_match = re.search(r'(19|20)\d{2}', text)
        return int(year_match.group(0)) if year_match else None
