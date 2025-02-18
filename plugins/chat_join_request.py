from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
from database.database import add_user

CONFIRM_TEXT = "<b><i>Welcome to Cinemagic_HD! Here is a quick navigation of TOP films for you to watch 😊 </i></b>\n\n" \
               "<a href='https://t.me/c/2044482291/412'>Kung Fu Panda 4 </a>\n" \
               "<a href='https://t.me/c/2044482291/400'>Dune 2</a>\n" \
               "<a href='https://t.me/c/2044482291/279'>Friends</a>\n" \
               "<a href='https://t.me/c/2044482291/230'>Rick and Morty</a>\n" \
               "<a href='https://t.me/c/2044482291/220'>Oppenheimer</a>\n" \
               "<a href='https://t.me/c/2044482291/200'>The Nun 2</a>\n" \
               "<a href='https://t.me/c/2044482291/180'>The Marvels</a>\n" \
               "<a href='https://t.me/c/2044482291/161'>Barbie</a>\n" \
               "<a href='https://t.me/c/2044482291/175'>Peaky Blinders</a>\n" \
               "<a href='https://t.me/c/2044482291/240'>Attack on Titans</a>\n\n" \
               "<b><i>Just click on movie name to get it, enjoy and don't forget the popcorn🍿!</i></b>"

@Client.on_chat_join_request()
async def req_accept(client: Client, request: ChatJoinRequest):
    try:
        # Get user info
        user = request.from_user
        chat = request.chat
        
        # Log the join request
        print(f"Join request from {user.first_name} ({user.id}) for {chat.title}")
        
        # Accept the request
        await client.approve_chat_join_request(
            chat_id=chat.id,
            user_id=user.id
        )
        print(f"Approved join request for {user.first_name} ({user.id})")
        
        # Add user to database
        await add_user(user.id)
        
        # Send confirmation message with /start command
        await client.send_message(user.id, CONFIRM_TEXT, disable_web_page_preview=True)
        
    except Exception as e:
        print(f"Error handling join request: {str(e)}")