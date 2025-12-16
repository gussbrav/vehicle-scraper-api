# Vehicle Scraper API

API for scraping European vehicle portals (mobile.de, AutoScout24).

## Endpoints

- `GET /health` - Health check
- `GET /api/portals` - List available portals
- `POST /api/scrape` - Execute scraping

## Deploy on EasyPanel

1. Connect GitHub repo
2. Set environment variable: `N8N_WEBHOOK_URL`
3. Expose port 5000
4. Deploy!
