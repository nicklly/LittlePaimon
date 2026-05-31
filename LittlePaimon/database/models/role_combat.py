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

class Concert_info(BaseModel):
    difficulty_id: Optional[int] = None
    """挑战难度"""
    max_round_id: Optional[int] = None
    """最高幕数"""
    medal_round_list: Optional[List] = None
    """明星挑战星章"""
    coin_num: Optional[int] = None
    """消耗幻剧之花"""
    avatar_bonus_num: Optional[int] = None
    """场外声援"""
    tarot_finished_cnt: Optional[int] = None
    """助演支援"""
    total_use_time: Optional[int] = None
    """演出时长"""

class Concert_infos(BaseModel):
    Concert_infos: List[Concert_info] = []
    """角色列表"""

    def __len__(self):
        return len(self.Concert_infos)

    def __getitem__(self, item):
        return self.Concert_infos[item]

    def __setitem__(self, key, value):
        self.Concert_infos[key] = value

    def __delitem__(self, key):
        del self.Concert_infos[key]

    def __iter__(self) -> Iterator[Concert_info]:
        return iter(self.Concert_infos)

    def __reversed__(self):
        return reversed(self.Concert_infos)

    def append(self, character: Concert_info):
        self.Concert_infos.append(character)

    def pop(self, index=-1):
        self.Concert_infos.pop(index)

class RoleCombat_Character(BaseModel):
    avatar_id: Optional[int]
    """角色ID"""
    value: Optional[int]
    """伤害数值"""
    rarity: Optional[int]
    """角色稀有度"""

class Charas(BaseModel):
    Characters: List[RoleCombat_Character] = []
    """角色列表"""

    def __len__(self):
        return len(self.Characters)

    def __getitem__(self, item):
        return self.Characters[item]

    def __setitem__(self, key, value):
        self.Characters[key] = value

    def __delitem__(self, key):
        del self.Characters[key]

    def __iter__(self) -> Iterator[RoleCombat_Character]:
        return iter(self.Characters)

    def __reversed__(self):
        return reversed(self.Characters)

    def append(self, character: RoleCombat_Character):
        self.Characters.append(character)

    def pop(self, index=-1):
        self.Characters.pop(index)

class Role_Combat_Info(Model):
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    user_id: str = fields.CharField(max_length=255)  # type: ignore
    """用户id"""
    uid: str = fields.CharField(max_length=255)  # type: ignore
    """原神uid"""
    teams: Floors = fields.JSONField(encoder=Floors.json, decoder=Floors.parse_raw, default=Floors()) # type: ignore
    """出战阵容"""
    stat: Concert_info = fields.JSONField(encoder=Concert_info.json, decoder=Concert_info.parse_raw, null=True) # type: ignore
    """数据简报"""
    max_defeat_avatar: RoleCombat_Character = fields.JSONField(encoder=RoleCombat_Character.json, decoder=RoleCombat_Character.parse_raw, null=True)# type: ignore
    """最高伤害输出"""
    max_damage_avatar: RoleCombat_Character = fields.JSONField(encoder=RoleCombat_Character.json, decoder=RoleCombat_Character.parse_raw, null=True)# type: ignore
    """击败最多"""
    max_take_damage_avatar: RoleCombat_Character = fields.JSONField(encoder=RoleCombat_Character.json, decoder=RoleCombat_Character.parse_raw, null=True)# type: ignore
    """最高承伤"""
    total_coin_consumed: RoleCombat_Character = fields.JSONField(encoder=RoleCombat_Character.json, decoder=RoleCombat_Character.parse_raw, null=True)# type: ignore
    """本次消耗最多"""
    shortest: Charas = fields.JSONField(encoder=Charas.json, decoder=Charas.parse_raw, null=True)# type: ignore
    """最快完成队伍"""

    class Meta:
        table = "Role_Combat_Info"
        table_description = "原神玩家幽境危战信息表"
    @classmethod
    async def update_info(cls, user_id: str, uid: str, data: dict, abyss_index: int):
        await cls.filter(user_id=user_id, uid=uid).delete()
        info, _ = await cls.get_or_create(user_id=user_id, uid=uid)
        rounds_data = data['data'][abyss_index]['detail']['rounds_data']
        stat_data = data['data'][abyss_index]['stat']
        flight_data = data['data'][abyss_index]['detail']['fight_statisic']
        shortest_data  = flight_data['shortest_avatar_list']

        info.use_time = Concert_info(
        )
        if flight_data['max_defeat_avatar'] is not None:
           info.max_defeat_avatar = RoleCombat_Character(
                avatar_id = flight_data['max_defeat_avatar']['avatar_id'],
                value = flight_data['max_defeat_avatar']['value'],
                rarity = flight_data['max_defeat_avatar']['rarity']
            )
        if flight_data['max_damage_avatar'] is not None:
            info.max_damage_avatar = RoleCombat_Character(
                avatar_id = flight_data['max_damage_avatar']['avatar_id'],
                value = flight_data['max_damage_avatar']['value'],
                rarity = flight_data['max_damage_avatar']['rarity']
            )
        if flight_data['max_take_damage_avatar'] is not None:
            info.max_take_damage_avatar = RoleCombat_Character(
                avatar_id = flight_data['max_take_damage_avatar'] ['avatar_id'],
                value = flight_data['max_take_damage_avatar'] ['value'],
                rarity = flight_data['max_take_damage_avatar'] ['rarity']
            )
        if flight_data['total_coin_consumed'] is not None:
            info.total_coin_consumed = RoleCombat_Character(
                value = flight_data['total_coin_consumed']['value']
            )
        if flight_data['shortest_avatar_list']:
            team_members = []
            for i in range(len(shortest_data)):
                team_members.append(
                    RoleCombat_Character(
                        avatar_id = shortest_data[i]['avatar_id'],
                        value = 0,
                        rarity = shortest_data[i]['rarity']
                    )
                )
            info.shortest = Charas(Characters=team_members)

        info.stat =  Concert_info(
                    difficulty_id = stat_data['difficulty_id'],
                    max_round_id = stat_data['max_round_id'],
                    medal_round_list = stat_data['get_medal_round_list'],
                    coin_num = stat_data['coin_num'],
                    avatar_bonus_num = stat_data['avatar_bonus_num'],
                    tarot_finished_cnt = stat_data['tarot_finished_cnt'],
                    total_use_time = flight_data['total_use_time']
                )

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