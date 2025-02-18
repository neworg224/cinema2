import os, asyncio, humanize
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, FILE_AUTO_DELETE, LANGUAGES
from helper_func import subscribed, encode, decode, get_messages, check_subscription
from plugins.translations import get_translated_message, get_custom_caption_translation, TRANSLATIONS

from database.database import (
    add_user, del_user, full_userbase, present_user,
    set_user_language, get_user_language,
    get_users_by_language, get_language_stats 
)

madflixofficials = FILE_AUTO_DELETE
jishudeveloper = madflixofficials
file_auto_delete = str(int(jishudeveloper / 60))

# Add language options dictionary with organized groups
LANGUAGES = LANGUAGES

# Dictionary to store broadcast sessions and messages
broadcast_sessions = {}
pending_broadcast_messages = {}

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass
    
    # Get the command parameter (file info) if any
    file_id = None
    if len(message.command) > 1:
        file_id = message.command[1]
    
    # Check if user has selected language
    user_lang = await get_user_language(id)
    
    if not user_lang:
        # Show language selection buttons with state management
        language_buttons = []
        row = []
        for lang_code, lang_name in LANGUAGES.items():
            # Include file_id in callback data
            callback_data = f"setlang_{lang_code}"
            if file_id:
                callback_data += f"_{file_id}"
            else:
                callback_data += "_none"
            row.append(InlineKeyboardButton(lang_name, callback_data=callback_data))
            if len(row) == 2:  # Create rows of 2 buttons each
                language_buttons.append(row)
                row = []
        if row:  # Add any remaining button
            language_buttons.append(row)
            
        reply_markup = InlineKeyboardMarkup(language_buttons)
        await message.reply_text(
            "🌐 Please select your language:",
            reply_markup=reply_markup
        )
        return
    
    try:
        if file_id:
            try:
                # Check subscription
                is_subbed, not_subbed_channels = await check_subscription(client, id)
                if not is_subbed:
                    # Get invite links for both channels
                    buttons = []
                    for channel_id in not_subbed_channels:
                        try:
                            chat = await client.get_chat(channel_id)
                            invite_link = chat.invite_link or await chat.export_invite_link()
                            buttons.append([InlineKeyboardButton(
                                f"{get_translated_message('BTN_JOIN_CHANNEL', user_lang)} {chat.title}", 
                                url=invite_link
                            )])
                        except Exception as e:
                            print(f"Error getting chat info: {str(e)}")
                            continue
                    
                    buttons.append([InlineKeyboardButton(
                        get_translated_message('BTN_CHECK_SUB', user_lang),
                        callback_data=f"checksub_{file_id}"
                    )])
                    
                    await message.reply_text(
                        text=get_translated_message('FORCE_MSG', user_lang),
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    return
                
                # User is subscribed, process the file
                temp_msg = await message.reply(get_translated_message('PLEASE_WAIT', user_lang))
                
                try:
                    # Decode the file_id if it's encoded
                    string = await decode(file_id)
                    argument = string.split("-")
                    
                    message_ids = []
                    if len(argument) == 3:
                        try:
                            start = int(int(argument[1]) / abs(client.db_channel.id))
                            end = int(int(argument[2]) / abs(client.db_channel.id))
                            if start <= end:
                                message_ids = list(range(start, end + 1))
                            else:
                                message_ids = list(range(end, start + 1))[::-1]
                        except Exception as e:
                            print(f"Error processing batch range: {e}")
                            await temp_msg.edit_text("Something went wrong processing the batch link..")
                            return
                    elif len(argument) == 2:
                        try:
                            msg_id = int(int(argument[1]) / abs(client.db_channel.id))
                            message_ids = [msg_id]
                        except Exception as e:
                            print(f"Error processing single message ID: {e}")
                            await temp_msg.edit_text("Something went wrong processing the link..")
                            return
                    
                    if not message_ids:
                        await temp_msg.edit_text("Invalid link format.")
                        return
                        
                    messages = await get_messages(client, message_ids)
                    if not messages:
                        await temp_msg.edit_text(get_translated_message('ERROR_GENERIC', user_lang))
                        return
                        
                    await temp_msg.delete()
                    
                    success_count = 0
                    copied_messages = []  # Keep track of copied messages
                    
                    for msg in messages:
                        if not msg:
                            continue
                            
                        try:
                            copied_msg = await msg.copy(
                                chat_id=message.chat.id,
                                caption=get_custom_caption_translation(msg.document.file_name if msg.document else msg.video.file_name if msg.video else "File", user_lang),
                                parse_mode=ParseMode.HTML,
                                protect_content=PROTECT_CONTENT
                            )
                            if copied_msg:
                                copied_messages.append(copied_msg)
                                success_count += 1
                                
                        except FloodWait as e:
                            await asyncio.sleep(e.x)
                            # Retry after flood wait
                            copied_msg = await msg.copy(
                                chat_id=message.chat.id,
                                caption=get_custom_caption_translation(msg.document.file_name if msg.document else msg.video.file_name if msg.video else "File", user_lang),
                                parse_mode=ParseMode.HTML,
                                protect_content=PROTECT_CONTENT
                            )
                            if copied_msg:
                                copied_messages.append(copied_msg)
                                success_count += 1
                            
                        except Exception as e:
                            print(f"Error copying message: {str(e)}")
                            continue
                            
                        await asyncio.sleep(0.5)
                    
                    # Send warning message after all files are sent
                    if success_count > 0 and file_auto_delete:
                        warning_msg = await message.reply_text(
                            get_translated_message('FILES_DELETE_WARNING', user_lang).format(
                                time_left=file_auto_delete
                            )
                        )
                        # Create deletion tasks for all messages
                        asyncio.create_task(delete_files(warning_msg, file_auto_delete))
                        for copied_msg in copied_messages:
                            asyncio.create_task(delete_files(copied_msg, file_auto_delete))
                    elif success_count == 0:
                        await message.reply_text(get_translated_message('ERROR_GENERIC', user_lang))
                    
                except Exception as e:
                    print(f"Error in batch processing: {e}")
                    await message.reply_text(f"Error processing batch: {str(e)}")
                return
                
            except Exception as e:
                print(f"Error in subscription check: {e}")
                await message.reply_text(f"Invalid link or something went wrong: {str(e)}")
            return
            
    except Exception as e:
        print(f"Error in start command: {str(e)}")
        pass

    buttons = [[
        InlineKeyboardButton(get_translated_message('BTN_ABOUT', user_lang), callback_data='about'),
        InlineKeyboardButton(get_translated_message('BTN_CHANGE_LANG', user_lang), callback_data='change_lang')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await message.reply_text(
        text=get_translated_message('START_MSG', user_lang).format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )

@Bot.on_message(filters.command('broadcast') & filters.private & filters.user(ADMINS))
async def broadcast_command(client: Bot, message: Message):
    if message.reply_to_message:
        # Store the message to broadcast
        pending_broadcast_messages[message.from_user.id] = message.reply_to_message
        
        # Show language selection buttons
        buttons = []
        # Add button for all users
        buttons.append([InlineKeyboardButton("📢 Broadcast to All", callback_data="broadcast_all")])
        
        # Add buttons for each language in pairs
        row = []
        for lang_code, lang_name in LANGUAGES.items():
            button_text = f"{lang_name}"
            row.append(InlineKeyboardButton(button_text, callback_data=f"broadcast_{lang_code}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:  # Add any remaining button
            buttons.append(row)
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_text(
            "Select target audience for your broadcast:",
            reply_markup=reply_markup
        )
    else:
        msg = await message.reply("Please reply to a message to broadcast it.")
        await asyncio.sleep(5)
        await msg.delete()
        await message.delete()

async def do_broadcast(client: Bot, message: Message, target: str, broadcast_msg: Message):
    try:
        # Get target users
        if target == 'all':
            users = await full_userbase()
        else:
            users = await get_users_by_language(target)
        
        if not users:
            await message.reply_text("No users found in the selected target group.")
            return
        
        # Initialize counters
        total = len(users)
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        progress_message = await message.reply_text(
            "<i>Broadcasting Message.. This will Take Some Time</i>\n"
            f"Target: {'All Users' if target == 'all' else f'Users with language {LANGUAGES.get(target, target)}'}\n"
            f"Total users: {total}"
        )
        
        # Broadcast the message
        for user_id in users:
            try:
                await broadcast_msg.copy(chat_id=user_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id=user_id)
                successful += 1
            except UserIsBlocked:
                blocked += 1
                await del_user(user_id)
            except InputUserDeactivated:
                deleted += 1
                await del_user(user_id)
            except Exception as e:
                print(e)
                unsuccessful += 1
            
            # Update progress every 20 users
            if (successful + blocked + deleted + unsuccessful) % 20 == 0:
                try:
                    await progress_message.edit_text(
                        f"<i>Broadcasting Message..</i>\n"
                        f"Target: {'All Users' if target == 'all' else f'Users with language {LANGUAGES.get(target, target)}'}\n"
                        f"<b>Total Users :</b> <code>{total}</code>\n"
                        f"<b>Successful :</b> <code>{successful}</code>\n"
                        f"<b>Blocked Users :</b> <code>{blocked}</code>\n"
                        f"<b>Deleted Accounts :</b> <code>{deleted}</code>\n"
                        f"<b>Unsuccessful :</b> <code>{unsuccessful}</code>"
                    )
                except:
                    pass
        
        # Send final status
        await progress_message.edit_text(
            f"<b><u>Broadcast Completed</u></b>\n\n"
            f"Target: {'All Users' if target == 'all' else f'Users with language {LANGUAGES.get(target, target)}'}\n"
            f"<b>Total Users :</b> <code>{total}</code>\n"
            f"<b>Successful :</b> <code>{successful}</code>\n"
            f"<b>Blocked Users :</b> <code>{blocked}</code>\n"
            f"<b>Deleted Accounts :</b> <code>{deleted}</code>\n"
            f"<b>Unsuccessful :</b> <code>{unsuccessful}</code>"
        )
    except Exception as e:
        print(f"Error in broadcast: {str(e)}")
        await message.reply_text("❌ An error occurred during broadcast. Please try again.")

@Bot.on_message(filters.command('cancel') & filters.private & filters.user(ADMINS))
async def cancel_broadcast(client: Bot, message: Message):
    user_id = message.from_user.id
    cancelled = False
    
    if user_id in broadcast_sessions:
        broadcast_sessions.pop(user_id)
        cancelled = True
        
    if user_id in pending_broadcast_messages:
        pending_broadcast_messages.pop(user_id)
        cancelled = True
        
    if cancelled:
        await message.reply_text("✅ Broadcast cancelled successfully.")
    else:
        await message.reply_text("❌ No active broadcast to cancel.")

@Bot.on_message(filters.private & filters.user(ADMINS) & ~filters.command(['broadcast', 'start', 'users', 'cancel', 'batch', 'genlink', 'stats']))
async def handle_broadcast_message(client: Bot, message: Message):
    user_id = message.from_user.id
    
    # Only handle messages if user has a pending broadcast
    if user_id not in broadcast_sessions:
        return
    
    try:
        # Get target and message
        target = broadcast_sessions.pop(user_id)
        broadcast_msg = pending_broadcast_messages.pop(user_id)
        
        await do_broadcast(client, message, target, broadcast_msg)
    except Exception as e:
        print(f"Error in broadcast: {str(e)}")
        await message.reply_text("❌ An error occurred during broadcast. Please try again.")

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def users_command(client: Bot, message: Message):
    # Get language statistics
    stats = await get_language_stats()
    
    # Calculate total users first
    total = sum(stats.values())
    if total == 0:
        await message.reply_text("No users found in database.")
        return
    
    # Create statistics message
    text = "📊 User Statistics:\n\n"
    
    # Add stats for each language with percentage
    for lang_code, count in stats.items():
        percentage = (count / total * 100)
        if lang_code == "no_language":
            text += f"🔸 No Language Selected: {count} users ({percentage:.1f}%)\n"
        else:
            lang_name = LANGUAGES.get(lang_code, lang_code)
            # Get flag emoji from language name if it contains one
            flag = "🌐"  # default flag if none found
            for item in lang_name.split():
                if len(item) == 2:  # Most flag emojis are 2 characters
                    flag = item
                    break
            text += f"🔸 {lang_name}: {count} users ({percentage:.1f}%)\n"
    
    text += f"\n📈 Total Users: {total}"
    
    # Add broadcast options
    buttons = [
        [InlineKeyboardButton(f"📢 Broadcast (All - {total} users)", callback_data="broadcast_all")],
    ]
    
    # Add language-specific broadcast buttons
    for lang_code, count in stats.items():
        if lang_code != "no_language" and count > 0:
            lang_name = LANGUAGES.get(lang_code, lang_code)
            buttons.append([InlineKeyboardButton(
                f"📢 {lang_name} ({count} users)",
                callback_data=f"broadcast_{lang_code}"
            )])
    
    # Add close button
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close")])
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Bot.on_callback_query(filters.regex('^broadcast_'))
async def broadcast_callback(client: Bot, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in ADMINS:
        await callback.answer("You are not authorized to broadcast messages.", show_alert=True)
        return
    
    target = callback.data.split('_')[1]
    
    # Store the broadcast target for later use
    broadcast_sessions[user_id] = target
    
    # Send instructions
    text = "Please send the message you want to broadcast.\n\n"
    if target == "all":
        text += "This will be sent to ALL users (including those who haven't selected a language)."
    else:
        lang_name = LANGUAGES.get(target, target)
        text += f"This will be sent to users who selected {lang_name}."
    
    text += "\n\nTo cancel, click the button below."
    
    # Add cancel button
    buttons = [[InlineKeyboardButton("❌ Cancel Broadcast", callback_data="cancel_broadcast")]]
    
    await callback.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await callback.answer()

# Function to handle file deletion
async def delete_files(msg, delete_after):
    try:
        await asyncio.sleep(int(delete_after) * 60)  # Convert minutes to seconds
        await msg.delete()
    except Exception as e:
        print(f"Error deleting message {msg.id}: {e}")

# Jishu Developer 
# Don't Remove Credit 
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper

# Add new callback handlers
@Bot.on_callback_query(filters.regex('^lang_'))
async def language_callback(client: Client, callback_query: CallbackQuery):
    # Extract language code and file_id from callback data
    parts = callback_query.data.split('_')
    lang_code = parts[1]
    file_id = parts[2] if len(parts) > 2 else None
    
    user_id = callback_query.from_user.id
    await set_user_language(user_id, lang_code)
    
    # Immediately show force subscription message in selected language
    buttons = [
        [
            InlineKeyboardButton(
                text=get_translated_message('BTN_JOIN_CHANNEL', lang_code),
                url=f"https://t.me/{FORCE_SUB_CHANNEL}"
            )
        ]
    ]
    
    if file_id:
        buttons.append([
            InlineKeyboardButton(
                text=get_translated_message('BTN_TRY_AGAIN', lang_code),
                url=f"https://t.me/{client.username}?start={file_id}"
            )
        ])
    
    await callback_query.message.edit_text(
        text=get_translated_message('FORCE_MSG', lang_code),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Bot.on_callback_query(filters.regex('^change_lang$'))
async def change_language_callback(client: Client, callback_query: CallbackQuery):
    language_buttons = []
    row = []
    for lang_code, lang_name in LANGUAGES.items():
        row.append(InlineKeyboardButton(lang_name, callback_data=f"lang_{lang_code}"))
        if len(row) == 2:
            language_buttons.append(row)
            row = []
    if row:
        language_buttons.append(row)
    
    await callback_query.message.edit_text(
        "Select your new language:",
        reply_markup=InlineKeyboardMarkup(language_buttons)
    )
