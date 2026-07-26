import asyncio
from openai import OpenAI
from splusthon import SoroushClient, events
from splusthon.sessions import StringSession
import group_manager
import setting_manager as setting_manager
import utils
from typing import Dict,Optional
from backup_manager import *
BLACKLIST_FILE = "gif_blacklist.json"
group_settings_path = 'groups_settings.json'

DEV_ID = 49245702






system_message="""
You are a funny, salty friend, incredibly warm and cool. You are the admin of the group and messenger, and your name is "گاردی".

Messages you receive are in this format:
`[username]: [message]`

Your job is to respond to the last user who sent a message. 
When you reply, speak directly to that user in a natural, conversational way. 
Do NOT include the username at the start of your response. Just reply with your message.

Always respond in Persian.
و جوری رفتار کن که انگار همه ی اعضای گروه رو میشناسی اما به هیچ وجه بی ادبی نکن

"""




def is_message_clean(event):
    pass



class AgentManager:
    def __init__(self,sp_client):
        self.sp_client = sp_client

        self.openai_client =  OpenAI(
                    api_key='sk-JcUnps6czsZz95dlsByQAXr9XPnJhWkoMMGKMXhPooij8wlg',
                    base_url="https://apihub.agnes-ai.com/v1/",
                    max_retries=9999999

                )
        self._clients_cache: Dict[int, OpenAI] = {}

        self.setting=setting_manager.SettingsManager()
    def get_client(self, event) -> OpenAI:
        group_id=event.chat_id
        if group_id not in self._clients_cache:
            llm_settings = self.get_agent_settings(event)
            client = OpenAI(
                api_key=llm_settings['api_key'],
                base_url=llm_settings['base_url'],
                max_retries=3
            )
            self._clients_cache[group_id] = client
        return self._clients_cache[group_id]
    
    def is_received_custom_llm_setting_valid(self,event,custom_llm):
        
        if custom_llm['api_key']=='':
            return (False,'')
        
    def get_agent_settings(self,event):
        custom_llm=self.setting.get_group_settings(event.chat_id)['llm_settings']
        if custom_llm['use_custom_llm'] and custom_llm['is_verified']:
            return custom_llm
        else:
            return self.setting.get_base_setting()['default_llm_setting']
        
    async def ask(self,event,messages):
        
        celient=self.get_client(event)
        llm_setting=self.get_agent_settings(event)
        return celient.chat.completions.create(
            messages=messages
,
            model=llm_setting['model'],

        ).choices[0].message.content
    
    async def bot_handler(self,event):
        role = 'user'
        self.setting.update_bot_memory(
                event=event,
                user_id=event.sender_id,
                role=role,
                content=event.raw_text,
                max_length=400
                )
            
        messages=[
                {
                    "role":"system",
                    "content":system_message
                    }
            ]
        name_cache = {}
        for i in self.setting.get_bot_memory(event):
            if i['sender']!= None:
                sender_id = int(i['sender'])
                if sender_id not in name_cache:
                    try:
                        user = await self.sp_client.get_entity(sender_id)
                        name_cache[sender_id] = user.first_name + ': '
                    except Exception:
                        name_cache[sender_id] = 'کاربر: '
                user_first_name = name_cache[sender_id]
            else :
                    
                user_first_name=''
            messages.append({
                "sender":user_first_name,
                "role":role,
                "content":user_first_name + i["content"]
            })
                
        messages.append({"sender":event.sender_id,"role":role,"content":event.raw_text})

        response=await self.ask(event,messages)
        try:
            await event.reply(response)
            role="assistant"
            self.setting.update_bot_memory(
                event=event,
                user_id=None,
                role=role,
                content=response,
                max_length=400
                )
            
        except Exception as e:
            await self.sp_client.send_message(DEV_ID,f"⚠️ خطا در ارسال پاسخ: ")




# کمتر به من برینه و بیشتر به پیمان برینه ناز @Mee_lii  رو بیشتر بکشه
# اضافه کردن پروفایل مخصوص برای هر کاربر
"""

 اضافه کردن شخصی سازی پذیری بیشتر ازجمله:
 بهش بگم که حداکثر کراکتر هاش چقدر باشه
 پرامت سیستمیک قابل تنظیم باشه البته فقط برای توسعه دهنده

"""
class SoroushBot:
    def __init__(self,session_string):
        self.sp_client = SoroushClient(StringSession(session_string))
        self.session_string = session_string
        

        
        self.group_manger=group_manager.GroupManager(self.sp_client)
        self.setting=setting_manager.SettingsManager()
        self.agent_manager=AgentManager(self.sp_client)






    
    async def _event_handler(self, event):
        me=await self.sp_client.get_me()

        if event.sender_id == me.id:
            return
        
        if "گاردی" in event.raw_text or await utils.is_reply_to_bot(event,self.sp_client):
            await self.agent_manager.bot_handler(event)
            


        
        if utils.is_sender_bot_admin(event):
            if event.raw_text.startswith('مجازات'):
                parts = event.raw_text.split()
                if len(parts) >= 2:
                    if parts[1] == 'بن':
                        self.setting.update_group_dict(event.chat_id, 'punishment_settings', 'type', 'ban')
                        await event.reply("✅ مجازات تخلف روی «بن» تنظیم شد.")
                    elif parts[1] == 'میوت' and len(parts) == 3 and parts[2].isdigit():
                        hours = int(parts[2])
                        self.setting.update_group_dict(event.chat_id, 'punishment_settings', 'type', 'mute')
                        self.setting.update_group_dict(event.chat_id, 'punishment_settings', 'mute_duration_hours', hours)
                        await event.reply(f"✅ مجازات تخلف روی «میوت {hours} ساعته» تنظیم شد.")
                    else:
                        await event.reply("❗فرمت درست: مجازات بن  یا  مجازات میوت [عدد ساعت]")

                        
            add_admin_word=self.setting.get_base_setting()['key_words']['add_admin_word']
            if add_admin_word in event.raw_text:
                parts = event.raw_text.split()
                if len(parts) == 3:
                    target_username = parts[-1].replace("@", "")
                    
                    try:
                        user = await self.sp_client.get_entity(target_username)
                        status=self.setting.add_to_group_settings(event.chat_id,'admins',user.id)
                        if status:
                            alert_text = f"""کاربر {user.username} اکنون دسترسی ویژه به گاردی داد✅"""
                            await event.reply(alert_text)
                        else:
                            alert_text=f"""❗عملیات ناموفق❗\n\n❕کاربر {user.username} در حال حاضر ادمین هست"""
                            await event.reply(alert_text)

                    except:
                        alert_text="""❗خطا❗\n⚠️لطفا چک کنید نام کاربری را به درستی وارد کرده اید.\n\n✅مثال:\nاد ادمین @EternalBot"""
                        await event.reply(alert_text)
            await self.group_manger.add_blocked_content(event)

            

        inappropriate_message=await self.group_manger.is_inappropriate_content(event)
        if inappropriate_message:

            await self.sp_client.delete_messages(event.chat_id,event.id)
            
            await self.group_manger.handle_violation(event,event.sender_id,inappropriate_message)




    async def start(self):
        self.sp_client.add_event_handler(self._event_handler, events.NewMessage)

        while True:
            while True:
                try:
                    await self.sp_client.start()
                    break
                except Exception:
                    print("⚠️ اتصال به سروش امکان‌پذیر نیست. ۵ ثانیه دیگه دوباره امتحان می‌شود...")
                    await asyncio.sleep(5)

            try:
                await self.sp_client.run_until_disconnected()
            except Exception as e:
                print(f"⚠️ اتصال قطع شد: {e}\nتلاش برای اتصال مجدد در ۵ ثانیه...")
                await asyncio.sleep(5)
                # حلقه دوباره از اول شروع میشه و سعی می‌کنه وصل بشه

    
async def main():
    session_string = '1AwASaW0tc2VydmVyLnNwbHVzLmlyAbtq4ckLRdNrsX-iGw_yoLPKCjtduYpni9z2DSu9xJFuKXb8hPcClh4-mtkGF41c_3iiUYNFTEKwYVfKUg-pIDTyckTrgvzYmI0KrxAbqvB9kaDMUtiE-41c8a9UzRIEjTlWWCv478KLuGZ-G7QThscOFHOh0pM748Sax4qwOYxuFZw-1JCtswNzOxbB1SH04hyiOv46YRkZH2PvtqiyPYUmDuKkVIlQHJx4ONXNMDGMbIn2PTifGv-od6FceRK19m8C5xPCXLL-gBP2AzrJ4e23KqseaT0BZ97FHS5uVE7gFNZvHzlQcSzn4NtEs8n19Xc52jmy8QGzPInwRo3NvQNI'
    bot = SoroushBot(session_string)
    
    asyncio.create_task(periodic_backup_loop(300))  # هر ۵ دقیقه بکاپ خودکار

    while True:
        try:
            await bot.start()
        except Exception as e:
            print(f"⚠️ خطای غیرمنتظره در سطح اصلی برنامه: {e}")
            try:
                await backup_all_to_github()  # آخرین تلاش بکاپ قبل از ری‌استارت
            except Exception:
                pass
            await asyncio.sleep(5)
            # حلقه دوباره از اول شروع میشه، bot.start() دوباره صدا زده میشه

asyncio.run(main())



# متن خام NewMessage.Event(original_update=UpdateNewChannelMessage(message=Message(id=123, peer_id=PeerChannel(channel_id=23125876), date=datetime.datetime(2026, 7, 20, 17, 22, 25, tzinfo=datetime.timezone.utc), message='Text', out=False, mentioned=False, media_unread=False, silent=False, post=False, from_scheduled=False, legacy=False, edit_hide=False, pinned=False, noforwards=False, invert_media=False, from_id=PeerUser(user_id=49245702), fwd_from=None, via_bot_id=None, reply_to=None, media=None, reply_markup=None, entities=[], views=None, forwards=None, replies=None, edit_date=None, post_author=None, grouped_id=None, reactions=None, restriction_reason=[], ttl_period=None), pts=152, pts_count=1), pattern_match=None, message=Message(id=123, peer_id=PeerChannel(channel_id=23125876), date=datetime.datetime(2026, 7, 20, 17, 22, 25, tzinfo=datetime.timezone.utc), message='Text', out=False, mentioned=False, media_unread=False, silent=False, post=False, from_scheduled=False, legacy=False, edit_hide=False, pinned=False, noforwards=False, invert_media=False, from_id=PeerUser(user_id=49245702), fwd_from=None, via_bot_id=None, reply_to=None, media=None, reply_markup=None, entities=[], views=None, forwards=None, replies=None, edit_date=None, post_author=None, grouped_id=None, reactions=None, restriction_reason=[], ttl_period=None))
# استیکر NewMessage.Event(original_update=UpdateNewChannelMessage(message=Message(id=125, peer_id=PeerChannel(channel_id=23125876), date=datetime.datetime(2026, 7, 20, 17, 23, 28, tzinfo=datetime.timezone.utc), message='', out=False, mentioned=False, media_unread=False, silent=False, post=False, from_scheduled=False, legacy=False, edit_hide=False, pinned=False, noforwards=False, invert_media=False, from_id=PeerUser(user_id=49245702), fwd_from=None, via_bot_id=None, reply_to=None, media=MessageMediaDocument(nopremium=False, spoiler=False, document=Document(id=144119586122368148, access_hash=-8162378924667830014, file_reference=b'\x02\x01\x02\x81g\x01\x01\x01\x02\x02\x04', date=datetime.datetime(2022, 10, 30, 12, 48, 18, tzinfo=datetime.timezone.utc), mime_type='image/webp', size=268685, dc_id=6, attributes=[DocumentAttributeFilename(file_name='TBZrr'), DocumentAttributeImageSize(w=512, h=512), DocumentAttributeImageSize(w=100, h=100), DocumentAttributeSticker(alt='', stickerset=InputStickerSetID(id=1010, access_hash=8407400864531218690), mask=False, mask_coords=None)], thumbs=[PhotoCachedSize(type='s', w=100, h=100, bytes=''), PhotoSize(type='m', w=320, h=320, size=16166), PhotoSize(type='x', w=512, h=512, size=268685)], video_thumbs=[]), alt_document=None, ttl_seconds=None), reply_markup=None, entities=[], views=None, forwards=None, replies=None, edit_date=None, post_author=None, grouped_id=None, reactions=None, restriction_reason=[], ttl_period=None))
# گیف NewMessage.Event(original_update=UpdateNewChannelMessage(message=Message(id=126, peer_id=PeerChannel(channel_id=23125876), date=datetime.datetime(2026, 7, 20, 17, 27, 7, tzinfo=datetime.timezone.utc), message='', out=False, mentioned=False, media_unread=False, silent=False, post=False, from_scheduled=False, legacy=False, edit_hide=False, pinned=False, noforwards=False, invert_media=False, from_id=PeerUser(user_id=49245702), fwd_from=None, via_bot_id=None, reply_to=None, media=MessageMediaDocument(nopremium=False, spoiler=False, document=Document(id=144353785819088831, access_hash=953511847564935426, file_reference=b'\x02\x01\x02\x81g\x01\x01\x01\x01\x02', date=datetime.datetime(2026, 2, 28, 9, 36, 45, tzinfo=datetime.timezone.utc), mime_type='video/mp4', size=90100, dc_id=6, attributes=[DocumentAttributeFilename(file_name='-2147483648_-217931.mp4'), DocumentAttributeVideo(duration=6.0, w=208, h=138, round_message=False, supports_streaming=True, nosound=False, preload_prefix_size=None), DocumentAttributeAnimated()], thumbs=[PhotoSize(type='m', w=320, h=212, size=11816), PhotoSize(type='s', w=100, h=66, size=2732)], video_thumbs=[]), alt_document=None, ttl_seconds=None), reply_markup=None, entities=[], views=None, forwards=None, replies=None, edit_date=None, post_author=None, grouped_id=None, reactions=None, restriction_reason=[], ttl_period=None), pts=155, pts_count=1), pattern_match=None, message=Message(id=126, peer_id=PeerChannel(channel_id=23125876), date=datetime.datetime(2026, 7, 20, 17, 27, 7, tzinfo=datetime.timezone.utc), message='', out=False, mentioned=False, media_unread=False, silent=False, post=False, from_scheduled=False, legacy=False, edit_hide=False, pinned=False, noforwards=False, invert_media=False, from_id=PeerUser(user_id=49245702), fwd_from=None, via_bot_id=None, reply_to=None, media=MessageMediaDocument(nopremium=False, spoiler=False, document=Document(id=144353785819088831, access_hash=953511847564935426, file_reference=b'\x02\x01\x02\x81g\x01\x01\x01\x01\x02', date=datetime.datetime(2026, 2, 28, 9, 36, 45, tzinfo=datetime.timezone.utc), mime_type='video/mp4', size=90100, dc_id=6, attributes=[DocumentAttributeFilename(file_name='-2147483648_-217931.mp4'), DocumentAttributeVideo(duration=6.0, w=208, h=138, round_message=False, supports_streaming=True, nosound=False, preload_prefix_size=None), DocumentAttributeAnimated()], thumbs=[PhotoSize(type='m', w=320, h=212, size=11816), PhotoSize(type='s', w=100, h=66, size=2732)], video_thumbs=[]), alt_document=None, ttl_seconds=None), reply_markup=None, entities=[], views=None, forwards=None, replies=None, edit_date=None, post_author=None, grouped_id=None, reactions=None, restriction_reason=[], ttl_period=None))
# عکس فشرده NewMessage.Event(original_update=UpdateNewChannelMessage(message=Message(id=128, peer_id=PeerChannel(channel_id=23125876), date=datetime.datetime(2026, 7, 20, 17, 28, 19, tzinfo=datetime.timezone.utc), message='', out=False, mentioned=False, media_unread=False, silent=False, post=False, from_scheduled=False, legacy=False, edit_hide=False, pinned=False, noforwards=False, invert_media=False, from_id=PeerUser(user_id=49245702), fwd_from=None, via_bot_id=None, reply_to=None, media=MessageMediaPhoto(spoiler=False, photo=Photo(id=144507719591657812, access_hash=8024177509244076290, file_reference=b'\x02\x01\x02\x81g\x01\x01\x01\x01\x02', date=datetime.datetime(2026, 7, 20, 17, 28, 19, tzinfo=datetime.timezone.utc), sizes=[PhotoSize(type='s', w=77, h=100, size=3074), PhotoSize(type='m', w=89, h=115, size=5833)], dc_id=6, has_stickers=False, video_sizes=[]), ttl_seconds=None), reply_markup=None, entities=[], views=None, forwards=None, replies=None, edit_date=None, post_author=None, grouped_id=None, reactions=None, restriction_reason=[], ttl_period=None), pts=157, pts_count=1), pattern_match=None, message=Message(id=128, peer_id=PeerChannel(channel_id=23125876), date=datetime.datetime(2026, 7, 20, 17, 28, 19, tzinfo=datetime.timezone.utc), message='', out=False, mentioned=False, media_unread=False, silent=False, post=False, from_scheduled=False, legacy=False, edit_hide=False, pinned=False, noforwards=False, invert_media=False, from_id=PeerUser(user_id=49245702), fwd_from=None, via_bot_id=None, reply_to=None, media=MessageMediaPhoto(spoiler=False, photo=Photo(id=144507719591657812, access_hash=8024177509244076290, file_reference=b'\x02\x01\x02\x81g\x01\x01\x01\x01\x02', date=datetime.datetime(2026, 7, 20, 17, 28, 19, tzinfo=datetime.timezone.utc), sizes=[PhotoSize(type='s', w=77, h=100, size=3074), PhotoSize(type='m', w=89, h=115, size=5833)], dc_id=6, has_stickers=False, video_sizes=[]), ttl_seconds=None), reply_markup=None, entities=[], views=None, forwards=None, replies=None, edit_date=None, post_author=None, grouped_id=None, reactions=None, restriction_reason=[], ttl_period=None))






















# import asyncio
# from splusthon import SoroushClient, events
# from splusthon.sessions import StringSession

# from openai import OpenAI

# openai_client = OpenAI(api_key='sk-JcUnps6czsZz95dlsByQAXr9XPnJhWkoMMGKMXhPooij8wlg',base_url="https://apihub.agnes-ai.com/v1/")
# import json
# import os



# BLACKLIST_FILE = "gif_blacklist.json"

# def load_blacklist():
#     if os.path.exists(BLACKLIST_FILE):
#         with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
#             return set(json.load(f))
#     return set()

# def save_blacklist(blacklist):
#     with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
#         json.dump(list(blacklist), f, ensure_ascii=False, indent=2)
# blocked_gif_ids = load_blacklist()

# blocked_words=['بچه کونی','بیو چک','بیوچک','رل پی','رلپی','فحش','لاشی','https://']
# print()









# ADMINS_ID='AdnanEternal'
# call_word="گاردی"
# START_WORD='لیست قفل'


# def get_chat_id(event):
#     return event.chat_id


# def is_private_chat(event):
#     from splusthon.tl.types import PeerUser
#     return isinstance(event.message.peer_id,PeerUser)






# async def main():
#     client = SoroushClient(StringSession(SESSION_STRING))
    
#     await client.start()


 
    
#     async def remove_warning_after_timeout(chat_id, message_id,timeout):
#         await asyncio.sleep(timeout)
#         await client.delete_messages(chat_id, message_ids=[message_id])
    




#     @client.on(events.NewMessage)
    
#     async def handler(event):
#         # print(is_private_chat(event))
        
#         asyncio.create_task(process_message(event))

        
#     async def add_to_blacklist(event):
#         replied_msg_id = event.reply_to_msg_id
#         gif=await client.get_messages(entity=get_chat_id(event),ids=replied_msg_id)
#         if gif.media.document.id not in blocked_gif_ids:
#             blocked_gif_ids.add(gif.media.document.id)
#             save_blacklist(blocked_gif_ids)
#         await client.delete_messages(get_chat_id(event),ids=replied_msg_id)


#     async def process_message(event):
#         # if is_private_chat(event):
#         #     if event.sender.username == ADMINS_ID:
#         #         if event.sender.username:
#         #             await client.send_message(event.sender.username,'')
                
                

#         # if event.chat_id == TARGET_ENTITY:
                
            
#             if any(word in event.raw_text.strip().lower() for word in blocked_words) :

#                 await client.delete_messages(event.chat_id, message_ids=[event.message.id])
#                 warn_msg = await client.send_message(get_chat_id(event), message='این کلمه ممنوعه!')
#                 asyncio.create_task(remove_warning_after_timeout(get_chat_id(event), warn_msg.id, 10))

#             if event.raw_text == 'فیلتر محتوا':
#                 if event.reply_to == None:
#                     return
#                 await add_to_blacklist(event)

#             if event.message.media and event.message.document:
#                 gif_id = event.message.document.id
#                 if gif_id in blocked_gif_ids:
#                     await client.delete_messages(event.chat_id, message_ids=[event.message.id])
            
#             if event.raw_text.strip().lower()[:len(call_word)] == call_word:
#                 # await client.send_message(TARGET_ENTITY, message='6565')
#                 await event.reply(
#                     openai_client.chat.completions.create(  
#                         model="agnes-2.0-flash",
#                         messages=[
#                         {"role": "user", "content": event.raw_text.strip().lower()[len(call_word):]}
#                     ]
#                 ).choices[0].message.content)

#     await client.run_until_disconnected()

# asyncio.run(main())



                
#                 # if call_word in event.raw_text.strip().lower():
#                # print(last_msg.id,last_msg.text)







# def get_chat_id(event):
#     return event.chat_id


# def is_private_chat(event):
#     return isinstance(event.message.peer_id, PeerUser)


# async def main():
#     client = SoroushClient(StringSession(SESSION_STRING))
#     await client.start()



#     async def add_to_blacklist(event):
#         replied_msg_id = event.reply_to_msg_id
#         gif = await client.get_messages(entity=get_chat_id(event), ids=replied_msg_id)
#         if gif.media.document.id not in blocked_gif_ids:
#             blocked_gif_ids.add(gif.media.document.id)
#             save_blacklist(blocked_gif_ids)
#         await client.delete_messages(get_chat_id(event), ids=replied_msg_id)

#     async def process_message(event):
#         if any(word in event.raw_text.strip().lower() for word in blocked_words):
#             await client.delete_messages(event.chat_id, message_ids=[event.message.id])
#             warn_msg = await client.send_message(get_chat_id(event), message='این کلمه ممنوعه!')
#             asyncio.create_task(remove_warning_after_timeout(get_chat_id(event), warn_msg.id, 10))

#         if event.raw_text == 'فیلتر محتوا':
#             if event.reply_to is None:
#                 return
#             await add_to_blacklist(event)

#         if event.message.media and event.message.document:
#             gif_id = event.message.document.id
#             if gif_id in blocked_gif_ids:
#                 await client.delete_messages(event.chat_id, message_ids=[event.message.id])


#     @client.on(events.NewMessage)
#     async def handler(event):
#         asyncio.create_task(process_message(event))

#     await client.run_until_disconnected()

# asyncio.run(main())
