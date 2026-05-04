"""Gmail API 邮件抓取模块"""
import base64
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from utils.logger import logger

# Gmail API 只读权限
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


@dataclass
class EmailMessage:
    """邮件消息数据模型"""
    id: str
    subject: str
    sender: str
    date: str
    body: str           # 纯文本，去掉 HTML 标签
    email_type: str     # "linkedin" | "job"


class GmailFetcher:
    """Gmail 邮件抓取器"""

    LINKEDIN_SENDERS = ['@linkedin.com', '@e.linkedin.com']
    JOB_KEYWORDS = [
        'interview', 'offer', 'application', 'hiring',
        'opportunity', 'position', "your application", "we'd like to",
        'recruiter', 'job opportunity', 'career opportunity'
    ]

    def __init__(self, credentials_path: str = 'config/gmail_credentials.json',
                 token_path: str = 'config/gmail_token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._service = None

    def authenticate(self):
        """OAuth2 鉴权，加载或生成 token"""
        creds = None

        # 尝试加载现有 token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # token 不存在或已过期
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing Gmail token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Gmail credentials not found at {self.credentials_path}. "
                        "Please run: python scripts/setup_gmail_auth.py"
                    )
                logger.info("Starting OAuth2 flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # 保存 token 供下次使用
            with open(self.token_path, 'w') as f:
                f.write(creds.to_json())
            logger.info(f"Gmail token saved to {self.token_path}")

        self._service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail authenticated successfully")

    def fetch_emails(self, days: int = 1) -> List[EmailMessage]:
        """
        抓取过去 N 天内的匹配邮件

        Args:
            days: 抓取最近几天的邮件

        Returns:
            匹配的邮件列表
        """
        if not self._service:
            self.authenticate()

        # 构建时间过滤（Gmail 使用 Unix timestamp）
        since_date = datetime.now() - timedelta(days=days)
        since_str = since_date.strftime('%Y/%m/%d')

        # 构建查询：LinkedIn 发件人 OR 招聘关键词
        linkedin_query = ' OR '.join(
            f'from:{sender}' for sender in self.LINKEDIN_SENDERS
        )
        job_keywords_query = ' OR '.join(
            f'subject:"{kw}"' for kw in self.JOB_KEYWORDS[:5]  # Gmail query 有长度限制
        )
        query = f'after:{since_str} ({linkedin_query} OR {job_keywords_query})'

        logger.info(f"Gmail query: {query}")

        try:
            results = self._service.users().messages().list(
                userId='me', q=query, maxResults=50
            ).execute()
        except Exception as e:
            logger.error(f"Gmail API error: {e}")
            return []

        messages = results.get('messages', [])
        logger.info(f"Found {len(messages)} matching emails")

        emails = []
        for msg_ref in messages:
            email = self._fetch_message(msg_ref['id'])
            if email:
                emails.append(email)

        return emails

    def _fetch_message(self, message_id: str) -> Optional[EmailMessage]:
        """抓取单封邮件详情"""
        try:
            msg = self._service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
        except Exception as e:
            logger.error(f"Error fetching message {message_id}: {e}")
            return None

        headers = {h['name'].lower(): h['value'] for h in msg['payload'].get('headers', [])}
        subject = headers.get('subject', '(no subject)')
        sender = headers.get('from', '')
        date = headers.get('date', '')

        body = self._decode_body(msg['payload'])
        email_type = self._classify_email(sender, subject)

        return EmailMessage(
            id=message_id,
            subject=subject,
            sender=sender,
            date=date,
            body=body,
            email_type=email_type
        )

    def _decode_body(self, payload: dict) -> str:
        """base64 解码邮件正文，HTML 转纯文本"""
        body_text = ''

        if 'parts' in payload:
            # multipart 邮件
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                if mime_type == 'text/plain':
                    body_text = self._extract_part_text(part)
                    break
                elif mime_type == 'text/html' and not body_text:
                    body_text = self._extract_part_text(part, html=True)
                elif mime_type.startswith('multipart/'):
                    # 递归处理嵌套 multipart
                    nested = self._decode_body(part)
                    if nested:
                        body_text = nested
                        break
        elif 'body' in payload:
            data = payload['body'].get('data', '')
            if data:
                decoded = base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='replace')
                if payload.get('mimeType', '') == 'text/html':
                    body_text = self._html_to_text(decoded)
                else:
                    body_text = decoded

        # 清理多余空行
        body_text = re.sub(r'\n{3,}', '\n\n', body_text.strip())
        return body_text[:3000]  # 限制长度避免 token 过多

    def _extract_part_text(self, part: dict, html: bool = False) -> str:
        """从邮件 part 中提取文本"""
        data = part.get('body', {}).get('data', '')
        if not data:
            return ''
        decoded = base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='replace')
        if html:
            return self._html_to_text(decoded)
        return decoded

    def _html_to_text(self, html: str) -> str:
        """HTML 转纯文本"""
        soup = BeautifulSoup(html, 'html.parser')
        # 移除 script 和 style
        for tag in soup(['script', 'style', 'head', 'meta', 'link']):
            tag.decompose()
        text = soup.get_text(separator='\n')
        return text

    def _classify_email(self, sender: str, subject: str) -> str:
        """分类邮件：linkedin 或 job"""
        sender_lower = sender.lower()
        if any(s in sender_lower for s in self.LINKEDIN_SENDERS):
            return 'linkedin'
        return 'job'
