from BrandrdXMusic import app
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import filters

games = {}

def get_board_markup(board):
    keyboard = []
    for i in range(0, 9, 3):
        row = [InlineKeyboardButton(board[i+j] if board[i+j] != " " else " ", callback_data=str(i+j)) for j in range(3)]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def check_winner(board):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a, b, c in wins:
        if board[a] == board[b] == board[c] and board[a] != " ":
            return board[a]
    if " " not in board:
        return "D"  # Draw
    return None

@app.on_message(filters.command("startgame", prefixes=["/"]))
async def start_game(client, message):
    chat_id = message.chat.id
    if chat_id in games:
        await message.reply("पहले से एक गेम चल रहा है!")
    else:
        games[chat_id] = {
            "board": [" "] * 9,
            "turn": "X",
            "players": [message.from_user.id],
        }
        await message.reply("टिक-टैक-टो शुरू! दूसरा खिलाड़ी /joingame से जुड़ें।", reply_markup=get_board_markup(games[chat_id]["board"]))

@app.on_message(filters.command("joingame", prefixes=["/"]))
async def join_game(client, message):
    chat_id = message.chat.id
    if chat_id not in games:
        await message.reply("कोई गेम शुरू नहीं है। पहले /startgame चलाएँ।")
        return

    game = games[chat_id]
    if len(game["players"]) >= 2:
        await message.reply("दो खिलाड़ी पहले से जुड़े हुए हैं।")
        return

    if message.from_user.id in game["players"]:
        await message.reply("आप पहले ही गेम में हैं।")
        return

    game["players"].append(message.from_user.id)
    await message.reply("आप गेम में जुड़ गए हैं! अब बटन दबाकर अपनी चाल चलें।")

@app.on_callback_query()
async def handle_move(client, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if chat_id not in games:
        await callback_query.answer("कोई गेम नहीं चल रहा है।", show_alert=True)
        return

    game = games[chat_id]
    if user_id not in game["players"]:
        await callback_query.answer("आप इस गेम में नहीं हैं।", show_alert=True)
        return

    index = int(callback_query.data)

    if game["board"][index] != " ":
        await callback_query.answer("यह जगह पहले से भरी हुई है।", show_alert=True)
        return

    current_turn = game["turn"]
    if (current_turn == "X" and user_id != game["players"][0]) or (current_turn == "O" and user_id != game["players"][1]):
        await callback_query.answer("अभी आपकी बारी नहीं है।", show_alert=True)
        return

    game["board"][index] = current_turn
    game["turn"] = "O" if current_turn == "X" else "X"

    winner = check_winner(game["board"])
    if winner:
        if winner == "D":
            result_text = "गेम ड्रा हुआ!"
        else:
            result_text = f"खेल ख़त्म — जीत: {winner}"
        await callback_query.message.edit_text(result_text)
        del games[chat_id]
    else:
        await callback_query.message.edit_reply_markup(reply_markup=get_board_markup(game["board"]))
        await callback_query.answer()
