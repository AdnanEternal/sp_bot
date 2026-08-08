from splusthon import SoroushClient, events
from splusthon.sessions import StringSession
from splusthon.tl.types import PeerUser
import managers.setting_manager as setting_manager
setting_manager=setting_manager.SettingsManager()

def get_media_id(event):
    if not event.media:
        return None
    
    # Document media types include music, video, stiker and gifs
    if hasattr(event.media, 'document') and event.media.document:
        return event.media.document.id
    
    # Photo
    if hasattr(event.media, 'photo') and event.media.photo:
        return event.media.photo.id
    
    # id media types include voice
    if hasattr(event.media, 'id'):
        return event.media.id
    
    return None


def is_private_chat(event):
    return isinstance(event.message.peer_id, PeerUser)
def is_sender_developer(event):
    if event.sender_id == setting_manager.get_base_setting()['developer_id']:
        return True
    return False

def is_sender_bot_admin(event):
    if event.sender_id in setting_manager.get_group_settings(event.chat_id)['admins'] or is_sender_developer(event):
        return True
    return False
def is_sender_chat_admin(event):
    if event.sender_id in get_bot_admins(event.chat_id) or event.sender_id == setting_manager.get_base_setting()['developer_id']:
        return True
    return False
def get_bot_admins(group_id):
    group = setting_manager.get_group_settings(group_id)
    return group['admins']


async def is_reply_to_bot(event,sp_client):
    if not event.reply_to:
        return False
    me = await sp_client.get_me()
    replied_msg=await sp_client.get_messages(event.chat_id,ids=event.reply_to_msg_id)

    if replied_msg.from_id.user_id == me.id:
        return True
    return False