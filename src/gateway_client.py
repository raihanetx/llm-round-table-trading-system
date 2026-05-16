#!/usr/bin/env python3
"""
Gateway Client — HTTP client for OpenCode Zen API.
"""

import json
import time
from typing import Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class GatewayClient:
    """Minimal HTTP client for OpenCode Zen chat completions."""

    def __init__(self, base_url: str, api_key: str, timeout: int = 30, max_retries: int = 3):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

    def chat_completion(
        self,
        model: str,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ) -> Dict:
        """
        Send a chat completion request.

        Returns: {"content": str, "model": str, "usage": dict} on success
                 {"error": str} on failure
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode("utf-8")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                req = Request(url, data=payload, headers=headers, method="POST")
                with urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                # Extract response
                choice = data.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                usage = data.get("usage", {})

                return {
                    "content": content,
                    "model": data.get("model", model),
                    "usage": usage,
                }

            except HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                if e.code == 429 and attempt < self.max_retries:
                    # Rate limited — wait and retry
                    wait = 2 ** attempt
                    time.sleep(wait)
                    continue
                return {"error": f"HTTP {e.code}: {body[:200]}"}

            except (URLError, TimeoutError) as e:
                if attempt < self.max_retries:
                    time.sleep(1)
                    continue
                return {"error": f"Connection error: {str(e)[:200]}"}

            except Exception as e:
                return {"error": f"Unexpected error: {str(e)[:200]}"}

        return {"error": "Max retries exceeded"}
