import os, random, threading, asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from data import GUESS_DB, MATHS_BRAIN_DB, BINGO_CALLS
from games_engine import check_ttt_winner, get_best_ai_move, render_ttt, render_mines, run_word_timer

app = Flask(__name__)
@app.route('/')
def h(): return "Bot Online 24/7"
def run_w(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

scores, ttt, guess, qz, mines, mem, bingo, wb = {}, {}, {}, {}, {}, {}, {}, {}

def add_score(uid, n, pts=10):
    if uid not in scores: scores[uid] = {"n": n, "s": 0}
    scores[uid]["s"] += pts

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    pts = scores.get(u.id, {}).get("s", 0)
    msg = f"╔══════════════════════╗\n   ⚡ ARCADE ARENA ⚡\n╚══════════════════════╝\n👤 `{u.first_name}` | 🏆 `{pts} PTS`\nSelect Game:"
    kb = [
        [InlineKeyboardButton("1️⃣ TicTacToe", callback_data="m_ttt"), InlineKeyboardButton("2️⃣ GuessMaster", callback_data="m_g")],
        [InlineKeyboardButton("3️⃣ WordKnockout", callback_data="m_w"), InlineKeyboardButton("4️⃣ Bingo", callback_data="m_b")],
        [InlineKeyboardButton("5️⃣ Maths/Brain", callback_data="m_q"), InlineKeyboardButton("6️⃣ Mines", callback_data="m_m")],
        [InlineKeyboardButton("7️⃣ Memory", callback_data="m_mem"), InlineKeyboardButton("🏆 Leaderboard", callback_data="m_ld")]
    ]
    if update.message: await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    else: await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, u, d, cid = update.callback_query, update.callback_query.from_user, update.callback_query.data, update.effective_chat.id
    if d == "main": await start(update, context); return

    if d == "m_ld":
        t = "🏆 *LEADERBOARD*\n\n" + "\n".join([f"{i}. *{p['n']}* - `{p['s']} PTS`" for i, p in enumerate(sorted(scores.values(), key=lambda x: x['s'], reverse=True)[:10], 1)]) if scores else "Khali hai!"
        await q.edit_message_text(t, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return

    if d == "m_ttt":
        ttt[cid] = {'board': [" "]*9, 'turn': 'X', 'p1': u.id, 'p1_n': u.first_name}
        await q.edit_message_text(f"❌⭕ Turn: `{u.first_name}`", reply_markup=render_ttt(ttt[cid]), parse_mode="Markdown"); return

    if d.startswith("tm_"):
        idx = int(d.split("_")[1])
        g = ttt.get(cid)
        if not g or g['board'][idx] != " ": return
        g['board'][idx] = "X"
        w = check_ttt_winner(g['board'])
        if not w:
            ai = get_best_ai_move(g['board'], "medium")
            g['board'][ai] = "O"
            w = check_ttt_winner(g['board'])
        if w:
            del ttt[cid]
            if w == "X": add_score(u.id, u.first_name, 15)
            await q.edit_message_text(f"🎉 Winner: {w}!" if w!="Draw" else "🤝 Draw!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]])); return
        await q.edit_message_text(f"Turn: `{u.first_name}`", reply_markup=render_ttt(g), parse_mode="Markdown"); return

    if d == "m_g":
        c = random.choice(["cricket", "movie", "anime"])
        item = random.choice(GUESS_DB[c])
        guess[cid] = {'a': item['answer'], 'd': item['display']}
        await q.edit_message_text(f"🎯 *GUESS ({c.upper()}):*\n`{item['clue']}`\n\nChat me answer likho!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return

    if d == "m_w":
        wb[cid] = {'st': 'lob', 'pls': {u.id: u.first_name}, 'r': 1, 'safe': set(), 'used': set()}
        kb = [[InlineKeyboardButton("🙋‍♂️ Join", callback_data="wj"), InlineKeyboardButton("🚀 Start", callback_data="ws")], [InlineKeyboardButton("🔙 Menu", callback_data="main")]]
        await q.edit_message_text(f"🔤 *WORD KNOCKOUT LOBBY*\nJoined: `{u.first_name}`", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d == "wj":
        if cid in wb and wb[cid]['st'] == 'lob':
            wb[cid]['pls'][u.id] = u.first_name
            await q.answer("Joined!")
        return

    if d == "ws":
        if cid in wb and wb[cid]['st'] == 'lob':
            wb[cid]['st'] = 'play'
            await q.edit_message_text("🚀 Game Starting...")
            asyncio.create_task(run_word_timer(cid, context, wb[cid], add_score))
        return

    if d == "m_b":
        bingo[cid] = list(range(1, 26))
        random.shuffle(bingo[cid])
        await q.edit_message_text("🔢 *BINGO ARENA*\nCard banao, draw dabao!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎲 Draw", callback_data="b_d")], [InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return

    if d == "b_d":
        if not bingo.get(cid): await q.answer("Over!"); return
        n = bingo[cid].pop()
        await q.edit_message_text(f"📢 *CALL: [ {n} ]*\n{BINGO_CALLS.get(n, '')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎲 Next", callback_data="b_d")], [InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return

    if d == "m_q":
        item = random.choice(MATHS_BRAIN_DB)
        qz[cid] = item['ans']
        kb = [[InlineKeyboardButton(o, callback_data=f"qa_{i}")] for i, o in enumerate(item['options'])]
        kb.append([InlineKeyboardButton("🔙 Menu", callback_data="main")])
        await q.edit_message_text(f"🧠 *QUIZ:*\n{item['q']}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"); return

    if d.startswith("qa_"):
        if int(d.split("_")[1]) == qz.get(cid):
            add_score(u.id, u.first_name, 10)
            t = "🎉 Sahi Jawab! (+10 PTS)"
        else: t = "❌ Galat!"
        await q.edit_message_text(t, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]])); return

    if d == "m_m":
        mines[cid] = {'b': ["?"]*9, 'm': set(random.sample(range(9), 2)), 'd': 0, 'p': u.id}
        await q.edit_message_text("💎 *MINES ROULETTE*", reply_markup=render_mines(mines[cid]), parse_mode="Markdown"); return

    if d.startswith("mc_"):
        idx, g = int(d.split("_")[1]), mines.get(cid)
        if not g or u.id != g['p']: return
        if idx in g['m']:
            del mines[cid]
            await q.edit_message_text("💥 *BOOM! Bomb foot gaya!*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]]), parse_mode="Markdown"); return
        if g['b'][idx] == "?": g['b'][idx] = "D"; g['d'] += 1
        await q.edit_message_text(f"💎 Diamonds: {g['d']}", reply_markup=render_mines(g), parse_mode="Markdown"); return

    if d == "m_cash":
        g = mines.pop(cid, None)
        if g: add_score(u.id, u.first_name, g['d']*5)
        await q.edit_message_text(f"💰 Cashout: +{g['d']*5 if g else 0} PTS", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data="main")]])); return

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

    if cid in wb and wb[cid].get('st') == 'play':
        w = wb[cid]
        if u.id in w['pls'] and u.id not in w['safe']:
            if t.startswith(w['pfx'].lower()) and len(t) >= w['mlen'] and t.isalpha() and t not in w['used']:
                w['safe'].add(u.id); w['used'].add(t)
                await update.message.reply_text(f"✅ Safe: `{u.first_name}` ({t.upper()})")

    if cid in guess and (t == guess[cid]['a'] or guess[cid]['a'] in t):
        add_score(u.id, u.first_name, 10)
        await update.message.reply_text(f"🎉 Correct: `{guess[cid]['d']}` (+10 PTS)")
        del guess[cid]

    if cid in mem and "".join(mem[cid]) == t.replace(" ", ""):
        add_score(u.id, u.first_name, 20)
        await update.message.reply_text(f"🧠 Sharp Memory! (+20 PTS)")
        del mem[cid]

def main():
    token = os.getenv("BOT_TOKEN")
    if not token: return
    a = ApplicationBuilder().token(token).build()
    a.add_handler(CommandHandler("start", start))
    a.add_handler(CommandHandler("games", start))
    a.add_handler(CallbackQueryHandler(cb))
    a.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_h))
    a.run_polling()

if __name__ == '__main__':
    t = threading.Thread(target=run_w)
    t.daemon = True
    t.start()
    main()
        
