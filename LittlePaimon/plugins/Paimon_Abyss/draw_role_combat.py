from typing import  List

from LittlePaimon.database import RoleCombat_Info, Buffs_Info, Role_Combat_Info
from LittlePaimon.utils.alias import get_chara_icon, get_name_by_id
from LittlePaimon.utils.image import PMImage
from LittlePaimon.utils.image import font_manager as fm
from LittlePaimon.utils.image import load_image
from LittlePaimon.utils.message import MessageBuild
from LittlePaimon.utils.path import RESOURCE_BASE_PATH

async def draw_character_card(bg, chara, x, y, card_width, card_height, RESOURCE_BASE_PATH, fm, element_type):
    """绘制单个角色卡片"""

    try:
        # 1. 创建卡片背景（根据星级使用不同背景）
        rarity_box_path = RESOURCE_BASE_PATH / 'icon' / f"{chara.rarity}starbox.png"
        avatar_bg = PMImage(await load_image(rarity_box_path), mode='RGBA')
        await avatar_bg.resize((card_width, card_height))

        # 2. 绘制角色头像
        if chara.icon:
            avatar_path = RESOURCE_BASE_PATH / 'avatar' / f"{chara.icon}.png"
            avatar = PMImage(await load_image(avatar_path), mode='RGBA')
            await avatar.resize((130, 135))
            await avatar_bg.paste(avatar, (5, 5))

            # 3. 绘制元素图标
            element_path = RESOURCE_BASE_PATH / 'icon' / f"{element_type.get(chara.element, 'UI_Element_None')}.png"
            element_icon = PMImage(await load_image(element_path), mode='RGBA')
            await element_icon.resize((30, 30))
            await avatar_bg.paste(element_icon, (108, 5))

            # 4. 绘制试玩标识
            if chara.is_trial == 2:
                trial_font = fm.get('汉仪雅酷黑.ttf', 18)
                await avatar_bg.text('【试用】', 2, 8, trial_font, '#00AA00')

            # 5. 绘制角色等级
            level_font = fm.get('SourceHanSansCN-Bold.otf', 24)
            level_text = f"Lv.{chara.level}"
            # 计算文字宽度（粗略估计）
            text_width = len(level_text) * 15
            level_x = (card_width - text_width) // 2
            await avatar_bg.text(level_text, level_x, 145, level_font, 'black')

        # 7. 将完成的卡片粘贴到背景
        await bg.paste(avatar_bg, (x, y))

    except Exception as e:
        print(f"绘制角色 {chara.name} 时出错: {e}")
        # 绘制一个错误占位符
        error_bg = PMImage.new('RGBA', (card_width, card_height), (100, 100, 100, 255))
        error_font = fm.get('汉仪雅酷黑.ttf', 12)
        await error_bg.text(chara.name, 10, card_height//2, error_font, '#FF0000')
        await bg.paste(error_bg, (x, y))

async def draw_role_combat_card(info: Role_Combat_Info):
    element_type = {
        "Pyro": "火",
        "Cryo": "冰",
        "Geo": "岩",
        "Dendro": "草",
        "Hydro": "水",
        "Electro": "雷",
        "Anemo": "风"
    }
    # 配置参数
    card_width = 145
    card_height = 175
    start_x = 40
    start_y = 500
    horizontal_gap = 20   # 角色卡片之间的水平间距
    vertical_gap  = 60    # 层之间的垂直间距

    if not info:
        return '暂无深渊挑战数据，请稍候再试'

    round_data = info.teams
    # 加载图片素材
    bg = PMImage(
        await load_image(RESOURCE_BASE_PATH / 'hard_challenge' / 'bg.png', mode='RGBA')
    )
    # 计算每层占用的高度
    floor_height = card_height + vertical_gap

    # 获取总层数
    total_floors = len(round_data.floors)
    print(f"总层数: {total_floors}")
    # 计算实际需要的高度
    required_height = start_y + total_floors * floor_height + 1350 # 额外1350px底部留白

    # 获取背景图当前高度
    current_height = bg.height

    if required_height <= current_height:
        return bg

    stretch_height = required_height - current_height
    # 确定拉伸区域（中间部分）
    stretch_start = 200
    stretch_end = current_height - 100

    if stretch_end <= stretch_start:
        # 如果保留区域重叠，只拉伸底部
        stretch_start = current_height - 100
        stretch_end = current_height

    try:
        await bg.stretch(
            pos=(stretch_start, stretch_end),
            length=stretch_height,
            type='height'
        )
        print(f"Y轴拉伸成功，新高度: {bg.height}")
    except Exception as e:
        print(f"Y轴拉伸失败: {e}")
        # 备用方案：创建新背景
        new_bg = PMImage.new('RGBA', (bg.width, required_height), (0, 0, 0, 255))
        await new_bg.paste(bg, (0, 0))
        bg = new_bg
        print("已创建新背景作为替代")
    # 标题文字
    await bg.text('幻想真境剧诗', 36, 29, fm.get('优设标题黑', 108), '#40342d')
    # UID和昵称
    await bg.text(f'UID{info.uid}', 1040, 114, fm.get('bahnschrift_bold', 36), '#252525', 'right')
    orange_line = await load_image(RESOURCE_BASE_PATH / 'general' / 'line.png')
    await bg.paste(orange_line, (40, 164))

    # 计算每个角色的X坐标偏移（4个角色等间距排列）
    card_positions = []
    for i in range(4):
        x = start_x + i * (card_width + horizontal_gap)
        card_positions.append(x)
    for floor_idx, (floor_key, floor_data) in enumerate(round_data.floors.items()):
        # 计算当前层的Y坐标
        current_y = start_y + floor_idx * (card_height + vertical_gap)
        # 绘制层标题
        try:
            title_font = fm.get('汉仪雅酷黑.ttf', 28)
            await bg.text(f"第{floor_idx + 1}幕", start_x, current_y + card_height // 2, title_font, 'black')
        except:
            pass
        # 获取该层的队伍数据
        if floor_data.battles_team:
            team_data = floor_data.battles_team[0]
            characters = team_data.Battleinfos
            for chara_idx, chara in enumerate(characters):
                if chara_idx >= 4:  # 最多只显示4个角色
                    break
                x_pos = card_positions[chara_idx]
                await draw_character_card(
                    bg, chara, x_pos, current_y,
                    card_width, card_height,
                    RESOURCE_BASE_PATH, fm, element_type
                )
        else:
            print(f"警告: 第{floor_idx}层没有队伍数据")
    return MessageBuild.Image(bg)