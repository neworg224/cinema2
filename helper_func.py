import base64
import re
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL_2, ADMINS
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait




async def is_subscribed(filter, client, update):
    if not FORCE_SUB_CHANNEL and not FORCE_SUB_CHANNEL_2:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
        
    try:
        # Use check_subscription function to maintain consistency
        is_subbed, _ = await check_subscription(client, user_id)
        return is_subbed
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False


async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string


async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    string = string_bytes.decode("ascii")
    return string


async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    
    # Convert to list if single ID
    if isinstance(message_ids, (int, str)):
        message_ids = [message_ids]
    elif isinstance(message_ids, range):
        message_ids = list(message_ids)
        
    # Convert all IDs to integers
    try:
        message_ids = [int(id) for id in message_ids]
    except (ValueError, TypeError) as e:
        print(f"Error converting message IDs to integers: {e}")
        return []
    
    # Process messages in chunks of 200
    while total_messages < len(message_ids):
        chunk = message_ids[total_messages:total_messages + 200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=chunk
            )
            if isinstance(msgs, list):
                messages.extend(msg for msg in msgs if msg is not None)
            else:
                if msgs is not None:
                    messages.append(msgs)
        except Exception as e:
            print(f"Error getting messages: {e}")
        total_messages += len(chunk)
        
    return messages


async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern,message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0


def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time


async def check_subscription(client, user_id):
    """Direct subscription check without filter"""
    if not FORCE_SUB_CHANNEL and not FORCE_SUB_CHANNEL_2:
        return True, []  
    if user_id in ADMINS:
        return True, []  
        
    try:
        not_subbed_channels = []
        
        # Check first channel
        if FORCE_SUB_CHANNEL:
            try:
                member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
                if not member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                    not_subbed_channels.append(FORCE_SUB_CHANNEL)
            except UserNotParticipant:
                not_subbed_channels.append(FORCE_SUB_CHANNEL)
        
        # Check second channel
        if FORCE_SUB_CHANNEL_2:
            try:
                member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL_2, user_id=user_id)
                if not member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                    not_subbed_channels.append(FORCE_SUB_CHANNEL_2)
            except UserNotParticipant:
                not_subbed_channels.append(FORCE_SUB_CHANNEL_2)
        
        # Return True only if subscribed to all required channels
        return len(not_subbed_channels) == 0, not_subbed_channels
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False, []  


subscribed = filters.create(is_subscribed)


# Jishu Developer 
# Don't Remove Credit 
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
