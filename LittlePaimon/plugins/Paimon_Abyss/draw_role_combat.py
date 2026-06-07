from typing import  List
import datetime

from scipy.sparse.csgraph import shortest_path

from LittlePaimon.database import RoleCombat_Info, Buffs_Info, Role_Combat_Info
from LittlePaimon.utils.alias import get_chara_icon
from LittlePaimon.utils.image import PMImage
from LittlePaimon.utils.image import font_manager as fm
from LittlePaimon.utils.image import load_image
from LittlePaimon.utils.message import MessageBuild
from LittlePaimon.utils.path import RESOURCE_BASE_PATH


nomedal = RESOURCE_BASE_PATH / 'role_combat' / 'nomedal.png'
medal = RESOURCE_BASE_PATH / 'role_combat' / 'medal.png'
flower = RESOURCE_BASE_PATH / 'role_combat' / 'flower.png'

game_mode = {
    1: '简单',
    2: '普通',
    3: '困难',
    4: '卓越',
    5: '月谕'
}

async def draw_role_combat_card(info: Role_Combat_Info):
    x = 570
    width = 100
    if not info:
        return '暂无深渊挑战数据，请稍候再试'
    # 加载图片素材
    bg = PMImage(
        await load_image(RESOURCE_BASE_PATH / 'general' / 'bg.png', mode='RGBA')
    )
    # 标题文字
    await bg.text('幻想真境剧诗', 36, 29, fm.get('优设标题黑', 108), '#40342d')
    # UID和昵称
    await bg.text(f'UID{info.uid}', 1040, 114, fm.get('bahnschrift_bold', 36), '#252525', 'right')
    orange_line = PMImage(await load_image(RESOURCE_BASE_PATH / 'general' / 'line.png'), mode='RGBA')
    await orange_line.text(f'{game_mode[info.stat.difficulty_id]}模式', 5, 8, fm.get('SourceHanSansCN-Bold.otf', 38))
    await orange_line.text(f'UPDATE BY: {datetime.datetime.now().strftime("%m-%d %H:%M")}', 980, 10, fm.get('bahnschrift_bold', 38, 'Bold'), '#252525', 'right')
    await bg.paste(orange_line, (40, 164))

    # 挑战星章
    await bg.text('明星挑战星章', 40, 250, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')
    spacing = 45
    medal_icon = PMImage(await load_image(medal), mode='RGBA')
    nomedal_icon = PMImage(await load_image(nomedal), mode='RGBA')
    medal_background = PMImage(await load_image(RESOURCE_BASE_PATH / 'general' / 'black2.png'), mode='RGBA')
    if len(info.stat.medal_round_list) == 12:
        x = 490
        width = 180
    start_x = x
    await medal_background.stretch((200, medal_background.width - 170), width, 'width')
    for i, medals in enumerate(info.stat.medal_round_list):
        current_x = 10 + (i * spacing)
        await medal_background.paste(medal_icon if medals == 1 else nomedal_icon, (current_x, 7))
    await bg.paste(medal_background, (start_x, 245))

    # 最佳挑战记录
    await bg.text('最佳纪录', 40, 350, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')
    await bg.text(f'第{info.stat.max_round_id}幕', 350, 350, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')
    # 场外观众声援
    await bg.text('场外观众声援', 40, 450, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')
    await bg.text(f'{info.stat.avatar_bonus_num}次', 390, 450, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')
    # 幻剧之花
    await bg.text('消耗「幻剧之花」', 535, 350, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')
    await bg.text(f'{info.stat.coin_num}', 950, 350, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')
    flower_icon = PMImage(await load_image(flower), mode='RGBA')
    await flower_icon.resize((50, 50))
    await bg.paste(flower_icon, (895, 345))
    # 角色支援其他玩家
    await bg.text('助演角色支援玩家', 535, 450, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')
    await bg.text(f'{info.stat.tarot_finished_cnt}次', 970, 450, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')

    await bg.stretch((600, bg.height - 250), 50, 'height')

    shortest_data = info.shortest
    if all([
        info.max_defeat_avatar,
        info.max_damage_avatar,
        info.max_take_damage_avatar,
        info.total_coin_consumed,
        shortest_data is not None
    ]):
        await bg.draw_line((40, 515), (1030, 515), color='orange')
        await bg.text('演出总时长', 40, 550, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')
        minutes, secs = divmod(info.stat.total_use_time, 60)
        await bg.text(f"{minutes}分{secs}秒", 450, 550, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')

        stat = [
            {
                'chara_id': info.max_damage_avatar.avatar_id,
                'label'   : '最高伤害输出',
                'label_y' : 580,
                'value'   : str(info.max_damage_avatar.value),
                'value_y' : 620,
                'avatar_y': 580
            },
            {
                'chara_id': info.max_defeat_avatar.avatar_id,
                'label'   : '击败最多敌人',
                'label_y' : 680,
                'value'   : str(info.max_defeat_avatar.value),
                'value_y' : 720,
                'avatar_y': 680
            },
            {
                'chara_id': info.max_take_damage_avatar.avatar_id,
                'label'   : '最高承受伤害',
                'label_y' : 780,
                'value'   : str(info.max_take_damage_avatar.value),
                'value_y' : 820,
                'avatar_y': 780
            },
        ]
        for stats in stat:
            bg1 = PMImage(await load_image(RESOURCE_BASE_PATH / 'general' / f"orange_circle.png"))
            await bg1.resize((80, 80))
            await bg.text(f'{stats["label"]}', 860, stats["label_y"], fm.get('SourceHanSansCN-Bold.otf', 30), '#40342d')
            await bg.text(f'{stats["value"]}', 860, stats["value_y"], fm.get('SourceHanSansCN-Bold.otf', 30), '#40342d')
            side_avatar = PMImage(await load_image(RESOURCE_BASE_PATH / 'avatar_side' / f'{get_chara_icon(chara_id=stats["chara_id"], icon_type="side")}.png'), mode='RGBA')
            await side_avatar.resize((80, 80))
            await side_avatar.to_circle('circle')
            await bg1.paste(side_avatar, (0, 0))
            await bg.paste(bg1, (750, stats["avatar_y"]))

        start_y = 725
        avatar_width = 140
        spacing = 10
        await bg.text('最快完成演出队伍', 40, 650, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')
        for i, chara in enumerate(shortest_data):
            current_x = spacing + i * (avatar_width + spacing)
            avatar_bg = PMImage(await load_image(RESOURCE_BASE_PATH / 'general' / f"orange_circle.png"))
            avatar = PMImage(await load_image(RESOURCE_BASE_PATH / 'avatar' / f'{get_chara_icon(chara_id=chara.avatar_id)}.png'), mode='RGBA')
            await avatar.resize((128, 128))
            await avatar.to_circle('circle')
            await avatar_bg.resize((135, 135))
            await avatar_bg.paste(avatar,(3, 3))
            await bg.paste(avatar_bg, (current_x + 20, start_y))
    else:
        no_data = PMImage(await load_image(RESOURCE_BASE_PATH / 'general' / f"orange_bord.png"))
        await no_data.stretch((100, 200), 760, 'width')
        await no_data.stretch((100, 110), 200, 'height')
        await no_data.text('暂无挑战数据', 280, 125, fm.get('SourceHanSansCN-Bold.otf', 60), '#40342d')
        await bg.paste(no_data, (40, 520))

    return MessageBuild.Image(bg)