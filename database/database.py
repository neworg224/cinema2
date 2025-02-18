import pymongo, os
from config import DB_URL, DB_NAME
import logging

try:
    dbclient = pymongo.MongoClient(DB_URL)
    database = dbclient[DB_NAME]
    user_data = database['users']
    # Test the connection
    dbclient.server_info()
    logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.error(f"Error connecting to MongoDB: {str(e)}")
    raise

async def present_user(user_id: int):
    try:
        found = user_data.find_one({'_id': user_id})
        return bool(found)
    except Exception as e:
        logging.error(f"Error checking user presence: {str(e)}")
        return False

async def add_user(user_id: int):
    try:
        # Use update_one with upsert to avoid duplicate key errors
        user_data.update_one(
            {'_id': user_id},
            {'$setOnInsert': {'_id': user_id}},
            upsert=True
        )
        return True
    except Exception as e:
        logging.error(f"Error adding user: {str(e)}")
        return False

async def full_userbase():
    try:
        user_docs = user_data.find()
        return [doc['_id'] for doc in user_docs]
    except Exception as e:
        logging.error(f"Error getting full userbase: {str(e)}")
        return []

async def del_user(user_id: int):
    try:
        result = user_data.delete_one({'_id': user_id})
        return result.deleted_count > 0
    except Exception as e:
        logging.error(f"Error deleting user: {str(e)}")
        return False

async def set_user_language(user_id: int, language: str):
    try:
        # First ensure user exists
        await add_user(user_id)
        # Then update language
        result = user_data.update_one(
            {'_id': user_id},
            {'$set': {'language': language}},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    except Exception as e:
        logging.error(f"Error setting user language: {str(e)}")
        raise  # Re-raise the exception to handle it in the callback

async def get_user_language(user_id: int) -> str:
    try:
        user = user_data.find_one({'_id': user_id})
        return user.get('language') if user else None
    except Exception as e:
        logging.error(f"Error getting user language: {str(e)}")
        return None

async def get_users_by_language(language: str = None):
    try:
        if language:
            # Get users with specific language
            users = user_data.find({'language': language})
        else:
            # Get users with no language set
            users = user_data.find({'language': {'$exists': False}})
        return [doc['_id'] for doc in users]
    except Exception as e:
        logging.error(f"Error getting users by language: {str(e)}")
        return []

async def get_language_stats():
    try:
        # Initialize stats dictionary
        stats = {}
        
        # Count users with language set
        cursor = user_data.find({"language": {"$exists": True}})
        for doc in cursor:
            lang = doc.get('language')
            if lang:
                stats[lang] = stats.get(lang, 0) + 1
        
        # Count users without language
        no_lang_count = user_data.count_documents({"language": {"$exists": False}})
        if no_lang_count > 0:
            stats["no_language"] = no_lang_count
            
        return stats
    except Exception as e:
        logging.error(f"Error getting language stats: {str(e)}")
        return {}

# Jishu Developer 
# Don't Remove Credit 
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
