import hashlib
import platform
import struct
import random
import time
import uuid
from dataclasses import dataclass
from typing import Tuple

from pydantic import BaseModel


# -------------------- 设备变体定义（与 C# 记录字段顺序一致）--------------------
@dataclass(frozen=True)
class DeviceVariant:
    DeviceModel: str      # 设备型号：如 '24031PN0DC'
    ProductName: str      # 产品代号，如 'aurora'
    Brand: str            # 品牌
    Board: str            # 主板型号
    Hardware: str         # 硬件平台
    DeviceName: str       # 设备名，如：小米13 pro
    DeviceType: str       # 设备类型/设备名
    Manufacturer: str     # 制造商
    DeviceInfo: str       # 构建指纹 (fingerprint)
    OsVersion: str        # 系统版本
    SdkVersion: str       # SDK 版本
    BuildId: str          # 增量版本
    BuildDisplay: str     # 构建描述
    BuildTime: int        # 构建时间戳（毫秒）
    Hostname: str         # 构建主机名

DEVICE_VARIANTS = [
    DeviceVariant(
        DeviceModel='24031PN0DC', DeviceName='Xiaomi 14', ProductName='aurora',
        Brand='Xiaomi', Board='24031PN0DC', Hardware='Xiaomi', DeviceType='aurora',
        Manufacturer='Xiaomi',
        DeviceInfo='Xiaomi/aurora/aurora:12/V417IR/1747:user/release-keys',
        OsVersion='12', SdkVersion='32', BuildId='V417IR',
        BuildDisplay='V417IR release-keys', BuildTime=1779448087000,
        Hostname='6b29a8384f29'
    ),
    DeviceVariant(
        DeviceModel='23127PN0CC', DeviceName='Xiaomi 13 Ultra', ProductName='shennong',
        Brand='Xiaomi', Board='23127PN0CC', Hardware='qcom', DeviceType='shennong',
        Manufacturer='Xiaomi',
        DeviceInfo='Xiaomi/shennong/shennong:15/AP3A.240805.005/18.6.10:user/release-keys',
        OsVersion='15', SdkVersion='35', BuildId='AP3A.240805.005',
        BuildDisplay='AP3A.240805.005 release-keys', BuildTime=1720000000000,
        Hostname='6b29a8384f29'
    ),
    DeviceVariant(
        DeviceModel='2211133C', DeviceName='Xiaomi 13', ProductName='fuxi',
        Brand='Xiaomi', Board='2211133C', Hardware='qcom', DeviceType='fuxi',
        Manufacturer='Xiaomi',
        DeviceInfo='Xiaomi/fuxi/fuxi:14/UKQ1.230804.001/18.3.21:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='UKQ1.230804.001',
        BuildDisplay='UKQ1.230804.001 release-keys', BuildTime=1700000000000,
        Hostname='dg02-pool03-kvm87'
    ),
    DeviceVariant(
        DeviceModel='2304FPN6DC', DeviceName='Xiaomi 13T Pro', ProductName='ishtar',
        Brand='Xiaomi', Board='2304FPN6DC', Hardware='qcom', DeviceType='ishtar',
        Manufacturer='Xiaomi',
        DeviceInfo='Xiaomi/ishtar/ishtar:13/TKQ1.220829.002/V14.0.8.0:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='V14.0.8.0',
        BuildDisplay='V14.0.8.0 release-keys', BuildTime=1685000000000,
        Hostname='cn-bj-xiaomi-11'
    ),
    DeviceVariant(
        DeviceModel='22127RK46C', DeviceName='Redmi K60 Ultra', ProductName='mondrian',
        Brand='Redmi', Board='22127RK46C', Hardware='qcom', DeviceType='mondrian',
        Manufacturer='Xiaomi',
        DeviceInfo='Redmi/mondrian/mondrian:13/TKQ1.220829.002/V14.0.6.0:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='V14.0.6.0',
        BuildDisplay='V14.0.6.0 release-keys', BuildTime=1682000000000,
        Hostname='cn-bj-xiaomi-12'
    ),
    DeviceVariant(
        DeviceModel='V2366GA', DeviceName='vivo X100 Pro', ProductName='PD2366',
        Brand='vivo', Board='V2366GA', Hardware='vivo', DeviceType='PD2366',
        Manufacturer='vivo',
        DeviceInfo='vivo/PD2366/PD2366:12/V417IR/1747:user/release-keys',
        OsVersion='12', SdkVersion='32', BuildId='V417IR',
        BuildDisplay='V417IR release-keys', BuildTime=1779448087000,
        Hostname='6b29a8384f29'
    ),
    DeviceVariant(
        DeviceModel='V2309A', DeviceName='vivo X90s', ProductName='vivoX100Pro',
        Brand='vivo', Board='V2309A', Hardware='mt6989', DeviceType='PD2309',
        Manufacturer='vivo',
        DeviceInfo='vivo/V2309A/PD2309:14/UP1A.231005.007/compiler1205:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='compiler1205',
        BuildDisplay='compiler1205 release-keys', BuildTime=1703000000000,
        Hostname='cn-dg-vivo-09'
    ),
    DeviceVariant(
        DeviceModel='PGEM10', DeviceName='OPPO Find X6 Pro', ProductName='pearl',
        Brand='OPPO', Board='PGEM10', Hardware='sm8550', DeviceType='OP5949L1',
        Manufacturer='OPPO',
        DeviceInfo='OPPO/PGEM10/OP5949L1:13/TP1A.220624.014/R.1d8e2_220925:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.1d8e2_220925',
        BuildDisplay='R.1d8e2_220925 release-keys', BuildTime=1683000000000,
        Hostname='cn-dg-oppo-03'
    ),
    DeviceVariant(
        DeviceModel='CPH2521', DeviceName='OPPO Reno10 Pro+', ProductName='douglas',
        Brand='OPPO', Board='CPH2521', Hardware='sm7450', DeviceType='OP594DL1',
        Manufacturer='OPPO',
        DeviceInfo='OPPO/CPH2521/OP594DL1:13/TP1A.220624.014/R.21015:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.21015',
        BuildDisplay='R.21015 release-keys', BuildTime=1698000000000,
        Hostname='cn-dg-oppo-10'
    ),
    DeviceVariant(
        DeviceModel='PHB110', DeviceName='OnePlus 12', ProductName='salami',
        Brand='OnePlus', Board='PHB110', Hardware='sm8550', DeviceType='OnePlusPHB110',
        Manufacturer='OnePlus',
        DeviceInfo='OnePlus/PHB110/OnePlusPHB110:13/TP1A.220905.001/R.20230401:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.20230401',
        BuildDisplay='R.20230401 release-keys', BuildTime=1681000000000,
        Hostname='cn-sz-oneplus-04'
    ),
    DeviceVariant(
        DeviceModel='RMX3888', DeviceName='realme GT5 Pro', ProductName='titan',
        Brand='realme', Board='RMX3888', Hardware='sm8550', DeviceType='RE58BAL1',
        Manufacturer='realme',
        DeviceInfo='realme/RMX3888/RE58BAL1:14/UKQ1.230804.001/R.20240115:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='R.20240115',
        BuildDisplay='R.20240115 release-keys', BuildTime=1705000000000,
        Hostname='cn-dg-realme-05'
    ),
    DeviceVariant(
        DeviceModel='ALN-AL80', DeviceName='Huawei Mate 60 Pro', ProductName='alps',
        Brand='Huawei', Board='ALN-AL80', Hardware='kirin9000s', DeviceType='HWALN',
        Manufacturer='Huawei',
        DeviceInfo='Huawei/ALN-AL80/HWALN:12/HarmonyOS3.0/103.0.0.168:user/release-keys',
        OsVersion='12', SdkVersion='31', BuildId='103.0.0.168',
        BuildDisplay='103.0.0.168 release-keys', BuildTime=1692000000000,
        Hostname='cn-sz-huawei-01'
    ),
    DeviceVariant(
        DeviceModel='MNA-AL00', DeviceName='Huawei P60', ProductName='mona',
        Brand='Huawei', Board='MNA-AL00', Hardware='sm8475', DeviceType='HWMNA',
        Manufacturer='Huawei',
        DeviceInfo='Huawei/MNA-AL00/HWMNA:13/HarmonyOS4.0/4.0.0.120:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='4.0.0.120',
        BuildDisplay='4.0.0.120 release-keys', BuildTime=1702000000000,
        Hostname='cn-sz-huawei-07'
    ),
    DeviceVariant(
        DeviceModel='PGT-AN10', DeviceName='Honor Magic5 Pro', ProductName='pegasus',
        Brand='Honor', Board='PGT-AN10', Hardware='sm8550', DeviceType='HNPEGASUS',
        Manufacturer='Honor',
        DeviceInfo='Honor/PGT-AN10/HNPEGASUS:13/MagicOS7.1/7.1.0.180:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='7.1.0.180',
        BuildDisplay='7.1.0.180 release-keys', BuildTime=1685000000000,
        Hostname='cn-bj-honor-02'
    ),
    DeviceVariant(
        DeviceModel='REA-AN00', DeviceName='Honor 90', ProductName='rea',
        Brand='Honor', Board='REA-AN00', Hardware='sm7450', DeviceType='HNREA',
        Manufacturer='Honor',
        DeviceInfo='Honor/REA-AN00/HNREA:13/MagicOS7.1/7.1.0.156:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='7.1.0.156',
        BuildDisplay='7.1.0.156 release-keys', BuildTime=1690000000000,
        Hostname='cn-bj-honor-08'
    ),
    DeviceVariant(
        DeviceModel='M391Q', DeviceName='Meizu 20 Pro', ProductName='meizu20pro',
        Brand='Meizu', Board='M391Q', Hardware='sm8550', DeviceType='meizu_M391Q',
        Manufacturer='Meizu',
        DeviceInfo='Meizu/M391Q/meizu_M391Q:13/TP1A.220624.014/Flyme10.0.0.0:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='Flyme10.0.0.0',
        BuildDisplay='Flyme10.0.0.0 release-keys', BuildTime=1679000000000,
        Hostname='cn-zh-meizu-06'
    ),
    DeviceVariant(
        DeviceModel='SM-S9080', DeviceName='Samsung Galaxy S22 Ultra', ProductName='b0s',
        Brand='samsung', Board='SM-S9080', Hardware='qcom', DeviceType='b0s',
        Manufacturer='samsung',
        DeviceInfo='samsung/b0s/b0s:12/SP1A.210812.016/S9080ZHU2AVE4:user/release-keys',
        OsVersion='12', SdkVersion='31', BuildId='S9080ZHU2AVE4',
        BuildDisplay='SP1A.210812.016 release-keys', BuildTime=1654000000000,
        Hostname='SEP-72'
    ),
    DeviceVariant(
        DeviceModel='CPH2449', DeviceName='OnePlus Nord 3', ProductName='larry',
        Brand='OnePlus', Board='CPH2449', Hardware='mt6895', DeviceType='OP5B78L1',
        Manufacturer='OnePlus',
        DeviceInfo='OnePlus/CPH2449/OP5B78L1:13/TP1A.220905.001/R.120:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.120',
        BuildDisplay='R.120 release-keys', BuildTime=1689000000000,
        Hostname='cn-sz-oneplus-13'
    ),
]

class DeviceProvider(BaseModel):


    def get_stable_hash_code(self, s: str) -> int:
        md5_bytes = hashlib.md5(s.encode('utf-8')).digest()
        return struct.unpack('<i', md5_bytes[:4])[0]

    def select_variant(self, account_id: str) -> DeviceVariant:
        """根据账号 ID 稳定选择设备"""
        hash_code = self.get_stable_hash_code(account_id)
        idx = (hash_code & 0x7FFFFFFF) % len(DEVICE_VARIANTS)
        return DEVICE_VARIANTS[idx]

    def build_ext_fields(self, v: DeviceVariant) -> dict:
        """
        根据设备变体生成完整请求字段，与 C# 的 BuildExtFields 完全一致。
        """
        # 按小时变化的随机种子
        session_seed = int(time.time() / 3600)
        rng = random.Random(session_seed & 0x7FFFFFFF)

        # 动态随机值
        battery = rng.randint(70, 99)          # Next(70, 100)
        ram_remain = rng.randint(120000, 129999)
        sd_remain = rng.randint(110000, 129999)

        # 加速度计 (保留8位小数)
        acc_x = 0.1 + rng.random() * 0.05
        acc_y = 9.78 + rng.random() * 0.04
        acc_z = 0.15 + rng.random() * 0.1
        accelerometer = f'{acc_x:.8f}x{acc_y:.8f}x{acc_z:.8f}'

        # 磁力计 (保留3位小数)
        mag_x = 15 + rng.random() * 2
        mag_y = -28 + rng.random() * -1
        mag_z = -32 + rng.random() * -1
        magnetometer = f'{mag_x:.3f}x{mag_y:.3f}x{mag_z:.3f}'

        gyroscope = '0.0x0.0x0.0'

        # 时间差
        current_ms = int(time.time() * 1000)
        time_diff = current_ms - 1782425023662

        rom_remain = rng.randint(400, 599)
        sd_capacity = rng.randint(127000, 128999)
        ram_capacity = ram_remain + rng.randint(500, 1499)

        # 按照 C# 字典键精准填充，属性名与 record 一致
        return {
            'proxyStatus': 1, 'isRoot': 0, 'romCapacity': '512', 'deviceName': v.DeviceModel,
            'productName': v.ProductName, 'romRemain': str(rom_remain), 'hostname': v.Hostname,
            'screenSize': '1080x1920', 'isTablet': 1, 'aaid': 'error_1008008',
            'model': v.DeviceModel, 'brand': v.Brand, 'hardware': v.Hardware,
            'deviceType': v.DeviceType, 'devId': 'REL', 'sdCapacity': sd_capacity,
            'buildTime': str(v.BuildTime), 'buildUser': 'abc', 'simState': 5,
            'ramRemain': str(ram_remain), 'appUpdateTimeDiff': time_diff, 'deviceInfo': v.DeviceInfo,
            'vaid': 'error_1008008', 'buildType': 'user', 'sdkVersion': v.SdkVersion,
            'ui_mode': 'UI_MODE_TYPE_NORMAL', 'isMockLocation': 0, 'cpuType': 'arm64-v8a',
            'isAirMode': 0, 'ringMode': 2, 'chargeStatus': 1,
            'manufacturer': v.Manufacturer, 'emulatorStatus': 0, 'appMemory': '512',
            'osVersion': v.OsVersion, 'vendor': 'unknown', 'accelerometer': accelerometer,
            'sdRemain': sd_remain, 'buildTags': 'release-keys', 'packageName': 'com.mihoyo.hyperion',
            'networkType': 'WiFi', 'oaid': 'error_1008008', 'debugStatus': 0,
            'ramCapacity': str(ram_capacity), 'magnetometer': magnetometer, 'display': v.BuildDisplay,
            'appInstallTimeDiff': time_diff, 'packageVersion': '2.42.0', 'gyroscope': gyroscope,
            'batteryStatus': battery, 'hasKeyboard': 1, 'board': v.Board,
    }

    def device_id(self) -> str:
        return uuid.uuid4()

    def device_seed(self):
        new_id = str(uuid.uuid4())
        new_time = str(int(time.time() * 1000))

        return new_id, new_time

    def generate_default_device_id(self) -> str:
        """
        生成 10 位数字字符串：首位 1-9，其余 9 位 0-9。
        """
        first = str(random.randint(1, 9))
        others = ''.join(str(random.randint(0, 9)) for _ in range(9))
        return first + others

    def generate_error_device_id(self) -> str:
        """
        生成 10 位数字字符串：首位 1-9，其余 9 位 0-9。
        """
        first = str(random.randint(1, 9))
        others = ''.join(str(random.randint(0, 10)) for _ in range(9))
        return first + others

    def get_device_id_for_account(self, uid: str) -> str:
        machine_name = platform.node()
        raw = f"{machine_name}{uid}LittlePaimon"
        md5_hash = hashlib.md5(raw.encode('utf-8')).hexdigest()
        return md5_hash[:16]
