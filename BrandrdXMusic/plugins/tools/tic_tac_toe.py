from BrandrdXMusic import app
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

games = {}

# बोर्ड UI
def get_board_markup(board):
    keyboard = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            idx = i + j
            text = board[idx] if board[idx] != " " else " "
            row.append(InlineKeyboardButton(text, callback_data=str(idx)))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# जीत चेक
def check_winner(b):
    wins = [
        (0,1,2),(3,4,5),(6,7,8),
        (0,3,6),(1,4,7),(2,5,8),
        (0,4,8),(2,4,6)
    ]
    for x, y, z in wins:
        if b[x] == b[y] == b[z] and b[x] != " ":
            return b[x]
    if " " not in b:
        return "D"
    return None

# कमांड चेक (username सहित)
def is_cmd(text, cmd):
    try:
        return text.split()[0].split("@")[0] == cmd
    except:
        return False

# /startgame
@app.on_message()
async def start_game(client, message):
    if not message.text:
        return
    
    if is_cmd(message.text, "/startgame"):
        chat_id = message.chat.id

        # अगर गेम पहले से चल रहा है
        if chat_id in games:
            await message.reply("पहले से एक गेम चल रहा है!")
            return
        
        # नया गेम बनाएँ
        games[chat_id] = {
            "board": [" "] * 9,
            "turn": "X",
            "players": [message.from_user.id]
        }

        await message.reply(
            "टिक-टैक-टो शुरू! दूसरा खिलाड़ी /joingame से जुड़ें।",
            reply_markup=get_board_markup(games[chat_id]["board"])
        )

# /joingame
@app.on_message()
async def join_game(client, message):
    if not message.text:
        return
    
    if is_cmd(message.text, "/joingame"):
        chat_id = message.chat.id

        if chat_id not in games:
            await message.reply("पहले /startgame करना पड़ेगा!")
            return

        game = games[chat_id]

        if len(game["players"]) == 2:
            await message.reply("दो खिलाड़ी पहले से जुड़े हैं।")
            return

        if message.from_user.id in game["players"]:
            await message.reply("आप पहले से गेम में हैं!")
            return

        game["players"].append(message.from_user.id)
        await message.reply("आप गेम में जुड़ गए! अब बटन दबाकर चाल चलें।")

# बटन / move
@app.on_callback_query()
async def move_handler(client, cq):
    chat = cq.message.chat.id
    user = cq.from_user.id

    if chat not in games:
        await cq.answer("कोई गेम नहीं चल रहा!", show_alert=True)
        return

    game = games[chat]

    if len(game["players"]) < 2:
        await cq.answer("अभी दूसरा खिलाड़ी नहीं जुड़ा!", show_alert=True)
        return

    if user not in game["players"]:
        await cq.answer("आप खिलाड़ी नहीं हैं!", show_alert=True)
        return

    idx = int(cq.data)
    board = game["board"]

    if board[idx] != " ":
        await cq.answer("यह जगह भरी हुई है!", show_alert=True)
        return

    expected = "X" if game["players"].index(user) == 0 else "O"

    if game["turn"] != expected:
        await cq.answer("अभी आपकी बारी नहीं है!", show_alert=True)
        return

    board[idx] = expected
    game["turn"] = "O" if expected == "X" else "X"

    winner = check_winner(board)

    if winner:
        msg = "ड्रा!" if winner == "D" else f"विजेता: {winner}"
        await cq.message.edit_text(msg)
        del games[chat]
        return

    await cq.message.edit_reply_markup(reply_markup=get_board_markup(board))
    await cq.answer()
