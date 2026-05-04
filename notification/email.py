"""邮件通知模块"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from models.job import Job


class EmailNotifier:
    """邮件通知器"""

    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

    def send_job_alert(self, jobs: List[Job], recipient_email: str) -> bool:
        """
        发送职位通知邮件

        Args:
            jobs: 匹配的职位列表
            recipient_email: 收件人邮箱

        Returns:
            是否发送成功
        """
        if not jobs:
            print("No jobs to notify")
            return False

        # 构建邮件内容
        subject = f"🎯 发现 {len(jobs)} 个匹配的新职位！"
        body = self._build_email_body(jobs)

        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = recipient_email

        # 添加HTML内容
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)

        # 发送邮件
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            print(f"✅ Email sent successfully to {recipient_email}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication Error: {e}")
            print("   Please check your Gmail App Password")
            return False
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

    def _build_email_body(self, jobs: List[Job]) -> str:
        """构建邮件HTML内容"""
        html = """
        <html>
        <body>
        <h2 style="color: #483fad;">以下是今天匹配的职位：</h2>
        <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
        """

        for job in jobs:
            html += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 15px 10px;">
                    <h3 style="margin: 0 0 5px 0; color: #333;">
                        📌 {job.title}
                    </h3>
                    <p style="margin: 5px 0; color: #666; font-size: 14px;">
                        <strong>公司:</strong> {job.company}<br>
                        <strong>地点:</strong> {job.location}<br>
                        <strong>平台:</strong> {job.platform}
                    </p>
                    <a href="{job.url}"
                       style="display: inline-block;
                              padding: 8px 16px;
                              background-color: #483fad;
                              color: white;
                              text-decoration: none;
                              border-radius: 4px;
                              margin-top: 10px;">
                        查看职位
                    </a>
                </td>
            </tr>
            """

        html += """
        </table>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            此邮件由 AAIP Job Aggregator 自动发送
        </p>
        </body>
        </html>
        """
        return html
