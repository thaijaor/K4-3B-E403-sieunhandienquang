"""HTTP boundary to the independently owned AI and Persona services."""
import httpx
from fastapi import HTTPException


class ContractError(Exception):
    """A successful upstream response was not valid JSON."""


class Services:
    def __init__(self, ai_url="", persona_url="", key=""):
        self.ai_url = ai_url.rstrip("/")
        self.persona_url = persona_url.rstrip("/")
        self.key = key

    def request(self, kind, method, path, owner, payload=None, request_id=None):
        base = self.ai_url if kind == "ai" else self.persona_url
        if not base:
            raise HTTPException(503, "API AI chưa kết nối." if kind == "ai" else "API Persona chưa kết nối.")
        headers = {"X-Learner-ID": owner}
        if self.key:
            headers["Authorization"] = f"Bearer {self.key}"
        if request_id:
            headers["Idempotency-Key"] = request_id
        try:
            with httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as client:
                response = client.request(method, base + path, headers=headers, json=payload)
            if response.status_code == 409:
                raise HTTPException(409, "Phiên bản đã thay đổi. Tải lại bản mới và đối chiếu bản nháp.")
            if response.status_code == 404:
                raise HTTPException(404, "Dữ liệu tích hợp không còn tồn tại.")
            response.raise_for_status()
            try:
                return response.json()
            except ValueError as exc:
                if kind == "ai":
                    raise ContractError("Invalid AI JSON") from exc
                raise HTTPException(502, "Persona trả JSON không hợp lệ.") from exc
        except httpx.TimeoutException:
            raise HTTPException(504, "Dịch vụ phản hồi quá lâu. Vui lòng thử lại.")
        except httpx.HTTPError:
            raise HTTPException(502, "Dịch vụ tích hợp lỗi hoặc trả dữ liệu không hợp lệ.")
