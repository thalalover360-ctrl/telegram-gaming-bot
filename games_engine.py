import random, asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from data import GUESS_DB, MATHS_BRAIN_DB, BINGO_CALLS, WORD_BATTLE_PROMPTS

def check_ttt_winner(b):
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for x, y, z in wins:
        if b[x] == b[y] == b[z] and b[x] != " ": return b[x]
    return "Draw" if " " not in b else None

def get_best_ai_move(board, diff):
    empty = [i for i, v in enumerate(board) if v == " "]
    return random.choice(empty)

def render_ttt(g):
    b = g['board']
    ic = {"X": "❌", "O": "⭕", " ": "⬜"}
    kb = [[InlineKeyboardButton(ic[b[r*3+c]], callback_data=f"tm_{r*3+c}") for c in range(3)] for r in range(3)]
    kb.append([InlineKeyboardButton("🏳️ End", callback_data="t_quit")])
    return InlineKeyboardMarkup(kb)

def render_mines(g):
    kb = [[InlineKeyboardButton("💎" if g['b'][r*3+c]=="D" else ("💣" if g['b'][r*3+c]=="M" else "❓"), callback_data=f"mc_{r*3+c}") for c in range(3)] for r in range(3)]
    kb.append([InlineKeyboardButton("💰 Cashout", callback_data="m_cash"), InlineKeyboardButton("🏳️ Quit", callback_data="m_quit")])
    return InlineKeyboardMarkup(kb)

async def run_word_timer(cid, context, wb, add_score):
    r_idx = min(wb['r'] - 1, len(WORD_BATTLE_PROMPTS) - 1)
    p = WORD_BATTLE_PROMPTS[r_idx]
    wb['pfx'], wb['mlen'], wb['safe'] = p['prefix'], p['min_len'], set()
    pl = "\n".join([f" • {n}" for n in wb['pls'].values()])
    await context.bot.send_message(chat_id=cid, text=f"🔥 *ROUND #{wb['r']}* 🔥\n🎯 Word with min *{wb['mlen']} letters* starting with *'{wb['pfx']}'*!\n\n👥 Players:\n{pl}\n⏱️ Timer: 40s", parse_mode="Markdown")
    await asyncio.sleep(40)
    if cid not in wb or wb.get('st') != 'play': return
    for uid in list(wb['pls'].keys()):
        if uid not in wb['safe']: del wb['pls'][uid]
    if len(wb['pls']) <= 1:
        if len(wb['pls']) == 1:
            wid, wn = list(wb['pls'].items())[0]
            add_score(wid, wn, 30)
            await context.bot.send_message(chat_id=cid, text=f"👑 *WINNER:* `{wn}` (+30 PTS)!", parse_mode="Markdown")
        else: await context.bot.send_message(chat_id=cid, text="💀 Sab eliminate ho gaye!")
        wb['st'] = 'end'
    else:
        wb['r'] += 1
        await context.bot.send_message(chat_id=cid, text="⚡ Next round starting...", parse_mode="Markdown")
        await asyncio.sleep(3)
        await run_word_timer(cid, context, wb, add_score)
        
