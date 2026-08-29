import sqlite3

DB_PATH = "arcade_database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            score INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 50,
            wins INTEGER DEFAULT 0,
            matches INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_player(user_id, name="Player"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id, name, score, coins, wins, matches, streak FROM players WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    if not row:
        c.execute('INSERT INTO players (user_id, name, score, coins, wins, matches, streak) VALUES (?, ?, 0, 50, 0, 0, 0)', (user_id, name))
        conn.commit()
        row = (user_id, name, 0, 50, 0, 0, 0)
    conn.close()
    return {"id": row[0], "name": row[1], "score": row[2], "coins": row[3], "wins": row[4], "matches": row[5], "streak": row[6]}

def add_stats(user_id, name, score_add=0, coins_add=0, is_win=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    p = get_player(user_id, name)
    new_score = p['score'] + score_add
    new_coins = p['coins'] + coins_add
    new_wins = p['wins'] + (1 if is_win else 0)
    new_matches = p['matches'] + 1
    new_streak = (p['streak'] + 1) if is_win else 0
    c.execute('''
        UPDATE players 
        SET name = ?, score = ?, coins = ?, wins = ?, matches = ?, streak = ?
        WHERE user_id = ?
    ''', (name, new_score, new_coins, new_wins, new_matches, new_streak, user_id))
    conn.commit()
    conn.close()

def get_leaderboard(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name, score, wins, coins FROM players ORDER BY score DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_rank_badge(score):
    if score >= 500: return "👑 LEGEND"
    elif score >= 300: return "💎 DIAMOND"
    elif score >= 150: return "🥇 GOLD"
    elif score >= 50: return "🥈 SILVER"
    return "🥉 BRONZE"
  
