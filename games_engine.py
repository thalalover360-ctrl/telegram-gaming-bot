import random, asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from data import GUESS_DB, MATHS_BRAIN_DB, BINGO_CALLS, WORD_BATTLE_PROMPTS

def check_ttt_winner(b):
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for x, y, z in wins:
        if b[x] == b[y] == b[z] and b[x] != " ": return b[x]
    return "Draw" if " " not in b else None

def get_best_ai_move(board):
    empty = [i for i, v in enumerate(board) if v == " "]
    return random.choice(empty)

def render_ttt(g, gid):
    b = g['board']
    ic = {"X": "❌", "O": "⭕", " ": "⬜"}
    kb = [[InlineKeyboardButton(ic[b[r*3+c]], callback_data=f"tm_{gid}_{r*3+c}") for c in range(3)] for r in range(3)]
    kb.append([InlineKeyboardButton("🏳️ End Match", callback_data=f"tq_{gid}")])
    return InlineKeyboardMarkup(kb)

def render_mines(g, gid):
    kb = [[InlineKeyboardButton("💎" if g['b'][r*3+c]=="D" else ("💣" if g['b'][r*3+c]=="M" else "❓"), callback_data=f"mc_{gid}_{r*3+c}") for c in range(3)] for r in range(3)]
    kb.append([InlineKeyboardButton("💰 Cashout", callback_data=f"mcash_{gid}"), InlineKeyboardButton("🏳️ Quit", callback_data=f"mq_{gid}")])
    return InlineKeyboardMarkup(kb)

# --- Instant Trigger Word Knockout Engine ---
async def run_word_timer(cid, context, wb, add_score):
    if wb.get('st') != 'play': return
    
    r_idx = min(wb['r'] - 1, len(WORD_BATTLE_PROMPTS) - 1)
    p = WORD_BATTLE_PROMPTS[r_idx]
    wb['pfx'] = p['prefix']
    wb['mlen'] = p['min_len']
    wb['safe'] = set()
    wb['event'] = asyncio.Event()  # Instant Trigger Event
    
    pl = "\n".join([f" • {n}" for n in wb['pls'].values()])
    await context.bot.send_message(
        chat_id=cid, 
        text=f"🔥 *ROUND #{wb['r']}* 🔥\n🎯 Word with min *{wb['mlen']} letters* starting with *'{wb['pfx']}'*!\n\n👥 *Alive Players:*\n{pl}\n\n⏱️ *Max Time:* `40s` (Sabka reply aate hi turant next round!)", 
        parse_mode="Markdown"
    )
    
    try:
        # Wait for all players to answer OR 40s timeout
        await asyncio.wait_for(wb['event'].wait(), timeout=40.0)
    except asyncio.TimeoutError:
        pass
    
    if wb.get('st') != 'play': return
    
    # Eliminate players who did not answer
    all_p = list(wb['pls'].keys())
    for uid in all_p:
        if uid not in wb['safe']:
            del wb['pls'][uid]
            
    if len(wb['pls']) == 0:
        await context.bot.send_message(chat_id=cid, text="💀 *KOI BHI SURVIVE NAHI HUA!* Match Draw!")
        wb['st'] = 'end'
    elif len(wb['pls']) == 1:
        wid, wn = list(wb['pls'].items())[0]
        add_score(wid, wn, 30)
        await context.bot.send_message(chat_id=cid, text=f"👑 *CHAMPION! LAST MAN STANDING!*\n\n🏆 Winner: `{wn}` (+30 PTS) ⭐", parse_mode="Markdown")
        wb['st'] = 'end'
    else:
        wb['r'] += 1
        survivors = ", ".join(wb['pls'].values())
        await context.bot.send_message(chat_id=cid, text=f"⚡ *Sab safe ho gaye!* ({survivors})\n👉 *Round #{wb['r']} starting immediately...*", parse_mode="Markdown")
        await asyncio.sleep(2)
        await run_word_timer(cid, context, wb, add_score)
        
