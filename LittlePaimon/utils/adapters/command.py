"""命令层：统一命令前缀与触发方式。

NoneBot 自带的 ``on_command`` 只解析「消息首段是文本」的情况：

- OneBot 里 ``@机器人 /指令`` 的首段是 ``at``，解析不到；
- QQ 官方适配器里 ``@机器人 指令`` 的首段是 ``mention_user``，同样解析不到；
- 两套适配器的默认前缀（``/``）与「私聊免前缀」「@ 免前缀」习惯也不一致。

``on_command_all`` 在解析前先剥掉开头的 @ / 引用段，并统一前缀规则：

1. 配置里的 ``COMMAND_START``（默认 ``/``）始终有效；
2. 私聊、或 ``to_me``（@ / 回复机器人）时允许**不带前缀**；
3. 解析结果写入 NoneBot 标准的 ``state[PREFIX_KEY]``，因此
   ``CommandArg()`` / ``CommandWhitespace()`` 等依赖可以照常使用。
"""
from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence, Union

from nonebot import get_driver, on_message
from nonebot.adapters import Bot, Event
from nonebot.consts import (
    CMD_ARG_KEY,
    CMD_KEY,
    CMD_START_KEY,
    CMD_WHITESPACE_KEY,
    PREFIX_KEY,
    RAW_CMD_KEY,
)
from nonebot.rule import Rule
from nonebot.typing import T_State

from .unified import UnifiedEvent, strip_leading_mentions


def get_command_start() -> set:
    """读取全局命令前缀，读不到时退回 ``/``。"""
    try:
        starts = getattr(get_driver().config, "command_start", None)
    except Exception:
        starts = None
    return set(starts) if starts else {"/"}


def parse_command(
    bot: Any,
    event: Any,
    names: Sequence[str],
    prefixes: Optional[Iterable[str]] = None,
) -> Optional[dict]:
    """尝试把事件解析成命令，成功返回 ``state[PREFIX_KEY]`` 需要的内容。"""
    get_type = getattr(event, "get_type", None)
    if not callable(get_type) or get_type() != "message":
        return None

    unified = UnifiedEvent(bot, event)
    message = strip_leading_mentions(event.get_message())
    if not message:
        return None
    first = message[0]
    if not first.is_text():
        return None
    text = str(first.data.get("text", ""))
    if not text:
        return None

    starts = set(prefixes) if prefixes is not None else get_command_start()
    if not starts:
        starts = {""}
    if unified.to_me or unified.is_private:
        starts.add("")

    best = None
    for start in starts:
        for name in names:
            key = f"{start}{name}"
            if not text.startswith(key):
                continue
            rest = text[len(key):]
            # 命令后必须是结尾或空白，避免 "info2" 命中 "info"
            if rest and not rest[0].isspace():
                continue
            if best is None or len(key) > len(best[0]):
                best = (key, start, name, rest)
    if best is None:
        return None

    key, start, name, rest = best
    command_arg = message.__class__()
    if rest.strip():
        command_arg = message.__class__(rest.strip())
    for segment in list(message)[1:]:
        command_arg.append(segment)
    whitespace = rest[: len(rest) - len(rest.lstrip())] or None
    return {
        CMD_KEY: (name,),
        RAW_CMD_KEY: key,
        CMD_ARG_KEY: command_arg,
        CMD_START_KEY: start,
        CMD_WHITESPACE_KEY: whitespace,
    }


def on_command_all(
    cmd: Union[str, Sequence[str]],
    aliases: Iterable[str] = (),
    *,
    prefixes: Optional[Iterable[str]] = None,
    priority: int = 1,
    block: bool = True,
    state: Optional[dict] = None,
    rule: Any = None,
    **kwargs: Any,
):
    """注册一个同时适用于 OneBot v11 / QQ 适配器的命令。

    :param cmd: 主命令名，如 ``"剧诗"``（也接受命令名元组）
    :param aliases: 别名
    :param prefixes: 额外前缀，默认取全局 ``COMMAND_START``；``""`` 表示免前缀
    :param state: 额外的 matcher state
    :param rule: 追加的 Rule
    """
    base = [cmd] if isinstance(cmd, str) else list(cmd)
    names = list(dict.fromkeys([*base, *aliases]))
    matcher_state = dict(state or {})
    matcher_state.setdefault("pm_name", base[0])

    async def _check_command(bot: Bot, event: Event, state: T_State) -> bool:
        parsed = parse_command(bot, event, names, prefixes)
        if parsed is None:
            return False
        state[PREFIX_KEY] = parsed
        return True

    checker = Rule(_check_command)
    if rule is not None:
        checker = checker & rule
    return on_message(rule=checker, priority=priority, block=block,
                      state=matcher_state, _depth=1, **kwargs)
