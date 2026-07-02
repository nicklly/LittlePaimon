from tortoise import fields
from tortoise.models import Model


class Devices(Model):
    """
    用户设备信息
    """
    id = fields.IntField(pk=True, generated=True, auto_increment=True)
    """自增主键"""
    user_id: str = fields.TextField()
    """用户id"""
    uid: str = fields.TextField()
    """原神uid"""
    device_id: str = fields.TextField()
    """设备ID"""
    device_name: str = fields.TextField()
    """设备名字"""
    device_model: str = fields.TextField()
    """设备型号"""
    device_fp: str = fields.TextField()
    """设备fingerprint"""

    class Meta:
        table = 'user_devices'
        table_description = '用户设备信息'

