import pandas as pd
import sqlite3

def get_stats_columns(stat_arg):
    if stat_arg == "*":
        return "SUM(pts) as POINTS, SUM(ast) as ASSISTS, SUM(reb) as REBOUNDS, SUM(fgm) as FGM, SUM(fga) as FGA"
    return f"SUM({stat_arg}) as {stat_arg.upper()}"

def generate_and_execute_sql(validated_data, db_path='data/box_scores.db'):
    if "error" in validated_data:
        return validated_data
    
    intent = validated_data["intent"]
    entities = validated_data["entities"]
    
    player = entities.get("PLAYER")
    team = entities.get("TEAM")
    stat = entities.get("STAT") or "*"
    window = entities.get("WINDOW")
    
    try:
        conn = sqlite3.connect(db_path)
    except Exception as e:
        return {"error": "Database connection error", "details": str(e)}

    query = ""
    
    date_constraint = entities.get("DATE")
    is_single_date = (window == 1) or (date_constraint is not None)
    
    if intent == "Intent_SinglePlayer":
        if player is None:
            return {"error": "Missing player name for single player query."}
            
        stat_select = "*" if stat == "*" else f"player_name as PLAYER, {stat} as {stat.upper()}"
        date_select = "" if stat == "*" else "date as DATE, "
        
        query = f"SELECT {date_select} {stat_select} FROM player_box_scores WHERE player_name = '{player}'"
        
        if date_constraint:
             query += f" AND date = '{date_constraint}'"
        
        if window:
            query += f" ORDER BY date DESC LIMIT {window}"
            
    elif intent == "Intent_TeamAgg":
        if team is None:
            return {"error": "Missing team abbreviation for team query."}
            
        stat_select = get_stats_columns(stat)
        date_select = "MAX(date) as DATE, " if is_single_date else ""
        
        query = f"SELECT {date_select}'{team}' as TEAM, {stat_select} FROM player_box_scores WHERE team_abbreviation = '{team}'"
        
        if date_constraint:
            query += f" AND date = '{date_constraint}'"
            
        if window:
            query += f" AND date IN (SELECT DISTINCT date FROM player_box_scores WHERE team_abbreviation = '{team}' ORDER BY date DESC LIMIT {window})"
            
    elif intent == "Intent_Leaderboard":
        if team is None:
            return {"error": "Missing team abbreviation for leaderboard query."}
        
        stat_select = get_stats_columns(stat)
        order_col = stat.upper() if stat != '*' else 'POINTS'
        date_select = "MAX(date) as DATE, " if is_single_date else ""
        
        query = f"SELECT {date_select}player_name as PLAYER, {stat_select} FROM player_box_scores WHERE team_abbreviation = '{team}'"
        
        if date_constraint:
            query += f" AND date = '{date_constraint}'"
            
        if window:
             query += f" AND date IN (SELECT DISTINCT date FROM player_box_scores WHERE team_abbreviation = '{team}' ORDER BY date DESC LIMIT {window})"
        
        query += f" GROUP BY player_name ORDER BY {order_col} DESC LIMIT 5"
        
    else:
        return {"error": f"Unhandled intent: {intent}"}

    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        return {"success": True, "dataframe": df, "query": query}
    except Exception as e:
        conn.close()
        return {"error": "SQL Execution error", "details": str(e), "query": query}
