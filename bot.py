import os, random, threading, asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from data import GUESS_DB, MATHS_BRAIN_DB, BINGO_CALLS
from games_engine import check_ttt_winner, get_best_ai_move, render_ttt, render_mines, run_word_timer
from db import init_db, get_player, add_stats, get_leaderboard, get_rank_badge

app = Flask(__name__)
@app.route('/')
def home(): return "⚡ 7-in-1 Arcade Bot is Active & Ready!"
def run_web(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

ttt, guess, qz, mines, mem, bingo, wb = {}, {}, {}, {}, {}, {}, {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    p = get_player(u.id, u.first_name)
    rank = get_rank_badge(p['score'])
    
    msg = (
        "╔══════════════════════════════════════╗\n"
        "   ⚡  A R C A D E   C O N T R O L L E R  ⚡\n"
        "╚══════════════════════════════════════╝\n"
        f"👤 *Pilot:* `{p['name']}` | Rank: *{rank}*\n"
        f"🏆 *Score:* `{p['score']} PTS` | 🪙 *Coins:* `{p['coins']}`\n"
        f"🔥 *Win Streak:* `{p['streak']}` | ⚔️ *Wins:* `{p['wins']}/{p['matches']}`\n"
        "────────────────────────────────────────\n"
        "🎮 *SELECT YOUR MISSION:* 👇"
    )
    kb = [
        [InlineKeyboardButton("1️⃣ TicTacToe ⚔️", callback_data="m_ttt"), InlineKeyboardButton("2️⃣ Guess Master 🎬", callback_data="m_g")],
        [InlineKeyboardButton("3️⃣ Word Knockout 💣", callback_data="m_w"), InlineKeyboardButton("4️⃣ Group Bingo 🔢", callback_data="m_b")],
        [InlineKeyboardButton("5️⃣ High-IQ Quiz 🧠", callback_data="m_q"), InlineKeyboardButton("6️⃣ Mines Roulette 💎", callback_data="m_m")],
        [InlineKeyboardButton("7️⃣ Memory Matrix 🧩", callback_data="m_mem"), InlineKeyboardButton("👤 My Profile 📊", callback_data="m_prof")],
        [InlineKeyboardButton("🏆 Hall of Fame (Leaderboard)", callback_data="m_ld")]
    ]
    if update.message: await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else: await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, u, d, cid = update.callback_query, update.callback_query.from_user, update.callback_query.data, update.effective_chat.id
    if d == "main": await start(update, context); return

    if d == "m_prof":
        p = get_player(u.id, u.first_name)
        rank = get_rank_badge(p['score'])
        wr = round((p['wins'] / p['matches'] * 100), 1) if p['matches'] > 0 else 0
        txt = f"👤 *PROFILE:* `{p['name']}`\n🎖️ *Badge:* {rank}\n🏆 *Score:* `{p['score']} PTS`\n🪙 *Coins:* `{p['coins']}`\n📈 *Win Rate:* `{wr}%`\n🔥 *Streak:* `{p['streak']}`"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return

    if d == "m_ld":
        rows = get_leaderboard(10)
        lines = [f"{'👑' if i==1 else f'{i}.'} *{name}* — `{sc} PTS`" for i, (name, sc, w, c) in enumerate(rows, 1)]
        await q.edit_message_text("🏆 *LEADERBOARD:*\n\n" + ("\n".join(lines) if lines else "No data"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return

    if d == "m_ttt":
        kb = [[InlineKeyboardButton("🤖 Play vs AI", callback_data="t_ai")], [InlineKeyboardButton("👥 1v1 PvP Challenge", callback_data="t_pvp")], [InlineKeyboardButton("🔙 Menu", callback_data="main")]]
        await q.edit_message_text("❌⭕ *TIC TAC TOE*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d == "t_ai":
        gid = f"ai_{u.id}_{random.randint(100,999)}"
        ttt[gid] = {'board': [" "]*9, 'turn': 'X', 'mode': 'ai', 'p1': u.id, 'p1_n': u.first_name}
        await q.edit_message_text(f"🤖 *VS AI*\nTurn: `{u.first_name}` (❌)", reply_markup=render_ttt(ttt[gid], gid), parse_mode="Markdown"); return

    if d == "t_pvp":
        gid = f"pvp_{random.randint(1000,9999)}"
        ttt[gid] = {'board': [" "]*9, 'turn': 'X', 'mode': 'pvp', 'p1': u.id, 'p1_n': u.first_name, 'p2': None, 'p2_n': None}
        await q.edit_message_text(f"⚔️ *1v1 LOBBY*\nHost: `{u.first_name}` (❌)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚔️ Join Challenge", callback_data=f"tj_{gid}")]]), parse_mode="Markdown"); return

    if d.startswith("tj_"):
        gid = d.replace("tj_", "")
        if gid not in ttt or ttt[gid]['p2'] is not None: await q.answer("Lobby full!"); return
        g = ttt[gid]
        g['p2'], g['p2_n'] = u.id, u.first_name
        await q.edit_message_text(f"⚔️ `{g['p1_n']}` vs `{g['p2_n']}`\n👉 Turn: *{g['p1_n']}*", reply_markup=render_ttt(g, gid), parse_mode="Markdown"); return

    if d.startswith("tm_"):
        _, gid, idx = d.split("_")
        idx, g = int(idx), ttt.get(gid)
        if not g or g['board'][idx] != " ": return
        if g['mode'] == 'ai' and u.id != g['p1']: return
        if g['mode'] == 'pvp' and u.id != (g['p1'] if g['turn'] == 'X' else g['p2']): return

        g['board'][idx] = g['turn']
        w = check_ttt_winner(g['board'])
        if not w and g['mode'] == 'ai':
            ai = get_best_ai_move(g['board'])
            g['board'][ai] = "O"
            w = check_ttt_winner(g['board'])

        if w:
            del ttt[gid]
            if w == "X": add_stats(g['p1'], g['p1_n'], score_add=15, coins_add=10, is_win=True)
            elif w == "O" and g['mode'] == 'pvp': add_stats(g['p2'], g['p2_n'], score_add=15, coins_add=10, is_win=True)
            win_txt = "🤝 Match Draw!" if w == "Draw" else f"🎉 Winner: *{g['p1_n'] if w=='X' else (g['p2_n'] if g['mode']=='pvp' else 'AI')}*!"
            await q.edit_message_text(win_txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Play Again", callback_data="m_ttt"), InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return

        if g['mode'] == 'pvp':
            g['turn'] = "O" if g['turn'] == "X" else "X"
            curr_name = g['p1_n'] if g['turn'] == 'X' else g['p2_n']
            await q.edit_message_text(f"👉 Turn: *{curr_name}* ({g['turn']})", reply_markup=render_ttt(g, gid), parse_mode="Markdown")
        else:
            await q.edit_message_text(f"Turn: `{g['p1_n']}` (❌)", reply_markup=render_ttt(g, gid), parse_mode="Markdown")
        return

    if d.startswith("tq_"):
        ttt.pop(d.replace("tq_", ""), None)
        await q.edit_message_text("Match End!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]])); return

    if d == "m_g":
        c = random.choice(["cricket", "movie", "anime"])
        item = random.choice(GUESS_DB[c])
        guess[cid] = {'a': item['answer'], 'd': item['display']}
        await q.edit_message_text(f"🎯 *GUESS ({c.upper()}):*\n`{item['clue']}`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return

    if d == "m_w":
        wb[cid] = {'st': 'lob', 'pls': {u.id: u.first_name}, 'r': 1, 'safe': set(), 'used': set(), 'event': None}
        kb = [[InlineKeyboardButton("🙋‍♂️ Join Battle", callback_data="wj"), InlineKeyboardButton("🚀 Start Game", callback_data="ws")], [InlineKeyboardButton("🔙 Menu", callback_data="main")]]
        await q.edit_message_text(f"🔤 *WORD KNOCKOUT*\nJoined: `{u.first_name}`", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d == "wj":
        if cid in wb and wb[cid]['st'] == 'lob':
            wb[cid]['pls'][u.id] = u.first_name
            await q.answer("Joined!")
        return

    if d == "ws":
        if cid in wb and wb[cid]['st'] == 'lob':
            wb[cid]['st'] = 'play'
            await q.edit_message_text("🚀 Game Starting...")
            asyncio.create_task(run_word_timer(cid, context, wb[cid], lambda uid, n, pts: add_stats(uid, n, score_add=pts, coins_add=20, is_win=True)))
        return

    if d == "m_b":
        bingo[cid] = list(range(1, 26))
        random.shuffle(bingo[cid])
        await q.edit_message_text("🔢 *BINGO ARENA*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎲 Draw Number", callback_data="b_d")], [InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return

    if d == "b_d":
        if not bingo.get(cid): await q.answer("Over!"); return
        n = bingo[cid].pop()
        await q.edit_message_text(f"📢 *CALL: [ {n} ]*\n{BINGO_CALLS.get(n, '')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎲 Next", callback_data="b_d")], [InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return

    if d == "m_q":
        item = random.choice(MATHS_BRAIN_DB)
        qz[cid] = item['ans']
        kb = [[InlineKeyboardButton(o, callback_data=f"qa_{i}")] for i, o in enumerate(item['options'])]
        kb.append([InlineKeyboardButton("🔙 Menu", callback_data="main")])
        await q.edit_message_text(f"🧠 *CHALLENGE:*\n`{item['q']}`", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d.startswith("qa_"):
        if int(d.split("_")[1]) == qz.get(cid):
            add_stats(u.id, u.first_name, score_add=15, coins_add=10, is_win=True)
            t = f"🎉 *Sahi Jawab {u.first_name}!* (+15 PTS)"
        else: t = "❌ *Galat Jawab!*"
        await q.edit_message_text(t, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Next", callback_data="m_q"), InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return

    if d == "m_m":
        gid = f"m_{u.id}_{random.randint(100,999)}"
        mines[gid] = {'b': ["?"]*9, 'm': set(random.sample(range(9), 2)), 'd': 0, 'p': u.id}
        await q.edit_message_text("💎 *MINES ROULETTE*", reply_markup=render_mines(mines[gid], gid), parse_mode="Markdown"); return

    if d.startswith("mc_"):
        _, gid, idx = d.split("_")
        idx, g = int(idx), mines.get(gid)
        if not g or u.id != g['p']: return
        if idx in g['m']:
            del mines[gid]
            await q.edit_message_text("💥 *BOOM! Bomb foot gaya!*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Try Again", callback_data="m_m"), InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return
        if g['b'][idx] == "?": g['b'][idx] = "D"; g['d'] += 1
        await q.edit_message_text(f"💎 Diamonds: `{g['d']}`", reply_markup=render_mines(g, gid), parse_mode="Markdown"); return

    if d.startswith("mcash_"):
        gid = d.replace("mcash_", "")
        g = mines.pop(gid, None)
        if g:
            pts = g['d'] * 8
            add_stats(u.id, u.first_name, score_add=pts, coins_add=pts, is_win=True)
            await q.edit_message_text(f"💰 Cashout: +{pts} PTS", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]])); return

    if d.startswith("mq_"):
        mines.pop(d.replace("mq_", ""), None)
        await q.edit_message_text("Mines End!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]])); return

    if d == "m_mem":
        seq = random.sample(["🍎", "🚀", "⚡", "💎", "🦁"], 4)
        mem[cid] = seq
        await q.edit_message_text(f"🧩 Pattern: {' '.join(seq)}\n(3s me gayab!)")
        await asyncio.sleep(3)
        await q.edit_message_text("❓ Emojis chat me likho!")
        return

async def msg_h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    cid, u, t = update.effective_chat.id, update.effective_user, update.message.text.strip().lower()

    # Word Knockout Instant Event Handler
    if cid in wb and wb[cid].get('st') == 'play':
        w = wb[cid]
        if u.id in w['pls'] and u.id not in w['safe']:
            if t.startswith(w['pfx'].lower()) and len(t) >= w['mlen'] and t.isalpha() and t not in w['used']:
                w['safe'].add(u.id)
                w['used'].add(t)
                await update.message.reply_text(f"✅ Safe: `{u.first_name}` ({t.upper()}) [{len(w['safe'])}/{len(w['pls'])}]")
                
                # Check if all players are safe -> Trigger next round instantly!
                if len(w['safe']) == len(w['pls']) and w.get('event'):
                    w['event'].set()

    if cid in guess and (t == guess[cid]['a'] or guess[cid]['a'] in t):
        add_stats(u.id, u.first_name, score_add=15, coins_add=10, is_win=True)
        await update.message.reply_text(f"🎉 Correct: `{guess[cid]['d']}` (+15 PTS)")
        del guess[cid]

    if cid in mem and "".join(mem[cid]) == t.replace(" ", ""):
        add_stats(u.id, u.first_name, score_add=20, coins_add=15, is_win=True)
        await update.message.reply_text(f"🧠 Sharp Memory! (+20 PTS)")
        del mem[cid]

def main():
    init_db()
    token = os.getenv("BOT_TOKEN")
    if not token: return
    a = ApplicationBuilder().token(token).build()
    a.add_handler(CommandHandler("start", start))
    a.add_handler(CommandHandler("games", start))
    a.add_handler(CommandHandler("profile", start))
    a.add_handler(CallbackQueryHandler(cb))
    a.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_h))
    a.run_polling()

if __name__ == '__main__':
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
    main()
    
