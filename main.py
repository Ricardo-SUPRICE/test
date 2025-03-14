from playwright.sync_api import sync_playwright
import json
from datetime import datetime
import time
import requests
import re

from datetime import datetime, timezone
from dateutil import parser

while True:
    def get_time_until_match(match_datetime):

        # Obtenir l'heure actuelle en UTC
        now = datetime.now(timezone.utc)
        
        # Vérifier si le match a déjà commencé
        if match_datetime <= now:
            return "Le match a déjà commencé"
        
        # Calculer le temps restant avant le match
        time_until_match = match_datetime - now
        
        # Extraire les composants du temps restant
        days = time_until_match.days
        hours, remainder = divmod(time_until_match.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Formater le temps restant de manière lisible
        time_until_str = ""
        if days > 0:
            time_until_str += f"{days} jour{'s' if days > 1 else ''} "
        if hours > 0 or days > 0:
            time_until_str += f"{hours} heure{'s' if hours > 1 else ''} "
        if minutes > 0 or hours > 0 or days > 0:
            time_until_str += f"{minutes} minute{'s' if minutes > 1 else ''} "
        time_until_str += f"{seconds} seconde{'s' if seconds > 1 else ''}"
        
        return time_until_str


    def get_combined_odds():
        # Récupérer les données de l'API
        print("Récupération des données depuis l'API...")
        
        api_urls = ["https://api.the-odds-api.com/v4/sports/tennis_atp_indian_wells/odds/?apiKey=7b17ced4a5f49f1c9a81e0892c38b17a&regions=uk,eu&markets=h2h&oddsFormat=decimal&bookmakers=betfair_ex_uk,winamax_fr,betclic,pinnacle&includeBetLimits=true","https://api.the-odds-api.com/v4/sports/tennis_wta_indian_wells/odds/?apiKey=7b17ced4a5f49f1c9a81e0892c38b17a&regions=uk,eu&markets=h2h&oddsFormat=decimal&bookmakers=betfair_ex_uk,winamax_fr,betclic,pinnacle&includeBetLimits=true"]
        combined_data = {}
        date_match = {}


        for api_url in api_urls:
            response = requests.get(api_url)
            response.raise_for_status()
            api_matches = response.json()
            
            # Traiter les données de l'API
            for match in api_matches:
                # Extraire seulement le nom de famille des joueurs
                home_player_full = match['home_team']
                away_player_full = match['away_team']

                commence_time = match['commence_time']
                #match_time = datetime.fromisoformat(commence_time)
                match_time = parser.isoparse(commence_time)
                print(match_time)  # ISO format avec timezone UTC
                time_left = get_time_until_match(match_time)
                
                # Extraire le nom de famille (dernier mot)
                home_player = home_player_full.split()[-1]
                away_player = away_player_full.split()[-1]
                
                match_key = f"{home_player} vs {away_player}"
                
                # Initialiser l'entrée pour ce match
                if match_key not in combined_data:
                    combined_data[match_key] = {
                        home_player: {},
                        away_player: {},
                        }
                
                if match_key not in date_match:
                    date_match[match_key] = time_left

                # Ajouter les cotes de chaque bookmaker
                for bookmaker in match['bookmakers']:
                    bookmaker_name = bookmaker['title']
                    
                    for market in bookmaker['markets']:
                        # Logique spécifique pour Betfair (h2h_lay)

                        if bookmaker['key'] == 'betfair_ex_uk':
                            bet_limit_total = 0
                            for market in bookmaker['markets']:
                                for outcome in market['outcomes']:
                                    bet_limit_total += int(outcome['bet_limit'])
                                    combined_data[match_key][away_player]["Liquidite_total"] = bet_limit_total
                                    combined_data[match_key][home_player]["Liquidite_total"] = bet_limit_total

                        if bookmaker['key'] == 'betfair_ex_uk' and market['key'] == 'h2h_lay':
                            for outcome in market['outcomes']:
                                player_name_full = outcome['name']
                                player_name = player_name_full.split()[-1]  # Extraire le nom de famille
                                price = outcome['price']
                                bet_limit = outcome['bet_limit']
                                
                                if player_name_full == home_player_full:
                                    combined_data[match_key][home_player][bookmaker_name] = price
                                    combined_data[match_key][home_player]["Liquidite"] = bet_limit
                                elif player_name_full == away_player_full:
                                    combined_data[match_key][away_player][bookmaker_name] = price
                                    combined_data[match_key][away_player]["Liquidite"] = bet_limit
                        
                        # Autres bookmakers (h2h)
                        elif bookmaker['key'] != 'betfair_ex_uk' and market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                player_name_full = outcome['name']
                                player_name = player_name_full.split()[-1]  # Extraire le nom de famille
                                price = outcome['price']
                                
                                if player_name_full == home_player_full:
                                    combined_data[match_key][home_player][bookmaker_name] = price
                                elif player_name_full == away_player_full:
                                    combined_data[match_key][away_player][bookmaker_name] = price

        return combined_data, date_match



    def get_macths_tennis_paris_en_sport():
        # Code de la fonction existante
        print("Récupération des données depuis Parions sport...")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto("https://www.enligne.parionssport.fdj.fr/paris-tennis")

            page.wait_for_load_state("networkidle")

            # Attendre quelques secondes avant de cliquer sur le bouton
            time.sleep(3)
            
            # Gestion des cookies
            try:
                page.get_by_role("button", name="Continuer sans accepter").click()
            except:
                print("Bouton de cookies non trouvé ou déjà accepté")
            
            # Attendre que les événements se chargent
            page.wait_for_selector(".psel-event", timeout=10000)
            
            # Faire défiler la page pour charger tous les événements
            previous_height = 0
            current_height = page.evaluate("document.body.scrollHeight")
            
            # Boucle de défilement jusqu'à atteindre le bas de page
            while previous_height < current_height:
                # Défiler vers le bas
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # Attendre le chargement du contenu
                time.sleep(2)
                
                # Mettre à jour les hauteurs
                previous_height = current_height
                current_height = page.evaluate("document.body.scrollHeight")
            
            # Récupérer tous les événements après le défilement complet
            events = page.query_selector_all(".psel-event")
            
            # Structure de données finale
            data = {
                "key": "Paris_en_Sport",
                "title": "Paris_en_Sport",
                "last_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "markets": []
            }
            
            for event in events:
                # Récupérer le nom du tournoi
                tournament_elem = event.query_selector(".psel-event-info__competition")
                tournament = tournament_elem.inner_text() if tournament_elem else "Unknown Tournament"
                
                # Récupérer les noms des joueurs
                joueurs = event.query_selector_all(".psel-opponent__name")
                
                # Récupérer les cotes
                cotes = event.query_selector_all(".psel-outcome__data")
                
                if len(joueurs) >= 2 and len(cotes) >= 2:
                    joueur1 = joueurs[0].inner_text()
                    joueur2 = joueurs[1].inner_text()
                    
                    # Convertir les cotes en nombres flottants (remplacer la virgule par un point si nécessaire)
                    try:
                        cote1 = float(cotes[0].inner_text().replace(',', '.'))
                        cote2 = float(cotes[1].inner_text().replace(',', '.'))
                        
                        # Créer la structure pour ce match
                        match_data = {
                            "key": "h2h",
                            "last_update": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "outcomes": [
                                {
                                    "name": joueur1,
                                    "price": cote1
                                },
                                {
                                    "name": joueur2,
                                    "price": cote2
                                }
                            ],
                            "tournament": tournament
                        }
                        
                        # Ajouter à la liste des marchés
                        data["markets"].append(match_data)
                    except ValueError:
                        print(f"Erreur lors de la conversion des cotes pour {joueur1} vs {joueur2}")
            
            browser.close()
        
        return data


    def format_to_dict_structure_paris_en_sport(data):
        """
        Transforme les données de matchs de tennis au format demandé
        """
        if isinstance(data, str):
            data = json.loads(data)
            
        matches_dict = {}
        
        for match in data["markets"]:
            if len(match["outcomes"]) < 2:
                continue
                
            joueur1 = match["outcomes"][0]["name"]
            joueur2 = match["outcomes"][1]["name"]
            
            cote_joueur1 = match["outcomes"][0]["price"]
            cote_joueur2 = match["outcomes"][1]["price"]
            
            # Créer la clé du match (format: "Joueur1 vs Joueur2")
            match_key = f"{joueur1} vs {joueur2}"
            
            # Si ce match n'existe pas encore dans le dictionnaire, l'initialiser
            if match_key not in matches_dict:
                matches_dict[match_key] = {
                    joueur1: {},
                    joueur2: {}
                }
            
            # Ajouter les cotes pour les bookmakers
            matches_dict[match_key][joueur1]["Paris_en_Sport"] = cote_joueur1
            matches_dict[match_key][joueur2]["Paris_en_Sport"] = cote_joueur2
        

            # Normalisation des noms
            matches_dict = normaliser_noms_de_joueurs(matches_dict)

        return matches_dict


    def normaliser_noms_de_joueurs(paris_en_sport_dict):

        nouveau_dict = {}
        
        for match_key, match_data in paris_en_sport_dict.items():
            # Extraire les noms des joueurs depuis la clé du match
            joueurs_dans_match = match_key.split(" vs ")
            
            # Créer de nouvelles clés pour le match avec noms normalisés
            joueur1_initial = joueurs_dans_match[0]
            joueur2_initial = joueurs_dans_match[1]
            
            # Extraire les noms de famille (tout ce qui vient après le point)
            nom_joueur1 = joueur1_initial.split(".")[-1] if "." in joueur1_initial else joueur1_initial
            nom_joueur2 = joueur2_initial.split(".")[-1] if "." in joueur2_initial else joueur2_initial
            
            # Nouvelle clé de match
            nouveau_match_key = f"{nom_joueur1} vs {nom_joueur2}"
            nouveau_dict[nouveau_match_key] = {}
            
            # Copier les données des joueurs avec les noms normalisés
            for joueur_key, joueur_data in match_data.items():
                nom_joueur = joueur_key.split(".")[-1] if "." in joueur_key else joueur_key
                nouveau_dict[nouveau_match_key][nom_joueur] = joueur_data.copy()
        
        return nouveau_dict



    # Fonction pour extraire seulement le nom de famille (dernier mot)
    def extraire_nom_famille_unibet(nom_complet):
        # Divise le nom complet en mots et prend le dernier
        return nom_complet.split()[-1]

    # Fonction pour transformer le dictionnaire de matchs
    def formaliser_noms_joueurs_unibet(api_dict):
        nouveau_dict = {}
        
        for match_key, match_data in api_dict.items():
            # Création d'une nouvelle clé de match avec uniquement les noms de famille
            joueurs_match = match_key.split(" vs ")
            nom_famille_1 = extraire_nom_famille_unibet(joueurs_match[0])
            nom_famille_2 = extraire_nom_famille_unibet(joueurs_match[1])
            nouvelle_cle_match = f"{nom_famille_1} vs {nom_famille_2}"
            
            # Initialisation de l'entrée pour ce match
            nouveau_dict[nouvelle_cle_match] = {}
            
            # Transformation des données de chaque joueur
            for joueur_complet, cotes in match_data.items():
                nom_famille = extraire_nom_famille_unibet(joueur_complet)
                nouveau_dict[nouvelle_cle_match][nom_famille] = cotes
        
        return nouveau_dict


    def get_macths_tennis_unibet():
        print("Récupération des données depuis Unibet...")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto("https://www.unibet.fr/sport")
            
            page.wait_for_selector(".oddbox-label span")

            # Refuser les cookies si nécessaire
            try:
                page.get_by_role("button", name="Continuer sans accepter").click()
            except:
                print("Bouton de cookies non trouvé ou déjà géré")
            


            # Naviguer vers la section Tennis      
            page.locator("div").filter(has_text=re.compile(r"^Tennis$")).click()

            # Attendre que la navigation soit terminée
            page.wait_for_load_state("networkidle")
            
            # Faire défiler la page pour charger tous les matchs
            #print("Chargement de tous les matchs...")
            
            # Récupérer la hauteur initiale de la page
            last_height = page.evaluate("document.body.scrollHeight")
            
            while True:
                # Faire défiler jusqu'en bas
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # Attendre le chargement du contenu
                page.wait_for_timeout(2000)  # 2 secondes d'attente
                
                # Calculer la nouvelle hauteur
                new_height = page.evaluate("document.body.scrollHeight")
                
                # Si la hauteur n'a pas changé, on a atteint la fin
                if new_height == last_height:
                    # Tenter de cliquer sur "Voir plus" s'il existe
                    try:
                        voir_plus = page.locator("button").filter(has_text="Voir plus").first
                        if voir_plus:
                            voir_plus.click()
                            page.wait_for_timeout(2000)
                            continue
                    except:
                        break
                    break
                
                last_height = new_height
                #print("Chargement en cours... hauteur:", new_height)
            
            #print("Tous les matchs sont chargés!")
            
            # Récupérer tous les matchs
            card = page.query_selector(".eventsdays-list")
            matchs = card.query_selector_all(".eventcard--toplight")
            
            #print(f"Nombre de matchs trouvés: {len(matchs)}")
            
            # Extraction du texte de chaque match
            match_texts = [elem.inner_text() for elem in matchs]
            
            # Structure de base pour le résultat final
            result = {
                "key": "unibet",
                "title": "unibet",
                "last_update": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "markets": []
            }
            
            # Traiter chaque match
            for match_text in match_texts:
                lines = match_text.strip().split('\n')
                
                # Initialiser un marché h2h pour chaque match
                market = {
                    "key": "h2h",
                    "last_update": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "outcomes": []
                }
                
                # Variables pour stocker les informations extraites
                tournament = ""
                players = []
                odds = []
                
                # Extraire les informations pertinentes
                if lines:
                    tournament = lines[0]  # Premier élément est généralement le tournoi
                
                # Chercher les cotes (valeurs numériques)
                for i, line in enumerate(lines):
                    cleaned_line = line.replace(',', '.')
                    try:
                        value = float(cleaned_line)
                        if 1.01 <= value <= 100000000000.0:  # Intervalle de cotes typique
                            odds.append(value)
                    except ValueError:
                        # Identifier les joueurs (généralement de longues chaînes de caractères qui ne sont pas des cotes)
                        if i > 0 and len(line) > 3 and not any(c.isdigit() for c in line.replace(' ', '')[:3]):
                            # Exclure les lignes qui contiennent probablement une heure (format hh:mm)
                            if ':' not in line or len(line) > 8:
                                players.append(line)
                
                # Ne garder que les 2 premiers joueurs identifiés
                players = players[:2]
                
                # Créer les outcomes si nous avons suffisamment d'informations
                if len(players) >= 2 and len(odds) >= 2:
                    for i in range(2):
                        outcome = {
                            "name": players[i],
                            "price": odds[i]
                        }
                        market["outcomes"].append(outcome)
                    
                    # Ajouter le marché seulement s'il a au moins 2 outcomes
                    if len(market["outcomes"]) >= 2:
                        # Ajouter le nom du tournoi comme information supplémentaire
                        market["tournament"] = tournament
                        result["markets"].append(market)
            
            # Fermer le navigateur
            browser.close()
            
            # Afficher le résultat en format JSON
            # formatted_json = json.dumps(result, ensure_ascii=False, indent=2)

            return result

    def format_to_dict_structure_unibet(data):
        """
        Transforme les données de matchs de tennis au format demandé
        """
        if isinstance(data, str):
            data = json.loads(data)
            
        matches_dict = {}
        
        for match in data["markets"]:
            if len(match["outcomes"]) < 2:
                continue
                
            joueur1 = match["outcomes"][0]["name"]
            joueur2 = match["outcomes"][1]["name"]
            
            cote_joueur1 = match["outcomes"][0]["price"]
            cote_joueur2 = match["outcomes"][1]["price"]
            
            # Créer la clé du match (format: "Joueur1 vs Joueur2")
            match_key = f"{joueur1} vs {joueur2}"
            
            # Si ce match n'existe pas encore dans le dictionnaire, l'initialiser
            if match_key not in matches_dict:
                matches_dict[match_key] = {
                    joueur1: {},
                    joueur2: {}
                }
            
            # Ajouter les cotes pour les bookmakers
            matches_dict[match_key][joueur1]["Unibet"] = cote_joueur1
            matches_dict[match_key][joueur2]["Unibet"] = cote_joueur2

        matches_dict = formaliser_noms_joueurs_unibet(matches_dict)
        
        return matches_dict


    # API
    api_dict, date_match = get_combined_odds()
    #print(api_dict)

    # Parions sport
    tennis_data = get_macths_tennis_paris_en_sport()
    paris_en_sport_dict = format_to_dict_structure_paris_en_sport(tennis_data)
    #print(paris_en_sport_dict)

    # unibet
    tennis_data_unibet = get_macths_tennis_unibet()
    unibet_dict = format_to_dict_structure_unibet(tennis_data_unibet)
    #print(unibet_dict)



    def ajouter_cote_par_joueur(api_dict, joueur, bookmaker, cote):
        """ ajout valeur dans api_dict"""
        # Variable pour suivre si le joueur a été trouvé
        joueur_trouve = False

        # Parcourir tous les matchs
        for match_key, match_data in api_dict.items():
            # Vérifier si le joueur existe dans ce match
            if joueur in match_data:
                # Ajouter/mettre à jour la cote
                api_dict[match_key][joueur][bookmaker] = cote
                joueur_trouve = True
        
        # Message si le joueur n'a pas été trouvé
        if not joueur_trouve:
            print(f"Attention: Le joueur '{joueur}' n'a été trouvé dans aucun match.")
        
        return api_dict



    def get_macths_tennis_unibet_live():
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto("https://www.unibet.fr/sport")

            page.get_by_role("link", name="Paris en live").click()

            try :
                page.locator("#cps-livefiltersbar").get_by_role("listitem").filter(has_text="Tennis").click()
            except:
                print("Pas de match en live")
                return {}
            
            current_url = page.url
            
            page.wait_for_load_state("networkidle")

            # Attendre que les événements de tennis en direct apparaissent
            page.wait_for_selector(".live-event-list")
            
            # Extraire le contenu HTML directement de Playwright
            html_content = page.content()
            
            card_live = page.query_selector(".live-event-list")

            player_elements = card_live.query_selector_all(".oddbox-label span")
            odds_elements = card_live.query_selector_all(".oddbox-value span")

            players = [elem.inner_text() for elem in player_elements]
            odds = [elem.inner_text() for elem in odds_elements]

            # Nouveau format de données
            matches_data = {}

            for i in range(0, len(players), 2):
                # Vérification qu'il reste bien deux joueurs à traiter
                if i + 1 < len(players):
                    player1 = players[i]
                    player2 = players[i+1]
                    odd1 = float(odds[i].replace(',', '.'))  # Convertir en float et gérer la notation décimale française
                    odd2 = float(odds[i+1].replace(',', '.'))
                    
                    # Créer la clé du match (format "Joueur1 vs Joueur2")
                    match_key = f"{player1} vs {player2}"
                    
                    # Créer la structure pour ce match
                    matches_data[match_key] = {
                        player1: {
                            "Unibet": odd1
                        },
                        player2: {
                            "Unibet": odd2
                        }
                    }
            
            # Fermer le navigateur
            browser.close()

            matches_data = formaliser_noms_joueurs_unibet(matches_data)

        return matches_data


    def recupere_liste_match_live(data):

        tous_les_joueurs_live = []
        for match_name, match_data in data.items():
            # Le nom du match est au format "Joueur1 vs Joueur2"
            joueurs_du_match = list(match_data.keys()) # de la forme ['Zheng', 'Swiatek']
            tous_les_joueurs_live.extend(joueurs_du_match)

        return tous_les_joueurs_live

    card_live = get_macths_tennis_unibet_live()
    joueur_en_live = recupere_liste_match_live(card_live)


    #tous joueur api
    tous_les_joueurs_api = []
    for match_name, match_data in api_dict.items():
        # Le nom du match est au format "Joueur1 vs Joueur2"
        joueurs_du_match = list(match_data.keys()) # de la forme ['Zheng', 'Swiatek']
        tous_les_joueurs_api.extend(joueurs_du_match)

    # Créer une nouvelle liste contenant seulement les éléments de tous_les_joueurs_api qui ne sont pas dans joueur_en_live
    tous_les_joueurs_api = [nom for nom in tous_les_joueurs_api if nom not in joueur_en_live]



    #unibet
    for joueur in tous_les_joueurs_api:
        for match_name, match_data in unibet_dict.items():
            joueurs_unibet = list(match_data.keys())
            joueurs_unibet_valeur = list(match_data.values())

            for i in range(2):
                if joueur == joueurs_unibet[i]:
                    #print("le joueur unit", joueurs_unibet[i], "aparait dans joueur api",joueur)
                    #print(joueurs_unibet_valeur[i]["Unibet"])
                    api_dict = ajouter_cote_par_joueur(api_dict, joueurs_unibet[i], "Unibet", joueurs_unibet_valeur[i]["Unibet"])
                        


    #paris en sport
    for joueur in tous_les_joueurs_api:
        for match_name, match_data in paris_en_sport_dict.items():
            joueurs_paris_en_sport = list(match_data.keys())
            joueurs_paris_en_sport_valeur = list(match_data.values())

            for i in range(2):
                if joueur == joueurs_paris_en_sport[i]:
                    #print("le joueur unit", joueurs_paris_en_sport[i], "aparait dans joueur api",joueur)
                    #print(joueurs_paris_en_sport_valeur[i]["Paris_en_Sport"])

                    api_dict = ajouter_cote_par_joueur(api_dict, joueurs_paris_en_sport[i], "Paris_en_Sport", joueurs_paris_en_sport_valeur[i]["Paris_en_Sport"])



    def filtrer_matchs(data):
        """
        Enlever match en direct ou sans certains bookmakers essentiels
        """
        cles_essentielles = ["Betfair", "Liquidite", "Liquidite_total","Unibet", "Paris_en_Sport"]  # Clés absolument nécessaires
        cles_optionnelles = ["Betclic", "Winamax (FR)", "Pinnacle"]  # Au moins X parmi ces clés
        min_bookmakers = 1  # Nombre minimum de bookmakers optionnels requis
        
        # Créer un nouveau dictionnaire pour stocker les matchs filtrés
        matchs_filtres = {}
        
        # Parcourir tous les matchs
        for match_name, match_data in data.items():
            garder_match = True
            
            # Vérifier chaque joueur
            for joueur, cotes in match_data.items():
                # Vérifier si toutes les clés essentielles sont présentes
                if not all(cle in cotes for cle in cles_essentielles):
                    garder_match = False
                    break
                    
                # Compter combien de bookmakers optionnels sont présents
                nb_bookmakers = sum(1 for cle in cles_optionnelles if cle in cotes)
                if nb_bookmakers < min_bookmakers:
                    garder_match = False
                    break
            
            # Si tous les joueurs satisfont les conditions, garder le match
            if garder_match:
                matchs_filtres[match_name] = match_data
        
        return matchs_filtres


    #sans match en direct
    matchs_filtres = filtrer_matchs(api_dict)
    #print(date_match)

    # with open("api_format_json.json", "w", encoding="utf-8") as f:
    #     json.dump(matchs_filtres, f, ensure_ascii=False, indent=2)




    """ ENVOIE ET COMPARAISON """




    # Données Telegram
    BOT_TOKEN = "7717805476:AAEKFqtpQ4rnqFZqiUiyTgzuRGmspPbBYQ8"
    CHANNEL_ID = "-1002576116758"

    # Fonction pour envoyer un message à Telegram
    def send_telegram_message(message):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": message,
            "parse_mode": "HTML"  # Pour permettre le formatage basique
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de l'envoi du message Telegram: {e}")
            return None

    # Charger le fichier JSON
    data = matchs_filtres

    # Fonction pour calculer l'EV (Expected Value)
    def calculate_ev(betfair_odds, other_odds):
        return ((other_odds / betfair_odds) - 1) * 100

    # Parcourir chaque match
    for match, teams in data.items():
        # Décomposer le nom du match pour obtenir les joueurs
        players = match.split(" vs ")
        
        # Vérifier pour chaque joueur
        for player, odds in teams.items():
            betfair_odds = odds.get("Betfair")
            liquidity = odds.get("Liquidite", "?")
            liquidity_total = odds.get("Liquidite_total", "?")
            pinnacle_odds = odds.get("Pinnacle", "N/A")
            
            # Variable pour suivre si une alerte est nécessaire
            alert_needed = False
            
            # Vérifier si au moins un bookmaker a une cote supérieure à Betfair
            for bookmaker, odd in odds.items():
                if bookmaker not in ["Betfair", "Liquidite", "Liquidite_total", "Pinnacle"] and odd > betfair_odds:
                    alert_needed = True
                    break
            
            # Si une alerte est nécessaire, la préparer et l'envoyer
            if alert_needed:
                opponent = players[1] if player == players[0] else players[0]
                
                # Formatage du match
                match_display = f"{opponent} vs {player}"

                for match, temps in date_match.items():
                    if match == match_display:
                        match_time = temps
                        break
                    else:
                        match_time = "Erreur dans récuperation date"
                
                # Construire le message
                message = f"🎾 [ATP] Value détectée !\n"
                message += f"📊 Match : {match_display}\n"
                message += f"⏰ Début : {match_time}\n"
                message += f"💰 Liquidité totale du match: {liquidity_total}€\n\n"
                message += f"▶️ {player}\n"
                message += f"- Betfair : {betfair_odds} | Liquidité: {liquidity}€\n"
                message += f"- Pinnacle : {pinnacle_odds}\n\n"
                
                # Collecter les autres bookmakers pour les trier
                bookmaker_odds = []
                for bookmaker, odd in odds.items():
                    if bookmaker not in ["Betfair", "Liquidite", "Liquidite_total", "Pinnacle"]:
                        # Gérer les différents noms de bookmakers
                        if bookmaker == "Paris_en_Sport":
                            display_name = "PSEL/ZeBet"
                        elif bookmaker == "Winamax (FR)":
                            display_name = "Winamax"
                        else:
                            display_name = bookmaker
                        
                        bookmaker_odds.append((display_name, odd))
                
                # Trier les bookmakers par ordre décroissant des cotes
                bookmaker_odds.sort(key=lambda x: x[1], reverse=True)
                
                # Ajouter les bookmakers triés au message
                for display_name, odd in bookmaker_odds:
                    if odd > betfair_odds:
                        emoji = "🟢"
                        ev = calculate_ev(betfair_odds, odd)
                        message += f"{emoji} {display_name} : {odd} | Ev +{ev:.2f}%\n"
                    elif odd == betfair_odds:
                        emoji = "🟡"
                        message += f"{emoji} {display_name} : {odd}\n"
                    else:
                        emoji = "🔴"
                        message += f"{emoji} {display_name} : {odd}\n"
                
                # Envoyer le message à Telegram
                send_telegram_message(message)
                
                # Attendre un peu pour éviter de spammer l'API Telegram
                time.sleep(1)
    print("Attente 5min")
    time.sleep(300)
