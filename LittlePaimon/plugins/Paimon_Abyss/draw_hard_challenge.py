import datetime
from typing import  List

from LittlePaimon.database import Hard_Challenge_Info, Abyss2Info
from LittlePaimon.utils.alias import get_chara_icon, get_name_by_id
from LittlePaimon.utils.image import PMImage
from LittlePaimon.utils.image import font_manager as fm
from LittlePaimon.utils.image import load_image
from LittlePaimon.utils.message import MessageBuild
from LittlePaimon.utils.path import RESOURCE_BASE_PATH

async def group_by_floor(info: Hard_Challenge_Info) -> List[dict]:
    """将角色数据按Boss分组"""
    floors = {}
    for character in info.teams:
        if character.Boss not in floors:
            floors[character.Boss] = {
                'boss': character.Boss,
                'battle_time': character.battle_time,
                'characters': [],
                'best_avatars': character.best_avatar or []
            }
        floors[character.Boss]['characters'].append(character)
    return list(floors.values())

async def draw_floor_team(bg: PMImage, characters: List[Abyss2Info], y_offset: int):
    """绘制队伍角色（单行4个）"""
    # 角色卡片参数
    card_width = 145  # 卡片宽度缩小以适应间隔
    spacing = 15      # 角色间隔
    start_x = 30      # 起始X坐标

    total_width = 4 * card_width + 3 * spacing
    start_x = (1080 - total_width) // 2  # 自动居中计算
    # 绘制4个角色
    for i, chara in enumerate(characters[:4]):
        avatar_bg = PMImage(await load_image(RESOURCE_BASE_PATH / 'icon' / f"star{chara.rarity}.png"), mode='RGBA')
        rank = await load_image(RESOURCE_BASE_PATH / 'icon' / f"命之座{chara.rank}.png", size=(30, 35))
        await avatar_bg.resize((130, 135))
        x_pos = 60 + i * (card_width + 10)
        # 角色头像
        if chara.icon:
            try:
                avatar = PMImage(await load_image(RESOURCE_BASE_PATH / 'avatar' / f"{chara.icon}.png"), mode='RGBA')
                await avatar.resize((120, 125))
                await avatar_bg.paste(avatar, (5, 5), True)
                await avatar_bg.paste(rank, (100, 100))
            except:
                pass
        # 角色信息
        await bg.paste(avatar_bg, (x_pos + (card_width - 100)//2 + 5, y_offset + 110))

async def draw_dps_card(bg: PMImage, avatar_data: dict, x_pos: int, y_pos: int):
    avatar_bg = PMImage(await load_image(RESOURCE_BASE_PATH / 'general' / f"orange_circle.png"))
    await avatar_bg.resize((60, 60))
    if avatar_data.get('avatar_id'):
        try:
            avatar = PMImage(await load_image(RESOURCE_BASE_PATH / 'avatar' / f"{get_chara_icon(name=get_name_by_id(avatar_data.get('avatar_id')))}.png"), mode='RGBA')
            await avatar.resize((55, 55))
            await avatar.to_circle('circle')
            await avatar_bg.paste(avatar, (2, 5))
            await bg.paste(avatar_bg, (x_pos, y_pos))
        except Exception as e:
            print(f"加载头像失败: {e}")

async def draw_best_avatars(bg: PMImage, best_avatars: list, y_offset: int):
    """绘制最佳角色区域"""
    if not best_avatars:
        return

    x_pos = 60
    await draw_dps_card(
        bg=bg,
        avatar_data=best_avatars[0],
        x_pos=x_pos + 30,
        y_pos=y_offset + 300
    )
    await bg.text('最强一击', x_pos + 100, y_offset + 310, fm.get('SourceHanSansCN-Bold.otf', 40),'#252525')
    await bg.text(f"{best_avatars[0].get('dps', '0')}", x_pos + 270, y_offset + 310, fm.get('SourceHanSansCN-Bold.otf', 40), '#252525')

    if len(best_avatars) > 1:
        await draw_dps_card(
            bg=bg,
            avatar_data=best_avatars[1],
            x_pos=x_pos + 450,
            y_pos=y_offset + 300
        )
        await bg.text( f"最高总伤害",x_pos + 520, y_offset + 310, fm.get('SourceHanSansCN-Bold.otf', 40), '#252525')
        await bg.text( f"{best_avatars[1].get('dps', '0')}", x_pos + 750, y_offset + 310, fm.get('SourceHanSansCN-Bold.otf', 40), '#252525')
    else:
        await bg.text("无其他突出表现", 60 + 180, y_offset + 60,  fm.get('hywh', 30))

async def draw_single_floor(bg: PMImage, floor_info: dict, floor_idx: int, y_offset: int):
    """绘制单层信息"""
    time_bg_width = 180
    floor_bg = PMImage(await load_image(RESOURCE_BASE_PATH / 'general' / 'frame.png'))
    await floor_bg.resize((1040, 450))
    # Boss名称
    boss_bg = PMImage(await load_image(RESOURCE_BASE_PATH / 'general' / 'orange_card.png'))
    await boss_bg.resize((550, 50))
    await bg.paste(boss_bg, (90, y_offset + 65))
    # 战斗用时
    await bg.text(floor_info['boss'], 105, y_offset + 70,  fm.get('SourceHanSansCN-Bold.otf', 40), align='center')
    await bg.text(f"{floor_info['battle_time']}秒", 800 - time_bg_width//2, y_offset + 70, fm.get('SourceHanSansCN-Bold.otf', 40), '#252525')
    await bg.paste(floor_bg, (20, y_offset))
    # 1. 最佳角色区域
    await draw_best_avatars(bg, floor_info['best_avatars'], y_offset + 30)
    # 2. 队伍角色区域
    await draw_floor_team(bg, floor_info['characters'], y_offset + 50)

async def draw_hard_challenge_card(info: Hard_Challenge_Info):
    if info is None:
        return '暂无深渊挑战数据，请稍候再试'
    # 加载图片素材
    bg = PMImage(
        await load_image(RESOURCE_BASE_PATH / 'hard_challenge' / 'bg.png', mode='RGBA')
    )
    orange_line = await load_image(RESOURCE_BASE_PATH / 'general' / 'line.png')
    difficult = await load_image(RESOURCE_BASE_PATH / 'hard_challenge' / f'Icon_Stygian_Onslaught_Medal_{info.battle[0].battle_difficult}.png', size=(60, 60))
    # 标题文字
    await bg.text('幽境危战', 36, 29, fm.get('优设标题黑', 108), '#40342d')
    # UID和昵称
    await bg.text(f'UID{info.uid}', 1040, 114, fm.get('bahnschrift_regular.ttf', 36), '#40342d', 'right')

    # 战绩速览标题
    await bg.paste(orange_line, (40, 164))
    await bg.text('最佳纪录', 63, 176, fm.get('SourceHanSansCN-Bold.otf', 30), 'white')
    await bg.paste(difficult,(870, 160))
    await bg.text(f'{info.battle[0].max_battle_time}秒', 940, 176, fm.get('SourceHanSansCN-Bold.otf', 30), '#252525')
    # logo和生成时间
    await bg.text( f'CREATED BY LITTLEPAIMON', 730, 1580, fm.get('bahnschrift_regular.ttf', 30), '#252525', 'right')
    # 2. 分组数据（按Boss分组）
    floor_data = await group_by_floor(info)

    # 3. 绘制三层信息
    for floor_idx in range(3):
        y_offset = 250 + floor_idx * 450  # 每层间隔50px

        if floor_idx < len(floor_data):
            floor_info = floor_data[floor_idx]
            await draw_single_floor(bg, floor_info, floor_idx, y_offset)
        else:
            # 绘制空白层提示
            await bg.draw_rounded_rectangle((40, y_offset, 1040, y_offset + 500),radius=15)
            await bg.text((540, y_offset + 250), f"第{floor_idx+1}层数据缺失", font=fm.get('hywh', 35), align='center', fill='#AAAAAA')

    return MessageBuild.Image(bg)