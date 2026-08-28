import os
import random
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from data import GUESS_DB, SCRAMBLE_WORDS, QUIZ_DB

# --- 1. Web Server for 24/7 Hosting ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "⚡ Arcade Arena Game Bot is Online 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- 2. State & Scores ---
ttt_games = {}
active_guess = {}      # chat_id: { 'answer': str, 'display': str, 'cat': str }
active_scramble = {}   # chat_id: { 'word': str }
active_quiz = {}       # chat_id: { 'ans': int, 'options': list }
mines_games = {}       # game_id: { 'board': list, 'mines': set, 'player': id, 'name': str, 'diamonds': int }
scores = {}            # user_id: { 'name': str, 'score': int }

def add_score(user_id, name, pts=10):
    if user_id not in scores:
        scores[user_id] = {"name": name, "score": 0}
    scores[user_id]["score"] += pts

# --- 3. Main Menu ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_pts = scores.get(user.id, {}).get("score", 0)

    msg = (
        "╔══════════════════════════════════════╗\n"
        "   ⚡  A R C A D E   A R E N A   ⚡\n"
        "╚══════════════════════════════════════╝\n"
        f"👤 *Player:* `{user.first_name}`\n"
        f"🏆 *Your Points:* `{user_pts} PTS`\n"
        "────────────────────────────────────────\n"
        "🎯 *SELECT YOUR GAME MODE:* 👇"
    )

    kb = [
        [
            InlineKeyboardButton("1️⃣ Tic Tac Toe ⚔️", callback_data="menu_ttt"),
            InlineKeyboardButton("2️⃣ Guess Master 🎬🏏", callback_data="menu_guess")
        ],
        [
            InlineKeyboardButton("3️⃣ Word Battles 🔤", callback_data="menu_word"),
            InlineKeyboardButton("4️⃣ CBSE Quiz / PYQ 🧠", callback_data="menu_quiz")
        ],
        [
            InlineKeyboardButton("5️⃣ Mines Diamond 💎💣", callback_data="menu_mines"),
            InlineKeyboardButton("🏆 Leaderboard 📊", callback_data="menu_board")
        ]
    ]

    if update.message:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

# --- 4. Tic Tac Toe Helpers ---
def check_ttt_winner(b):
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for x, y, z in wins:
        if b[x] == b[y] == b[z] and b[x] != " ": return b[x]
    return "Draw" if " " not in b else None

def minimax(b, depth, is_max):
    res = check_ttt_winner(b)
    if res == "O": return 10 - depth
    if res == "X": return depth - 10
    if res == "Draw": return 0
    best = -1000 if is_max else 1000
    for i in range(9):
        if b[i] == " ":
            b[i] = "O" if is_max else "X"
            val = minimax(b, depth + 1, not is_max)
            b[i] = " "
            best = max(best, val) if is_max else min(best, val)
    return best

def get_best_ai_move(board, diff):
    empty = [i for i, v in enumerate(board) if v == " "]
    if diff == "easy" or (diff == "medium" and random.random() < 0.5):
        return random.choice(empty)
    best_val, best_move = -1000, empty[0]
    for i in empty:
        board[i] = "O"
        move_val = minimax(board, 0, False)
        board[i] = " "
        if move_val > best_val: best_val, best_move = move_val, i
    return best_move

def render_ttt_board(game_id):
    b = ttt_games[game_id]['board']
    icons = {"X": "❌", "O": "⭕", " ": "⬜"}
    kb = [[InlineKeyboardButton(icons[b[r*3+c]], callback_data=f"ttt_move_{game_id}_{r*3+c}") for c in range(3)] for r in range(3)]
    kb.append([InlineKeyboardButton("🏳️ End Match", callback_data=f"ttt_quit_{game_id}")])
    return InlineKeyboardMarkup(kb)

def render_mines_board(game_id):
    g = mines_games[game_id]
    kb = []
    for r in range(3):
        row = []
        for c in range(3):
            idx = r * 3 + c
            val = g['board'][idx]
            txt = "💎" if val == "D" else ("💣" if val == "M" else "❓")
            row.append(InlineKeyboardButton(txt, callback_data=f"mines_click_{game_id}_{idx}"))
        kb.append(row)
    kb.append([
        InlineKeyboardButton("💰 Cash Out", callback_data=f"mines_cashout_{game_id}"),
        InlineKeyboardButton("🏳️ Quit", callback_data=f"mines_quit_{game_id}")
    ])
    return InlineKeyboardMarkup(kb)

# --- 5. Callback Routing ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    chat_id = update.effective_chat.id

    if data == "menu_main":
        await start(update, context)
        return

    # Leaderboard
    if data == "menu_board":
        if not scores:
            text = "🏆 *LEADERBOARD*\n\nAbhi tak kisi ke points nahi hain! Games khelo."
        else:
            sorted_s = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
            text = "╔══════════════════════════════════════╗\n"
            text += "   🏆  A R C A D E   L E A D E R S  🏆\n"
            text += "╚══════════════════════════════════════╝\n\n"
            for i, p in enumerate(sorted_s[:10], 1):
                badge = "👑" if i == 1 else f"{i}."
                text += f"{badge} *{p['name']}* — `{p['score']} PTS`\n"
        kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    # --- TTT Logic ---
    if data == "menu_ttt":
        kb = [
            [InlineKeyboardButton("🤖 Play vs AI", callback_data="ttt_opt_ai")],
            [InlineKeyboardButton("👥 Play vs Friend (Group)", callback_data="ttt_opt_pvp")],
            [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]
        ]
        await query.edit_message_text("❌⭕ *TIC TAC TOE ARENA*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if data == "ttt_opt_ai":
        kb = [
            [InlineKeyboardButton("🟢 Easy", callback_data="ttt_start_ai_easy")],
            [InlineKeyboardButton("🟡 Medium", callback_data="ttt_start_ai_medium")],
            [InlineKeyboardButton("🔴 Hard (Unbeatable)", callback_data="ttt_start_ai_hard")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_ttt")]
        ]
        await query.edit_message_text("🤖 *Select AI Difficulty:*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if data.startswith("ttt_start_ai_"):
        diff = data.replace("ttt_start_ai_", "")
        gid = f"ai_{user.id}_{random.randint(100,999)}"
        ttt_games[gid] = {'board': [" "]*9, 'turn': 'X', 'mode': 'ai', 'p1': user.id, 'p1_name': user.first_name, 'difficulty': diff}
        await query.edit_message_text(f"🤖 *MATCH VS BOT ({diff.upper()})*\n👉 Your turn (❌)!", reply_markup=render_ttt_board(gid), parse_mode="Markdown")
        return

    if data == "ttt_opt_pvp":
        gid = f"pvp_{random.randint(1000,9999)}"
        ttt_games[gid] = {'board': [" "]*9, 'turn': 'X', 'mode': 'pvp', 'p1': user.id, 'p1_name': user.first_name, 'p2': None, 'p2_name': None}
        await query.edit_message_text(f"⚔️ *1v1 LOBBY*\nHost: `{user.first_name}` (❌)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚔️ Join", callback_data=f"ttt_join_{gid}")]]), parse_mode="Markdown")
        return

    if data.startswith("ttt_join_"):
        gid = data.replace("ttt_join_", "")
        if gid not in ttt_games or ttt_games[gid]['p2'] is not None:
            await query.answer("Lobby unavailable!")
            return
        g = ttt_games[gid]
        g['p2'], g['p2_name'] = user.id, user.first_name
        await query.edit_message_text(f"⚔️ `{g['p1_name']}` vs `{g['p2_name']}`\n👉 Turn: {g['p1_name']}", reply_markup=render_ttt_board(gid), parse_mode="Markdown")
        return

    if data.startswith("ttt_move_"):
        _, _, gid, idx = data.split("_")
        idx = int(idx)
        if gid not in ttt_games:
            await query.answer("Game over!")
            return
        g = ttt_games[gid]
        if (g['mode'] == 'ai' and user.id != g['p1']) or (g['mode'] == 'pvp' and user.id != (g['p1'] if g['turn'] == 'X' else g['p2'])):
            await query.answer("Aapki turn nahi hai!")
            return
        if g['board'][idx] != " ":
            await query.answer("Box already filled!")
            return

        g['board'][idx] = g['turn']
        win = check_ttt_winner(g['board'])
        if win:
            msg = "🤝 Match Draw!" if win == "Draw" else f"🎉 *Winner: {g['p1_name'] if win=='X' else g['p2_name']}!*"
            if win != "Draw": add_score(user.id, user.first_name, 15)
            del ttt_games[gid]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Play Again", callback_data="menu_ttt")]]), parse_mode="Markdown")
            return

        if g['mode'] == 'ai':
            ai_idx = get_best_ai_move(g['board'], g['difficulty'])
            g['board'][ai_idx] = "O"
            ai_win = check_ttt_winner(g['board'])
            if ai_win:
                del ttt_games[gid]
                await query.edit_message_text("💀 Bot jeet gaya!" if ai_win == "O" else "🤝 Draw!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Play Again", callback_data="menu_ttt")]]), parse_mode="Markdown")
                return
            await query.edit_message_text(f"🤖 Turn: `{g['p1_name']}` (❌)", reply_markup=render_ttt_board(gid), parse_mode="Markdown")
        else:
            g['turn'] = "O" if g['turn'] == "X" else "X"
            await query.edit_message_text(f"👉 Turn: `{g['p1_name'] if g['turn']=='X' else g['p2_name']}` ({g['turn']})", reply_markup=render_ttt_board(gid), parse_mode="Markdown")
        return

    if data.startswith("ttt_quit_"):
        ttt_games.pop(data.replace("ttt_quit_", ""), None)
        await query.edit_message_text("Match Ended!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]))
        return

    # --- Guess Master Logic ---
    if data == "menu_guess":
        kb = [
            [InlineKeyboardButton("🏏 Cricket", callback_data="guess_start_cricket")],
            [InlineKeyboardButton("🎬 Movies", callback_data="guess_start_movie")],
            [InlineKeyboardButton("⛩️ Anime", callback_data="guess_start_anime")],
            [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]
        ]
        await query.edit_message_text("🎯 *GUESS MASTER*\nCategory choose karo:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if data.startswith("guess_start_"):
        cat = data.replace("guess_start_", "")
        item = random.choice(GUESS_DB[cat])
        active_guess[chat_id] = {'answer': item['answer'], 'display': item['display'], 'cat': cat}
        msg = f"╔══════════════════════════════════════╗\n   🎯 GUESS MASTER: {cat.upper()}\n╚══════════════════════════════════════╝\n\n📜 *CLUE:*\n`{item['clue']}`\n\n💬 *Group chat me answer type karo!*"
        kb = [[InlineKeyboardButton("⏭️ Skip / Next", callback_data=f"guess_start_{cat}")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_guess")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    # --- Word Battles Logic ---
    if data == "menu_word":
        sc = random.choice(SCRAMBLE_WORDS)
        active_scramble[chat_id] = {'word': sc['word']}
        msg = (
            "╔══════════════════════════════════════╗\n"
            "   🔤  W O R D   S C R A M B L E  🔤\n"
            "╚══════════════════════════════════════╝\n\n"
            f"🧩 *Unscramble this word:*\n`{sc['scrambled']}`\n\n"
            "🎁 *Points:* `+10 PTS`\n"
            "💬 *Direct chat me sahi word type karo!*"
        )
        kb = [[InlineKeyboardButton("⏭️ Next Word", callback_data="menu_word")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    # --- CBSE 10th PYQ Quiz Logic ---
    if data == "menu_quiz":
        q = random.choice(QUIZ_DB)
        active_quiz[chat_id] = {'ans': q['ans']}
        msg = f"🧠 *CBSE 10th & BRAIN QUIZ*\n\n❓ *Question:*\n{q['q']}\n\n👉 Option choose karo:"
        kb = [[InlineKeyboardButton(opt, callback_data=f"quiz_ans_{i}")] for i, opt in enumerate(q['options'])]
        kb.append([InlineKeyboardButton("🔙 Menu", callback_data="menu_main")])
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    if data.startswith("quiz_ans_"):
        ans_idx = int(data.replace("quiz_ans_", ""))
        correct_idx = active_quiz.get(chat_id, {}).get('ans', -1)
        if ans_idx == correct_idx:
            add_score(user.id, user.first_name, 10)
            msg = f"🎉 *SHABAASH {user.first_name}!* Bilkul sahi jawab! (+10 PTS) ⭐"
        else:
            msg = f"❌ *Opps {user.first_name}!* Galat jawab ho gaya."
        kb = [[InlineKeyboardButton("▶️ Next Question", callback_data="menu_quiz")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    # --- Mines Diamond Logic ---
    if data == "menu_mines":
        gid = f"mines_{user.id}_{random.randint(100,999)}"
        # 3x3 grid = 9 boxes, 2 mines
        mine_spots = set(random.sample(range(9), 2))
        mines_games[gid] = {
            'board': ["?"] * 9,
            'mines': mine_spots,
            'player': user.id,
            'name': user.first_name,
            'diamonds': 0
        }
        msg = (
            "╔══════════════════════════════════════╗\n"
            "   💎 MINES ROULETTE (HIGH RISK) 💣\n"
            "╚══════════════════════════════════════╝\n"
            f"👤 *Player:* `{user.first_name}`\n"
            "💎 *Diamonds Found:* `0` | 💣 *Mines Hidden:* `2`\n\n"
            "Safe box choose karo!"
        )
        await query.edit_message_text(msg, reply_markup=render_mines_board(gid), parse_mode="Markdown")
        return

    if data.startswith("mines_click_"):
        _, _, gid, idx = data.split("_")
        idx = int(idx)
        if gid not in mines_games:
            await query.answer("Game expire ho chuka hai!")
            return
        g = mines_games[gid]
        if user.id != g['player']:
            await query.answer("Ye game aapka nahi hai!")
            return

        if idx in g['mines']:
            # Hit Mine! BOOM
            g['board'][idx] = "M"
            del mines_games[gid]
            msg = f"💥 *BOOM! {user.first_name} ne Bomb pe click kar diya!* 💀\nGame over!"
            kb = [[InlineKeyboardButton("🎮 Play Again", callback_data="menu_mines")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
            return
        else:
            if g['board'][idx] == "?":
                g['board'][idx] = "D"
                g['diamonds'] += 1
            
            if g['diamonds'] == 7: # All diamonds cleared!
                add_score(user.id, user.first_name, 35)
                del mines_games[gid]
                msg = f"👑 *JACKPOT! Saare Diamonds dhoond liye!* (+35 PTS)"
                kb = [[InlineKeyboardButton("🎮 Play Again", callback_data="menu_mines")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
                await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
                return

            msg = (
                "╔══════════════════════════════════════╗\n"
                "   💎 MINES ROULETTE (HIGH RISK) 💣\n"
                "╚══════════════════════════════════════╝\n"
                f"👤 *Player:* `{user.first_name}`\n"
                f"💎 *Diamonds Found:* `{g['diamonds']}`\n\n"
                "Agla box chuno ya cashout karo:"
            )
            await query.edit_message_text(msg, reply_markup=render_mines_board(gid), parse_mode="Markdown")
            return

    if data.startswith("mines_cashout_"):
        gid = data.replace("mines_cashout_", "")
        if gid in mines_games:
            g = mines_games[gid]
            pts = g['diamonds'] * 5
            add_score(user.id, user.first_name, pts)
            del mines_games[gid]
            msg = f"💰 *CASHOUT SUCCESSFUL!*\n`{user.first_name}` secured *+{pts} PTS*!"
            kb = [[InlineKeyboardButton("🎮 Play Again", callback_data="menu_mines")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
            return

    if data.startswith("mines_quit_"):
        mines_games.pop(data.replace("mines_quit_", ""), None)
        await query.edit_message_text("Mines match band kar diya gaya!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]))
        return

# --- 6. Group Chat Answer Listener ---
async def chat_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    chat_id, user, text = update.effective_chat.id, update.effective_user, update.message.text.strip().lower()

    # 1. Guess Master Verification
    if chat_id in active_guess:
        target = active_guess[chat_id]['answer']
        disp = active_guess[chat_id]['display']
        cat = active_guess[chat_id]['cat']
        tokens = target.split()
        if text == target or target in text or any(t in text for t in tokens if len(t) > 3):
            add_score(user.id, user.first_name, 10)
            del active_guess[chat_id]
            kb = [[InlineKeyboardButton("▶️ Next Question", callback_data=f"guess_start_{cat}")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
            await update.message.reply_text(f"🎉 *SHABAASH {user.first_name}!* (+10 PTS)\n✅ Sahi Answer: *{disp}*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
            return

    # 2. Word Scramble Verification
    if chat_id in active_scramble:
        correct_word = active_scramble[chat_id]['word']
        if text == correct_word:
            add_score(user.id, user.first_name, 10)
            del active_scramble[chat_id]
            kb = [[InlineKeyboardButton("▶️ Next Word", callback_data="menu_word")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
            await update.message.reply_text(f"🎉 *GENIUS {user.first_name}!* (+10 PTS)\n✅ Word tha: *{correct_word.upper()}*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
            return

# --- 7. Runner ---
def run_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("BOT_TOKEN missing!")
        return

    tg_app = ApplicationBuilder().token(token).build()

    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("games", start))
    tg_app.add_handler(CallbackQueryHandler(handle_callback))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_message_handler))

    print("⚡ Arcade Arena Bot is Running...")
    tg_app.run_polling()

if __name__ == '__main__':
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    
    run_bot()
    
