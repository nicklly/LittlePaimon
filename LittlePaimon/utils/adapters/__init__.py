"""跨适配器兼容层

统一 ``nonebot-adapter-onebot`` (OneBot v11) 与 ``nonebot-adapter-qq`` (QQ 官方机器人)
在**事件字段**、**消息构造**、**发送**、**命令触发**上的差异，让同一份代码可以同时跑在
两套适配器上。

设计原则：
- 只依赖 ``nonebot`` 公共 API，QQ 适配器按需延迟导入，没装也不会影响 OneBot 运行；
- 未知适配器退化为「纯文本」能力，不会抛错；
- 事件字段全部用鸭子类型读取，适配器升级新增字段时不受影响。

用法示例::

    from nonebot.params import CommandArg
    from LittlePaimon.utils.adapters import on_command_all, get_sender

    matcher = on_command_all("剧诗", aliases=("hxzjjs",), priority=10)

    @matcher.handle()
    async def _(bot: Bot, event: MessageEvent, arg: Message = CommandArg()):
        ue = UnifiedEvent(bot, event)
        if ue.is_group:
            ...
        sender = get_sender(bot, event)
        await sender.text("稍等，正在制图…")
        await sender.image(bg)          # 本地文件 / bytes / BytesIO / URL 均可
"""

from .command import on_command_all, parse_command
from .message import MessageBuilder
from .sender import Sender, get_sender, send_image, send_text
from .unified import (
    ADAPTER_ONEBOT11,
    ADAPTER_QQ,
    UnifiedEvent,
    get_adapter_name,
    get_self_id,
    strip_leading_mentions,
)

__all__ = [
    "ADAPTER_ONEBOT11",
    "ADAPTER_QQ",
    "UnifiedEvent",
    "get_adapter_name",
    "get_self_id",
    "strip_leading_mentions",
    "MessageBuilder",
    "Sender",
    "get_sender",
    "send_text",
    "send_image",
    "on_command_all",
    "parse_command",
]
