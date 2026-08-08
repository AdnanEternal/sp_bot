import json
import os
import aiofiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

async def load_settings(path):
    if os.path.exists(path):
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)
    return {}


async def save_settings(data, file_path):
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))


class SettingsManager:
    def __init__(self, base_settings_path=None, groups_settings_path=None, bot_memory_path=None):
        self.base_settings_path = base_settings_path or os.path.join(BASE_DIR, "base_settings.json")
        self.group_settings_path = groups_settings_path or os.path.join(BASE_DIR, "groups_settings.json")
        self.bot_memory = bot_memory_path or os.path.join(BASE_DIR, "bot_memory.json")

    def remove_from_group_dict(self, group_id, dict_key, sub_key):
        group_id = str(group_id)
        sub_key = str(sub_key)
        settings = self.get_group_settings(group_id)
        if dict_key in settings and sub_key in settings[dict_key]:
            del settings[dict_key][sub_key]
            data = load_settings(self.group_settings_path)
            data[group_id] = settings
            save_settings(data, self.group_settings_path)
            return True
        return False
    
    def get_bot_memory(self, event):
        group_id = str(event.chat_id)
        data = load_settings(self.bot_memory)
        if group_id not in data:
            data[group_id] = []
            save_settings(data, self.bot_memory)
        return data[group_id]
    def remove_from_group_settings(self, group_id, keyword, valeu):
        group_id = str(group_id)
        valeu = str(valeu).strip()
        settings = self.get_group_settings(group_id)
        if valeu not in settings[keyword]:
            return False
        if isinstance(settings[keyword],list):
            
            settings[keyword].remove(valeu)
            
        if isinstance(settings[keyword],dict):
            del settings[keyword]
        data = load_settings(self.group_settings_path)
        data[group_id] = settings
        save_settings(data, self.group_settings_path)
        return True
    
    def update_bot_memory(self, user_id, event, role: str, content: str, max_length: int = 200):
        group_id = str(event.chat_id)
        memory = self.get_bot_memory(event)
        memory.append({"sender": user_id, "role": role, "content": content})
        if len(memory) > max_length:
            memory = memory[-max_length:]
        data = load_settings(self.bot_memory)
        data[group_id] = memory
        save_settings(data, self.bot_memory)

    def get_base_setting(self):
        return load_settings(self.base_settings_path)

    def get_group_settings(self, group_id):
        group_id = str(group_id)
        data = load_settings(self.group_settings_path)

        if group_id not in data:
            data[group_id] = {
                "admins": [],
                "blocked_words": [],
                "blocked_media": [],
                "user_warnings": {},
                "custom_llm_settings": {
                    "use_custom_llm": False,
                    "is_verified": False,
                    "api_key": "",
                    "base_url": "",
                    "model": ""
                },
                "punishment_settings": {
                    "max_warning_before_punish":5,
                    "type": None,
                    "mute_duration_hours": 0
                }
            }
            save_settings(data, self.group_settings_path)

        return data[group_id]

    def add_to_group_settings(self, group_id, keyword, valeu):
        group_id = str(group_id)
        valeu = str(valeu).strip()
        settings = self.get_group_settings(group_id)
        if valeu in settings[keyword]:
            return False
        settings[keyword].append(valeu)
        data = load_settings(self.group_settings_path)
        data[group_id] = settings
        save_settings(data, self.group_settings_path)
        return True

    def update_group_dict(self, group_id, dict_key, sub_key, value):
        group_id = str(group_id)
        settings = self.get_group_settings(group_id)
        if dict_key not in settings:
            settings[dict_key] = {}
        settings[dict_key][sub_key] = value
        data = load_settings(self.group_settings_path)
        data[group_id] = settings
        save_settings(data, self.group_settings_path)

    def update_group_setting(self, group_id, key, new_value):
        group_id = str(group_id)
        settings = self.get_group_settings(group_id)
        settings[key] = new_value
        data = load_settings(self.group_settings_path)
        data[group_id] = settings
        save_settings(data, self.group_settings_path)
        return True