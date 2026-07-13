"""OpenAI-compatible LLM client wrapper."""

from __future__ import annotations

import json
from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.openai_api_key:
            raise ExternalServiceError(
                "OPENAI_API_KEY is not configured",
                service="llm",
            )
        self._chat = ChatOpenAI(
            model=self.settings.openai_model,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            api_key=SecretStr(self.settings.openai_api_key.get_secret_value()),
            base_url=self.settings.openai_base_url,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def complete(
        self,
        *,
        system: str,
        user: str,
        response_model: type[T] | None = None,
    ) -> str | T:
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=user),
        ]
        try:
            if response_model is not None:
                structured = self._chat.with_structured_output(response_model)
                result = await structured.ainvoke(messages)
                if isinstance(result, response_model):
                    return result
                if isinstance(result, dict):
                    return response_model.model_validate(result)
                return response_model.model_validate(result)

            response = await self._chat.ainvoke(messages)
            content = response.content
            if isinstance(content, list):
                return "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
            return str(content)
        except Exception as exc:  # noqa: BLE001
            logger.exception("llm_complete_failed")
            raise ExternalServiceError(str(exc), service="llm") from exc

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
    ) -> dict[str, Any]:
        text = await self.complete(
            system=system + "\nRespond with valid JSON only.",
            user=user,
        )
        assert isinstance(text, str)
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        return json.loads(cleaned)
