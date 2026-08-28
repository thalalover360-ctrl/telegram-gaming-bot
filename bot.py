import os, random, threading, asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from data import GUESS_DB, SCRAMBLE_WORDS, QUIZ_DB
from games_engine import check_ttt_winner, get_best_ai_move

web_app = Flask(__name__)
@web_app.route('/')
def home(): return "⚡ 7-in-1 Arcade Bot is Online 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

ttt_games, active_guess, active_scramble = {}, {}, {}
active_quiz, mines_games, memory_games, bingo_games, scores = {}, {}, {}, {}, {}

def add_score(user_id, name, pts=10):
    if user_id not in scores: scores[user_id] = {"name": name, "score": 0}
    scores[user_id]["score"] += pts

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    pts = scores.get(u.id, {}).get("score", 0)
    msg = f"╔══════════════════════════════════════╗\n   ⚡  A R C A D E   A R E N A   ⚡\n╚══════════════════════════════════════╝\n👤 *Player:* `{u.first_name}` | 🏆 *Points:* `{pts} PTS`\n────────────────────────────────────────\n🎯 *CHOOSE A GAME MODE:* 👇"
    kb = [
        [InlineKeyboardButton("1️⃣ Tic Tac Toe ⚔️", callback_data="menu_ttt"), InlineKeyboardButton("2️⃣ Guess Master 🎬🏏", callback_data="menu_guess")],
        [InlineKeyboardButton("3️⃣ Word Battles 🔤", callback_data="menu_word"), InlineKeyboardButton("4️⃣ Group Bingo 🔢", callback_data="menu_bingo")],
        [InlineKeyboardButton("5️⃣ CBSE 10th Quiz 🧠", callback_data="menu_quiz"), InlineKeyboardButton("6️⃣ Mines Diamond 💎💣", callback_data="menu_mines")],
        [InlineKeyboardButton("7️⃣ Memory Matrix 🧩", callback_data="menu_memory"), InlineKeyboardButton("🏆 Leaderboard 📊", callback_data="menu_board")]
    ]
    if update.message: await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    elif update.callback_query: await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

def render_ttt(gid):
    b = ttt_games[gid]['board']
    icons = {"X": "❌", "O": "⭕", " ": "⬜"}
    kb = [[InlineKeyboardButton(icons[b[r*3+c]], callback_data=f"ttt_move_{gid}_{r*3+c}") for c in range(3)] for r in range(3)]
    kb.append([InlineKeyboardButton("🏳️ End Match", callback_data=f"ttt_quit_{gid}")])
    return InlineKeyboardMarkup(kb)

def render_mines(gid):
    g = mines_games[gid]
    kb = [[InlineKeyboardButton("💎" if g['board'][r*3+c]=="D" else ("💣" if g['board'][r*3+c]=="M" else "❓"), callback_data=f"mines_click_{gid}_{r*3+c}") for c in range(3)] for r in range(3)]
    kb.append([InlineKeyboardButton("💰 Cash Out", callback_data=f"mines_cashout_{gid}"), InlineKeyboardButton("🏳️ Quit", callback_data=f"mines_quit_{gid}")])
    return InlineKeyboardMarkup(kb)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, u, d = update.callback_query, update.callback_query.from_user, update.callback_query.data
    cid = update.effective_chat.id

    if d == "menu_main": await start(update, context); return

    if d == "menu_board":
        txt = "🏆 *LEADERBOARD*\n\n" + ("No points yet!" if not scores else "\n".join([f"{'👑' if i==1 else f'{i}.'} *{p['name']}* — `{p['score']} PTS`" for i, p in enumerate(sorted(scores.values(), key=lambda x: x['score'], reverse=True)[:10], 1)]))
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]), parse_mode="Markdown"); return

    if d == "menu_ttt":
        kb = [[InlineKeyboardButton("🤖 Play vs AI", callback_data="ttt_opt_ai")], [InlineKeyboardButton("👥 Play vs Friend", callback_data="ttt_opt_pvp")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
        await q.edit_message_text("❌⭕ *TIC TAC TOE*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d == "ttt_opt_ai":
        kb = [[InlineKeyboardButton("🟢 Easy", callback_data="ttt_ai_easy")], [InlineKeyboardButton("🟡 Medium", callback_data="ttt_ai_medium")], [InlineKeyboardButton("🔴 Hard", callback_data="ttt_ai_hard")], [InlineKeyboardButton("🔙 Back", callback_data="menu_ttt")]]
        await q.edit_message_text("🤖 *Select Difficulty:*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d.startswith("ttt_ai_"):
        diff = d.replace("ttt_ai_", "")
        gid = f"ai_{u.id}_{random.randint(100,999)}"
        ttt_games[gid] = {'board': [" "]*9, 'turn': 'X', 'mode': 'ai', 'p1': u.id, 'p1_name': u.first_name, 'diff': diff}
        await q.edit_message_text(f"🤖 *VS {diff.upper()} AI*\n👉 Your Turn (❌):", reply_markup=render_ttt(gid), parse_mode="Markdown"); return

    if d == "ttt_opt_pvp":
        gid = f"pvp_{random.randint(1000,9999)}"
        ttt_games[gid] = {'board': [" "]*9, 'turn': 'X', 'mode': 'pvp', 'p1': u.id, 'p1_name': u.first_name, 'p2': None, 'p2_name': None}
        await q.edit_message_text(f"⚔️ *1v1 LOBBY*\nHost: `{u.first_name}` (❌)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚔️ Join Challenge", callback_data=f"ttt_join_{gid}")]]), parse_mode="Markdown"); return

    if d.startswith("ttt_join_"):
        gid = d.replace("ttt_join_", "")
        if gid not in ttt_games or ttt_games[gid]['p2'] is not None: await q.answer("Lobby unavailable!"); return
        g = ttt_games[gid]
        g['p2'], g['p2_name'] = u.id, u.first_name
        await q.edit_message_text(f"⚔️ `{g['p1_name']}` vs `{g['p2_name']}`\n👉 Turn: {g['p1_name']}", reply_markup=render_ttt(gid), parse_mode="Markdown"); return

    if d.startswith("ttt_move_"):
        _, _, gid, idx = d.split("_")
        idx = int(idx)
        if gid not in ttt_games: await q.answer("Game over!"); return
        g = ttt_games[gid]
        if (g['mode'] == 'ai' and u.id != g['p1']) or (g['mode'] == 'pvp' and u.id != (g['p1'] if g['turn'] == 'X' else g['p2'])):
            await q.answer("Aapki turn nahi hai!"); return
        if g['board'][idx] != " ": await q.answer("Box already filled!"); return

        g['board'][idx] = g['turn']
        win = check_ttt_winner(g['board'])
        if win:
            msg = "🤝 Draw!" if win == "Draw" else f"🎉 *Winner: {g['p1_name'] if win=='X' else g['p2_name']}!*"
            if win != "Draw": add_score(u.id, u.first_name, 15)
            del ttt_games[gid]
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Play Again", callback_data="menu_ttt")]]), parse_mode="Markdown"); return

        if g['mode'] == 'ai':
            ai_idx = get_best_ai_move(g['board'], g['diff'])
            g['board'][ai_idx] = "O"
            ai_win = check_ttt_winner(g['board'])
            if ai_win:
                del ttt_games[gid]
                await q.edit_message_text("💀 Bot jeet gaya!" if ai_win == "O" else "🤝 Draw!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Play Again", callback_data="menu_ttt")]]), parse_mode="Markdown"); return
            await q.edit_message_text(f"🤖 Turn: `{g['p1_name']}` (❌)", reply_markup=render_ttt(gid), parse_mode="Markdown")
        else:
            g['turn'] = "O" if g['turn'] == "X" else "X"
            await q.edit_message_text(f"👉 Turn: `{g['p1_name'] if g['turn']=='X' else g['p2_name']}` ({g['turn']})", reply_markup=render_ttt(gid), parse_mode="Markdown")
        return

    if d.startswith("ttt_quit_"):
        ttt_games.pop(d.replace("ttt_quit_", ""), None)
        await q.edit_message_text("Match End!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]])); return

    if d == "menu_guess":
        kb = [[InlineKeyboardButton("🏏 Cricket", callback_data="guess_cricket")], [InlineKeyboardButton("🎬 Movies", callback_data="guess_movie")], [InlineKeyboardButton("⛩️ Anime", callback_data="guess_anime")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
        await q.edit_message_text("🎯 *GUESS MASTER*\nChoose Category:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d.startswith("guess_"):
        cat = d.replace("guess_", "")
        item = random.choice(GUESS_DB[cat])
        active_guess[cid] = {'answer': item['answer'], 'display': item['display'], 'cat': cat}
        msg = f"╔══════════════════════════════════════╗\n   🎯 GUESS MASTER: {cat.upper()}\n╚══════════════════════════════════════╝\n\n📜 *CLUE:*\n`{item['clue']}`\n\n💬 *Type answer directly in chat!*"
        kb = [[InlineKeyboardButton("⏭️ Next", callback_data=f"guess_{cat}")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_guess")]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d == "menu_word":
        sc = random.choice(SCRAMBLE_WORDS)
        active_scramble[cid] = {'word': sc['word']}
        msg = f"╔══════════════════════════════════════╗\n   🔤 WORD SCRAMBLE BATTLE\n╚══════════════════════════════════════╝\n\n🧩 *Unscramble:*\n`{sc['scrambled']}`\n\n💬 *Type word in chat!*"
        kb = [[InlineKeyboardButton("⏭️ Next Word", callback_data="menu_word")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d == "menu_bingo":
        gid = f"bingo_{cid}"
        bingo_games[gid] = {'numbers': list(range(1, 26)), 'called': []}
        random.shuffle(bingo_games[gid]['numbers'])
        msg = "🔢 *GROUP BINGO*\n1 se 25 matrix banao, button daba kar number call karo!"
        kb = [[InlineKeyboardButton("🎲 Draw Number", callback_data=f"bdraw_{gid}")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d.startswith("bdraw_"):
        gid = d.replace("bdraw_", "")
        if gid not in bingo_games or not bingo_games[gid]['numbers']: await q.answer("Numbers over!"); return
        n = bingo_games[gid]['numbers'].pop()
        bingo_games[gid]['called'].append(n)
        msg = f"📢 *BINGO CALL: [ {n} ]*\n📜 Recent: `{', '.join(map(str, bingo_games[gid]['called'][-5:]))}`"
        kb = [[InlineKeyboardButton("🎲 Next Number", callback_data=f"bdraw_{gid}")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d == "menu_quiz":
        q_item = random.choice(QUIZ_DB)
        active_quiz[cid] = {'ans': q_item['ans']}
        msg = f"🧠 *CBSE 10th & BRAIN QUIZ*\n\n❓ *Question:*\n`{q_item['q']}`"
        kb = [[InlineKeyboardButton(opt, callback_data=f"qans_{i}")] for i, opt in enumerate(q_item['options'])]
        kb.append([InlineKeyboardButton("🔙 Menu", callback_data="menu_main")])
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d.startswith("qans_"):
        ans_idx = int(d.replace("qans_", ""))
        correct = active_quiz.get(cid, {}).get('ans', -1)
        if ans_idx == correct:
            add_score(u.id, u.first_name, 10)
            msg = f"🎉 *SHABAASH {u.first_name}!* (+10 PTS) ⭐"
        else: msg = "❌ *Galat jawab!*"
        kb = [[InlineKeyboardButton("▶️ Next Question", callback_data="menu_quiz")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d == "menu_mines":
        gid = f"mines_{u.id}_{random.randint(100,999)}"
        mines_games[gid] = {'board': ["?"]*9, 'mines': set(random.sample(range(9), 2)), 'player': u.id, 'diamonds': 0}
        msg = f"💎 *MINES ROULETTE*\nPlayer: `{u.first_name}` | Diamonds: `0` | 💣 Mines: `2`"
        await q.edit_message_text(msg, reply_markup=render_mines(gid), parse_mode="Markdown"); return

    if d.startswith("mines_click_"):
        _, _, gid, idx = d.split("_")
        idx = int(idx)
        if gid not in mines_games: await q.answer("Game over!"); return
        g = mines_games[gid]
        if u.id != g['player']: await q.answer("Aapka game nahi hai!"); return

        if idx in g['mines']:
            del mines_games[gid]
            await q.edit_message_text(f"💥 *BOOM! {u.first_name} hit a Bomb!* 💀", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Play Again", callback_data="menu_mines")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]), parse_mode="Markdown")
            return
        else:
            if g['board'][idx] == "?": g['board'][idx] = "D"; g['diamonds'] += 1
            if g['diamonds'] == 7:
                add_score(u.id, u.first_name, 35)
                del mines_games[gid]
                await q.edit_message_text("👑 *JACKPOT! Saare Diamonds dhoond liye!* (+35 PTS)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Play Again", callback_data="menu_mines")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]))
                return
            await q.edit_message_text(f"💎 *Diamonds Found:* `{g['diamonds']}`\nNext box chuno:", reply_markup=render_mines(gid), parse_mode="Markdown")
            return

    if d.startswith("mines_cashout_"):
        gid = d.replace("mines_cashout_", "")
        if gid in mines_games:
            pts = mines_games[gid]['diamonds'] * 5
            add_score(u.id, u.first_name, pts)
            del mines_games[gid]
            await q.edit_message_text(f"💰 *CASHOUT!* `{u.first_name}` got *+{pts} PTS*!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Play Again", callback_data="menu_mines")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]))
            return

    if d.startswith("mines_quit_"):
        mines_games.pop(d.replace("mines_quit_", ""), None)
        await q.edit_message_text("Mines End!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]])); return

    if d == "menu_memory":
        emojis = ["🍎", "🚀", "⚡", "💎", "🦁", "🔥", "👑", "🎯"]
        seq = random.sample(emojis, 4)
        memory_games[cid] = {'seq': seq}
        await q.edit_message_text(f"🧩 *MEMORY MATRIX*\n\n👀 Sequence:  *{' '.join(seq)}*\n\n⏳ *3 seconds me gayab hoga...*", parse_mode="Markdown")
        await asyncio.sleep(3)
        await q.edit_message_text("🧩 *MEMORY MATRIX*\n\n❓ Chat me sequence wale emojis type karo!", parse_mode="Markdown")
        return

async def chat_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    cid, u, t = update.effective_chat.id, update.effective_user, update.message.text.strip().lower()

    if cid in active_guess:
        target, disp, cat = active_guess[cid]['answer'], active_guess[cid]['display'], active_guess[cid]['cat']
        if t == target or target in t or any(tok in t for tok in target.split() if len(tok) > 3):
            add_score(u.id, u.first_name, 10)
            del active_guess[cid]
            await update.message.reply_text(f"🎉 *CORRECT {u.first_name}!* (+10 PTS)\n✅ Answer: *{disp}*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Next", callback_data=f"guess_{cat}")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]), parse_mode="Markdown")
            return

    if cid in active_scramble:
        word = active_scramble[cid]['word']
        if t == word:
            add_score(u.id, u.first_name, 10)
            del active_scramble[cid]
            await update.message.reply_text(f"🎉 *GENIUS {u.first_name}!* (+10 PTS)\n✅ Word: *{word.upper()}*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Next Word", callback_data="menu_word")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]), parse_mode="Markdown")
            return

    if cid in memory_games:
        seq = memory_games[cid]['seq']
        if t.replace(" ", "") == "".join(seq) or all(em in t for em in seq):
            add_score(u.id, u.first_name, 20)
            del memory_games[cid]
            await update.message.reply_text(f"🧠 *SHARP MEMORY {u.first_name}!* (+20 PTS)\nPattern: {' '.join(seq)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Play Again", callback_data="menu_memory")], [InlineKeyboardButton("🔙 Menu", callback_data="menu_main")]]), parse_mode="Markdown")
            return

def run_bot():
    token = os.getenv("BOT_TOKEN")
    if not token: return
    tg_app = ApplicationBuilder().token(token).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("games", start))
    tg_app.add_handler(CallbackQueryHandler(handle_callback))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_message_handler))
    tg_app.run_polling()

if __name__ == '__main__':
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    run_bot()
    
