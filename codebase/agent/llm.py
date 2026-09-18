"""Gọi model qua API tương thích OpenAI (hiện là Gemini). Đổi provider = đổi 3 biến env."""
import os

from openai import OpenAI

REQUIRED_ENV = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL")


class LLM:
    def __init__(self, timeout=20.0):
        missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
        if missing:
            raise RuntimeError(f"Thiếu biến môi trường: {', '.join(missing)} (xem .env.example)")
        self.model = os.environ["OPENAI_MODEL"]
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_BASE_URL"],
                             timeout=timeout, max_retries=1)

    def complete(self, messages, **kwargs):
        """Trả về message của model. kwargs chuyển thẳng vào API (tools, tool_choice, temperature...)."""
        response = self.client.chat.completions.create(model=self.model, messages=messages, **kwargs)
        return response.choices[0].message
