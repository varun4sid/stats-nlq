import sqlite3
import joblib
import pandas as pd
from fuzzywuzzy import process
import re
from nlp_engine.train_models import sent2features

STAT_MAP = {
    "points": "pts", "pts": "pts", "buckets": "pts",
    "assists": "ast", "ast": "ast", "dimes": "ast",
    "rebounds": "reb", "reb": "reb", "boards": "reb",
    "field goals": "fgm", "fgm": "fgm",
    "shots": "fga", "fga": "fga"
}

valid_players = []
valid_teams = []

def load_db_cache():
    global valid_players, valid_teams
    try:
        conn = sqlite3.connect('data/box_scores.db')
        valid_players = pd.read_sql_query("SELECT DISTINCT player_name FROM player_box_scores", conn)['player_name'].tolist()
        valid_teams = pd.read_sql_query("SELECT DISTINCT team_abbreviation FROM player_box_scores", conn)['team_abbreviation'].tolist()
        conn.close()
    except Exception as e:
        print("Database not loaded yet or missing.")

intent_clf = None
ner_crf = None

def load_models():
    global intent_clf, ner_crf
    try:
        intent_clf = joblib.load('models/intent_clf.pkl')
        ner_crf = joblib.load('models/ner_crf.pkl')
    except Exception as e:
        print("Models not found. Did you run train_models.py?")

def tokenize(text):
    return re.findall(r"[\w'-]+|[.,!?;]", text.lower())

def process_query(text):
    if not intent_clf or not ner_crf:
        load_models()
    if not valid_players or not valid_teams:
        load_db_cache()

    # Predict Intent
    probs = intent_clf.predict_proba([text])[0]
    classes = intent_clf.classes_
    max_prob_idx = probs.argmax()
    intent = classes[max_prob_idx]
    confidence = probs[max_prob_idx]

    if confidence < 0.60:
        return {"error": "I couldn't understand that query. Can you clarify?", "confidence": confidence}

    if intent == "Intent_OOD":
        return {"error": "This seems out of domain. Please ask about basketball stats.", "confidence": confidence}

    # NER Extraction
    tokens = tokenize(text)
    features = [sent2features(tokens)]
    tags = ner_crf.predict(features)[0]

    entities = {"PLAYER": None, "TEAM": None, "STAT": None, "DATE": None, "WINDOW": None}
    
    current_entity = []
    current_label = None

    def save_entity():
        if current_label and current_entity:
            entity_val = " ".join(current_entity)
            if entities[current_label] is None:
                entities[current_label] = entity_val
            else:
                 entities[current_label] += f" {entity_val}"

    for token, tag in zip(tokens, tags):
        if tag.startswith("B-"):
            save_entity()
            current_label = tag[2:]
            current_entity = [token]
        elif tag.startswith("I-") and current_label == tag[2:]:
            current_entity.append(token)
        else:
            save_entity()
            current_label = None
            current_entity = []
    save_entity()

    # Defensive fallback for brittle NER on windows
    if not entities["WINDOW"]:
        text_lower = text.lower()
        window_match = re.search(r'(?:last|past)\s+(\d+)\s+games?', text_lower)
        if window_match:
            entities["WINDOW"] = int(window_match.group(1))
        elif "last game" in text_lower or "past game" in text_lower:
            entities["WINDOW"] = 1

    # Validation Gates
    if entities["STAT"]:
        if entities["STAT"] in ["*", "statline", "stats", "game"]:
            entities["STAT"] = "*"
        else:
            mapped_stat = STAT_MAP.get(entities["STAT"])
            if mapped_stat:
                entities["STAT"] = mapped_stat
            else:
                return {"error": f"Stat '{entities['STAT']}' is not supported.", "intent": intent}
    
    if entities["PLAYER"] and valid_players:
        match, score = process.extractOne(entities["PLAYER"], valid_players)
        if score > 70:
            entities["PLAYER"] = match
        else:
             return {"error": f"Player '{entities['PLAYER']}' not found in database.", "intent": intent}

    if entities["TEAM"] and valid_teams:
        # A simple check: if length is 3, try uppercase match.
        search_team = entities["TEAM"].upper() if len(entities["TEAM"]) <= 3 else entities["TEAM"].title()
        match, score = process.extractOne(search_team, valid_teams)
        if score > 50:
            entities["TEAM"] = match
        else:
             return {"error": f"Team '{entities['TEAM']}' not found.", "intent": intent}

    if entities["WINDOW"]:
        num = re.search(r'\d+', str(entities["WINDOW"]))
        if num:
            window_val = int(num.group())
            if window_val > 10:
                print("Warning: Window clamped to 10")
                window_val = 10
            entities["WINDOW"] = window_val
        elif "last game" in str(entities["WINDOW"]).lower():
            entities["WINDOW"] = 1
        else:
            entities["WINDOW"] = None 

    if entities["DATE"]:
        date_str = entities["DATE"].lower()
        if "last game" in date_str and not entities["WINDOW"]:
             entities["WINDOW"] = 1
             entities["DATE"] = None
        elif re.search(r'\d{4}-\d{2}-\d{2}', date_str):
             entities["DATE"] = re.search(r'\d{4}-\d{2}-\d{2}', date_str).group()
        else:
             # Unmapped colloquial date, ignore or just treat as no date constraint
             entities["DATE"] = None

    return {
        "intent": intent,
        "confidence": confidence,
        "entities": entities
    }
