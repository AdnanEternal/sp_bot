from splusthon import SoroushClient
from splusthon.sessions import StringSession



class SPClient:
    def __init__(self,session_string):
        self.session_string = session_string

        if not self.session_string:
            raise ValueError("❌ خطا: متغیر محیطی SESSION_STRING تنظیم نشده است!")
        
        self.client = None

    async def start(self):
        self.client = SoroushClient(StringSession(self.session_string))
        try:
            await self.client.start()
            print("client connected✅")
            return self.client
        except Exception as e:
            print(f"❌ خطا در اتصال: {e}")
            return None

    async def stop(self):
        if self.client:
            await self.client.disconnect()
            print("🔌 اتصال بسته شد.")