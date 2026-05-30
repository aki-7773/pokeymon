from bottle import request, route, run, static_file, template
import sqlite3
import re
import json

# Typ-Farben für das Styling
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

# --------------------------------------------------
# DB
# --------------------------------------------------
def connectDB():
    conn = sqlite3.connect("pokemon.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

# --------------------------------------------------
# INDEX
# --------------------------------------------------
@route("/")
def index():
    return static_file("start.html", root="./views")

# --------------------------------------------------
# STATIC FILES für GitHub Pages (wichtig!)
# --------------------------------------------------
@route("/views/<filename>")
def serve_views(filename):
    return static_file(filename, root="./views")

@route("/static/<filename>")
def serve_static(filename):
    return static_file(filename, root="./static")

@route("/<filename>")
def serve_pages(filename):
    # Für direkte HTML-Dateien (ohne views/ Pfad)
    import os
    if os.path.exists(f"./views/{filename}"):
        return static_file(filename, root="./views")
    return "Not found", 404

# --------------------------------------------------
# API für Pokémon-Daten (für die Frontend-JavaScript)
# --------------------------------------------------
@route("/api/pokemon/<id:int>")
def api_pokemon(id):
    """Proxy für Pokémon API - vermeidet CORS-Probleme"""
    import requests
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{id}", timeout=10)
        return r.json()
    except:
        return {"error": "Not found"}

@route("/api/pokemon-species/<id:int>")
def api_pokemon_species(id):
    """Proxy für Pokémon Species API"""
    import requests
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{id}", timeout=10)
        return r.json()
    except:
        return {"error": "Not found"}

@route("/api/search")
def api_search():
    """JSON API für Live-Suche"""
    query = request.query.q.lower()
    if not query or len(query) < 2:
        return {"results": []}
    
    results = []
    
    db = connectDB()
    cursor = db.cursor()
    db_results = cursor.execute("""
        SELECT id, identifier
        FROM pokemon_species
        WHERE lower(identifier) LIKE ?
        AND id < 722
        LIMIT 15
    """, (f"%{query}%",)).fetchall()
    
    for p in db_results:
        results.append({"id": p["id"], "name": p["identifier"].capitalize(), "source": "db"})
    
    db.close()
    
    return {"results": results}
    
@route('/favicon.ico')
def favicon():
    return static_file('favicon.ico', root='./static')
# --------------------------------------------------
# RUN 
# --------------------------------------------------
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    run(host='0.0.0.0', port=port, reloader=False, debug=False)
