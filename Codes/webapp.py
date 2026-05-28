from bottle import request, route, run, static_file, template
import sqlite3
import re
import requests

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
# API HELPER
# --------------------------------------------------
def get_pokemon_api(name_or_id):
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{name_or_id}"
        print(f"API Request: {url}")
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            print(f"API Error: {r.status_code}")
            return None
        return r.json()
    except Exception as e:
        print(f"API Exception: {e}")
        return None

def get_pokedex_entry(pokemon_id, api_data=None):
    """Hilfsfunktion für Pokédex-Einträge - funktioniert auch für Mega-Entwicklungen"""
    try:
        species_name = None
        
        if api_data and "species" in api_data:
            species_name = api_data["species"]["name"]
        
        species_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}"
        r = requests.get(species_url, timeout=10)
        
        if r.status_code == 200:
            species_data = r.json()
            for entry in species_data.get("flavor_text_entries", []):
                if entry["language"]["name"] == "en":
                    return entry["flavor_text"].replace("\n", " ").replace("\f", " ").replace("\x0c", " ")
        elif species_name:
            species_url2 = f"https://pokeapi.co/api/v2/pokemon-species/{species_name}"
            r2 = requests.get(species_url2, timeout=10)
            if r2.status_code == 200:
                species_data = r2.json()
                for entry in species_data.get("flavor_text_entries", []):
                    if entry["language"]["name"] == "en":
                        return entry["flavor_text"].replace("\n", " ").replace("\f", " ").replace("\x0c", " ")
    except Exception as e:
        print(f"Error fetching dex entry for {pokemon_id}: {e}")
    
    return None

# --------------------------------------------------
# BULK API LIST (FAST!)
# --------------------------------------------------
def get_all_api_pokemon():
    try:
        url = "https://pokeapi.co/api/v2/pokemon?limit=2000"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []

        data = r.json()
        result = []

        for item in data["results"]:
            poke_id = int(item["url"].rstrip("/").split("/")[-1])
            if poke_id >= 722:
                result.append({
                    "id": poke_id,
                    "identifier": item["name"]
                })

        return result
    except:
        return []

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
    return template("start.html")

@route("/sound-test")
def sound_test():
    return template("sound_test.html")
# --------------------------------------------------
# POKEMON LIST (DB + API)
# --------------------------------------------------
@route("/pokemon")
def pokemon_list():
    return template("pokemon_list.html")
# --------------------------------------------------
# --------------------------------------------------
@route("/pokemon-data")
def pokemon_data():
    """Gibt alle Pokémon (Gen 1-9) als JSON zurück - OHNE API-Aufrufe pro Pokémon!"""
    db = connectDB()
    cursor = db.cursor()
    
    # Gen 1-6 aus der Datenbank
    db_pokemon = cursor.execute("""
        SELECT id, identifier
        FROM pokemon_species
        WHERE id < 722
        ORDER BY id
    """).fetchall()
    
    pokemon_list = []
    
    for p in db_pokemon:
        pokemon_list.append({
            "id": p["id"],
            "name": p["identifier"].capitalize(),
            "isApi": False
        })
    
    db.close()
    
    # Gen 7+ aus der API (ein einziger Aufruf für alle)
    try:
        url = "https://pokeapi.co/api/v2/pokemon?limit=2000"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for item in data["results"]:
                poke_id = int(item["url"].rstrip("/").split("/")[-1])
                if poke_id >= 722:
                    pokemon_list.append({
                        "id": poke_id,
                        "name": item["name"].capitalize(),
                        "isApi": True
                    })
    except Exception as e:
        print(f"Error loading API Pokémon: {e}")
    
    # Nach ID sortieren
    pokemon_list.sort(key=lambda x: x["id"])
    
    return {"pokemon": pokemon_list}
# --------------------------------------------------
# DETAIL (DB + API)
# --------------------------------------------------
@route("/pokemon/<id:int>")
def pokemon_detail(id):
    api_data = get_pokemon_api(id)
    
    if id >= 722 or id > 10000:
        if not api_data:
            return "Pokémon not found"
        
        api_dex_entry = get_pokedex_entry(id, api_data)
        
        region_id = 7
        region_name = "Alola"
        if id >= 906:
            region_id = 9
            region_name = "Paldea"
        elif id >= 810:
            region_id = 8
            region_name = "Galar"
        
        return template(
            "pokemon_detail_api",
            api=api_data,
            api_dex_entry=api_dex_entry,
            region_id=region_id,
            region_name=region_name,
            source="api",
            get_type_color=get_type_color
        )
    
    db = connectDB()
    cursor = db.cursor()

    pokemon = cursor.execute("""
        SELECT * FROM pokemon
        WHERE id = ?
    """, (id,)).fetchone()

    if pokemon:
        species = cursor.execute("""
            SELECT * FROM pokemon_species
            WHERE id = ?
        """, (pokemon["species_id"],)).fetchone()

        if not species:
            db.close()
            return "Species not found"

        previous_evolution = None
        if species["evolves_from_species_id"]:
            previous_evolution = cursor.execute("""
                SELECT identifier, id
                FROM pokemon_species
                WHERE id = ?
            """, (species["evolves_from_species_id"],)).fetchone()

        next_evolutions = cursor.execute("""
            SELECT identifier, id
            FROM pokemon_species
            WHERE evolves_from_species_id = ?
        """, (species["id"],)).fetchall()

        regions = {
            1: "Kanto", 2: "Johto", 3: "Hoenn",
            4: "Sinnoh", 5: "Unova", 6: "Kalos",
            7: "Alola", 8: "Galar", 9: "Paldea"
        }

        region = regions.get(species["generation_id"], "Unknown")
        region_id = species["generation_id"]

        dex = cursor.execute("""
            SELECT f.flavor_text, f.version_id
            FROM pokemon_species_flavor_text f
            WHERE f.species_id = ?
            AND f.language_id = 9
            LIMIT 1
        """, (species["id"],)).fetchone()

        dex_text = None
        if dex:
            dex_text = re.sub(r'\s+', ' ', dex["flavor_text"].replace("\n", " "))

        generation = cursor.execute("""
            SELECT * FROM generations
            WHERE id = ?
        """, (species["generation_id"],)).fetchone()

        version = None
        if dex:
            version = cursor.execute("""
                SELECT identifier
                FROM versions
                WHERE id = ?
            """, (dex["version_id"],)).fetchone()

        db.close()
        
        api_dex_entry = get_pokedex_entry(id, api_data)

        return template(
            "pokemon_detail",
            pokemon=pokemon,
            species=species,
            previous_evolution=previous_evolution,
            next_evolutions=next_evolutions,
            generation=generation,
            version=version,
            region=region,
            region_id=region_id,
            dex=dex_text,
            api_dex_entry=api_dex_entry,
            source="db",
            api_data=api_data,
            get_type_color=get_type_color
        )

    db.close()
    return "Pokémon not found"

# --------------------------------------------------
# SEARCH (DB + API)
# --------------------------------------------------
@route("/search")
def search():
    query = request.query.q
    
    if not query:
        return template("search_results", results=[], api_results=[], query="")
    
    try:
        poke_id = int(query)
        api_pokemon = get_pokemon_api(poke_id)
        if api_pokemon:
            region_id = 7
            region_name = "Alola"
            if poke_id >= 906:
                region_id = 9
                region_name = "Paldea"
            elif poke_id >= 810:
                region_id = 8
                region_name = "Galar"
            
            api_dex_entry = get_pokedex_entry(poke_id, api_pokemon)
            
            return template(
                "pokemon_detail_api",
                api=api_pokemon,
                api_dex_entry=api_dex_entry,
                region_id=region_id,
                region_name=region_name,
                source="api",
                get_type_color=get_type_color
            )
    except:
        pass
    
    db = connectDB()
    cursor = db.cursor()
    
    db_results = cursor.execute("""
        SELECT id, identifier
        FROM pokemon_species
        WHERE lower(identifier) LIKE lower(?)
        AND id < 722
        ORDER BY id
    """, ("%" + query + "%",)).fetchall()
    
    db.close()
    
    api_results = []
    
    try:
        url = "https://pokeapi.co/api/v2/pokemon?limit=2000"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for item in data["results"]:
                poke_id = int(item["url"].rstrip("/").split("/")[-1])
                if poke_id >= 722 and query.lower() in item["name"].lower():
                    if not any(str(db_p["id"]) == str(poke_id) for db_p in db_results):
                        api_results.append({
                            "id": poke_id,
                            "identifier": item["name"]
                        })
    except Exception as e:
        print(f"API search error: {e}")
    
    try:
        api_pokemon = get_pokemon_api(query.lower())
        if api_pokemon and api_pokemon["id"] >= 722:
            if not any(r["id"] == api_pokemon["id"] for r in api_results):
                if not any(str(db_p["id"]) == str(api_pokemon["id"]) for db_p in db_results):
                    api_results.append({
                        "id": api_pokemon["id"],
                        "identifier": api_pokemon["name"]
                    })
    except:
        pass
    
    api_results.sort(key=lambda x: x["id"])
    
    return template(
        "search_results",
        results=db_results,
        api_results=api_results,
        query=query
    )

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
        LIMIT 10
    """, (f"%{query}%",)).fetchall()
    
    for p in db_results:
        results.append({"id": p["id"], "name": p["identifier"], "source": "db"})
    
    db.close()
    
    if len(results) < 10:
        try:
            url = "https://pokeapi.co/api/v2/pokemon?limit=2000"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for item in data["results"]:
                    poke_id = int(item["url"].rstrip("/").split("/")[-1])
                    if poke_id >= 722 and query in item["name"].lower():
                        if not any(r["id"] == poke_id for r in results):
                            results.append({"id": poke_id, "name": item["name"], "source": "api"})
                            if len(results) >= 20:
                                break
        except:
            pass
    
    return {"results": results[:20]}

# --------------------------------------------------
# REGIONEN
# --------------------------------------------------
@route("/regions")
def regions_list():
    regions_data = {
        1: {"name": "Kanto", "generation": 1, "starter": "Bulbasaur, Charmander, Squirtle", "games": "Red/Blue/Yellow"},
        2: {"name": "Johto", "generation": 2, "starter": "Chikorita, Cyndaquil, Totodile", "games": "Gold/Silver/Crystal"},
        3: {"name": "Hoenn", "generation": 3, "starter": "Treecko, Torchic, Mudkip", "games": "Ruby/Sapphire/Emerald"},
        4: {"name": "Sinnoh", "generation": 4, "starter": "Turtwig, Chimchar, Piplup", "games": "Diamond/Pearl/Platinum"},
        5: {"name": "Unova", "generation": 5, "starter": "Snivy, Tepig, Oshawott", "games": "Black/White"},
        6: {"name": "Kalos", "generation": 6, "starter": "Chespin, Fennekin, Froakie", "games": "X/Y"},
        7: {"name": "Alola", "generation": 7, "starter": "Rowlet, Litten, Popplio", "games": "Sun/Moon"},
        8: {"name": "Galar", "generation": 8, "starter": "Grookey, Scorbunny, Sobble", "games": "Sword/Shield"},
        9: {"name": "Paldea", "generation": 9, "starter": "Sprigatito, Fuecoco, Quaxly", "games": "Scarlet/Violet"}
    }
    
    return template("regions_list", regions=regions_data)

@route("/region/<region_id:int>")
def region_detail(region_id):
    regions_data = {
        1: {"name": "Kanto", "generation": 1, "starter": "Bulbasaur, Charmander, Squirtle", 
            "games": "Red/Blue/Yellow", "description": "The Kanto region is the original Pokémon region...",
            "pokemon_count": 151, "legendary": "Articuno, Zapdos, Moltres, Mewtwo"},
        2: {"name": "Johto", "generation": 2, "starter": "Chikorita, Cyndaquil, Totodile", 
            "description": "Johto is located west of Kanto...",
            "games": "Gold/Silver/Crystal", "pokemon_count": 100, "legendary": "Raikou, Entei, Suicune, Ho-Oh, Lugia"},
        3: {"name": "Hoenn", "generation": 3, "starter": "Treecko, Torchic, Mudkip", 
            "description": "Hoenn is a tropical region...",
            "games": "Ruby/Sapphire/Emerald", "pokemon_count": 135, "legendary": "Groudon, Kyogre, Rayquaza"},
        4: {"name": "Sinnoh", "generation": 4, "starter": "Turtwig, Chimchar, Piplup", 
            "description": "Sinnoh is a northern region...",
            "games": "Diamond/Pearl/Platinum", "pokemon_count": 107, "legendary": "Dialga, Palkia, Giratina"},
        5: {"name": "Unova", "generation": 5, "starter": "Snivy, Tepig, Oshawott", 
            "description": "Unova is based on New York City...",
            "games": "Black/White", "pokemon_count": 156, "legendary": "Reshiram, Zekrom, Kyurem"},
        6: {"name": "Kalos", "generation": 6, "starter": "Chespin, Fennekin, Froakie", 
            "description": "Kalos is based on France...",
            "games": "X/Y", "pokemon_count": 72, "legendary": "Xerneas, Yveltal, Zygarde"},
        7: {"name": "Alola", "generation": 7, "starter": "Rowlet, Litten, Popplio", 
            "description": "Alola is a tropical region based on Hawaii...",
            "games": "Sun/Moon", "pokemon_count": 88, "legendary": "Solgaleo, Lunala, Necrozma"},
        8: {"name": "Galar", "generation": 8, "starter": "Grookey, Scorbunny, Sobble", 
            "description": "Galar is based on the United Kingdom...",
            "games": "Sword/Shield", "pokemon_count": 89, "legendary": "Zacian, Zamazenta, Eternatus"},
        9: {"name": "Paldea", "generation": 9, "starter": "Sprigatito, Fuecoco, Quaxly", 
            "description": "Paldea is based on the Iberian Peninsula...",
            "games": "Scarlet/Violet", "pokemon_count": 103, "legendary": "Koraidon, Miraidon"}
    }
    
    region = regions_data.get(region_id)
    if not region:
        return "Region not found"
    
    pokemon_list = []
    
    if region_id <= 6:
        db = connectDB()
        cursor = db.cursor()
        db_pokemon = cursor.execute("""
            SELECT p.id, p.identifier
            FROM pokemon p
            JOIN pokemon_species ps ON p.species_id = ps.id
            WHERE ps.generation_id = ?
            GROUP BY p.id
            LIMIT 20
        """, (region_id,)).fetchall()
        db.close()
        
        for p in db_pokemon:
            pokemon_list.append({"id": p["id"], "name": p["identifier"]})
    else:
        start_ids = {7: 722, 8: 810, 9: 906}
        end_ids = {7: 809, 8: 905, 9: 1025}
        start_id = start_ids.get(region_id, 722)
        end_id = end_ids.get(region_id, 1025)
        
        for pid in range(start_id, min(end_id + 1, start_id + 30)):
            api_pokemon = get_pokemon_api(pid)
            if api_pokemon and api_pokemon.get("id"):
                pokemon_list.append({"id": api_pokemon["id"], "name": api_pokemon["name"]})
    
    return template("region_detail", region=region, region_id=region_id, pokemon_list=pokemon_list)

# --------------------------------------------------
# NEUE ROUTES für Team, Compare, Type-Chart
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

@route("/print")
def print_pokemon():
    return template("print_pokemon.html")

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

@route("/language")
def language():
    return template("language_test.html")

@route("/share-team")
def share_team():
    code = request.query.code
    return template("share_team.html", code=code)

@route("/offline")
def offline():
    return template("offline.html")
# --------------------------------------------------
# STATIC
# --------------------------------------------------
@route('/static/<filename>')
def static(filename):
    return static_file(filename, root="./static")

# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    run(host='0.0.0.0', port=port, reloader=False, debug=False)