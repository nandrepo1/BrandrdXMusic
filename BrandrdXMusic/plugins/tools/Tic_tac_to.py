from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

games = {}

def get_board_markup(board):
    # इनलाइन कीबोर्ड बनाने का फंक्शन
    keyboard = []
    for i in range(0, 9, 3):
        row = [InlineKeyboardButton(board[i+j] if board[i+j] != " " else " ", callback_data=str(i+j)) for j in range(3)]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

@Client.on_message(filters.command("startgame", prefixes=["/"]))
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
        await message.reply("टिक-टैक-टो गेम शुरू! दूसरा खिलाड़ी /joingame से जुड़ें।", reply_markup=get_board_markup(games[chat_id]["board"]))

@Client.on_message(filters.command("joingame", prefixes=["/"]))
async def join_game(client, message):
    chat_id = message.chat.id
    if chat_id in games and len(games[chat_id]["players"]) == 1:
        games[chat_id]["players"].append(message.from_user.id)
        await message.reply("आप जुड़ गए! अब बटनों पर क्लिक करके मूव करें।")
    else:
        await message.reply("या तो कोई गेम नहीं है या गेम में पहले से दो खिलाड़ी हैं।")

@Client.on_callback_query()
async def handle_move(client, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if chat_id not in games:
        await callback_query.answer("कोई गेम नहीं चल रहा है।", show_alert=True)
        return

    game = games[chat_id]
    if user_id not in game["players"]:
        await callback_query.answer("आप इस गेम का हिस्सा नहीं हैं।", show_alert=True)
        return

    index = int(callback_query.data)

    if game["board"][index] != " ":
        await callback_query.answer("यह जगह पहले से भरी हुई है।", show_alert=True)
        return

    current_turn = game["turn"]
    game["board"][index] = current_turn
    game["turn"] = "O" if current_turn == "X" else "X"

    # यहाँ पर आप जीत की चेकिंग का लॉजिक भी जोड़ सकते हैं

    await callback_query.message.edit_reply_markup(reply_markup=get_board_markup(game["board"]))
    await callback_query.answer()

# आप इस कोड को अपने टेलीग्राम क्लाइंट में जोड़कर टेस्ट कर सकते हैं।
