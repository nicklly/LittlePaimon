"""Paimon_Abyss 跨适配器改写示例

.. note::
   这个文件**不会被 NoneBot 自动加载**（只加载 ``Paimon_Abyss/__init__.py``），
   放在这里纯粹作为「把现有 OneBot 插件迁到 OneBot v11 + QQ 官方适配器」的参照。

对照 ``Paimon_Abyss/__init__.py`` 的改动：

- ``on_command(...)`` → ``on_command_all(...)``
- ``event: MessageEvent`` → ``event: Event``（基类，两个适配器都能注入）
- ``GroupMessageEvent`` 判断 → ``UnifiedEvent(bot, event).is_group``
- ``CommandPlayer()`` → ``UnifiedEvent`` + ``Player`` 查询（见 ``resolve_players``）
- ``matcher.finish(msg)`` → ``get_sender(bot, event).text/image(...)``
- ``MessageBuild.Image(...)`` 照常使用，``Sender`` 会自动转成当前适配器的段
- 适配器扩展 API（如 ``get_group_member_list``）用 ``hasattr`` 探测
"""

import re

from nonebot.adapters import Bot, Event, Message
from nonebot.params import CommandArg

from LittlePaimon.database import Player
from LittlePaimon.utils.adapters import UnifiedEvent, get_sender, on_command_all
from LittlePaimon.utils.genshin import GenshinInfoManager

from .abyss_statistics import get_statistics
from .draw_role_combat import draw_role_combat_card


# ---------------------------------------------------------------------------
# 1. 命令注册：前缀 / @ 的差异由 on_command_all 统一
#    - 群聊里 “/hxzjjs”、“@机器人 hxzjjs” 都能触发
#    - 私聊里直接 “hxzjjs” 也能触发（命令前缀见 COMMAND_START 配置）
#    - state 与 on_command 完全一致，插件管理/帮助系统照常识别
# ---------------------------------------------------------------------------
role_combat = on_command_all(
    'hxzjjs',
    aliases=('幻想真境剧诗', '剧诗', 'js'),
    priority=10,
    block=True,
    state={
        'pm_name': 'hxzjjs',
        'pm_description': '查看本期幻想真境剧诗战报',
        'pm_usage': 'hxzjjs(uid)',
        'pm_priority': 1,
    },
)


async def resolve_players(unified: UnifiedEvent, text: str) -> list:
    """跨适配器版的 CommandPlayer（简化）。

    ``CommandPlayer`` 内部依赖 OneBot 的 ``msg['at']`` 段和 QQ 号，QQ 适配器下用不了；
    这里退化成「命令里带 UID」或「数据库里已绑定 UID」两种方式。
    """
    if uids := re.findall(r'[1258]\d{8}', text):
        return [(unified.user_id, uid) for uid in uids][:3]
    bound = await Player.filter(user_id=unified.user_id)
    return [(unified.user_id, player.uid) for player in bound][:3]


@role_combat.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    # UnifiedEvent：不用关心底层是 OneBot 还是 QQ
    unified = UnifiedEvent(bot, event)
    sender = get_sender(bot, event)

    text = args.extract_plain_text()
    index = 1 if '上期' in text else 0

    # 群聊/私聊判断：群聊可以一次查多个 UID，私聊只查自己
    players = await resolve_players(unified, text)
    if not players:
        await sender.text('第一次查询请把 UID 加在指令后面', at_sender=True)
        return

    if unified.is_group:
        # 群号：OneBot 是 group_id，QQ 官方群是 group_openid
        await sender.text(f'开始查询，群号 {unified.group_id}')

    for user_id, uid in players:
        info = await GenshinInfoManager(user_id, uid).get_role_combat_info(index)
        if isinstance(info, str):
            await sender.text(f'UID{uid} {info}', reply=True)
            continue

        try:
            # draw_* 目前返回的是 OneBot 的 MessageSegment，
            # Sender 内部会自动转成当前适配器需要的段（图片会走 file_image）
            image = await draw_role_combat_card(info)
        except Exception as exc:
            await sender.text(f'UID{uid} 制图时出错：{exc}', reply=True)
            continue

        await sender.send_parts(image)


# ---------------------------------------------------------------------------
# 2. 群限定命令 + 适配器能力探测
#    ``get_statistics`` 内部调用了 OneBot 的 ``bot.get_group_member_list``，
#    QQ 官方适配器没有这个方法，所以这里先探测能力再调用。
# ---------------------------------------------------------------------------
abyss_stat = on_command_all(
    '深渊统计',
    aliases=('深渊群数据', '深渊群排行'),
    priority=10,
    block=True,
    state={
        'pm_name': '深渊统计',
        'pm_description': '查看本群深渊统计，仅群可用',
        'pm_usage': '深渊统计',
        'pm_priority': 2,
    },
)


@abyss_stat.handle()
async def _(bot: Bot, event: Event):
    unified = UnifiedEvent(bot, event)
    sender = get_sender(bot, event)

    if not unified.is_group:
        await sender.text('该指令只能在群里使用')
        return

    # 能力探测：不同适配器的扩展 API 不完全一致
    if not hasattr(bot, 'get_group_member_list'):
        await sender.text('当前适配器不支持获取群成员列表，暂时无法统计')
        return

    try:
        result = await get_statistics(int(unified.group_id), bot)
    except Exception as exc:
        result = f'制作深渊统计时出错：{exc}'
    await sender.send_parts(result)
