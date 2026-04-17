# 🏀 Stat NLQ

A Natural Language Interface to a Database (NLIDB) that translates conversational English queries about basketball statistics directly into executed SQL queries. 

Built strictly with **Classical/Statistical Machine Learning** architectures (no LLMs APIs like OpenAI or Gemini were used), this project highlights the inner workings of query interpretation, entity extraction, and structured database traversal.

## 🚀 Overview

The application features a fully modular Natural Language Processing (NLP) pipeline which interprets queries, parses dynamic slots, executes dynamically generated SQLite statements, and presents output nicely rendered in a **Streamlit** UI frontend context.

The database is populated intelligently through local CSV aggregations encompassing the latest season records (or the NBA API) and caches everything systematically.

## 🧠 Architecture & The NLP Pipeline

Every query the user enters passes through a strict sequential 4-step NLP pipeline:

### 1. Intent Classification (SVM)
Determine which pre-written SQL structure/heuristic applies to the query. 
* **Mechanism:** Queries are passed through a `TF-IDF Vectorizer` to generate an N-dimensional vocabulary matrix. A supervised `Linear Support Vector Machine (LinearSVC)` categorizes the query.
* **Target Classes:** `Intent_SinglePlayer`, `Intent_TeamAgg`, `Intent_Leaderboard`, and `Intent_OOD` (Out of Domain).

### 2. Named Entity Recognition (CRF)
We use sequence labeling to parse and dynamically extract parameters needed to satisfy the SQL.
* **Mechanism:** Tokens are annotated using a **Conditional Random Field (CRF)** model (`sklearn-crfsuite`). 
* **Tagging Strategy:** Features are extracted based on word syntax, suffixes, and casing. We rely heavily on the **BIO (Begin, In, Out)** schema.
* **Entities:** `[PLAYER]`, `[TEAM]`, `[STAT]`, `[DATE]`, `[WINDOW]`

### 3. Validation Gates
Language is inherently fuzzy. Thus, extracted entities must be cross-verified before database interaction.
* **Intent Threshold Gate:** SVM confidence score must clear a probability threshold (`> 60%`), otherwise the UI rejects it gracefully.
* **Entity Validation:** Uses **Fuzzy String Matching (FuzzyWuzzy Levenshtein distance)** against cached SQLite table datasets (e.g., verifying that "Steph Curry" correctly matches `Stephen Curry` within the un-nested box score DB schema).
* **Vocabulary Mappings:** Converts slang like "dimes" or "buckets" into precise schema strings `ast` or `pts`. Employs defensive regex parsing for phrases like `last 4 games`.

### 4. Code Generation & Execution
Safely injects validated slots into contextual SQL layouts based on the SVM Intent. Subqueries and aggregate logic accurately execute complex queries inside the `player_box_scores` SQLite space without risking generic limit breakdowns. Handled and cleanly returned via `pandas.DataFrame`.

## 🛠 Project Structure

```bash
nba-stats-nlidb/
│
├── app.py                      # Main Streamlit Graphical Interface
├── data_pipeline/
│   └── fetch_nba_data.py       # Reads datasets, formats, & seeds the SQLite db
├── nlp_engine/
│   ├── generate_data.py        # Generates synthetic queries & automated BIO labels
│   ├── train_models.py         # Trains and serializes the TF-IDF SVM & NER CRF models
│   ├── pipeline.py             # Inference pipeline routing, extraction, validation gates
│   └── query_builder.py        # Entity-to-SQL compiler
├── data/
│   └── box_scores.db           # SQLite runtime local database
├── models/                     # Model artifacts (*.pkl)
└── requirements.txt
```

## ⚙️ Setup & Deployment

1. **Environment Sandbox:**
Ensure you have `python3` running, establish a virtual execution environment, and install base packages:
```bash
python3 -m venv .venv
source ./.venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

2. **Run Initialization Scripts:**
These scripts will build the database from datasets, construct the synthetic training instances, train the Classical ML model components, and serialize them:
```bash
python data_pipeline/fetch_nba_data.py
python nlp_engine/generate_data.py
python nlp_engine/train_models.py
```

3. **Start the Interface:**
```bash
streamlit run app.py
```

## Example Queries
* "LeBron James points last game"
* "Steph Curry statline last 4 games"
* "Lakers total rebounds last 3 games"
* "Who scored the most points for the Warriors yesterday?"
