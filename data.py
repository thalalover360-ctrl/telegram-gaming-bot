# ==========================================
# 🎯 1. GUESS MASTER QUESTION BANK
# ==========================================
GUESS_DB = {
    "cricket": [
        {"clue": "Fastest IPL 50 in 13 balls & Rajasthan Royals explosive opener!", "answer": "yashasvi jaiswal", "display": "Yashasvi Jaiswal"},
        {"clue": "'Captain Cool', 3 ICC Trophies & Iconic No. 7 Jersey.", "answer": "ms dhoni", "display": "MS Dhoni"},
        {"clue": "'Run Machine', 183 against Pakistan & 50 ODI centuries.", "answer": "virat kohli", "display": "Virat Kohli"},
        {"clue": "'Hitman', 3 Double Centuries in ODI cricket.", "answer": "rohit sharma", "display": "Rohit Sharma"},
        {"clue": "Universe Boss, 175* runs in a single IPL inning.", "answer": "chris gayle", "display": "Chris Gayle"},
        {"clue": "Yorker King jo death overs me balling karta hai (MI).", "answer": "jasprit bumrah", "display": "Jasprit Bumrah"},
        {"clue": "Mr. 360 Degree batsman in World & IPL cricket.", "answer": "ab de villiers", "display": "AB de Villiers"},
        {"clue": "Mr. IPL ke naam se kise jaana jaata hai jo CSK ka core tha?", "answer": "suresh raina", "display": "Suresh Raina"}
    ],
    "movie": [
        {"clue": "Dialogue: 'Mogambo khush hua!' (Movie name)", "answer": "mr india", "display": "Mr. India"},
        {"clue": "Dialogue: 'Picture abhi baaki hai mere dost!'", "answer": "om shanti om", "display": "Om Shanti Om"},
        {"clue": "Dialogue: 'Kitne aadmi the?'", "answer": "sholay", "display": "Sholay"},
        {"clue": "Dialogue: 'Pushpa, Jhukega nahi sala!'", "answer": "pushpa", "display": "Pushpa"},
        {"clue": "Dialogue: 'Why so serious?' (Joker movie)", "answer": "the dark knight", "display": "The Dark Knight"},
        {"clue": "Guess Movie: 🤫 🤫 🤫 (3 Engineering friends + Virus)", "answer": "3 idiots", "display": "3 Idiots"},
        {"clue": "Guess Movie: 🚢 ❄️ 💔 (Jack & Rose love story)", "answer": "titanic", "display": "Titanic"},
        {"clue": "Guess Movie: Space me 1 hour = Earth par 7 years.", "answer": "interstellar", "display": "Interstellar"}
    ],
    "anime": [
        {"clue": "Sapna: Hokage Banna | Power: Nine-Tails Jinchuriki.", "answer": "naruto", "display": "Naruto Uzumaki"},
        {"clue": "Straw Hat Captain who wants to become King of Pirates.", "answer": "luffy", "display": "Monkey D. Luffy"},
        {"clue": "Saiyan Prince who calls Goku 'Kakarot'.", "answer": "vegeta", "display": "Vegeta"},
        {"clue": "Blindfolded Jujutsu Sorcerer (Limitless user).", "answer": "gojo", "display": "Satoru Gojo"},
        {"clue": "Shinigami Notebook jisme naam likhne se log marte hain.", "answer": "death note", "display": "Death Note"},
        {"clue": "One Punch Man universe ka hero jo ek ghuse me harata hai.", "answer": "saitama", "display": "Saitama"}
    ]
}

# ==========================================
# 🔤 2. WORD SCRAMBLE & PROMPTS
# ==========================================
SCRAMBLE_WORDS = [
    {"scrambled": "N T H Y O P", "word": "python"},
    {"scrambled": "E L T E M R A G", "word": "telegram"},
    {"scrambled": "T K R I C E C", "word": "cricket"},
    {"scrambled": "D R O B N A I", "word": "android"},
    {"scrambled": "R B O L A F T O", "word": "football"},
    {"scrambled": "A C A D R E", "word": "arcade"},
    {"scrambled": "V I R A T", "word": "virat"},
    {"scrambled": "G A M I N G", "word": "gaming"},
    {"scrambled": "D I A M O N D", "word": "diamond"}
]

# Multiplayer Elimination Prompts (Prefix & Min-length)
WORD_BATTLE_PROMPTS = [
    {"prefix": "Y", "min_len": 2},
    {"prefix": "CA", "min_len": 3},
    {"prefix": "TR", "min_len": 3},
    {"prefix": "SH", "min_len": 4},
    {"prefix": "PL", "min_len": 4},
    {"prefix": "BL", "min_len": 4},
    {"prefix": "STR", "min_len": 5},
    {"prefix": "CON", "min_len": 5},
    {"prefix": "PRO", "min_len": 5},
    {"prefix": "EX", "min_len": 4}
]

# ==========================================
# 🧠 3. MATHS SPEED & BRAIN LOGIC QUIZ
# ==========================================
MATHS_BRAIN_DB = [
    {
        "q": "Speed Maths: (25 × 25) - (24 × 24) = ?",
        "options": ["49", "1", "98", "50"],
        "ans": 0
    },
    {
        "q": "Algebra Trick: If x + 1/x = 3, then what is x² + 1/x²?",
        "options": ["9", "7", "11", "6"],
        "ans": 1
    },
    {
        "q": "Trigonometry: Value of (sin 30° + cos 60°) is:",
        "options": ["1/2", "1", "√3", "0"],
        "ans": 1
    },
    {
        "q": "Mental Maths: What is 15% of 240?",
        "options": ["32", "36", "40", "24"],
        "ans": 1
    },
    {
        "q": "Arithmetic: 7 + 7 ÷ 7 + 7 × 7 - 7 = ?",
        "options": ["50", "56", "0", "49"],
        "ans": 0
    },
    {
        "q": "Brain Teaser: I have branches, but no fruit, trunk or leaves. What am I?",
        "options": ["A River", "A Bank", "A Mountain", "A Tree"],
        "ans": 1
    },
    {
        "q": "Logic: If 1=3, 2=3, 3=5, 4=4, 5=4, then 6=?",
        "options": ["3 (number of letters in 'SIX')", "6", "4", "5"],
        "ans": 0
    },
    {
        "q": "Brain Riddle: What has to be broken before you can use it?",
        "options": ["An Egg", "A Lock", "A Secret", "Glass"],
        "ans": 0
    },
    {
        "q": "Brain Riddle: What gets wetter the more it dries?",
        "options": ["A Towel", "Sponge", "Soap", "Cloud"],
        "ans": 0
    },
    {
        "q": "Logic Puzzle: A doctor gives you 3 pills to take 1 every 30 mins. How long do they last?",
        "options": ["60 Minutes", "90 Minutes", "30 Minutes", "120 Minutes"],
        "ans": 0
    }
]

# ==========================================
# 🔢 4. BINGO TAMBOLA CALLOUTS (1-25)
# ==========================================
BINGO_CALLS = {
    1: "Top of the world / Ek Number! 🥇",
    2: "Kaala Teeka / Jodi No. 1 ✌️",
    3: "Three Musketeers / Teen Tigada 🔱",
    4: "Char Minar / Four Corners 🏛️",
    5: "High Five / Panch Pandav ✋",
    6: "Super Sixer 🏏",
    7: "Thala for a reason / Lucky 7 👑",
    8: "Canteen plate / Infinite loop ♾️",
    9: "Navratri Special 🪔",
    10: "Sachin No. 10 / Dus ka Dum 🔟",
    11: "Two sticks / Eleven Stars 🥢",
    12: "One Dozen / Ek Barah 🥚",
    13: "Unlucky for some, Lucky for us! 🃏",
    14: "Valentine Special ❤️",
    15: "Independence Spirit 🇮🇳",
    16: "Sweet Sixteen 🎂",
    17: "Dancing Queen 💃",
    18: "Voting Age / Virat jersey no. 18 🏏",
    19: "Last of the teens 🚀",
    20: "T20 Cricket Mania 🏟️",
    21: "Royal salute / Ek kiss 💋",
    22: "Two Little Ducks 🦆🦆",
    23: "Michael Jordan jump 🏀",
    24: "Two dozen / Full day hours ⏰",
    25: "Silver Jubilee Winner! 🥈"
}
