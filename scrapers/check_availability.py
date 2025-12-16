import requests
import psycopg2
from datetime import datetime, timedelta

# Configuración
DB_CONFIG = {
    'host': 'tu_host',
    'database': 'amt_concesionaria',
    'user': 'postgres',
    'password': 'tu_password'
}

def check_url(url):
    """Verifica si una URL está activa"""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def mark_old_vehicles_unavailable():
    """Marca vehículos viejos como no disponibles"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Marcar vehículos de más de 3 días como no disponibles
    three_days_ago = datetime.now() - timedelta(days=3)
    
    cur.execute("""
        UPDATE vehicles 
        SET is_available = false 
        WHERE scraped_at < %s 
        AND is_available = true
        AND source_portal = 'mobile_de'
    """, (three_days_ago,))
    
    updated = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Marcados {updated} vehículos como no disponibles")

if __name__ == "__main__":
    mark_old_vehicles_unavailable()