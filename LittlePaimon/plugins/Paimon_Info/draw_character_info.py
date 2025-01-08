import asyncio
import datetime
import os.path
import random
import re
from typing import Optional, List, Tuple

from LittlePaimon.database import Player
from LittlePaimon.utils.files import load_json
from LittlePaimon.utils.path import JSON_DATA
from LittlePaimon.utils.alias import get_chara_icon, get_name_by_id, get_id_by_name
from LittlePaimon.utils.message import MessageBuild
from LittlePaimon.utils.path import RESOURCE_BASE_PATH
from LittlePaimon.utils.image import PMImage, get_qq_avatar, font_manager as fm, load_image

RESOURCES = RESOURCE_BASE_PATH / 'player_info'
ICON = RESOURCE_BASE_PATH / 'icon'

role_data = load_json(JSON_DATA / 'roles_data.json')
role_alias = load_json(JSON_DATA / 'alias.json')['角色']


async def get_avatar(qid: str, size: Tuple[int, int] = (146, 146)) -> PMImage:
    try:
        avatar = await get_qq_avatar(qid)
        await avatar.resize(size)
        await avatar.to_circle('circle')
        await avatar.add_border(6, '#ddcdba', 'circle')
        return avatar
    except Exception:
        return PMImage(size=size, color=(255, 255, 255, 255))


async def draw_character_info(avatarId: dict) -> Optional[PMImage]:
    if avatarId is None:
        return None
    role_id = avatarId['avatarId']
    role_name = get_name_by_id(str(role_id))

    if role_name in ['空', '荧']:
        role_name = '旅行者'

    rarity = role_data[str(role_name)]['star']

    # 背景
    img = PMImage(await load_image(RESOURCES / f'遮盖层.png', mode='RGBA'))
    img_bg = PMImage(await load_image(ICON / f'star{rarity}_no_line.png', mode='RGBA'))
    text_box = PMImage(await load_image(RESOURCES / f'文字遮盖层.png', mode='RGBA'))

    await img_bg.resize((210, 210))
    await img_bg.to_circle('circle')
    await img_bg.add_border(10, '#b59adb' if rarity == 4 else '#c68956', 'circle')

    await img.resize((240, 270))
    await img.paste(img_bg, (5, 5))

    # 角色头像
    faceQ_path = RESOURCE_BASE_PATH / 'avatar' / 'faceQ' / f'{role_id}.png'
    avatar_path = RESOURCE_BASE_PATH / 'avatar' / f'{get_chara_icon(name=get_name_by_id(role_id))}.png'
    if os.path.isfile(faceQ_path):
        avatar = PMImage(await load_image(faceQ_path, mode='RGBA'))
        await avatar.to_circle('circle')
    else:
        avatar = PMImage(await load_image(avatar_path, mode='RGBA'))
        await avatar.to_circle('circle')

    await avatar.resize((210, 210))
    await img.paste(avatar, (10, 10))

    await text_box.resize((220, 100))

    # 角色名简化
    role_id2 = get_id_by_name(role_name)
    filter_alias = [alias for alias in role_alias[role_id2] if len(alias) not in (4, 5, 6)]
    if filter_alias:
        role_name = random.choice(filter_alias)

    talent = len(avatarId['talentIdList']) if 'talentIdList' in avatarId else 0
    # # 命座图标
    constellation = await load_image(ICON / f'命之座{talent}.png')
    constellation = constellation.resize((20, 28))

    await text_box.paste(constellation, (2, 7))
    await text_box.text(role_name, 30, 1, fm.get('hywh', 32), '#252525', 'center')
    await img.paste(text_box, (50, 230))

    # await img.paste(constellation, (5, 235))
    return img


async def draw_char_info_bag(player: Player, PlayerInfo: dict):

    # 确定角色行数，4个为一行
    # row = math.ceil(len(characters) / 5)
    img = PMImage(await load_image(RESOURCES / 'bg.png'))
    await img.resize((1920, 1050))
    # 左右拉伸
    await img.stretch((255, 1100), 295 * 3 - 21, 'width')
    # 上下拉伸
    await img.stretch((50, 100), 45 * 3 - 21, 'height')

    # QQ头像
    avatar = await get_avatar(player.user_id)
    await img.paste(avatar, (47, 52))
    # 昵称
    await img.text(PlayerInfo['playerInfo']['nickname'], 220, 60, fm.get('hywh', 75), '#252525')
    # 个性签名
    if 'signature' in PlayerInfo['playerInfo']:
        await img.text(PlayerInfo['playerInfo']['signature'], 220, 150, fm.get('hywh', 35), '#D3D3D3')
    # 玩家UID
    await img.text(f'UID: {player.uid}', 50, 1050, fm.get('bahnschrift_bold', 25), '#252525')
    # 更新面板bar
    await img.paste(await load_image(RESOURCES / 'update_bar.png'), (44, 230))
    # 角色数量和logo
    await img.text(f'共计{len(PlayerInfo["playerInfo"]["showAvatarInfoList"])}名角色', 1660, 1000, fm.get('hywh', 35), '#252525')
    await img.text(f'Created By LITTLEPAIMON', 1870, 1050, fm.get('bahnschrift_bold', 25, 'Bold'), '#252525', 'right')
    await img.text(f'UPDATE BY: {datetime.datetime.now().strftime("%m-%d %H:%M")}', 1850, 265, fm.get('bahnschrift_bold', 48, 'Bold'), '#252525', 'right')

    # 角色列表
    await asyncio.gather(
        *[img.paste(
            await draw_character_info(PlayerInfo['avatarInfoList'][i]),
            (47 + 266 * (i % 7),
             400 + 300 * (i // 7))) for i in range(len(PlayerInfo['playerInfo']['showAvatarInfoList']))]
    )

    return MessageBuild.Image(img, quality=100, mode='RGB')
