import pandas as pd
import sqlite3
import os

def load_and_clean_data(details_path='datasets/games_details.csv', games_path='datasets/games.csv'):
    print("Loading CSV datasets...")
    # Read files
    try:
        details_df = pd.read_csv(details_path, low_memory=False)
        games_df = pd.read_csv(games_path)
    except Exception as e:
        print(f"Error reading CSVs: {e}")
        return None

    print(f"details_df shape: {details_df.shape}")
    print(f"games_df shape: {games_df.shape}")

    # Extract needed columns from details
    details_cols = ['GAME_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'PTS', 'AST', 'REB', 'FGM', 'FGA']
    details_sub = details_df[details_cols].copy()
    
    # Extract date from games
    games_cols = ['GAME_ID', 'GAME_DATE_EST']
    games_sub = games_df[games_cols].copy()

    # Merge on GAME_ID
    merged_df = pd.merge(details_sub, games_sub, on='GAME_ID', how='inner')
    
    # Rename columns to match db schema
    column_mapping = {
        'GAME_ID': 'game_id',
        'GAME_DATE_EST': 'date',
        'PLAYER_NAME': 'player_name',
        'TEAM_ABBREVIATION': 'team_abbreviation',
        'PTS': 'pts',
        'AST': 'ast',
        'REB': 'reb',
        'FGM': 'fgm',
        'FGA': 'fga'
    }
    merged_df = merged_df.rename(columns=column_mapping)
    
    # Drop rows without names or dates
    merged_df = merged_df.dropna(subset=['game_id', 'date', 'player_name', 'team_abbreviation'])
    
    # Fill NA for stats with 0
    stat_cols = ['pts', 'ast', 'reb', 'fgm', 'fga']
    merged_df[stat_cols] = merged_df[stat_cols].fillna(0)
    
    # Format date
    merged_df['date'] = pd.to_datetime(merged_df['date']).dt.strftime('%Y-%m-%d')
    merged_df.sort_values(by='date', ascending=False, inplace=True)
    
    # Take latest 50,000 records (about 2 seasons) to ensure speedy SQL lookups
    merged_df = merged_df.head(50000)
    
    print(f"Cleaned data shape: {merged_df.shape}")
    return merged_df

def save_to_sqlite(df, db_path='data/box_scores.db'):
    if df is None:
        print("No dataframe to save.")
        return
        
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    df.to_sql('player_box_scores', conn, if_exists='replace', index=False)
    conn.close()
    print(f"Saved to SQLite database at {db_path}")

if __name__ == "__main__":
    df = load_and_clean_data()
    save_to_sqlite(df)
