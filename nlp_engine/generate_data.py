import random
import json
import os
import re

players = ["LeBron James", "Steph Curry", "Kevin Durant", "Anthony Edwards", "Luka Doncic", "Nikola Jokic", "Jayson Tatum"]
teams = ["Lakers", "Warriors", "LAL", "GSW", "Celtics", "BOS", "Nuggets", "DEN"]
stats = ["points", "pts", "buckets", "assists", "ast", "dimes", "rebounds", "reb", "boards", "statline", "stats"]
dates = ["tonight", "last game", "yesterday", "2024-10-25", "on 2024-11-01"]
windows = ["last 3 games", "past 5 games", "last 10 games", "past 2 games"]

templates = [
    ("[PLAYER] [STAT] [DATE]", "Intent_SinglePlayer"),
    ("How many [STAT] did [PLAYER] get [DATE]?", "Intent_SinglePlayer"),
    ("what is [PLAYER] [STAT] in [WINDOW]?", "Intent_SinglePlayer"),
    ("[PLAYER] [STAT] [WINDOW]", "Intent_SinglePlayer"),
    
    ("What were the [TEAM] [STAT] [DATE]?", "Intent_TeamAgg"),
    ("[TEAM] total [STAT] [WINDOW]?", "Intent_TeamAgg"),
    ("how many [STAT] for [TEAM] [DATE]?", "Intent_TeamAgg"),
    
    ("Who scored the most [STAT] for the [TEAM] [DATE]?", "Intent_Leaderboard"),
    ("most [STAT] [TEAM] [WINDOW]?", "Intent_Leaderboard"),
    ("who had the highest [STAT] [DATE]?", "Intent_Leaderboard")
]

ood_sentences = [
    "what time is it in New York?",
    "tell me a joke",
    "how to bake a cake",
    "who is the president",
    "weather tomorrow"
]

def generate_dataset(num_samples=1000, out_path='data/training_data.json'):
    dataset = []
    
    for _ in range(num_samples):
        if random.random() < 0.1: # 10% OOD
            text = random.choice(ood_sentences)
            tokens = re.findall(r"[\w']+|[.,!?;]", text.lower())
            tags = ["O"] * len(tokens)
            dataset.append({
                "text": text,
                "tokens": tokens,
                "tags": tags,
                "intent": "Intent_OOD"
            })
            continue

        template, intent = random.choice(templates)
        
        # We need to map tokens to tags
        # Replace placeholders with random choices, but remember mapping
        replacements = {
            "[PLAYER]": random.choice(players),
            "[TEAM]": random.choice(teams),
            "[STAT]": random.choice(stats),
            "[DATE]": random.choice(dates),
            "[WINDOW]": random.choice(windows)
        }
        
        text = template
        for k, v in replacements.items():
            text = text.replace(k, v)
        
        # Basic tokenization
        tokens = re.findall(r"[\w'-]+|[.,!?;]", text.lower())
        tags = ["O"] * len(tokens)
        
        # Find index of generated words to label them
        # Note: A smarter way is to tokenize the choices as well and find sublists
        def find_and_tag(target_str, label):
            target_tokens = re.findall(r"[\w'-]+|[.,!?;]", target_str.lower())
            # Find sublist
            for i in range(len(tokens) - len(target_tokens) + 1):
                if tokens[i:i+len(target_tokens)] == target_tokens:
                    # check if already tagged to avoid overlaps
                    if all(t == "O" for t in tags[i:i+len(target_tokens)]):
                        tags[i] = f"B-{label}"
                        for j in range(1, len(target_tokens)):
                            tags[i+j] = f"I-{label}"
                        break

        if "[PLAYER]" in template: find_and_tag(replacements["[PLAYER]"], "PLAYER")
        if "[TEAM]" in template: find_and_tag(replacements["[TEAM]"], "TEAM")
        if "[STAT]" in template: find_and_tag(replacements["[STAT]"], "STAT")
        if "[DATE]" in template: find_and_tag(replacements["[DATE]"], "DATE")
        if "[WINDOW]" in template: find_and_tag(replacements["[WINDOW]"], "WINDOW")
            
        dataset.append({
            "text": text,
            "tokens": tokens,
            "tags": tags,
            "intent": intent
        })
        
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(dataset, f, indent=2)
    print(f"Generated {num_samples} samples at {out_path}")

if __name__ == "__main__":
    generate_dataset(2000)
