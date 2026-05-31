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
# STATIC FILES
# --------------------------------------------------
@route("/views/<filename>")
def serve_views(filename):
    return static_file(filename, root="./views")

@route("/static/<filename>")
def serve_static(filename):
    return static_file(filename, root="./static")

@route("/<filename>")
def serve_pages(filename):
    import os
    if os.path.exists(f"./views/{filename}"):
        return static_file(filename, root="./views")
    return "Not found", 404

# --------------------------------------------------
# API für Pokémon-Daten
# --------------------------------------------------
@route("/api/pokemon/<id:int>")
def api_pokemon(id):
    import requests
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{id}", timeout=10)
        return r.json()
    except:
        return {"error": "Not found"}

@route("/api/pokemon-species/<id:int>")
def api_pokemon_species(id):
    import requests
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{id}", timeout=10)
        return r.json()
    except:
        return {"error": "Not found"}

@route("/api/search")
def api_search():
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
# NORMALE POKÉMON ROUTES
# --------------------------------------------------
@route("/pokemon")
def pokemon_list():
    return template("pokemon_list.html")

@route("/pokemon/<id:int>")
def pokemon_detail(id):
    return template("pokemon_detail.html", id=id)

# --------------------------------------------------
# SPEZIELLE FORMEN ROUTES (NEU)
# --------------------------------------------------
@route("/special-detail")
def special_detail():
    """Detailansicht für spezielle Formen"""
    return template("special_detail.html")

@route("/special/<id:int>")
def special_detail_id(id):
    """Detailansicht für spezielle Formen mit ID"""
    return template("special_detail.html", id=id)

# --------------------------------------------------
# WEITERE ROUTES
# --------------------------------------------------
@route("/team")
def team_page():
    return template("team.html")

@route("/compare")
def compare_page():
    return template("compare.html")

@route("/type-chart")
def type_chart():
    return template("type_chart.html")

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
    return template("profile.html")

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
    return template("search_results.html")

@route("/print")
def print_pokemon():
    return template("print_pokemon.html")

@route("/offline")
def offline():
    return template("offline.html")

@route("/sound-test")
def sound_test():
    return template("sound_test.html")

# --------------------------------------------------
# RUN 
# --------------------------------------------------
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    run(host='0.0.0.0', port=port, reloader=False, debug=False)
