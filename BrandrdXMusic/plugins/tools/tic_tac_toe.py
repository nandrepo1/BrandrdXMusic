from BrandrdXMusic import app
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import filters

games = {}

def get_board_markup(board):
    keyboard = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            idx = i + j
            val = board[idx]
            text = val if val is not None else "·"
            row.append(InlineKeyboardButton(text, callback_data=str(idx)))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def check_winner(board):
    wins = [
        (0,1,2), (3,4,5), (6,7,8),
        (0,3,6), (1,4,7), (2,5,8),
        (0,4,8), (2,4,6)
    ]
    for a, b, c in wins:
        if board[a] is not None and board[a] == board[b] == board[c]:
            return board[a]

    if all(cell is not None for cell in board):
        return "D"

    return None


@app.on_message(filters.command("stopgame", prefixes=["/"]))
async def stop_game(client, message):
    chat_id = message.chat.id
    if chat_id in games:
        del games[chat_id]
        await message.reply("Game stopped.")
    else:
        await message.reply("No game is running.")


@app.on_message(filters.command("startgame", prefixes=["/"]))
async def start_game(client, message):
    chat_id = message.chat.id
    if chat_id in games:
        await message.reply("A game is already running here!")
        return

    games[chat_id] = {
        "board": [None] * 9,
        "turn": "X",
        "players": [message.from_user.id],
    }

    await message.reply(
        "Tic-Tac-Toe Started! Second player, use /joingame.",
        reply_markup=get_board_markup(games[chat_id]["board"])
    )


@app.on_message(filters.command("joingame", prefixes=["/"]))
async def join_game(client, message):
    chat_id = message.chat.id

    if chat_id not in games:
        await message.reply("No game is running. Use /startgame.")
        return

    game = games[chat_id]

    if len(game["players"]) >= 2:
        await message.reply("Two players already joined.")
        return

    if message.from_user.id in game["players"]:
        await message.reply("You already joined.")
        return

    game["players"].append(message.from_user.id)
    await message.reply("Joined! Now play by clicking buttons.")


@app.on_callback_query()
async def handle_move(client, callback_query):
    try:
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id
        data = callback_query.data

        if chat_id not in games:
            await callback_query.answer("No game running.", show_alert=True)
            return

        game = games[chat_id]

        if user_id not in game["players"]:
            await callback_query.answer("You are not a player.", show_alert=True)
            return

        if not data.isdigit():
            await callback_query.answer("Invalid move.", show_alert=True)
            return

        index = int(data)
        if index < 0 or index > 8:
            await callback_query.answer("Invalid move.", show_alert=True)
            return

        if game["board"][index] is not None:
            await callback_query.answer("Spot already taken.", show_alert=True)
            return

        current_turn = game["turn"]

        if current_turn == "X":
            expected = game["players"][0]
        else:
            if len(game["players"]) < 2:
                await callback_query.answer("Waiting for second player.", show_alert=True)
                return
            expected = game["players"][1]

        if user_id != expected:
            await callback_query.answer("Not your turn.", show_alert=True)
            return

        game["board"][index] = current_turn
        game["turn"] = "O" if current_turn == "X" else "X"

        winner = check_winner(game["board"])
        if winner:
            if winner == "D":
                msg = "Match Draw!"
            else:
                msg = f"Winner: {winner}"

            await callback_query.message.edit_text(msg)
            del games[chat_id]
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_board_markup(game["board"])
        )
        await callback_query.answer()

    except Exception as e:
        print("Error:", e)
        try:
            await callback_query.answer("Error occurred.")
        except:
            pass
