import datetime
from typing import Optional, List, Iterator, Union

from pydantic import BaseModel
from tortoise import fields
from tortoise.models import Model
from .player_info import PlayerInfo
from LittlePaimon.utils.alias import get_chara_icon, get_name_by_id


def timestamp_to_datetime(
        timestamp: Optional[Union[int, str]]
) -> Optional[datetime.datetime]:
    if timestamp is None:
        return None
    if isinstance(timestamp, str):
        timestamp = int(timestamp)
    return datetime.datetime.fromtimestamp(timestamp)

class BattleInfo(BaseModel):
    battle_difficult: Optional[str] = None
    """总战斗时间"""
    max_battle_time: Optional[int] = None

class BattleInfos(BaseModel):
    BattleInfos: List[BattleInfo] = []
    """角色列表"""

    def __len__(self):
        return len(self.BattleInfos)

    def __getitem__(self, item):
        return self.BattleInfos[item]

    def __setitem__(self, key, value):
        self.BattleInfos[key] = value

    def __delitem__(self, key):
        del self.BattleInfos[key]

    def __iter__(self) -> Iterator[BattleInfo]:
        return iter(self.BattleInfos)

    def __reversed__(self):
        return reversed(self.BattleInfos)

    def append(self, character: BattleInfo):
        self.BattleInfos.append(character)

    def pop(self, index=-1):
        self.BattleInfos.pop(index)

class Abyss2Info(BaseModel):
    """角色名称"""
    name: str
    """角色id"""
    character_id: int
    """稀有度"""
    rarity: Optional[int] = None
    """等级"""
    level: Optional[int] = None
    """图标"""
    icon: Optional[str] = None
    """命座"""
    rank: Optional[int] = None
    """最佳角色"""
    best_avatar: Optional[List] = None
    """层间战斗信息"""
    """Boss"""
    Boss: str = None
    """战斗用时"""
    battle_time: Optional[int] = None
    """战斗难度"""

class Abyss2Infos(BaseModel):
    Abyss2Infos: List[Abyss2Info] = []
    """角色列表"""

    def __len__(self):
        return len(self.Abyss2Infos)

    def __getitem__(self, item):
        return self.Abyss2Infos[item]

    def __setitem__(self, key, value):
        self.Abyss2Infos[key] = value

    def __delitem__(self, key):
        del self.Abyss2Infos[key]

    def __iter__(self) -> Iterator[Abyss2Info]:
        return iter(self.Abyss2Infos)

    def __reversed__(self):
        return reversed(self.Abyss2Infos)

    def append(self, character: Abyss2Info):
        self.Abyss2Infos.append(character)

    def pop(self, index=-1):
        self.Abyss2Infos.pop(index)

class Hard_Challenge_Info(Model):
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    user_id: str = fields.CharField(max_length=255)  # type: ignore
    """用户id"""
    uid: str = fields.CharField(max_length=255)  # type: ignore
    """原神uid"""
    teams: Abyss2Infos = fields.JSONField(encoder=Abyss2Infos.json, decoder=Abyss2Infos.parse_raw, null=True)
    """出战阵容"""
    battle: BattleInfos = fields.JSONField(encoder=BattleInfos.json, decoder=BattleInfos.parse_raw, null=True)
    """战斗信息"""


    class Meta:
        table = "hard_challenge_info"
        table_description = "原神玩家幽境危战信息表"
    @classmethod
    async def update_info(cls, user_id: str, uid: str, data: dict, battle_type: Optional[str] = 'single'):
        await cls.filter(user_id=user_id, uid=uid).delete()
        info, _ = await cls.get_or_create(user_id=user_id, uid=uid)
        info.battle = BattleInfos(
            BattleInfos=[
                BattleInfo(
                    battle_difficult=data['data'][0][battle_type]['best']['difficulty'],
                    max_battle_time=data['data'][0][battle_type]['best']['second']
                )
            ]
        )
        info.teams = Abyss2Infos(
            Abyss2Infos=[
                Abyss2Info(
                    name=character['name'],
                    character_id=character['avatar_id'],
                    level=character['level'],
                    rarity=character['rarity'],
                    rank=character['rank'],
                    icon=get_chara_icon(name=get_name_by_id(character['avatar_id'])),
                    best_avatar=challenge['best_avatar'],
                    Boss=challenge['name'],
                    battle_time=challenge['second']
                )
                for challenge in data['data'][0][battle_type]['challenge']
                for character in challenge['teams']
            ]
        )
        await info.save()
