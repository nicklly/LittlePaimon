from typing import Dict
from .card import CARD_API

API: Dict[str, str] = {
    '角色图鉴': '{proxy}https://raw.githubusercontent.com/CMHopeSunshine/GenshinWikiMap/master/results/character_map/{name}.jpg',
    '角色攻略': '{proxy}https://raw.githubusercontent.com/CMHopeSunshine/LittlePaimonRes/main/genshin_guide/guide/{name}.jpg',
    '角色材料': '{proxy}https://raw.githubusercontent.com/Nwflower/genshin-atlas/master/material%20for%20role/{name}.png',
    '收益曲线': 'https://static.cherishmoon.fun/LittlePaimon/blue/{name}.jpg',
    '参考面板': '{proxy}https://raw.githubusercontent.com/CMHopeSunshine/LittlePaimonRes/main/genshin_guide/panel/{name}.jpg',
    '武器图鉴': '{proxy}https://raw.githubusercontent.com/Nwflower/genshin-atlas/master/weapon/{name}.png',
    '圣遗物图鉴': '{proxy}https://raw.githubusercontent.com/Nwflower/genshin-atlas/master/artifact/{name}.png',
    '原魔图鉴': 'https://static.cherishmoon.fun/LittlePaimon/MonsterMaps/{name}.jpg',
    '七圣召唤图鉴': CARD_API
}