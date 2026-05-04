"""本地翻译/摘要占位模块。

当前项目不再依赖外部大模型翻译 API。这个类保留旧调用接口，
避免邮件处理代码导入失败；如需高质量翻译，后续接入 Codex/OpenAI 路径。
"""
from typing import Optional


class Translator:
    """本地摘要器：不调用外部服务。"""

    def __init__(self, api_key: Optional[str] = None, model: str = "local-rule"):
        self.api_key = api_key
        self.model = model

    def translate(self, text: str, context: str = "") -> str:
        """返回简短中文摘要占位，不做外部API调用。"""
        if not text or not text.strip():
            return "(邮件内容为空)"

        cleaned = " ".join(text.strip().split())
        snippet = cleaned[:220]
        prefix = f"邮件背景：{context}。 " if context else ""
        return f"{prefix}本地摘要：{snippet}"
