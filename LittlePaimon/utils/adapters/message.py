"""消息层：按当前适配器构造消息段。"""
from __future__ import annotations

from base64 import b64decode
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable, List, Optional, Union
from urllib.parse import urlparse
from urllib.request import url2pathname

from .unified import ADAPTER_ONEBOT11, ADAPTER_QQ

#: 可以直接传给 ``image()`` 的数据
ImageData = Union[str, bytes, BytesIO, Path]


def get_segment_class(adapter: str):
    """取适配器的 ``MessageSegment`` 类；不支持时返回 ``None``。"""
    if adapter == ADAPTER_QQ:
        from nonebot.adapters.qq import MessageSegment  # 延迟导入，没装 QQ 适配器也不影响

        return MessageSegment
    if adapter == ADAPTER_ONEBOT11:
        from nonebot.adapters.onebot.v11 import MessageSegment

        return MessageSegment
    return None


def get_message_class(adapter: str):
    """取适配器的 ``Message`` 类；不支持时返回 ``None``。"""
    if adapter == ADAPTER_QQ:
        from nonebot.adapters.qq import Message
        return Message
    if adapter == ADAPTER_ONEBOT11:
        from nonebot.adapters.onebot.v11 import Message
        return Message
    return None


def _flatten(parts: Iterable[Any]) -> List[Any]:
    result = []
    for part in parts:
        if isinstance(part, (list, tuple)):
            result.extend(_flatten(part))
        else:
            result.append(part)
    return result


class MessageBuilder:
    """构造与适配器匹配的消息。

    不支持未知适配器时退化为纯文本拼接，尽量不让调用方报错。
    """

    SUPPORTED = (ADAPTER_ONEBOT11, ADAPTER_QQ)

    def __init__(self, adapter: str):
        self.adapter = adapter

    @classmethod
    def for_bot(cls, bot: Any) -> "MessageBuilder":
        from .unified import get_adapter_name

        return cls(get_adapter_name(bot))

    @property
    def supported(self) -> bool:
        return self.adapter in self.SUPPORTED

    def text(self, content: Any) -> Any:
        if content is None:
            return None
        segment_class = get_segment_class(self.adapter)
        if segment_class is None:
            return str(content)
        return segment_class.text(str(content))

    def image(self, data: ImageData) -> Any:
        segment_class = get_segment_class(self.adapter)
        if segment_class is None:
            # 未知适配器：只能把链接当文本发出去
            return str(data) if isinstance(data, str) else None
        if self.adapter == ADAPTER_QQ:
            if isinstance(data, str):
                if data.startswith(("http://", "https://")):
                    return segment_class.image(data)
                if data.startswith("base64://"):
                    # OneBot 的 MessageSegment.image(BytesIO) 会转成 base64://...
                    return segment_class.file_image(b64decode(data[len("base64://"):]))
                if data.startswith("file://"):
                    return segment_class.file_image(Path(url2pathname(urlparse(data).path)))
                path = Path(data)
                if path.exists():
                    return segment_class.file_image(path)
                return None
            return segment_class.file_image(data)
        return segment_class.image(data)

    def at(self, user_id: Any) -> Any:
        if not user_id:
            return None
        segment_class = get_segment_class(self.adapter)
        if segment_class is None:
            return None
        if self.adapter == ADAPTER_QQ:
            return segment_class.mention_user(str(user_id))
        return segment_class.at(user_id)

    def reply(self, message_id: Any) -> Any:
        if not message_id:
            return None
        segment_class = get_segment_class(self.adapter)
        if segment_class is None:
            return None
        if self.adapter == ADAPTER_QQ:
            return segment_class.reference(str(message_id))
        return segment_class.reply(message_id)

    def convert(self, part: Any) -> Any:
        """把「别的适配器」的消息段转成当前适配器的消息段。

        旧代码里 ``MessageBuild.Image()`` 之类产出的是 OneBot v11 的段，
        在 QQ 适配器下直接塞进 ``Message`` 会报类型错误；这里按段类型做一次转换。
        无法识别的段返回 ``None``。
        """
        segment_class = get_segment_class(self.adapter)
        if segment_class is None:
            return str(part)
        if isinstance(part, segment_class):
            return part
        if isinstance(part, str):
            return segment_class.text(part)
        segment_type = getattr(part, "type", None)
        data = getattr(part, "data", None) or {}
        if segment_type == "text":
            return segment_class.text(data.get("text", ""))
        if segment_type == "image":
            file = data.get("file") or data.get("url")
            return self.image(file) if file is not None else None
        if segment_type in ("at", "mention_user"):
            return self.at(data.get("qq") or data.get("user_id"))
        if segment_type in ("reply", "reference"):
            reference = data.get("id") or data.get("reference")
            if isinstance(reference, dict):
                reference = reference.get("message_id")
            elif reference is not None and not isinstance(reference, str):
                reference = getattr(reference, "message_id", reference)
            return self.reply(reference)
        return None

    def build(self, *parts: Any) -> Any:
        """把若干片段拼成一条消息；片段可以是 ``str`` / 消息段 / ``None`` / 嵌套列表。"""
        message_class = get_message_class(self.adapter)
        segments = []
        for part in _flatten(parts):
            if part is None or part == "":
                continue
            if message_class is None:
                segments.append(str(part))
            else:
                converted = self.convert(part)
                if converted is not None:
                    segments.append(converted)
        if message_class is None:
            return "".join(segments)
        return message_class(segments)
