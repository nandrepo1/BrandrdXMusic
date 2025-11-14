from BrandrdXMusic import app
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import filters

games = {}

def get_board_markup(board):
    keyboard = []
    for i in range(0, 9, 3):
        row = [
            InlineKeyboardButton(
                board[i+j] if board[i+j] != " " else " ",
                callback_data=str(i+j)
            )
            for j in range(3)
        ]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def check_winner(board):
    wins = [
        (0,1,2), (3,4,5), (6,7,8),
        (0,3,6), (1,4,7), (2,5,8),
        (0,4,8), (2,4,6)
    ]
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
        await message.reply("A game is already running here!")
    else:
        games[chat_id] = {
            "board": [" "] * 9,
            "turn": "X",
            "players": [message.from_user.id],
        }
        await message.reply(
            "Tic-Tac-Toe started! Second player, join using /joingame.",
            reply_markup=get_board_markup(games[chat_id]["board"])
        )


@app.on_message(filters.command("joingame", prefixes=["/"]))
async def join_game(client, message):
    chat_id = message.chat.id

    if chat_id not in games:
        await message.reply("No game is running. Start one using /startgame.")
        return

    game = games[chat_id]

    if len(game["players"]) >= 2:
        await message.reply("Two players have already joined.")
        return

    if message.from_user.id in game["players"]:
        await message.reply("You are already part of this game.")
        return

    game["players"].append(message.from_user.id)
    await message.reply("You joined the game! Now click buttons to make your move.")


@app.on_callback_query()
async def handle_move(client, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if chat_id not in games:
        await callback_query.answer("No game is currently running.", show_alert=True)
        return

    game = games[chat_id]

    if user_id not in game["players"]:
        await callback_query.answer("You are not a player in this game.", show_alert=True)
        return

    index = int(callback_query.data)

    if game["board"][index] != " ":
        await callback_query.answer("This spot is already taken.", show_alert=True)
        return

    current_turn = game["turn"]

    # Turn check
    if (current_turn == "X" and user_id != game["players"][0]) or \
       (current_turn == "O" and user_id != game["players"][1]):
        await callback_query.answer("It’s not your turn yet.", show_alert=True)
        return

    game["board"][index] = current_turn
    game["turn"] = "O" if current_turn == "X" else "X"

    winner = check_winner(game["board"])
    if winner:
        if winner == "D":
            result_text = "The game is a draw!"
        else:
            result_text = f"Game Over — Winner: {winner}"

        await callback_query.message.edit_text(result_text)
        del games[chat_id]
    else:
        await callback_query.message.edit_reply_markup(
            reply_markup=get_board_markup(game["board"])
        )
        await callback_query.answer()
