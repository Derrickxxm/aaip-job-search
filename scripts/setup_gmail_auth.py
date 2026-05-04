"""Gmail OAuth2 一次性授权脚本

使用步骤：
1. 前往 https://console.cloud.google.com/
2. 新建项目 → 启用 Gmail API
3. 创建 OAuth 2.0 客户端 ID（类型选 Desktop app）
4. 下载 JSON → 保存为 config/gmail_credentials.json
5. 运行本脚本：python scripts/setup_gmail_auth.py
6. 浏览器会自动打开，完成 Google 账号授权
7. 授权完成后 config/gmail_token.json 自动保存，后续无需重复操作
"""
import os
import sys

# 将项目根目录加入路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from google_auth_oauthlib.flow import InstalledAppFlow
from utils.logger import logger

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_PATH = os.path.join(project_root, 'config', 'gmail_credentials.json')
TOKEN_PATH = os.path.join(project_root, 'config', 'gmail_token.json')


def main():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"\n[ERROR] credentials 文件不存在: {CREDENTIALS_PATH}")
        print("\n请按以下步骤获取：")
        print("  1. 访问 https://console.cloud.google.com/")
        print("  2. 新建项目 → APIs & Services → Enable APIs")
        print("  3. 搜索并启用 'Gmail API'")
        print("  4. 左侧 Credentials → Create Credentials → OAuth client ID")
        print("  5. 应用类型选择 'Desktop app'")
        print("  6. 下载 JSON 文件，重命名为 gmail_credentials.json")
        print(f"  7. 将文件放置到: {CREDENTIALS_PATH}")
        sys.exit(1)

    print(f"[INFO] Found credentials: {CREDENTIALS_PATH}")
    print("[INFO] Opening browser for OAuth2 authorization...")

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, 'w') as f:
        f.write(creds.to_json())

    print(f"\n[SUCCESS] Token saved to: {TOKEN_PATH}")
    print("[INFO] Gmail authorization complete. You can now run: python email_digest.py")


if __name__ == '__main__':
    main()
