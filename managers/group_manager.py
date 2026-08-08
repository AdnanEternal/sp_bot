
import asyncio
import json
import os

from openai import OpenAI
from splusthon.tl.types import MessageEntitySpoiler
import managers.setting_manager as setting_manager
import utils

import datetime




class GroupManager:
    def __init__(self,sp_client):
        self.sp_client = sp_client
        self.blocked_media_ids = set()
        
        self.setting= setting_manager.SettingsManager()




    async def list_violators(self, event):
        settings = self.setting.get_group_settings(event.chat_id)
        warnings_dict = settings['user_warnings']
        max_warnings = settings.get('max_warning_before_ban', 5)

        if not warnings_dict:
            await event.reply("✅ هیچ کاربر متخلفی ثبت نشده.")
            return

        lines = []
        for user_id_str, remaining in warnings_dict.items():
            name = await self._get_display_name(int(user_id_str))
            violations = max(0, max_warnings - remaining)
            lines.append(f"👤 کاربر {name} : {violations} تخلف.")

        text = "📋 لیست کاربران متخلف:\n\n" + "\n".join(lines) +f"\nسقف مجاز تخلف برای هر کاربر: { max_warnings}"
        await event.reply(text)


    async def set_max_warnings(self, event):
        parts = event.raw_text.split()
        if len(parts) != 3 or not parts[2].isdigit():
            await event.reply("❗فرمت درست: حداکثر اخطار [عدد]\nمثال: حداکثر اخطار 5")
            return

        print(parts[2])
        count = int(parts[2])
        if count < 1 or count > 50:
            await event.reply("❗عدد باید بین ۱ تا ۵۰ باشه.")
            return

        self.setting.update_group_setting(event.chat_id, 'max_warning_before_ban', count)
        await event.reply(f"✅ حداکثر اخطار قبل از مجازات روی {count} تنظیم شد.")


    async def remove_violator(self, event):
        target_id, _ = await self._resolve_target_user(event)
        if target_id is None:
            await event.reply(
                "❗فرمت درست:\nحذف تخلف @username\nیا روی پیام کاربر ریپلای کن و بنویس: حذف تخلف"
            )
            return

        name = await self._get_display_name(target_id)
        status = self.setting.remove_from_group_dict(event.chat_id, 'user_warnings', target_id)

        if status:
            await event.reply(f"✅ سابقه‌ی تخلف {name} پاک شد.")
        else:
            await event.reply(f"ℹ️ {name} سابقه‌ی تخلفی نداشت.")


    async def _resolve_target_user(self, event):
        parts = event.raw_text.split()
        print(parts[2])
        if event.reply_to:
            replied_msg = await self.sp_client.get_messages(event.chat_id, ids=event.reply_to_msg_id)
            return replied_msg.sender_id, parts[2:] 
        if len(parts) == 3 and parts[2].startswith('@'):
            username = parts[2].replace('@', '')
            try:
                user = await self.sp_client.get_entity(username)
                return user.id, parts[2:]
            except Exception:
                return None, None
        return None, None

    async def _get_display_name(self, user_id):
        try:
            entity = await self.sp_client.get_entity(user_id)
            return '@' + entity.username if entity.username else entity.first_name
        except Exception:
            return str(user_id)

    async def mute_user_command(self, event):
        target_id, args = await self._resolve_target_user(event)
        if target_id is None:
            await event.reply(
            "❗فرمت درست:\nمیوت @username [تعداد ساعت]\n"
            "یا روی پیام کاربر ریپلای کن و بنویس: میوت [تعداد ساعت]"
        )
            return
        hours = 1
        if args and args[0].isdigit():
            hours = int(args[0])
        if hours <= 0 or hours > 720:  # سقف ۳۰ روز، برای جلوگیری از عدد اشتباه/بیش از حد
            await event.reply("❗تعداد ساعت باید بین ۱ تا ۷۲۰ (۳۰ روز) باشه.")
            return
        name = await self._get_display_name(target_id)
        until_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)
        try:
            await self.sp_client.edit_permissions(
            event.chat_id,
            target_id,
            send_messages=False,
            until_date=until_date,
        )
            await event.reply(f"🔇 کاربر {name} به مدت {hours} ساعت میوت شد.")

        except Exception as e:
            await event.reply("❗نتونستم کاربر رو میوت کنم. مطمئن شو ربات دسترسی ادمین داره.")

    async def unmute_user_command(self, event):
        target_id, args = await self._resolve_target_user(event)
        if target_id is None:
            await event.reply(
        "❗فرمت درست:\nآنمیوت @username\nیا روی پیام کاربر ریپلای کن و بنویس: آنمیوت"
        )
            return
        name = await self._get_display_name(target_id)

        try:
            await self.sp_client.edit_permissions(
        event.chat_id,
        target_id,
        send_messages=True,
    )
            await event.reply(f"🔊 کاربر {name} آنمیوت شد.")
        except Exception:
            await event.reply("❗نتونستم کاربر رو آنمیوت کنم. مطمئن شو ربات دسترسی ادمین داره.")

    def get_group_admins(self,group_id):
        group = self.setting.get_group_settings(group_id)
        return group['admins']


        
    def mute_user():
        pass

    def ban_user():
        pass
    
    # async def un_mute_user(
    #     self,
    #     group_id:int,
    #     event
    #     ):
    #     user_id=None
    #     parts = event.raw_text.split()
    #     if len(parts) == 3:
            
    #     status = self.setting.remove_from_group_settings(group_id, 'user_warnings', user_id)
        # if status:
        #     await self.sp_client.edit_permissions(
        #         group_id,
        #         user_id,
        #         send_messages=True,
        #         )
            


    
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



        # همیشه با .get و مقدار پیش‌فرض کار کن، نه با "in"
        current_warnings = violators_list.get(str(user_id), self.setting.get_group_settings(event.chat_id)['max_warning_before_ban'])

        if current_warnings <= 1:
            await self.punish_user(
                event.sender_id,
                event.chat_id,
                event
            )
            self.setting.remove_from_group_dict(event.chat_id,'user_warnings',str(user_id))
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
        if 'لغو فیلتر کلمه ی' in event.raw_text or 'لغو فیلتر کلمه' in event.raw_text:
            target_word = event.raw_text.replace('لغو فیلتر کلمه ی', '').replace('لغو فیلتر کلمه', '').strip()
            if not target_word:
                await event.reply("❗کلمه‌ای که میخوای از فیلتر خارج کنی رو بنویس.\nمثال: لغو فیلتر کلمه ی سلام")
                return
            status = self.setting.remove_from_group_settings(event.chat_id, 'blocked_words', target_word)
            if status:
                await event.reply(f"✅ کلمه‌ی «{target_word}» از فیلتر خارج شد.")
            else:
                await event.reply(f"❗همچین کلمه‌ای توی لیست فیلتر نبود.")
            return
        
        if 'لغو فیلتر محتوا' in event.raw_text:
            target_media = event.raw_text.replace('لغو فیلتر محتوا', '').strip()
            if not target_media:
                await event.reply("محتوایی که میخوای از فیلتر خارج کنی رو بنویس.\nمثال: لغو فیلتر محتوا 123456789")
                return
            status = self.setting.remove_from_group_settings(event.chat_id, 'blocked_media', target_media)
            if status:
                await event.reply(f"✅ محتوای «{target_media}» از فیلتر خارج شد.")
            else:
                await event.reply(f"❗همچین شناسه ی محتوایی توی لیست فیلتر نبود.")
            return

                
        if event.raw_text == 'فیلتر محتوا' or event.raw_text == "فیلتر":
            if event.reply_to == None:
                alert_text="""📒راهنمای دستور فیلتر محتوا:
        برای استفاده از این دستور جمله ی فیلتر محتوا را روی محتوای مورد نظر ریپلای کنید
        📌نکته:این دستور جزو دستور های ویژه هست و فقط ادمین های ربات میتوانند از این دستور استفاده کنند"""
                await event.reply(alert_text)
                return

            media = await self.sp_client.get_messages(event.chat_id, ids=event.reply_to_msg_id)
            media_id = utils.get_media_id(media)

            if not media_id:
                await event.reply("❗این پیام محتوای قابل فیلتر (عکس/فایل/گیف) نداره.")
                return

            self.setting.add_to_group_settings(event.chat_id, "blocked_media", media_id)

            ids_to_delete = []
            async for message in self.sp_client.iter_messages(event.chat_id, limit=50):
                if message.media:
                    if utils.get_media_id(message) == media_id:
                        ids_to_delete.append(message.id)

            if ids_to_delete:
                try:
                    await self.sp_client.delete_messages(event.chat_id, ids_to_delete)
                except Exception as e:
                    await self.sp_client.send_message(
                        event.chat_id,
                        "⚠️ محتوا فیلتر شد ولی توی پاک کردن نمونه‌های قبلی مشکلی پیش اومد."
                    )

            await self.sp_client.send_message(
                event.chat_id,
                'محتوای مورد نظر فیلتر شد\nکاربران لطفا از فرستادن آن خودداری کنند'
            )
            return

        if 'فیلتر کلمه' in event.raw_text or 'فیلتر کلمه ی' in event.raw_text:
            target_word=event.raw_text.replace('فیلتر کلمه ی','').replace('فیلتر کلمه','')
            
            if target_word == '':
                alert_text="""📒راهنمای دستور فیلتر کلمه:
برای استفاده از این دستور بعد از نوشتن جمله ی فیلتر کلمه کلمه ی مورد نظر خود را بنویسید \n
📌نکته:این دستور جزو دستور های ویژه هست و فقط ادمین های ربات میتوانند از این دستور استفاده کنند"""
                await event.reply(alert_text)
                return
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
        



