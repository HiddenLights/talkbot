#
# Copyright (C) 2021-2022 by TeamYukki@Github, < https://github.com/YukkiChatBot >.
#
# This file is part of < https://github.com/TeamYukki/YukkiChatBot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TeamYukki/YukkiChatBot/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
from sys import version as pyver

import pyrogram
from pyrogram import __version__ as pyrover
from pyrogram import filters, idle, StopPropagation
from pyrogram.errors import FloodWait
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import config
import mongo
from mongo import db

loop = asyncio.get_event_loop()
SUDO_USERS = config.SUDO_USER

app = pyrogram.Client(
    ":YukkiBot:",
    config.API_ID,
    config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

save = {}
grouplist = 1


async def init():
    await app.start()

    @app.on_message(filters.command(["start", "help"]))
    async def start_command(_, message: Message):
        if await mongo.is_banned_user(message.from_user.id):
            return
        await mongo.add_served_user(message.from_user.id)
#         await message.reply_photo(
#                     photo="https://telegra.ph/file/d61dc463c5d58be062ba6.jpg",
#                     caption="<b>👋Salut!\n\nAi fost trimis(ă) la verificări, deoarece încercăm să eliminăm conturile false din comunitatea noastră.\nTe rugăm să trimiți un mesaj vocal sau de preferat un video în care să spui: 'Salut, sunt femeie/bărbat și am X ani.\n\nAi 30 minute să trimiți mesajul vocal, altfel accesul îți va fi restricționat pe toată suita de grupuri @intalniri!\nMulțumim!</b>",
#                     reply_markup=InlineKeyboardMarkup(
#                                                       [
#                                                        [
#                                                         InlineKeyboardButton("💬Contact", url="https://t.me/hubcontactbot")
#                                                        ]
#                                                       ]

#                                                      )
# )

    @app.on_message(
        filters.command("mode") & filters.user(SUDO_USERS)
    )
    async def mode_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )
        usage = "**Mod de folosire:**\n\n/mode [group | private]\n\n**Grup**: Toate mesajele primite vor fi redirecționate către grupul de jurnal.\n\n**Private**: Toate mesajele primite vor fi redirecționate către mesajele private ale administratorilor."
        if len(message.command) != 2:
            return await message.reply_text(usage)
        state = message.text.split(None, 1)[1].strip()
        state = state.lower()
        if state == "group":
            await mongo.group_on()
            await message.reply_text(
                "Modul Grup iniţiat. Toate mesajele primite vor fi redirecționate către grupul de jurnal."
            )
        elif state == "private":
            await mongo.group_off()
            await message.reply_text(
                "Modul Privat iniţiat. Toate mesajele primite vor fi redirecționate către mesajele private ale administratorilor."
            )
        else:
            await message.reply_text(usage)

    @app.on_message(
        filters.command("blocat") & filters.user(SUDO_USERS)
    )
    async def block_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )
        if message.reply_to_message:
            if not message.reply_to_message.forward_sender_name:
                return await message.reply_text(
                    "Dă-i reply la mesajul trimis de robot"
                )
            replied_id = message.reply_to_message_id
            try:
                replied_user_id = save[replied_id]
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Nu s-a putut prelua utilizatorul. Este posibil să fi repornit botul sau să fi apărut o eroare. Vă rugăm să verificați jurnalele serverului"
                )
            if await mongo.is_banned_user(replied_user_id):
                return await message.reply_text("Utilizator deja blocat")
            else:
                await mongo.add_banned_user(replied_user_id)
                await message.reply_text("Utilizator restricţionat.")
                try:
                    await app.send_message(
                        replied_user_id,
                        "Ai fost blocat de către administrator.",
                    )
                except:
                    pass
        else:
            return await message.reply_text(
                "Răspundeți la mesajul redirecționat al unui utilizator pentru a-l împiedica să folosească botul"
            )

    @app.on_message(
        filters.command("deblocat") & filters.user(SUDO_USERS)
    )
    async def unblock_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )

        if message.reply_to_message:

            # if not message.reply_to_message.forward_sender_name:
            #     return await message.reply_text(
            #         "Please reply to forwarded messages only."
            #     )

            replied_id = message.reply_to_message_id
            try:
                replied_user_id = save[replied_id]
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Nu s-a putut prelua utilizatorul. Este posibil să fi repornit botul sau să fi apărut o eroare. Vă rugăm să verificați jurnalele serverului"
                )
            if not await mongo.is_banned_user(replied_user_id):
                return await message.reply_text("Utilizatorul nu este restricţionat.")
            else:
                await mongo.remove_banned_user(replied_user_id)
                await message.reply_text(
                    "Utilizator deblocat"
                )
                try:
                    await app.send_message(
                        replied_user_id,
                        "Ai fost deblocat de către administrator.",
                    )
                except:
                    pass
        else:
            return await message.reply_text(
                "Răspundeți la mesajul redirecționat al unui utilizator pentru a-i ridica restricţia."
            )

    @app.on_message(
        filters.command("statistici") & filters.user(SUDO_USERS)
    )
    async def stats_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )
        served_users = len(await mongo.get_served_users())
        blocked = await mongo.get_banned_count()
        text = f""" **Statistici:**
        
**Versiune Python:** {pyver.split()[0]}
**Versiune Pyrogram:** {pyrover}

**Utilizatori conectaţi:** {served_users} 
**Utilizatori blocaţi:** {blocked}"""
        await message.reply_text(text)

    @app.on_message(
        filters.command("emisie") & filters.user(SUDO_USERS)
    )
    async def broadcast_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )
        if message.reply_to_message:
            x = message.reply_to_message.message_id
            y = message.chat.id
        else:
            if len(message.command) < 2:
                return await message.reply_text(
                    "**Usage**:\n/emisie [mesaj] sau [Reply la un mesaj]"
                )
            query = message.text.split(None, 1)[1]

        susr = 0
        served_users = []
        susers = await mongo.get_served_users()
        for user in susers:
            served_users.append(int(user["user_id"]))
        for i in served_users:
            try:
                await app.forward_messages(
                    i, y, x
                ) if message.reply_to_message else await app.send_message(
                    i, text=query
                )
                susr += 1
            except FloodWait as e:
                flood_time = int(e.x)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except Exception:
                pass
        try:
            await message.reply_text(
                f"**Mesaj trimis către {susr} utilizatori.**"
            )
        except:
            pass

    @app.on_message(filters.private & ~filters.edited)
    async def incoming_private(_, message):
        user_id = message.from_user.id
        if await mongo.is_banned_user(user_id):
            return
        if user_id in SUDO_USERS:
            if message.reply_to_message:
                if (
                    message.text == "/deblocat"
                    or message.text == "/blocat"
                    or message.text == "/emisie"
                ):
                    return
                if not message.reply_to_message.forward_sender_name:
                    return await message.reply_text(
                        "Vă rugăm să răspundeți numai la mesajele redirecționate."
                    )
                replied_id = message.reply_to_message_id
                try:
                    replied_user_id = save[replied_id]
                except Exception as e:
                    print(e)
                    return await message.reply_text(
                        "Nu s-a putut prelua utilizatorul. Este posibil să fi repornit botul sau să fi apărut o eroare. Vă rugăm să verificați jurnalele serverului"
                    )
                try:
                    return await app.copy_message(
                        replied_user_id,
                        message.chat.id,
                        message.message_id,
                    )
                except Exception as e:
                    print(e)
                    return await message.reply_text(
                        "Trimiterea mesajului nu a reușit, este posibil ca utilizatorul să fi blocat botul sau s-a întâmplat ceva greșit. Vă rugăm să verificați jurnalele"
                    )
        else:
            if await mongo.is_group():
                try:
                    forwarded = await app.forward_messages(
                        config.LOG_GROUP_ID,
                        message.chat.id,
                        message.message_id,
                        # message.user_id,
                    )

                    save[forwarded.message_id] = user_id
                    await app.sendMessage(chat_id=config.LOG_GROUP_ID, text=f"#id{user_id}")
                except:
                    pass
            else:
                for user in SUDO_USERS:
                    try:
                        forwarded = await app.forward_messages(
                            user, message.chat.id, message.message_id
                        )
                        save[forwarded.message_id] = user_id
                    except:
                        pass

    @app.on_message(
        filters.group & ~filters.edited & filters.user(SUDO_USERS),
        group=grouplist,
    )
    async def incoming_groups(_, message):
        if message.reply_to_message:
            if (
                message.text == "/deblocat"
                or message.text == "/blocat"
                or message.text == "/emisie"
            ):
                return
            replied_id = message.reply_to_message_id
            # if not message.reply_to_message.forward_sender_name:
            #     return await message.reply_text(
            #         "Vă rugăm să răspundeți numai la mesajele redirecționate."
            # )
            try:
                replied_user_id = save[replied_id]
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Nu s-a putut prelua utilizatorul. Este posibil să fi repornit botul sau să fi apărut o eroare. Vă rugăm să verificați jurnalele serverului"
                )
            try:
                return await app.copy_message(
                    replied_user_id,
                    message.chat.id,
                    message.message_id,
                )
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Trimiterea mesajului nu a reușit, este posibil ca utilizatorul să fi blocat botul sau s-a întâmplat ceva greșit. Vă rugăm să verificați jurnalele"
                )

    @app.on_message(
        filters.command("esc") & ~filters.edited & ~filters.bot)
    async def send(_, message):
        await message.delete()
        chat_id = message.chat.id
        if not message.reply_to_message and len(message.command) < 2:
         return await message.reply_text("Offff")
        if message.reply_to_message:
            if len(message.command) > 1:
                send = message.text.split(None, 1)[1]
                reply_id = message.reply_to_message.message_id
                return await app.send_message(chat_id,
                                          text=send,
                                          reply_to_message_id=reply_id)
            else:
                return await message.reply_to_message.copy(chat_id)
        else:
            await bot.send_message(chat_id, text=message.text.split(None, 1)[1])

    print("[LOG] - VerificareBot Started")
    await idle()


if __name__ == "__main__":
    loop.run_until_complete(init())
