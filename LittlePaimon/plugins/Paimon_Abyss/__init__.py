from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageEvent
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

from LittlePaimon.utils import logger
from LittlePaimon.utils.genshin import GenshinInfoManager
from LittlePaimon.utils.message import CommandPlayer

from .abyss_statistics import get_statistics
from .draw_abyss import draw_abyss_card
from .draw_hard_challenge import draw_hard_challenge_card
from .draw_role_combat import draw_role_combat_card
from .youchuang import draw_team

__plugin_meta__ = PluginMetadata(
    name='原神深渊查询',
    description='原神深渊查询',
    usage='...',
    extra={
        'author': '惜月',
        'version': '3.0',
        'priority': 2,
    },
)

sy = on_command(
    'sy',
    aliases={'深渊战报', '深渊信息'},
    priority=10,
    block=True,
    state={
        'pm_name': 'sy',
        'pm_description': '查看本期|上期的深渊战报',
        'pm_usage': 'sy(uid)(本期|上期)',
        'pm_priority': 1,
    },
)
abyss_stat = on_command(
    '深渊统计',
    aliases={'深渊群数据', '深渊群排行'},
    priority=10,
    block=True,
    state={
        'pm_name': '深渊统计',
        'pm_description': '查看本群深渊统计，仅群可用',
        'pm_usage': '深渊统计',
        'pm_priority': 2,
    },
)
abyss_team = on_command(
    '深渊配队',
    aliases={'配队推荐', '深渊阵容'},
    priority=10,
    block=True,
    state={
        'pm_name': '深渊配队',
        'pm_description': '查看深渊配队推荐，数据来源于游创工坊',
        'pm_usage': '深渊配队',
        'pm_priority': 3,
    },
)

hard_challenge = on_command(
    'yjwz',
    aliases={'幽境危战', 'yjwz'},
    priority=10,
    block=True,
    state={
        'pm_name': 'yjwz',
        'pm_description': '查看本期幽境危战战报',
        'pm_usage': 'yjwz(uid)[单人|多人]',
        'pm_priority': 1,
    }
)
#
role_combat = on_command(
    'hxzjjs',
    aliases={'幻想真境剧诗', 'hxzjjs', '剧诗'},
    priority=10,
    block=True,
    state={
        'pm_name': 'hxzjs',
        'pm_description': '查看本期幻想真境剧诗战报',
        'pm_usage': 'hxzjs(uid)',
        'pm_priority': 1,
    }
)
#
# @role_combat.handle()
# async def _(event: MessageEvent, players=CommandPlayer(), msg: Message = CommandArg()):
#     logger.info('原神幻想真境剧诗战报', '开始执行')
#     text = msg.extract_plain_text()  # 先提取文本
#     role_combat_index = 1 if '上期' in text else 0
#     msg = Message()
#     for player in players:
#         logger.info('原神幻想真境剧诗战报', '➤ ', {'用户': players[0].user_id, 'UID': players[0].uid})
#         gim = GenshinInfoManager(player.user_id, player.uid)
#         role_combat_info = await gim.get_role_combat_info(role_combat_index )
#         if isinstance(role_combat_info, str):
#             logger.info('原神幻想真境剧诗', '➤➤', {}, role_combat_info, False)
#             msg += f'UID{player.uid} {role_combat_info}\n'
#         else:
#             logger.info('原神幻想真境剧诗战报', '➤➤', {}, '数据获取成功', True)
#             try:
#                 img = await draw_role_combat_card(role_combat_info)
#                 logger.info('原神幻想真境剧诗战报', '➤➤➤', {}, '制图完成', True)
#                 msg += img
#             except Exception as e:
#                 logger.info('原神幻想真境剧诗战报', '➤➤➤', {}, f'制图出错:{e}', False)
#                 msg += F'UID{player.uid}制图时出错：{e}\n'
#
#     await role_combat.finish(msg)


@hard_challenge.handle()
async def _(event: MessageEvent, players=CommandPlayer(), msg: Message = CommandArg()):
    logger.info('原神幽境危战战报', '开始执行')
    text = msg.extract_plain_text()  # 先提取文本
    battle_type = 'mp' if '多人' in text else 'single'
    abyss2_index = 1 if '上期' in text else 0
    msg = Message()
    for player in players:
        logger.info('原神幽境危战战报', '➤ ', {'用户': players[0].user_id, 'UID': players[0].uid})
        gim = GenshinInfoManager(player.user_id, player.uid)
        hard_challenge_info = await gim.get_abyss2_Info(battle_type, abyss2_index)
        if isinstance(hard_challenge_info, str):
            logger.info('原神幽境危战战报', '➤➤', {}, hard_challenge_info, False)
            msg += f'UID{player.uid} {hard_challenge_info}\n'
        else:
            logger.info('原神幽境危战战报', '➤➤', {}, '数据获取成功', True)
            try:
                img = await draw_hard_challenge_card(hard_challenge_info)
                logger.info('原神幽境危战战报', '➤➤➤', {}, '制图完成', True)
                msg += img
            except Exception as e:
                logger.info('原神幽境危战战报', '➤➤➤', {}, f'制图出错:{e}', False)
                msg += F'UID{player.uid}制图时出错：{e}\n'

    await hard_challenge.finish(msg)


@sy.handle()
async def _(event: MessageEvent, players=CommandPlayer(), msg: Message = CommandArg()):
    logger.info('原神深渊战报', '开始执行')
    abyss_index = 2 if any(i in msg.extract_plain_text() for i in ['上', 'last']) else 1
    msg = Message()
    for player in players:
        logger.info('原神深渊战报', '➤ ', {'用户': players[0].user_id, 'UID': players[0].uid})
        gim = GenshinInfoManager(player.user_id, player.uid)
        abyss_info = await gim.get_abyss_info(abyss_index)
        if isinstance(abyss_info, str):
            logger.info('原神深渊战报', '➤➤', {}, abyss_info, False)
            msg += f'UID{player.uid}{abyss_info}\n'
        else:
            logger.info('原神深渊战报', '➤➤', {}, '数据获取成功', True)
            try:
                img = await draw_abyss_card(abyss_info)
                logger.info('原神深渊战报', '➤➤➤', {}, '制图完成', True)
                msg += img
            except Exception as e:
                logger.info('原神深渊战报', '➤➤➤', {}, f'制图出错:{e}', False)
                msg += F'UID{player.uid}制图时出错：{e}\n'
    await sy.finish(msg, at_sender=True)


@abyss_stat.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    try:
        result = await get_statistics(event.group_id, bot)
    except Exception as e:
        result = f'制作深渊统计时出错：{e}'
    await abyss_stat.finish(result)


@abyss_team.handle()
async def _(event: MessageEvent):
    try:
        result = await draw_team(str(event.user_id))
    except Exception as e:
        result = f'制作深渊配队时出错：{e}'
    await abyss_team.finish(result, at_sender=True)
