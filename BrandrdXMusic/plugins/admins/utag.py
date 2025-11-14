import asyncio
from collections import defaultdict
from pyrogram import filters
from BrandrdXMusic import app
from BrandrdXMusic.utils.branded_ban import admin_filter

SPAM_CHATS = defaultdict(bool)

@app.on_message(filters.command(["utag", "uall"], prefixes=["/", "@", ".", "#"]) & admin_filter)
async def tag_all_users(_, message):
    chat_id = message.chat.id

    if len(message.text.split()) == 1:
        return await message.reply_text("**Give some text to tag all, like »** `@utag Hello`")

    text = message.text.split(None, 1)[1]
    await message.reply_text(
        "**Unlimited tagging started!**\n\n"
        "**Stop it anytime with » /stoputag**"
    )

    SPAM_CHATS[chat_id] = True

    while SPAM_CHATS[chat_id]:
        usernum = 0
        usertxt = ""
        async for m in app.get_chat_members(chat_id):
            if not SPAM_CHATS[chat_id]:
                break  # 🔥 तुरंत stop कर देगा

            if m.user.is_bot:
                continue
            usernum += 1
            usertxt += f"\n⊚ [{m.user.first_name}](tg://user?id={m.user.id})"

            if usernum == 5:
                await app.send_message(
                    chat_id,
                    f"{text}\n{usertxt}\n\n|| ➥ Off tagging by » /stoputag ||"
                )
                usernum = 0
                usertxt = ""

                # 🔥 Instead of one long sleep, छोटे हिस्सों में check करो
                for _ in range(7):
                    if not SPAM_CHATS[chat_id]:
                        break
                    await asyncio.sleep(1)

        if not SPAM_CHATS[chat_id]:
            break

    await message.reply_text("**Unlimited tagging stopped successfully.**")

@app.on_message(filters.command(
    ["stoputag", "stopuall", "offutag", "offuall", "utagoff", "ualloff"],
    prefixes=["/", ".", "@", "#"]) & admin_filter
)
async def stop_tagging(_, message):
    chat_id = message.chat.id
    if SPAM_CHATS.get(chat_id):
        SPAM_CHATS[chat_id] = False
        await message.reply_text("**Stopping unlimited tagging...**")
    else:
        await message.reply_text("**No active utag process in this chat.**")
        
