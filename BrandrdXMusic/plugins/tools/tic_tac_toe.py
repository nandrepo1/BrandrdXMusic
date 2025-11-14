# 
# Place this file in BrandrdXMusic/plugins/tools/

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
try:
    # most BrandrdXMusic forks export bot instance as `app`
    from BrandrdXMusic import app
    client = app
except Exception:
    # fallback: import Client class (only used for decorator name)
    # if your repo uses a different instance name, replace `client` below with that instance
    from pyrogram import Client
    # NOTE: if you don't have an instance named `app`, change decorators to match your instance
    client = Client  # decorator will fail if Client is class — see notes below

games = {}  # chat_id -> game state dict

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

def check_winner(b):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,c,d in wins:
        if b[a] != " " and b[a] == b[c] == b[d]:
            return b[a]
    if " " not in b:
        return "D"  # draw
    return None

# --- NOTE: if your repo uses `app` instance, decorators below will work unchanged.
# If your repo uses a different instance name, replace `@client.on_message` with
# e.g. `@app.on_message` or `@bot.on_message` to match your repo.
@client.on_message()
async def start_game_handler(client_obj, message):
    if not message.text:
        return
    if message.text.startswith("/startgame"):
        chat_id = message.chat.id
        if chat_id in games:
            await message.reply("एक गेम पहले से चल रहा है!")
            return
        games[chat_id] = {
            "board": [" "] * 9,
            "turn": "X",
            "players": [message.from_user.id],  # first player
        }
        await message.reply("टिक-टैक-टो शुरू! दूसरा खिलाड़ी /joingame से जुड़ें।", reply_markup=get_board_markup(games[chat_id]["board"]))

@client.on_message()
async def join_game_handler(client_obj, message):
    if not message.text:
        return
    if message.text.startswith("/joingame"):
        chat_id = message.chat.id
        if chat_id not in games:
            await message.reply("कोई गेम चल नहीं रहा। /startgame से शुरू करें।")
            return
        game = games[chat_id]
        if len(game["players"]) >= 2:
            await message.reply("इस चैट में पहले से दो खिलाड़ी हैं।")
            return
        if message.from_user.id in game["players"]:
            await message.reply("आप पहले ही गेम में हैं।")
            return
        game["players"].append(message.from_user.id)
        await message.reply("आप जुड़ गए! अब बटन दबाकर चाल चलें।")

@client.on_callback_query()
async def callback_move(client_obj, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    if chat_id not in games:
        await callback_query.answer("कोई गेम चल नहीं रहा।", show_alert=True)
        return

    game = games[chat_id]
    if len(game["players"]) < 2:
        await callback_query.answer("दिलचस्प — अभी दूसरा खिलाड़ी नहीं जुड़ा है।", show_alert=True)
        return
    if user_id not in game["players"]:
        await callback_query.answer("आप इस गेम के खिलाड़ी नहीं हैं।", show_alert=True)
        return

    idx = int(callback_query.data)
    if game["board"][idx] != " ":
        await callback_query.answer("यह जगह पहले से भरी हुई है।", show_alert=True)
        return

    # ensure correct turn: player 0 -> X, player1 -> O
    expected_symbol = "X" if game["players"].index(user_id) == 0 else "O"
    if game["turn"] != expected_symbol:
        await callback_query.answer("अभी आपकी बारी नहीं है।", show_alert=True)
        return

    game["board"][idx] = expected_symbol
    game["turn"] = "O" if game["turn"] == "X" else "X"

    winner = check_winner(game["board"])
    if winner:
        if winner == "D":
            text = "खेल ड्रॉ हुआ!"
        else:
            text = f"खेल ख़त्म — जीतने वाला: {winner}"
        # edit message to show final board and remove buttons
        await callback_query.message.edit_text(text + "\n\nFinal board:", reply_markup=None)
        await callback_query.message.reply_text(f"{game['board'][0:3]}\n{game['board'][3:6]}\n{game['board'][6:9]}")
        del games[chat_id]
    else:
        # update board buttons
        await callback_query.message.edit_reply_markup(reply_markup=get_board_markup(game["board"]))
        await callback_query.answer()

# Optional: /endgame to force-stop
@client.on_message()
async def end_game_handler(client_obj, message):
    if not message.text:
        return
    if message.text.startswith("/endgame"):
        chat_id = message.chat.id
        if chat_id in games:
            del games[chat_id]
            await message.reply("गेम रोक दिया गया।")
        else:
            await message.reply("कोई गेम चल नहीं रहा।")
