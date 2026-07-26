
import asyncio
import json
import os

from openai import OpenAI
from splusthon.tl.types import MessageEntitySpoiler
import setting_manager as setting_manager
import utils

import datetime




class GroupManager:
    def __init__(self,sp_client):
        self.sp_client = sp_client
        self.blocked_media_ids = set()
        
        self.setting= setting_manager.SettingsManager()
        




    def get_group_admins(self,group_id):
        group = self.setting.get_group_settings(group_id)
        return group['admins']
        


    
    async def punish_user(
            self,
            user_id:int,
            group_id:int,
            event
            ):
        if event.sender.username:
            violator_name='@'+event.sender.username
        else:
            violator_name=event.sender.first_name
        punishment = self.setting.get_group_settings(group_id)["punishment_settings"]
        if punishment['type'] == 'ban':
            await self.sp_client.edit_permissions(
                group_id,
                user_id,
                view_messages=False,   # حذف کامل از گروه
            )
            alert_text=f"""❗کاربر {violator_name} به دلیل تخلف بیش از حد بن شد❗"""
            await self.sp_client.send_message(group_id,alert_text)

        else:
            until_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            hours=punishment['mute_duration_hours']
            
            )
            await self.sp_client.edit_permissions(
                group_id,
                user_id,
                send_messages=False,
                until_date=until_date,
            )
            alert_text=f"""❗کاربر {violator_name} به دلیل تخلف بیش از حد به مدت {punishment['mute_duration_hours']} ساعت میوت شد❗"""
            await self.sp_client.send_message(group_id,alert_text)



    async def handle_violation(self, event, user_id, violation_type):
        if utils.is_sender_bot_admin(event):
            return
        violators_list = self.setting.get_group_settings(event.chat_id)["user_warnings"]
        punishment = self.setting.get_group_settings(event.chat_id)["punishment_settings"]

        if event.sender.username:
            violator_name = '@' + event.sender.username
        else:
            violator_name = event.sender.first_name

        MAX_WARNINGS_BEFORE_BAN = 5

        # همیشه با .get و مقدار پیش‌فرض کار کن، نه با "in"
        current_warnings = violators_list.get(str(user_id), MAX_WARNINGS_BEFORE_BAN)

        if current_warnings <= 1:
            await self.punish_user(
                event.sender_id,
                event.chat_id,
                event
            )
            new_warnings = MAX_WARNINGS_BEFORE_BAN
            return
        else:
            new_warnings = current_warnings - 1

        self.setting.update_group_dict(event.chat_id, 'user_warnings', str(user_id), new_warnings)

        WARNING_TEMPLATE = f"\n\n⚠️{new_warnings} اخطار باقی مانده تا مجازات⚠️"

        if violation_type == 'media':
            alert_text = f"""{violator_name}⚠️هشدار⚠️\n❗این محتوا توسط ادمین گروه فیلتر شده.❗\n📛لطفا از فرستادن دوباره ی آن خودداری کنید.""" + WARNING_TEMPLATE
            await event.reply(alert_text)

        if isinstance(violation_type, tuple) and violation_type[0] == 'blocked word':
            alert_text = f"""{violator_name} گرامی❗\n ❌استفاده از کلمه ی {violation_type[1]} توسط ادمین گروه ممنوع شده❌""" + WARNING_TEMPLATE
            entities = [MessageEntitySpoiler(offset=alert_text.find(violation_type[1]), length=len(violation_type[1]))]
            await self.sp_client.send_message(event.chat_id, alert_text, formatting_entities=entities)
            
    
    async def is_inappropriate_content(self, event):
        



        # ========== blocked media filter ==========
        if hasattr(event.media, 'document') and event.media.document:
            
            if any(media_id in str(event.media.document.id) for media_id in self.setting.get_group_settings(event.chat_id)['blocked_media']):

                return 'media'
            
        if hasattr(event.media, 'photo') and event.media.photo:
            if any(media_id in event.media.photo.id for media_id in self.setting.get_group_settings(event.chat_id)['blocked_media']):
                return 'photo'
        
        # ========== blocked words filter==========
        if event.raw_text:
            for word in self.setting.get_group_settings(event.chat_id)['blocked_words']:
                if word in event.raw_text:
                    return 'blocked word', word
        return False
    
        
    async def add_blocked_content(self,event):
        if event.raw_text == 'فیلتر محتوا':
            if event.reply_to == None:
                alert_text="""📒راهنمای دستور فیلتر محتوا:
برای استفاده از این دستور جمله ی فیلتر محتوا را روی محتوای مورد نظر ریپلای کنید
📌نکته:این دستور جزو دستور های ویژه هست و فقط ادمین های ربات میتوانند از این دستور استفاده کنند"""
                await event.reply(alert_text)
                return
            media=await self.sp_client.get_messages(event.chat_id,ids=event.reply_to_msg_id)
                
            media_id=utils.get_media_id(media)
            if media_id:
                self.setting.add_to_group_settings(event.chat_id,"blocked_media",media_id)
            return

        if 'فیلتر کلمه' in event.raw_text or 'فیلتر کلمه ی' in event.raw_text:
            target_word=event.raw_text.replace('فیلتر کلمه ی','').replace('فیلتر کلمه','')
            parts = event.raw_text.split()
            if len(parts)>8 or len(event.raw_text)>50:
                alert_text="""❗جمله ی انتخاب شده برای فیلتر کردن بیش از حد طولانی است"""
                await event.reply(alert_text)
                return
            if len(target_word)<2:
                if event.reply_to == None:
                    # event.reply()
                    return
                await self.sp_client.get_messages(event.chat_id,ids=event.reply_to_msg_id)
                if len(parts)>8 or len(event.raw_text)>50:
                    alert_text="""❗جمله ی انتخاب شده برای فیلتر کردن بیش از حد طولانی است"""
                    await event.reply(alert_text)
                    return
            
            self.setting.add_to_group_settings(event.chat_id,'blocked_words',target_word)
            await event.reply("کلمه ی مورد نظر فیلتر شد")
            return
        



