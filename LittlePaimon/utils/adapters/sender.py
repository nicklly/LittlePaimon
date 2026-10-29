"""发送层：用统一接口把消息发回当前会话。"""
from __future__ import annotations

from typing import Any

from .message import ImageData, MessageBuilder
from .unified import UnifiedEvent


class Sender:
    """绑定 ``bot`` + ``event`` 的发送器。

    所有方法都直接透传到 ``bot.send(event, message)``，
    因此超时、频率限制等适配器差异仍由各自适配器处理。
    """

    def __init__(self, bot: Any, event: Any):
        self.bot = bot
        self.event = event
        self.unified = UnifiedEvent(bot, event)
        self.builder = MessageBuilder(self.unified.adapter)

    # ---------- 基础发送 ----------

    async def send(self, message: Any, **kwargs: Any) -> Any:
        if message is None or message == "":
            return None
        return await self.bot.send(self.event, message, **kwargs)

    async def send_parts(self, *parts: Any, **kwargs: Any) -> Any:
        return await self.send(self.builder.build(*parts), **kwargs)

    def _head_parts(self, at_sender: bool, reply: bool) -> list:
        parts = []
        if reply and self.unified.message_id:
            parts.append(self.builder.reply(self.unified.message_id))
        if at_sender and self.unified.user_id:
            parts.append(self.builder.at(self.unified.user_id))
            parts.append(self.builder.text(" "))
        return parts

    # ---------- 常用消息 ----------

    async def text(self, content: Any, *, at_sender: bool = False, reply: bool = False,
                   **kwargs: Any) -> Any:
        parts = self._head_parts(at_sender, reply) + [self.builder.text(content)]
        return await self.send_parts(*parts, **kwargs)

    async def image(self, data: ImageData, *, at_sender: bool = False, reply: bool = False,
                    **kwargs: Any) -> Any:
        parts = self._head_parts(at_sender, reply) + [self.builder.image(data)]
        return await self.send_parts(*parts, **kwargs)

    async def text_and_image(self, content: Any, data: ImageData, *,
                             at_sender: bool = False, reply: bool = False,
                             **kwargs: Any) -> Any:
        parts = self._head_parts(at_sender, reply) + [self.builder.text(content), self.builder.image(data)]
        return await self.send_parts(*parts, **kwargs)

    async def at(self, user_id: Any, **kwargs: Any) -> Any:
        return await self.send(self.builder.at(user_id), **kwargs)


def get_sender(bot: Any, event: Any) -> Sender:
    """取一个绑定当前会话的发送器。"""
    return Sender(bot, event)


async def send_text(bot: Any, event: Any, content: Any, **kwargs: Any) -> Any:
    return await Sender(bot, event).text(content, **kwargs)


async def send_image(bot: Any, event: Any, data: ImageData, **kwargs: Any) -> Any:
    return await Sender(bot, event).image(data, **kwargs)
