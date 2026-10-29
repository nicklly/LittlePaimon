"""事件层：把不同适配器的事件归一成统一字段。"""
from __future__ import annotations

from typing import Any, Optional

ADAPTER_ONEBOT11 = "OneBot V11"
ADAPTER_QQ = "QQ"

#: 消息开头需要剥掉的段类型：@、提及、引用回复
MENTION_SEGMENT_TYPES = frozenset({"at", "mention_user", "reply", "reference"})


def get_adapter_name(bot: Any) -> str:
    """取适配器名字（``OneBot V11`` / ``QQ`` / 其他），取不到返回空串。"""
    adapter = getattr(bot, "adapter", None)
    get_name = getattr(adapter, "get_name", None)
    if callable(get_name):
        try:
            return str(get_name())
        except Exception:
            pass
    return str(getattr(bot, "type", "") or "")


def get_self_id(bot: Any, event: Any = None) -> str:
    """取机器人自身 ID。"""
    for source in (bot, event):
        value = getattr(source, "self_id", None)
        if value:
            return str(value)
    return ""


def is_message_event(event: Any) -> bool:
    """是否是消息事件。"""
    get_type = getattr(event, "get_type", None)
    if not callable(get_type):
        return False
    try:
        return get_type() == "message"
    except Exception:
        return False


def get_message_id(event: Any) -> Optional[str]:
    """取消息 ID（OneBot 是 ``message_id``，QQ 是 ``id``）。"""
    for attr in ("message_id", "id"):
        value = getattr(event, attr, None)
        if value:
            return str(value)
    return None


def strip_leading_mentions(message: Any) -> Any:
    """去掉消息开头的 @ / 引用段以及随后的空白。

    两个适配器在「被 @ 时」的消息首段都不一样（OneBot 是 ``at``，QQ 是 ``mention_user``），
    命令解析前统一剥掉，后续逻辑就不用再关心平台差异。
    """
    segments = list(message)
    index = 0
    while index < len(segments) and segments[index].type in MENTION_SEGMENT_TYPES:
        index += 1
    segments = segments[index:]
    if not segments:
        return message.__class__()
    first = segments[0]
    if first.is_text():
        text = str(first.data.get("text", ""))
        stripped = text.lstrip()
        if stripped != text:
            if stripped:
                segments[0] = message.get_segment_class().text(stripped)
            else:
                segments.pop(0)
    return message.__class__(segments)


class UnifiedEvent:
    """包一层事件，提供与适配器无关的字段。"""

    def __init__(self, bot: Any, event: Any):
        self.bot = bot
        self.event = event
        self.adapter = get_adapter_name(bot)

    @classmethod
    def from_event(cls, event: Any, bot: Any = None) -> "UnifiedEvent":
        if bot is None:
            bot = event.get_bot()
        return cls(bot, event)

    def __repr__(self) -> str:
        return (f"<UnifiedEvent adapter={self.adapter!r} user={self.user_id!r} "
                f"group={self.group_id!r} private={self.is_private}>")

    # ---------- 基础信息 ----------

    @property
    def is_message(self) -> bool:
        return is_message_event(self.event)

    @property
    def is_qq(self) -> bool:
        return self.adapter == ADAPTER_QQ

    @property
    def self_id(self) -> str:
        return get_self_id(self.bot, self.event)

    @property
    def user_id(self) -> str:
        get_user_id = getattr(self.event, "get_user_id", None)
        try:
            return str(get_user_id()) if callable(get_user_id) else ""
        except Exception:
            return ""

    @property
    def group_id(self) -> Optional[str]:
        """群号。QQ 官方群用 ``group_openid``，OneBot 用 ``group_id``。"""
        if self.is_qq:
            value = getattr(self.event, "group_openid", None) or getattr(self.event, "group_id", None)
        else:
            value = getattr(self.event, "group_id", None)
        return str(value) if value else None

    @property
    def channel_id(self) -> Optional[str]:
        """频道子频道 ID（QQ 频道场景）。"""
        value = getattr(self.event, "channel_id", None)
        return str(value) if value else None

    @property
    def guild_id(self) -> Optional[str]:
        value = getattr(self.event, "guild_id", None)
        return str(value) if value else None

    @property
    def message_id(self) -> Optional[str]:
        return get_message_id(self.event)

    @property
    def session_id(self) -> str:
        get_session_id = getattr(self.event, "get_session_id", None)
        try:
            return str(get_session_id()) if callable(get_session_id) else ""
        except Exception:
            return ""

    # ---------- 场景判断 ----------

    @property
    def is_guild(self) -> bool:
        return self.channel_id is not None and not self.group_id

    @property
    def is_group(self) -> bool:
        return self.group_id is not None

    @property
    def is_private(self) -> bool:
        return self.is_message and not self.is_group and not self.is_guild

    # ---------- 消息 ----------

    @property
    def message(self) -> Any:
        return self.event.get_message()

    @property
    def plaintext(self) -> str:
        get_plaintext = getattr(self.event, "get_plaintext", None)
        try:
            return str(get_plaintext()) if callable(get_plaintext) else ""
        except Exception:
            return ""

    @property
    def stripped_message(self) -> Any:
        """去掉开头 @ / 引用后的消息。"""
        return strip_leading_mentions(self.message)

    @property
    def to_me(self) -> bool:
        """是否在叫机器人（私聊 / @ / 回复机器人）。"""
        is_tome = getattr(self.event, "is_tome", None)
        if callable(is_tome):
            try:
                return bool(is_tome())
            except Exception:
                pass
        return bool(getattr(self.event, "to_me", False))
