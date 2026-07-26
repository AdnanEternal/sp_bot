import asyncio
import base64
import requests
import os

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = "AdnanEternal/jsons"  # اسم ریپوی خودت اینجا
GITHUB_BRANCH = "main"
FILES_TO_BACKUP = ["groups_settings.json", "bot_memory.json"]


def _upload_file_sync(local_path, repo_path):
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN تنظیم نشده، بکاپ رد شد.")
        return
    try:
        with open(local_path, 'r', encoding='utf-8') as f:
            content = f.read()
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{repo_path}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        get_resp = requests.get(api_url, headers=headers, params={"ref": GITHUB_BRANCH}, timeout=10)
        sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

        payload = {
            "message": f"backup: {repo_path}",
            "content": encoded_content,
            "branch": GITHUB_BRANCH
        }
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(api_url, headers=headers, json=payload, timeout=10)
        if put_resp.status_code not in (200, 201):
            print(f"⚠️ بکاپ ناموفق برای {repo_path}: {put_resp.status_code} {put_resp.text}")
    except Exception as e:
        print(f"⚠️ خطا در بکاپ {repo_path}: {e}")


async def backup_all_to_github():
    loop = asyncio.get_event_loop()
    for file_path in FILES_TO_BACKUP:
        if os.path.exists(file_path):
            await loop.run_in_executor(None, _upload_file_sync, file_path, file_path)


async def periodic_backup_loop(interval_seconds=300):
    while True:
        try:
            await backup_all_to_github()
            print("✅ بکاپ با موفقیت انجام شد.")
        except Exception as e:
            print(f"⚠️ بکاپ دوره‌ای ناموفق: {e}")
        await asyncio.sleep(interval_seconds)