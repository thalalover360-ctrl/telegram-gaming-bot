import os
import random
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. Web Server for Render & Cron-job 24/7 ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Gaming Arcade Bot is Online 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- 2. In-Memory Game States ---
# ttt_games = { game_id: { 'board': list, 'turn': str, 'mode': 'ai'/'pvp', 'p1': id, 'p2': id, 'p1_name': str, 'p2_name': str, 'difficulty': str } }
ttt_games = {}

# --- 3. Main Menu / Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("1️⃣ Tic Tac Toe ❌⭕", callback_data="menu_ttt"),
            InlineKeyboardButton("2️⃣ Guess Master 🎬", callback_data="menu_guess")
        ],
        [
            InlineKeyboardButton("3️⃣ Word Battles 🔤", callback_data="menu_word"),
            InlineKeyboardButton("4️⃣ Group Bingo 🔢", callback_data="menu_bingo")
        ],
        [
            InlineKeyboardButton("5️⃣ CBSE 10th PYQ Quiz 🧠", callback_data="menu_quiz"),
            InlineKeyboardButton("6️⃣ Mines Diamond 💎💣", callback_data="menu_mines")
        ],
        [
            InlineKeyboardButton("7️⃣ Memory Matrix 🧩", callback_data="menu_memory")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        f"🎮 *WELCOME TO THE ARCADE, {user.first_name.upper()}!* 🎮\n\n"
        "Niche diye gaye games me se apna favorite game select karo aur khelna shuru karo!"
    )
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

# --- 4. Tic-Tac-Toe Game Engine ---
def check_winner(b):
    wins = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for x, y, z in wins:
        if b[x] == b[y] == b[z] and b[x] != " ":
            return b[x]
    if " " not in b:
        return "Draw"
    return None

def minimax(b, depth, is_max):
    res = check_winner(b)
    if res == "O": return 10 - depth
    if res == "X": return depth - 10
    if res == "Draw": return 0

    if is_max:
        best = -1000
        for i in range(9):
            if b[i] == " ":
                b[i] = "O"
                best = max(best, minimax(b, depth + 1, False))
                b[i] = " "
        return best
    else:
        best = 1000
        for i in range(9):
            if b[i] == " ":
                b[i] = "X"
                best = min(best, minimax(b, depth + 1, True))
                b[i] = " "
        return best

def get_best_ai_move(board, diff):
    empty = [i for i, v in enumerate(board) if v == " "]
    if diff == "easy":
        return random.choice(empty)
    elif diff == "medium":
        if random.random() < 0.5:
            return random.choice(empty)
    
    # Hard Mode (Minimax - Unbeatable)
    best_val = -1000
    best_move = empty[0]
    for i in empty:
        board[i] = "O"
        move_val = minimax(board, 0, False)
        board[i] = " "
        if move_val > best_val:
            best_val = move_val
            best_move = i
    return best_move

def render_ttt_board(game_id):
    g = ttt_games[game_id]
    b = g['board']
    icons = {"X": "❌", "O": "⭕", " ": "⬜"}
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            idx = r * 3 + c
            row.append(InlineKeyboardButton(icons[b[idx]], callback_data=f"ttt_move_{game_id}_{idx}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ End Game", callback_data=f"ttt_quit_{game_id}")])
    return InlineKeyboardMarkup(keyboard)

# --- 5. Callback Handlers ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user

    # Main Menus
    if data == "menu_main":
        await start(update, context)
        return

    # TTT Sub-Menu
    if data == "menu_ttt":
        kb = [
            [InlineKeyboardButton("🤖 Play vs AI (Single Player)", callback_data="ttt_opt_ai")],
            [InlineKeyboardButton("👥 Play vs Friend (Group)", callback_data="ttt_opt_pvp")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
        ]
        await query.edit_message_text("❌⭕ *TIC TAC TOE*\n\nKaise khelna chahte ho?", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    # TTT AI Difficulty Menu
    if data == "ttt_opt_ai":
        kb = [
            [InlineKeyboardButton("🟢 Easy", callback_data="ttt_start_ai_easy")],
            [InlineKeyboardButton("🟡 Medium", callback_data="ttt_start_ai_medium")],
            [InlineKeyboardButton("🔴 Hard (Unbeatable)", callback_data="ttt_start_ai_hard")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_ttt")]
        ]
        await query.edit_message_text("🤖 *Select AI Difficulty:*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    # Start TTT vs AI
    if data.startswith("ttt_start_ai_"):
        diff = data.replace("ttt_start_ai_", "")
        gid = f"ai_{user.id}_{random.randint(100,999)}"
        ttt_games[gid] = {
            'board': [" "] * 9,
            'turn': 'X',
            'mode': 'ai',
            'p1': user.id,
            'p1_name': user.first_name,
            'p2': 'AI',
            'p2_name': f"Bot ({diff.capitalize()})",
            'difficulty': diff
        }
        await query.edit_message_text(
            f"❌⭕ *Game Started vs {diff.capitalize()} AI!*\n\n👤 *{user.first_name}* (❌) vs 🤖 *Bot* (⭕)\n👉 *Your turn!*",
            reply_markup=render_ttt_board(gid),
            parse_mode="Markdown"
        )
        return

    # Create TTT Group Lobby (PvP)
    if data == "ttt_opt_pvp":
        gid = f"pvp_{random.randint(1000,9999)}"
        ttt_games[gid] = {
            'board': [" "] * 9,
            'turn': 'X',
            'mode': 'pvp',
            'p1': user.id,
            'p1_name': user.first_name,
            'p2': None,
            'p2_name': None
        }
        kb = [[InlineKeyboardButton("⚔️ Join Challenge", callback_data=f"ttt_join_{gid}")]]
        await query.edit_message_text(
            f"🎮 *Tic Tac Toe PvP Lobby!*\n\nChallenger: *{user.first_name}* (❌)\nWaiting for Player 2 to join...",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )
        return

    # Join PvP Lobby
    if data.startswith("ttt_join_"):
        gid = data.replace("ttt_join_", "")
        if gid not in ttt_games:
            await query.answer("Ye game lobby expire ho chuki hai!", show_alert=True)
            return
        g = ttt_games[gid]
        if g['p1'] == user.id:
            await query.answer("Aapne khud hi challenge create kiya hai! Kisi aur ko join karne do.", show_alert=True)
            return
        if g['p2'] is not None:
            await query.answer("Lobby already full hai!", show_alert=True)
            return

        g['p2'] = user.id
        g['p2_name'] = user.first_name
        await query.edit_message_text(
            f"⚔️ *Battle Started!*\n\n❌ *{g['p1_name']}* vs ⭕ *{g['p2_name']}*\n👉 Turn: *{g['p1_name']}*",
            reply_markup=render_ttt_board(gid),
            parse_mode="Markdown"
        )
        return

    # TTT Move Clicked
    if data.startswith("ttt_move_"):
        parts = data.split("_")
        gid = parts[2]
        idx = int(parts[3])

        if gid not in ttt_games:
            await query.answer("Game khatam ho chuka hai!", show_alert=True)
            return
        
        g = ttt_games[gid]
        
        # Turn verification
        if g['mode'] == 'ai':
            if user.id != g['p1']:
                await query.answer("Ye game aapka nahi hai!", show_alert=True)
                return
        else:
            current_id = g['p1'] if g['turn'] == 'X' else g['p2']
            if user.id != current_id:
                await query.answer("Abhi aapki turn nahi hai!", show_alert=True)
                return

        if g['board'][idx] != " ":
            await query.answer("Ye box pehle se bhara hua hai!")
            return

        # Player move
        g['board'][idx] = g['turn']
        winner = check_winner(g['board'])

        if winner:
            if winner == "Draw":
                text = "🤝 *Match Draw ho gaya!*"
            else:
                win_name = g['p1_name'] if winner == 'X' else g['p2_name']
                text = f"🎉 *Winner: {win_name} ({winner})!*"
            del ttt_games[gid]
            kb = [[InlineKeyboardButton("🎮 Play Again", callback_data="menu_ttt")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
            return

        # Next Turn Logic
        if g['mode'] == 'ai':
            # Bot Turn
            ai_idx = get_best_ai_move(g['board'], g['difficulty'])
            g['board'][ai_idx] = "O"
            ai_winner = check_winner(g['board'])
            if ai_winner:
                if ai_winner == "Draw":
                    text = "🤝 *Match Draw ho gaya!*"
                else:
                    text = f"💀 *Bot jeet gaya! Try again.*"
                del ttt_games[gid]
                kb = [[InlineKeyboardButton("🎮 Play Again", callback_data="menu_ttt")]]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
                return

            await query.edit_message_text(
                f"❌⭕ *vs {g['difficulty'].capitalize()} AI*\n👤 *{g['p1_name']}* (❌) vs 🤖 *Bot* (⭕)\n👉 *Your turn!*",
                reply_markup=render_ttt_board(gid),
                parse_mode="Markdown"
            )
        else:
            # PvP switch turn
            g['turn'] = "O" if g['turn'] == "X" else "X"
            next_name = g['p1_name'] if g['turn'] == 'X' else g['p2_name']
            await query.edit_message_text(
                f"⚔️ *Tic Tac Toe*\n❌ *{g['p1_name']}* vs ⭕ *{g['p2_name']}*\n👉 Turn: *{next_name}* ({g['turn']})",
                reply_markup=render_ttt_board(gid),
                parse_mode="Markdown"
            )
        return

    # Quit TTT
    if data.startswith("ttt_quit_"):
        gid = data.replace("ttt_quit_", "")
        if gid in ttt_games:
            del ttt_games[gid]
        kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
        await query.edit_message_text("Match band kar diya gaya!", reply_markup=InlineKeyboardMarkup(kb))
        return

    # Placeholders for Next Games
    if data in ["menu_guess", "menu_word", "menu_bingo", "menu_quiz", "menu_mines", "menu_memory"]:
        game_names = {
            "menu_guess": "Guess Master 🎬🏏",
            "menu_word": "Word Battles 🔤",
            "menu_bingo": "Group Bingo 🔢",
            "menu_quiz": "CBSE 10th PYQ Quiz 🧠",
            "menu_mines": "Mines Diamond 💎💣",
            "menu_memory": "Memory Matrix 🧩"
        }
        kb = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
        await query.edit_message_text(
            f"⚙️ *{game_names[data]} is under setup!*\n\nNext update me live ho raha hai.",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )
        return

# --- 6. Bot Runner ---
def run_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("BOT_TOKEN missing!")
        return

    tg_app = ApplicationBuilder().token(token).build()

    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("games", start))
    tg_app.add_handler(CallbackQueryHandler(handle_callback))

    print("Gaming Bot is Running...")
    tg_app.run_polling()

if __name__ == '__main__':
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    
    run_bot()
      
