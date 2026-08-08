import asyncio
import json
import os
import aiofiles
from typing import Dict, List


class MemoryManager:
    def __init__(
            self,
            file_path
            ):

        self.file_path = file_path
        self._cache: Dict[str, List[dict]] = {}
        self._dirty_groups = set()

    async def load(self):
        if os.path.exists(self.file_path):
            async with aiofiles.open(self.file_path,'r',encoding='utf-8') as f:
                content = await f.read()
                self._cache = json.loads(content) if content else {}
        else:
            self._cache = {}
        self._dirty_groups.clear()

