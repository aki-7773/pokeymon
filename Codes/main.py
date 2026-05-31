from bottle import request, route, run, static_file, template, error, redirect
import sqlite3
import re
import json
import os
import requests
from datetime import datetime, timedelta
from functools import wraps
import hashlib

# ============================================================
# KONFIGURATION
# ============================================================
APP_NAME = "Pokémon Database"
APP_VERSION = "2.0.0"
CACHE_TIMEOUT = 3600  # 1 Stunde Cache für API-Aufrufe

# ============================================================
# CACHE FÜR API-AUFRUFE (verbessert Performance)
# ============================================================
api_cache = {}

def cached_api_call(url, timeout=CACHE_TIMEOUT):
    """Cached API calls to reduce rate limiting"""
    cache_key = hashlib.md5(url.encode()).hexdigest()
    
    # Prüfen ob Cache existiert und noch gültig ist
    if cache_key in api_cache:
        data, timestamp = api_cache[cache_key]
        if datetime.now() - timestamp < timedelta(seconds=timeout):
            return data
    
    # API aufrufen
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            api_cache[cache_key] = (data, datetime.now())
            return data
    except Exception as e:
        print(f"API Error: {e}")
    
    return None

# ============================================================
# TYP-FARBEN
# ============================================================
def get_type_color(type_name):
    colors = {
        "normal": "#A8A878", "fire": "#F08030", "water": "#6890F0",
        "electric": "#F8D030", "grass": "#78C850", "ice": "#98D8D8",
        "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
        "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820",
        "rock": "#B8A038", "ghost": "#705898", "dragon": "#7038F8",
        "dark": "#705848", "steel": "#B8B8D0", "fairy": "#EE99AC"
    }
    return colors.get(type_name, "#68A090")

def get_type_icon(type_name):
    """Gibt ein Emoji/Icon für den Typ zurück"""
    icons = {
        "normal": "⚪", "fire": "🔥", "water": "💧", "electric": "⚡",
        "grass": "🌿", "ice": "❄️", "fighting": "👊", "poison": "☠️",
        "ground": "⛰️", "flying": "🕊️", "psychic": "🔮", "bug": "🐛",
        "rock": "🪨", "ghost": "👻", "dragon": "🐉", "dark": "🌙",
        "steel": "⚙️", "fairy": "✨"
    }
    return icons.get(type_name, "⭐")

# ============================================================
# DB
# ============================================================
def connectDB():
    conn = sqlite3.connect("pokemon.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialisiert die Datenbank mit Tabellen falls nicht vorhanden"""
    conn = connectDB()
    cursor = conn.cursor()
    
    # Tabelle für Favoriten/Team
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemon_id INTEGER UNIQUE,
            notes TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabelle für Benutzereinstellungen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Datenbank beim Start initialisieren
init_db()

# ============================================================
# AUTHENTIFIKATION / SESSION (vereinfacht)
# ============================================================
def get_user_session():
    """Einfache Session-Verwaltung über Cookies"""
    # In einer echten App würde man hier Sessions verwenden
    return {"user_id": 1, "username": "Trainer"}

# ============================================================
# INDEX & STATIC FILES
# ============================================================
@route("/")
def index():
    return static_file("start.html", root="./views")

@route("/views/<filename>")
def serve_views(filename):
    return static_file(filename, root="./views")

@route("/static/<filename>")
def serve_static(filename):
    return static_file(filename, root="./static")

@route("/<filename>")
def serve_pages(filename):
    if os.path.exists(f"./views/{filename}"):
        return static_file(filename, root="./views")
    return "Not found", 404

# ============================================================
# API FÜR POKÉMON-DATEN (MIT CACHING)
# ============================================================
@route("/api/pokemon/<id:int>")
def api_pokemon(id):
    data = cached_api_call(f"https://pokeapi.co/api/v2/pokemon/{id}")
    if data:
        return data
    return {"error": "Not found"}

@route("/api/pokemon-species/<id:int>")
def api_pokemon_species(id):
    data = cached_api_call(f"https://pokeapi.co/api/v2/pokemon-species/{id}")
    if data:
        return data
    return {"error": "Not found"}

@route("/api/evolution-chain/<id:int>")
def api_evolution_chain(id):
    data = cached_api_call(f"https://pokeapi.co/api/v2/evolution-chain/{id}")
    if data:
        return data
    return {"error": "Not found"}

@route("/api/type/<name>")
def api_type(name):
    data = cached_api_call(f"https://pokeapi.co/api/v2/type/{name}")
    if data:
        return data
    return {"error": "Not found"}

# ============================================================
# VERBESSERTE SUCHE (mit mehr Optionen)
# ============================================================
@route("/api/search")
def api_search():
    query = request.query.q.lower()
    search_type = request.query.type or "pokemon"  # pokemon, type, ability
    limit = int(request.query.limit or 20)
    
    if not query or len(query) < 2:
        return {"results": []}
    
    results = []
    
    if search_type == "pokemon":
        db = connectDB()
        cursor = db.cursor()
        
        # Suche in der Datenbank (falls vorhanden)
        db_results = cursor.execute("""
            SELECT id, identifier, generation_id
            FROM pokemon_species
            WHERE lower(identifier) LIKE ?
            LIMIT ?
        """, (f"%{query}%", limit)).fetchall()
        
        for p in db_results:
            results.append({
                "id": p["id"],
                "name": p["identifier"].capitalize(),
                "generation": p["generation_id"],
                "type": "pokemon",
                "url": f"/pokemon/{p['id']}"
            })
        
        db.close()
    
    elif search_type == "type":
        # Typ-Suche über API
        for type_name in ["normal", "fire", "water", "electric", "grass", "ice", "fighting", 
                          "poison", "ground", "flying", "psychic", "bug", "rock", "ghost", 
                          "dragon", "dark", "steel", "fairy"]:
            if query in type_name:
                results.append({
                    "name": type_name.capitalize(),
                    "type": "type",
                    "url": f"/type-chart?type={type_name}"
                })
    
    return {"results": results, "count": len(results), "type": search_type}

# ============================================================
# TEAM / FAVORITEN API
# ============================================================
@route("/api/team", method="GET")
def get_team():
    """Holt das aktuelle Team des Benutzers"""
    db = connectDB()
    cursor = db.cursor()
    team = cursor.execute("SELECT pokemon_id, notes, added_date FROM user_team ORDER BY added_date").fetchall()
    db.close()
    return {"team": [dict(row) for row in team]}

@route("/api/team/<pokemon_id:int>", method="POST")
def add_to_team(pokemon_id):
    """Fügt ein Pokémon zum Team hinzu"""
    db = connectDB()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO user_team (pokemon_id, notes) VALUES (?, ?)", 
                      (pokemon_id, request.forms.get("notes", "")))
        db.commit()
        success = True
    except Exception as e:
        success = False
    db.close()
    return {"success": success, "pokemon_id": pokemon_id}

@route("/api/team/<pokemon_id:int>", method="DELETE")
def remove_from_team(pokemon_id):
    """Entfernt ein Pokémon aus dem Team"""
    db = connectDB()
    cursor = db.cursor()
    cursor.execute("DELETE FROM user_team WHERE pokemon_id = ?", (pokemon_id,))
    db.commit()
    db.close()
    return {"success": True, "pokemon_id": pokemon_id}

# ============================================================
# BENUTZEREINSTELLUNGEN
# ============================================================
@route("/api/settings/<key>", method="GET")
def get_setting(key):
    db = connectDB()
    cursor = db.cursor()
    result = cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,)).fetchone()
    db.close()
    return {"key": key, "value": result["value"] if result else None}

@route("/api/settings/<key>", method="POST")
def set_setting(key):
    value = request.forms.get("value", "")
    db = connectDB()
    cursor = db.cursor()
    cursor.execute("INSERT OR REPLACE INTO user_settings (key, value) VALUES (?, ?)", (key, value))
    db.commit()
    db.close()
    return {"success": True, "key": key, "value": value}

# ============================================================
# STATISTIKEN
# ============================================================
@route("/api/stats")
def api_stats():
    """Gibt verschiedene Statistiken zurück"""
    stats = {
        "total_pokemon": 1025,
        "generations": 9,
        "types": 18,
        "api_status": "online",
        "cached_requests": len(api_cache),
        "version": APP_VERSION
    }
    
    # Prüfe API-Status
    try:
        response = requests.get("https://pokeapi.co/api/v2/pokemon/pikachu", timeout=5)
        stats["api_status"] = "online" if response.status_code == 200 else "degraded"
    except:
        stats["api_status"] = "offline"
    
    return stats

@route("/api/random")
def api_random():
    """Gibt ein zufälliges Pokémon zurück"""
    import random
    random_id = random.randint(1, 1025)
    data = cached_api_call(f"https://pokeapi.co/api/v2/pokemon/{random_id}")
    if data:
        return {"id": random_id, "name": data["name"], "data": data}
    return {"error": "Could not fetch random Pokémon"}

# ============================================================
# POKÉMON ROUTES (Gen 1-6)
# ============================================================
@route("/pokemon")
def pokemon_list():
    """Gen 1-6 Pokédex (IDs 1-721)"""
    return template("pokemon_list.html")

@route("/pokemon-gen7plus")
def pokemon_list_gen7plus():
    """Gen 7-9 Pokédex (IDs 722-1025)"""
    return template("pokemon_list_gen7plus.html")

@route("/pokemon/<id:int>")
def pokemon_detail(id):
    """Detailansicht für Gen 1-6 Pokémon"""
    return template("pokemon_detail.html", id=id)

@route("/pokemon/compare")
def pokemon_compare():
    """Vergleichsseite für Pokémon"""
    ids = request.query.ids or ""
    pokemon_ids = [int(x) for x in ids.split(",") if x.strip()]
    return template("compare.html", ids=pokemon_ids)

# ============================================================
# SPEZIELLE FORMEN ROUTES
# ============================================================
@route("/special-detail")
def special_detail():
    """Detailansicht für spezielle Formen"""
    return template("special_detail.html")

@route("/special/<id:int>")
def special_detail_id(id):
    """Detailansicht für spezielle Formen mit ID"""
    return template("special_detail.html", id=id)

# ============================================================
# WEITERE ROUTES (alle vorhandenen)
# ============================================================
@route("/team")
def team_page():
    return template("team.html")

@route("/compare")
def compare_page():
    return template("compare.html")

@route("/type-chart")
def type_chart():
    type_filter = request.query.type or ""
    return template("type_chart.html", selected_type=type_filter)

@route("/gallery")
def gallery():
    return template("gallery.html")

@route("/top-10")
def top_10():
    return template("top_10.html")

@route("/generation-stats")
def generation_stats():
    return template("generation_stats.html")

@route("/advanced-compare")
def advanced_compare():
    return template("advanced_compare.html")

@route("/profile")
def profile():
    user = get_user_session()
    return template("profile.html", user=user)

@route("/quiz")
def quiz():
    return template("quiz.html")

@route("/weather")
def weather_pokemon():
    return template("weather_pokemon.html")

@route("/share-team")
def share_team():
    return template("share_team.html")

@route("/regions")
def regions_list():
    return template("regions_list.html")

@route("/region/<id:int>")
def region_detail(id):
    return template("region_detail.html", id=id)

@route("/search")
def search():
    query = request.query.q or ""
    search_type = request.query.type or "pokemon"
    return template("search_results.html", query=query, search_type=search_type)

@route("/print")
def print_pokemon():
    return template("print_pokemon.html")

@route("/offline")
def offline():
    return template("offline.html")

@route("/sound-test")
def sound_test():
    return template("sound_test.html")

@route("/about")
def about():
    """Über die App Seite"""
    return template("about.html", app_name=APP_NAME, version=APP_VERSION)

@route("/api-docs")
def api_docs():
    """API Dokumentation"""
    return template("api_docs.html")

# ============================================================
# ERROR HANDLING (verbessert)
# ============================================================
@error(404)
def error404(error):
    return template("error.html", code=404, message="Page not found! The Pokémon you're looking for might have fled."), 404

@error(500)
def error500(error):
    return template("error.html", code=500, message="Internal server error! Team Rocket might be causing trouble."), 500

# ============================================================
# HEALTH CHECK (für Render/Railway)
# ============================================================
@route("/health")
def health_check():
    """Health Check für Hosting-Dienste"""
    return {
        "status": "healthy",
        "app": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# RUN 
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 {APP_NAME} v{APP_VERSION} starting...")
    print(f"📍 Running on http://localhost:{port}")
    print(f"📊 Cache size: {len(api_cache)} entries")
    run(host='0.0.0.0', port=port, reloader=False, debug=False)
