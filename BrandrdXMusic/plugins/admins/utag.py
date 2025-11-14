import asyncio
from typing import Optional

from pyrogram import filters
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message
from BrandrdXMusic import app
from BrandrdXMusic.utils.branded_ban import admin_filter

# ----------------- CONFIG -----------------
BATCH_SIZE = 5                # एक message में कितने users tag करना है
SLEEP_BETWEEN_BATCHES = 7     # हर batch के बाद कितने सेकंड रुके
USE_MARKDOWN_V2 = True        # True => parse_mode="markdownv2" (safer escaping)
# ------------------------------------------

# chat_id -> asyncio.Task
SPAM_CHATS: dict[int, asyncio.Task] = {}


def escape_md_v2(text: str) -> str:
    """
    Escape text for Telegram MarkdownV2.
    Characters to escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    if not text:
        return text
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return "".join(f"\\{c}" if c in escape_chars else c for c in text)


async def _utag_worker(chat_id: int, text: str, origin_message: Message):
    """
    Background worker: iterate members, send batched mentions, honour cancellation.
    """
    try:
        usernum = 0
        usertxt = ""

        async for member in app.get_chat_members(chat_id):
            # stop if task was cancelled or removed
            task = SPAM_CHATS.get(chat_id)
            if task is None or task.cancelled():
                return

            # skip bots
            if getattr(member.user, "is_bot", False):
                continue

            name = getattr(member.user, "first_name", None) or "User"
            if USE_MARKDOWN_V2:
                name = escape_md_v2(name)

            # build mention line (using tg://user?id=)
            usertxt += f"\n⊚ [{name}](tg://user?id={member.user.id})"
            usernum += 1

            if usernum >= BATCH_SIZE:
                # send batch
                try:
                    if USE_MARKDOWN_V2:
                        await app.send_message(
                            chat_id,
                            f"{escape_md_v2(text)}\n{usertxt}\n\n|| ➥ ᴏғғ ᴛᴀɢɢɪɴɢ ʙʏ » /stoputag ||",
                            parse_mode="markdownv2",
                        )
                    else:
                        await app.send_message(
                            chat_id,
                            f"{text}\n{usertxt}\n\n|| ➥ ᴏғғ ᴛᴀɢɢɪɴɢ ʙʏ » /stoputag ||",
                        )
                except FloodWait as fw:
                    # respect server ask
                    await asyncio.sleep(fw.x)
                except RPCError as e:
                    # log and continue
                    print("send_message RPCError:", e)
                except Exception as e:
                    print("send_message error:", e)

                # reset batch and sleep
                usernum = 0
                usertxt = ""

                # Before sleeping, check if stop requested
                if SPAM_CHATS.get(chat_id) is None:
                    return

                await asyncio.sleep(SLEEP_BETWEEN_BATCHES)

        # send any leftover
        if usernum > 0 and SPAM_CHATS.get(chat_id) is not None:
            try:
                if USE_MARKDOWN_V2:
                    await app.send_message(
                        chat_id,
                        f"{escape_md_v2(text)}\n{usertxt}\n\n|| ➥ ᴏғғ ᴛᴀɢɢɪɴɢ ʙʏ » /stoputag ||",
                        parse_mode="markdownv2",
                    )
                else:
                    await app.send_message(
                        chat_id,
                        f"{text}\n{usertxt}\n\n|| ➥ ᴏғғ ᴛᴀɢɢɪɴɢ ʙʏ » /stoputag ||",
                    )
            except FloodWait as fw:
                await asyncio.sleep(fw.x)
            except Exception as e:
                print("final send error:", e)

    except asyncio.CancelledError:
        # expected on stop — just exit quietly
        return
    except FloodWait as fw:
        print("FloodWait while iterating members:", fw.x)
        await asyncio.sleep(fw.x)
    except Exception as e:
        print("Unexpected error in utag worker:", e)
    finally:
        # cleanup mapping if still present
        SPAM_CHATS.pop(chat_id, None)


@app.on_message(filters.command(["utag", "uall"], prefixes=["/", "@", ".", "#"]) & admin_filter)
async def tag_all_users(_, message: Message):
    chat_id = message.chat.id

    # ensure user provided text
    if len(message.text.split()) == 1:
        return await message.reply_text("**Give some text to tag with — e.g.** `/utag Hi friends`")

    text = message.text.split(None, 1)[1].strip()
    if not text:
        return await message.reply_text("**Provide a valid message to tag with.**")

    # if already running, notify
    existing = SPAM_CHATS.get(chat_id)
    if existing and not existing.done():
        return await message.reply_text("**ᴜᴛᴀɢ ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ ɪɴ ᴛʜɪs ᴄʜᴀᴛ.**")

    # ack and start worker
    await message.reply_text(
        f"**ᴜᴛᴀɢ [started] — Batch {BATCH_SIZE}, Delay {SLEEP_BETWEEN_BATCHES}s.**\nStop with `/stoputag`"
    )

    task = asyncio.create_task(_utag_worker(chat_id, text, message))
    SPAM_CHATS[chat_id] = task


@app.on_message(
    filters.command(
        ["stoputag", "stopuall", "offutag", "offuall", "utagoff", "ualloff"],
        prefixes=["/", ".", "@", "#"],
    )
    & admin_filter
)
async def stop_tagging(_, message: Message):
    chat_id = message.chat.id
    task: Optional[asyncio.Task] = SPAM_CHATS.get(chat_id)

    if task is None:
        return await message.reply_text("**ᴜᴛᴀɢ ɪs ɴᴏᴛ ᴀᴄᴛɪᴠᴇ.**")

    # cancel and remove mapping immediately
    if not task.done():
        task.cancel()
    SPAM_CHATS.pop(chat_id, None)
    await message.reply_text("**Stopping UTAG...**")
