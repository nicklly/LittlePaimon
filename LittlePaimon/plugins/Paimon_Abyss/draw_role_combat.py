import datetime

from LittlePaimon.database import Role_Combat_Info
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

# 元素英文名 -> 图标文件名
element_type = {
    'Pyro': '火',
    'Cryo': '冰',
    'Geo': '岩',
    'Dendro': '草',
    'Hydro': '水',
    'Electro': '雷',
    'Anemo': '风'
}

# 角色卡尺寸与配色
CARD_WIDTH = 140
CARD_HEIGHT = 175
CARD_AVATAR_WIDTH = 130
CARD_AVATAR_HEIGHT = 135
CARD_GAP = 15
SECTION_TITLE_HEIGHT = 80
FLOOR_TITLE_FONT = 26
FLOOR_TITLE_HEIGHT = 34
TEAM_GAP = 18

# 每一幕的边框
PANEL_PAD = 16
PANEL_RADIUS = 18
PANEL_GAP = 20
PANEL_BORDER = '#e0d5c2'
PANEL_LEFT = 30
PANEL_WIDTH = 1020
TITLE_TO_CARDS = 12


async def draw_chara_card(chara) -> PMImage:
    """绘制单个角色卡：星章底框 + 头像 + 元素图标 + 试用标签 + 等级"""
    box = RESOURCE_BASE_PATH / 'icon' / f'{chara.rarity}starbox.png'
    if not box.exists():
        box = RESOURCE_BASE_PATH / 'icon' / '5starbox.png'
    card = PMImage(await load_image(box, size=(CARD_WIDTH, CARD_HEIGHT), mode='RGBA'))
    # 角色头像
    icon = chara.icon or get_chara_icon(chara_id=chara.character_id)
    try:
        avatar = PMImage(await load_image(RESOURCE_BASE_PATH / 'avatar' / f'{icon}.png', mode='RGBA'))
        await avatar.resize((CARD_AVATAR_WIDTH, CARD_AVATAR_HEIGHT))
        await card.paste(avatar, (5, 5))
    except Exception:
        pass
    # 元素图标
    element = element_type.get(chara.element)
    element_path = RESOURCE_BASE_PATH / 'icon' / f'{element}.png'
    if element and element_path.exists():
        element_icon = PMImage(await load_image(element_path, size=(24, 28), mode='RGBA'))
        await card.paste(element_icon, (4, 4))
    # 试用标签
    if chara.is_trial:
        trial_tag = PMImage(size=(42, 22), color=(0, 0, 0, 0), mode='RGBA')
        await trial_tag.draw_rounded_rectangle((0, 0, 42, 22), radius=6, color='#d8625c')
        await trial_tag.text('试用', (0, 42), (0, 22), fm.get('SourceHanSansCN-Bold.otf', 15), 'white', 'center')
        await card.paste(trial_tag, (CARD_WIDTH - 46, 4))
    # 等级
    level = chara.level if chara.level is not None else 0
    await card.text(f'Lv.{level}', (0, CARD_WIDTH), (139, 173),
                    fm.get('bahnschrift_bold', 24), '#4b3d33', 'center')
    return card


def collect_team_floors(info) -> list:
    """把 teams 整理成 [(幕序号, [队伍成员列表, ...]), ...]"""
    teams = getattr(info, 'teams', None)
    if not teams:
        return []
    floors = teams.items() if hasattr(teams, 'items') else list(enumerate(teams))
    result = []
    for key, floor in floors:
        if floor is None or not getattr(floor, 'battles_team', None):
            continue
        index = key if getattr(floor, 'index', None) is None else floor.index
        floor_teams = []
        for team in floor.battles_team:
            members = [member for member in (getattr(team, 'Battleinfos', None) or []) if member][:4]
            if members:
                floor_teams.append(members)
        if floor_teams:
            result.append((index, floor_teams))
    return result


def floor_panel_height(floor_teams: list) -> int:
    """单幕边框的高度"""
    rows = len(floor_teams)
    return (PANEL_PAD * 2 + FLOOR_TITLE_HEIGHT + TITLE_TO_CARDS
            + rows * CARD_HEIGHT + (rows - 1) * TEAM_GAP)


def team_section_height(floors: list) -> int:
    """演出详情区总高度"""
    height = SECTION_TITLE_HEIGHT
    for _, floor_teams in floors:
        height += floor_panel_height(floor_teams) + PANEL_GAP
    return height


async def draw_team_section(bg: PMImage, floors: list, top: int, medal_list: list = None):
    """绘制演出详情：每一幕一个带边框的区块，标题在区块顶部"""
    await bg.draw_line((40, top), (1030, top), color='orange')
    await bg.text('演出详情', 40, top + 18, fm.get('SourceHanSansCN-Bold.otf', 40), '#40342d')
    await bg.text(f'共{len(floors)}幕', 1030, top + 30, fm.get('SourceHanSansCN-Bold.otf', 26),
                  '#8b7a63', 'right')
    medal_list = medal_list or []
    medal_icon = PMImage(await load_image(medal, size=(30, 30), mode='RGBA'))
    nomedal_icon = PMImage(await load_image(nomedal, size=(30, 30), mode='RGBA'))
    y = top + SECTION_TITLE_HEIGHT
    for index, floor_teams in floors:
        panel_height = floor_panel_height(floor_teams)
        bg.draw.rounded_rectangle((PANEL_LEFT, y, PANEL_LEFT + PANEL_WIDTH, y + panel_height),
                                  radius=PANEL_RADIUS, outline=PANEL_BORDER, width=2)
        # 明星挑战星章，与上方星章一一对应
        got_medal = index < len(medal_list) and medal_list[index] == 1
        await bg.paste(medal_icon if got_medal else nomedal_icon, (40, y + PANEL_PAD + 2))
        await bg.text(f'第{index + 1}幕', 78, y + PANEL_PAD, fm.get('SourceHanSansCN-Bold.otf', FLOOR_TITLE_FONT),
                      '#40342d')
        card_y = y + PANEL_PAD + FLOOR_TITLE_HEIGHT + TITLE_TO_CARDS
        for i, members in enumerate(floor_teams):
            if i:
                card_y += TEAM_GAP
            for pos, chara in enumerate(members):
                await bg.paste(await draw_chara_card(chara), (40 + pos * (CARD_WIDTH + CARD_GAP), card_y))
            card_y += CARD_HEIGHT
        y += panel_height + PANEL_GAP


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

    # 先算出演出详情区需要的高度，让底图一次性撑到位
    team_floors = collect_team_floors(info)
    detail_height = team_section_height(team_floors) if team_floors else 0
    shortest_data = info.shortest
    has_detail = all([
        info.max_defeat_avatar,
        info.max_damage_avatar,
        info.max_take_damage_avatar,
        info.total_coin_consumed,
        shortest_data is not None
    ])
    if has_detail:
        # 上方内容绘制到 860 结束
        content_bottom = 860
    else:
        no_data = PMImage(await load_image(RESOURCE_BASE_PATH / 'general' / 'orange_bord.png'))
        await no_data.stretch((100, 200), 760, 'width')
        await no_data.stretch((100, 110), 200, 'height')
        await no_data.text('暂无挑战数据', 280, 125, fm.get('SourceHanSansCN-Bold.otf', 60), '#40342d')
        content_bottom = 520 + no_data.height
    extra = max(content_bottom + detail_height + 80 - 880, 0) if team_floors else 0

    await bg.stretch((600, bg.height - 250), 50 + extra, 'height')

    if has_detail:
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
        await bg.paste(no_data, (40, 520))

    # 演出详情：逐幕阵容
    if team_floors:
        await draw_team_section(bg, team_floors, content_bottom + 40, info.stat.medal_round_list)

    return MessageBuild.Image(bg)
