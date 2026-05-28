// Globale Sprachunterstützung
let currentLang = localStorage.getItem('language') || 'en';

const translations = {
    en: {
        // Allgemein
        loading: "Loading...",
        error: "Error",
        back: "Back",
        home: "Home",
        
        // Pokémon Detail
        height: "Height",
        weight: "Weight",
        baseExp: "Base Experience",
        types: "Types",
        abilities: "Abilities",
        generation: "Generation",
        region: "Region",
        pokedexEntry: "Pokédex Entry",
        evolutionChain: "Evolution Chain",
        previousEvolution: "Previous Evolution",
        nextEvolutions: "Next Evolutions",
        noEvolution: "No further evolutions",
        basicPokemon: "Basic Pokémon",
        playCry: "Play Cry",
        backToList: "Back to list",
        print: "Print / PDF",
        
        // Quiz
        quizTitle: "Pokémon Trainer Quiz",
        nameQuiz: "Name that Pokémon",
        typeQuiz: "Type Effectiveness",
        statsQuiz: "Stats Challenge",
        score: "Score",
        correct: "Correct!",
        wrong: "Wrong!",
        quizComplete: "Quiz Complete!",
        playAgain: "Play Again",
        
        // Profil
        myProfile: "My Profile",
        trainerName: "Pokémon Trainer",
        editName: "Edit Name",
        pokemonCollected: "Pokémon Collected",
        teamsCreated: "Teams Created",
        achievements: "Achievements",
        favorites: "Favorites",
        myTeams: "My Teams",
        createNewTeam: "Create New Team",
        
        // Vergleichen
        compareTitle: "Advanced Pokémon Comparison",
        addPokemon: "Add Pokémon",
        clearAll: "Clear All",
        attribute: "Attribute",
        total: "Total",
        
        // Wetter
        weatherTitle: "Pokémon Weather & Time",
        timeOfDay: "Time of Day",
        morning: "Morning",
        afternoon: "Afternoon",
        evening: "Evening",
        night: "Night",
        weather: "Weather",
        clear: "Clear",
        rainy: "Rainy",
        snowy: "Snowy",
        foggy: "Foggy"
    },
    de: {
        loading: "Laden...",
        error: "Fehler",
        back: "Zurück",
        home: "Startseite",
        
        height: "Größe",
        weight: "Gewicht",
        baseExp: "Basis-Erfahrung",
        types: "Typen",
        abilities: "Fähigkeiten",
        generation: "Generation",
        region: "Region",
        pokedexEntry: "Pokédex-Eintrag",
        evolutionChain: "Entwicklungskette",
        previousEvolution: "Vorherige Entwicklung",
        nextEvolutions: "Nächste Entwicklungen",
        noEvolution: "Keine weiteren Entwicklungen",
        basicPokemon: "Basis-Pokémon",
        playCry: "Ruf abspielen",
        backToList: "Zurück zur Liste",
        print: "Drucken / PDF",
        
        quizTitle: "Pokémon-Trainer-Quiz",
        nameQuiz: "Wie heißt dieses Pokémon?",
        typeQuiz: "Typen-Effektivität",
        statsQuiz: "Werte-Challenge",
        score: "Punktestand",
        correct: "Richtig!",
        wrong: "Falsch!",
        quizComplete: "Quiz abgeschlossen!",
        playAgain: "Nochmal spielen",
        
        myProfile: "Mein Profil",
        trainerName: "Pokémon-Trainer",
        editName: "Name bearbeiten",
        pokemonCollected: "Pokémon gesammelt",
        teamsCreated: "Teams erstellt",
        achievements: "Errungenschaften",
        favorites: "Favoriten",
        myTeams: "Meine Teams",
        createNewTeam: "Neues Team erstellen",
        
        compareTitle: "Erweiterter Pokémon-Vergleich",
        addPokemon: "Pokémon hinzufügen",
        clearAll: "Alle löschen",
        attribute: "Attribut",
        total: "Gesamt",
        
        weatherTitle: "Pokémon-Wetter & Tageszeiten",
        timeOfDay: "Tageszeit",
        morning: "Morgen",
        afternoon: "Nachmittag",
        evening: "Abend",
        night: "Nacht",
        weather: "Wetter",
        clear: "Klar",
        rainy: "Regnerisch",
        snowy: "Verschneit",
        foggy: "Neblig"
    },
    fr: {
        loading: "Chargement...",
        error: "Erreur",
        back: "Retour",
        home: "Accueil",
        
        height: "Taille",
        weight: "Poids",
        baseExp: "Expérience de base",
        types: "Types",
        abilities: "Capacités",
        generation: "Génération",
        region: "Région",
        pokedexEntry: "Entrée Pokédex",
        evolutionChain: "Chaîne d'évolution",
        previousEvolution: "Évolution précédente",
        nextEvolutions: "Prochaines évolutions",
        noEvolution: "Pas d'autres évolutions",
        basicPokemon: "Pokémon de base",
        playCry: "Jouer le cri",
        backToList: "Retour à la liste",
        print: "Imprimer / PDF",
        
        quizTitle: "Quiz Pokémon",
        nameQuiz: "Nommez ce Pokémon",
        typeQuiz: "Efficacité des types",
        statsQuiz: "Défi statistiques",
        score: "Score",
        correct: "Correct !",
        wrong: "Faux !",
        quizComplete: "Quiz terminé !",
        playAgain: "Rejouer",
        
        myProfile: "Mon Profil",
        trainerName: "Dresseur Pokémon",
        editName: "Modifier le nom",
        pokemonCollected: "Pokémon collectionnés",
        teamsCreated: "Équipes créées",
        achievements: "Succès",
        favorites: "Favoris",
        myTeams: "Mes Équipes",
        createNewTeam: "Créer une équipe",
        
        compareTitle: "Comparaison Avancée",
        addPokemon: "Ajouter un Pokémon",
        clearAll: "Tout effacer",
        attribute: "Attribut",
        total: "Total",
        
        weatherTitle: "Météo Pokémon",
        timeOfDay: "Heure",
        morning: "Matin",
        afternoon: "Après-midi",
        evening: "Soir",
        night: "Nuit",
        weather: "Météo",
        clear: "Clair",
        rainy: "Pluvieux",
        snowy: "Neigeux",
        foggy: "Brumeux"
    }
};

function applyLanguage() {
    currentLang = localStorage.getItem('language') || 'en';
    const t = translations[currentLang];
    if (!t) return;
    
    // Alle Elemente mit data-i18n Attribut übersetzen
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key]) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = t[key];
            } else {
                el.textContent = t[key];
            }
        }
    });
}

function setLanguage(lang) {
    localStorage.setItem('language', lang);
    currentLang = lang;
    applyLanguage();
    location.reload(); // Seite neu laden für vollständige Übersetzung
}

// Beim Laden anwenden
document.addEventListener('DOMContentLoaded', applyLanguage);