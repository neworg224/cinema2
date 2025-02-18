import os
import logging
import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from config import ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, FILE_AUTO_DELETE, LANGUAGES
from helper_func import subscribed, encode, decode, get_messages, check_subscription
from database.database import add_user, del_user, full_userbase, present_user, set_user_language, get_user_language
from plugins.translations import get_translated_message, TRANSLATIONS
from plugins.start import delete_files, broadcast_sessions, pending_broadcast_messages, do_broadcast
from pyrogram.enums import ParseMode

madflixofficials = FILE_AUTO_DELETE
jishudeveloper = madflixofficials
file_auto_delete = str(int(jishudeveloper / 60)) if jishudeveloper else None

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    try:
        data = query.data
        user_lang = await get_user_language(query.from_user.id) or 'en'

        # Handle broadcast callbacks
        if data.startswith("broadcast_"):
            if query.from_user.id not in ADMINS:
                await query.answer("You are not authorized to broadcast messages.", show_alert=True)
                return
                
            target = data.split('_')[1]
            user_id = query.from_user.id
            
            # Check if there's a pending broadcast message
            if user_id not in pending_broadcast_messages:
                await query.answer("No message selected for broadcast. Please reply to a message with /broadcast", show_alert=True)
                return
            
            # Get the message to broadcast
            broadcast_msg = pending_broadcast_messages.pop(user_id)
            
            # Answer the callback query
            await query.answer("Starting broadcast...")
            
            # Delete the selection message
            await query.message.delete()
            
            # Do the broadcast
            await do_broadcast(client, query.message, target, broadcast_msg)
            return

        # Handle language selection with state preservation
        if data.startswith("setlang_"):
            parts = data.split("_")
            if len(parts) < 2:
                await query.answer("Invalid language selection.", show_alert=True)
                return
                
            lang_code = parts[1]
            file_id = parts[2] if len(parts) > 2 else None
            
            try:
                # Show processing message
                await query.answer("Setting language...", show_alert=False)
                
                # Set the language
                success = await set_user_language(query.from_user.id, lang_code)
                if not success:
                    await query.answer("Failed to set language. Please try again.", show_alert=True)
                    return

                # After setting language, check subscription
                if file_id and file_id != "none":
                    is_subbed, not_subbed_channels = await check_subscription(client, query.from_user.id)
                    if not is_subbed:
                        # Get invite links for both channels
                        buttons = []
                        for channel_id in not_subbed_channels:
                            try:
                                chat = await client.get_chat(channel_id)
                                invite_link = chat.invite_link or await chat.export_invite_link()
                                buttons.append([InlineKeyboardButton(
                                    f"{get_translated_message('BTN_JOIN_CHANNEL', lang_code)} {chat.title}", 
                                    url=invite_link
                                )])
                            except Exception as e:
                                logging.error(f"Error getting chat info: {str(e)}")
                                continue
                        
                        buttons.append([InlineKeyboardButton(
                            get_translated_message('BTN_CHECK_SUB', lang_code),
                            callback_data=f"checksub_{file_id}"
                        )])
                        
                        await query.message.edit_text(
                            text=get_translated_message('FORCE_MSG', lang_code),
                            reply_markup=InlineKeyboardMarkup(buttons)
                        )
                        return
                    
                    # Only process file if user is subscribed
                    await process_file(client, query.message, file_id, lang_code)
                else:
                    # Show main menu
                    reply_markup = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(
                                get_translated_message('BTN_ABOUT', lang_code),
                                callback_data="about"
                            ),
                            InlineKeyboardButton(
                                get_translated_message('BTN_CHANGE_LANG', lang_code),
                                callback_data="change_lang"
                            )
                        ],
                        [InlineKeyboardButton(
                            get_translated_message('BTN_CLOSE', lang_code),
                            callback_data="close"
                        )]
                    ])
                    await query.message.edit_text(
                        text=get_translated_message('START_MSG', lang_code).format(
                            first=query.from_user.first_name,
                            last=query.from_user.last_name,
                            username=None if not query.from_user.username else '@' + query.from_user.username,
                            mention=query.from_user.mention,
                            id=query.from_user.id
                        ),
                        reply_markup=reply_markup
                    )
            except Exception as e:
                logging.error(f"Error in language setting: {str(e)}")
                await query.answer("An error occurred. Please try again.", show_alert=True)

        elif data.startswith("checksub_"):
            file_id = data.split("_")[1]
            
            is_subbed, not_subbed_channels = await check_subscription(client, query.from_user.id)
            if is_subbed:
                await process_file(client, query.message, file_id, user_lang)
            else:
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
                        logging.error(f"Error getting chat info: {str(e)}")
                        continue
                
                buttons.append([InlineKeyboardButton(
                    get_translated_message('BTN_CHECK_SUB', user_lang),
                    callback_data=f"checksub_{file_id}"
                )])
                
                await query.answer(get_translated_message('SUB_FAIL', user_lang), show_alert=True)
                await query.message.edit_text(
                    text=get_translated_message('FORCE_MSG', user_lang),
                    reply_markup=InlineKeyboardMarkup(buttons)
                )

        elif data == "about":
            await query.message.edit_text(
                text=get_translated_message('ABOUT_MSG', user_lang),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        get_translated_message('BTN_BACK', user_lang),
                        callback_data="start"
                    )]
                ])
            )

        elif data == "close":
            await query.message.delete()
            try:
                await query.message.reply_to_message.delete()
            except:
                pass

        elif data == "start":
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        get_translated_message('BTN_ABOUT', user_lang),
                        callback_data="about"
                    ),
                    InlineKeyboardButton(
                        get_translated_message('BTN_CHANGE_LANG', user_lang),
                        callback_data="change_lang"
                    )
                ],
                [InlineKeyboardButton(
                    get_translated_message('BTN_CLOSE', user_lang),
                    callback_data="close"
                )]
            ])
            await query.message.edit_text(
                text=get_translated_message('START_MSG', user_lang).format(
                    first=query.from_user.first_name,
                    last=query.from_user.last_name,
                    username=None if not query.from_user.username else '@' + query.from_user.username,
                    mention=query.from_user.mention,
                    id=query.from_user.id
                ),
                reply_markup=reply_markup
            )

        elif data == "change_lang":
            try:
                language_buttons = []
                for lang_code, lang_name in LANGUAGES.items():
                    language_buttons.append([InlineKeyboardButton(lang_name, callback_data=f"setlang_{lang_code}_none")])
                
                language_buttons.append([InlineKeyboardButton(
                    get_translated_message('BTN_BACK', user_lang),
                    callback_data="start"
                )])
                
                await query.message.edit_text(
                    text=get_translated_message('SELECT_LANG', user_lang),
                    reply_markup=InlineKeyboardMarkup(language_buttons)
                )
            except Exception as e:
                logging.error(f"Error in language selection: {str(e)}")
                await query.answer("An error occurred. Please try again.", show_alert=True)

    except Exception as e:
        logging.error(f"Error in callback handler: {str(e)}")
        try:
            await query.answer("An error occurred. Please try again.", show_alert=True)
        except Exception as answer_error:
            logging.error(f"Error sending error message: {str(answer_error)}")

async def process_file(client, message, file_id, user_lang):
    try:
        await message.edit_text(get_translated_message('PLEASE_WAIT', user_lang))
        
        try:
            # Decode the file_id if it's encoded
            decoded_file_id = await decode(file_id)
            if decoded_file_id.startswith('get-'):
                # Extract the actual message ID
                msg_id = int(decoded_file_id.split('-')[1])
                if msg_id < 0:
                    msg_id = abs(msg_id)
                msg_id = int(msg_id / abs(client.db_channel.id))
            else:
                msg_id = int(file_id)
        except Exception as e:
            logging.error(f"Error decoding file ID: {str(e)}")
            msg_id = int(file_id)
        
        messages = await get_messages(client, msg_id)
        
        if not messages:
            await message.edit_text(get_translated_message('ERROR_GENERIC', user_lang))
            return
            
        for msg in messages:
            if not msg:
                continue
                
            try:
                copied_msg = await msg.copy(
                    chat_id=message.chat.id,
                    caption=CUSTOM_CAPTION if CUSTOM_CAPTION else msg.caption,
                    parse_mode=ParseMode.HTML,
                    protect_content=PROTECT_CONTENT
                )
                
                # Send file deletion warning after the file is sent
                if file_auto_delete:
                    warning_msg = await message.reply_text(
                        get_translated_message('FILE_DELETE_WARNING', user_lang).format(
                            time_left=file_auto_delete
                        )
                    )
                    # Create deletion tasks
                    asyncio.create_task(delete_files(warning_msg, file_auto_delete))
                    asyncio.create_task(delete_files(copied_msg, file_auto_delete))
                    
            except Exception as e:
                logging.error(f"Error copying message: {str(e)}")
                await message.edit_text(get_translated_message('ERROR_GENERIC', user_lang))
                return
                
            await asyncio.sleep(0.5)
        
        await message.delete()
        
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        await message.edit_text(get_translated_message('ERROR_GENERIC', user_lang))

# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Thank you ❤️
