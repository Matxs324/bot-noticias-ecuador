import requests
from bs4 import BeautifulSoup
import os

# --- CONFIGURACIÓN ---
# Usamos os.getenv para que GitHub Actions oculte tus llaves por seguridad
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
MI_ID_TELEGRAM = os.getenv("MI_ID_TELEGRAM")
ARCHIVO_MEMORIA = "vistas.txt"
CABECERAS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def cargar_memoria():
    """Lee el archivo de texto para recordar qué noticias ya enviamos"""
    if not os.path.exists(ARCHIVO_MEMORIA):
        return []
    with open(ARCHIVO_MEMORIA, "r", encoding="utf-8") as f:
        return [linea.strip() for linea in f.readlines()]

def guardar_memoria(lista_noticias):
    """Guarda los títulos en el archivo para la próxima hora"""
    # Solo guardamos las últimas 50 para que el archivo no pese mucho
    with open(ARCHIVO_MEMORIA, "w", encoding="utf-8") as f:
        for noticia in lista_noticias[-50:]:
            f.write(f"{noticia}\n")

def enviar_telegram(mensaje):
    if not TOKEN_TELEGRAM or not MI_ID_TELEGRAM:
        print("Error: No se encontraron las llaves de Telegram en Environments.")
        return
    url_api = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {"chat_id": MI_ID_TELEGRAM, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url_api, data=payload, timeout=10)
    except:
        print("Error al conectar con Telegram")

def raspar_fuente(nombre_medio, url_sitio, base_url, memoria):
    nuevas = 0
    try:
        res = requests.get(url_sitio, headers=CABECERAS, timeout=15)
        sopas = BeautifulSoup(res.text, 'html.parser')
        articulos = sopas.find_all('a', href=True)
        
        # Filtros de importancia para Ecuador
        palabras_vip = ["urgente", "decreto", "noboa", "asamblea", "atentado", "seguridad", "capturado", "sri", "ley", "fiscalía", "manabí"]
        lista_negra = ["fútbol", "deportes", "horóscopo", "farándula", "cocina", "receta", "lotería"]

        for art in articulos:
            texto = art.get_text().strip()
            link = art['href']
            if link.startswith("/"):
                link = base_url.rstrip('/') + link

            if len(texto) > 45:
                texto_low = texto.lower()
                if not any(b in texto_low for b in lista_negra):
                    if any(v in texto_low for v in palabras_vip) or "ecuador" in texto_low:
                        if texto not in memoria:
                            msg = f"🔔 *{nombre_medio.upper()}*\n\n{texto}\n\n🔗 [Ver noticia completa]({link})"
                            enviar_telegram(msg)
                            memoria.append(texto)
                            nuevas += 1
    except Exception as e:
        print(f"Error en {nombre_medio}: {e}")
    return nuevas

if __name__ == "__main__":
    print("🤖 Iniciando revisión de noticias...")
    
    # 1. Cargar lo que ya conocemos
    memoria_actual = cargar_memoria()
    
    fuentes = [
        ("Primicias", "https://www.primicias.ec/secciones/politica/", "https://www.primicias.ec"),
        ("Teleamazonas", "https://www.teleamazonas.com/noticias/actualidad/", "https://www.teleamazonas.com"),
        ("Ecuavisa", "https://www.ecuavisa.com/noticias/ecuador/", "https://www.ecuavisa.com"),
        ("El Universo", "https://www.eluniverso.com/noticias/ecuador/", "https://www.eluniverso.com"),
        ("Expreso", "https://www.expreso.ec/actualidad/politica/", "https://www.expreso.ec")
    ]
    
    total_nuevas = 0
    for nombre, url, base in fuentes:
        total_nuevas += raspar_fuente(nombre, url, base, memoria_actual)
    
    # 2. Guardar la memoria actualizada
    guardar_memoria(memoria_actual)
    
    if total_nuevas == 0:
        # Enviar reporte de tranquilidad (opcional)
        enviar_telegram("✅ *Reporte:* Sin novedades importantes en esta hora.")
        print("No se encontraron noticias nuevas.")
    else:
        print(f"Ronda terminada: {total_nuevas} enviadas.")