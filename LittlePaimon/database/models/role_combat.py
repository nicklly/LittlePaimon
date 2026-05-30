import datetime
from typing import Optional, List, Iterator, Union, Dict

from pydantic import BaseModel
from tortoise import fields
from tortoise.models import Model
from LittlePaimon.utils.alias import get_chara_icon, get_name_by_id

def timestamp_to_datetime(
        timestamp: Optional[Union[int, str]]
) -> Optional[datetime.datetime]:
    if timestamp is None:
        return None
    if isinstance(timestamp, str):
        timestamp = int(timestamp)
    return datetime.datetime.fromtimestamp(timestamp)

class Buffs_Info(BaseModel):
    buff_name: Optional[str] = None
    """祝福等级"""
    buff_level: Optional[int] = None
    """祝福等级"""
    buff_icon: Optional[str] = None
    """祝福图标"""

class BuffsInfos(BaseModel):
    BuffsInfos: List[Buffs_Info] = []
    """角色列表"""

    def __len__(self):
        return len(self.BuffsInfos)

    def __getitem__(self, item):
        return self.BuffsInfos[item]

    def __setitem__(self, key, value):
        self.BuffsInfos[key] = value

    def __delitem__(self, key):
        del self.BuffsInfos[key]

    def __iter__(self) -> Iterator[Buffs_Info]:
        return iter(self.BuffsInfos)

    def __reversed__(self):
        return reversed(self.BuffsInfos)

    def append(self, character: Buffs_Info):
        self.BuffsInfos.append(character)

    def pop(self, index=-1):
        self.BuffsInfos.pop(index)


class RoleCombat_Info(BaseModel):
    name: str
    """角色名称"""
    character_id: int
    """角色id"""
    rarity: Optional[int] = None
    """稀有度"""
    level: Optional[int] = None
    """等级"""
    icon: Optional[str] = None
    """角色头像"""
    element: Optional[str] = None
    """元素类型"""
    is_trial: Optional[int] = None
    """是否为试用"""

class RoleCombat_Infos(BaseModel):
    Battleinfos: List[RoleCombat_Info] = []
    """角色列表"""

    def __len__(self):
        return len(self.Battleinfos)

    def __getitem__(self, item):
        return self.Battleinfos[item]

    def __setitem__(self, key, value):
        self.Battleinfos[key] = value

    def __delitem__(self, key):
        del self.Battleinfos[key]

    def __iter__(self) -> Iterator[RoleCombat_Info]:
        return iter(self.Battleinfos)

    def __reversed__(self):
        return reversed(self.Battleinfos)

    def append(self, character: RoleCombat_Info):
        self.Battleinfos.append(character)

    def pop(self, index=-1):
        self.Battleinfos.pop(index)


class FloorInfo(BaseModel):
    index: int
    """楼层数"""
    battles_team: Optional[List[RoleCombat_Infos]]
    """出战阵容"""
    battles_buff: Optional[List[Buffs_Info]]
    """战斗buff"""

class Floors(BaseModel):
    floors: Dict[int, Optional[FloorInfo]] = {}

    def __len__(self):
        return len(self.floors)

    def __getitem__(self, item) -> Optional[FloorInfo]:
        return self.floors[item]

    def __setitem__(self, key, value):
        self.floors[key] = value

    def __delitem__(self, key):
        del self.floors[key]

    def items(self):
        return self.floors.items()

    def keys(self):
        return self.floors.keys()

    def values(self):
        return self.floors.values()

    def get(self, index, default=None):
        return self.floors.get(index, default)

class Role_Combat_Info(Model):
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    user_id: str = fields.CharField(max_length=255)  # type: ignore
    """用户id"""
    uid: str = fields.CharField(max_length=255)  # type: ignore
    """原神uid"""
    teams: Floors = fields.JSONField(encoder=Floors.json, decoder=Floors.parse_raw, default=Floors()) # type: ignore
    """出战阵容"""

    class Meta:
        table = "Role_Combat_Info"
        table_description = "原神玩家幽境危战信息表"
    @classmethod
    async def update_info(cls, user_id: str, uid: str, data: dict, abyss_index: int):
        await cls.filter(user_id=user_id, uid=uid).delete()
        info, _ = await cls.get_or_create(user_id=user_id, uid=uid)
        rounds_data = data['data'][abyss_index]['detail']['rounds_data']

        for floors in range(len(rounds_data)):
            floor_info = FloorInfo(index=floors)

            # 获取当前层的avatars列表
            avatars = rounds_data[floors]['avatars']
            buffs = rounds_data[floors]['splendour_buff']['buffs']
            floor_team = []
            floor_buff = []
            for group_start in range(0, len(avatars), 4):
                avatar_group = avatars[group_start:group_start + 4]
                # 创建这一组的角色信息
                floor_team.append(
                    RoleCombat_Infos(
                        Battleinfos=[
                            RoleCombat_Info(
                                name=character['name'],
                                character_id=character['avatar_id'],
                                level=character['level'],
                                rarity=character['rarity'],
                                element=character['element'],
                                icon=get_chara_icon(name=get_name_by_id(character['avatar_id'])),
                                is_trial=character['avatar_type']
                            )
                            for character in avatar_group
                        ]
                    )
                )

            for group_start in range(0, len(buffs), 3):
                buff_group = buffs[group_start:group_start + 3]
                # 创建这一组的buff信息
                floor_buff.append(
                    BuffsInfos(
                        BuffsInfos=[
                            Buffs_Info(
                                buff_name=buff['name'],
                                buff_icon=buff['icon'],
                                buff_level=buff['level']
                            )
                        for buff in buff_group
                        ]
                    )
                )

            floor_info.battles_team = floor_team
            floor_info.battles_buff = floor_buff
            info.teams[floors] = floor_info
        await info.save()