import hashlib
import platform
import struct
import random
import time
import uuid
from dataclasses import dataclass

from pydantic import BaseModel

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
        BuildDisplay='V417IR release-keys', BuildTime=1779448087000, Hostname='6b29a8384f29'
    ),
    DeviceVariant(
        DeviceModel='2211133C', DeviceName='Xiaomi 13', ProductName='fuxi',
        Brand='Xiaomi', Board='2211133C', Hardware='qcom', DeviceType='fuxi',
        Manufacturer='Xiaomi',
        DeviceInfo='Xiaomi/fuxi/fuxi:14/UKQ1.230804.001/18.3.21:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='UKQ1.230804.001',
        BuildDisplay='UKQ1.230804.001 release-keys', BuildTime=1700000000000, Hostname='dg02-pool03-kvm87'
    ),
    DeviceVariant(
        DeviceModel='2311BPN23C', DeviceName='Xiaomi 14 Pro', ProductName='shennong',
        Brand='Xiaomi', Board='2311BPN23C', Hardware='qcom', DeviceType='shennong',
        Manufacturer='Xiaomi',
        DeviceInfo='Xiaomi/shennong/shennong:14/UKQ1.230804.001/V816.0.14.0:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='V816.0.14.0',
        BuildDisplay='V816.0.14.0 release-keys', BuildTime=1705000000000, Hostname='cn-xiaomi-14pro'
    ),
    DeviceVariant(
        DeviceModel='2206123SC', DeviceName='Xiaomi 12S Ultra', ProductName='thor',
        Brand='Xiaomi', Board='thor', Hardware='qcom', DeviceType='thor',
        Manufacturer='Xiaomi',
        DeviceInfo='Xiaomi/thor/thor:13/TKQ1.220829.002/V14.0.3.0.TLACNXM:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='V14.0.3.0.TLACNXM',
        BuildDisplay='V14.0.3.0.TLACNXM release-keys', BuildTime=1682000000000, Hostname='cn-xiaomi-12su'
    ),
    DeviceVariant(
        DeviceModel='22127RK46C', DeviceName='Redmi K60 Ultra', ProductName='mondrian',
        Brand='Redmi', Board='22127RK46C', Hardware='qcom', DeviceType='mondrian',
        Manufacturer='Xiaomi',
        DeviceInfo='Redmi/mondrian/mondrian:13/TKQ1.220829.002/V14.0.6.0:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='V14.0.6.0',
        BuildDisplay='V14.0.6.0 release-keys', BuildTime=1682000000000, Hostname='cn-bj-xiaomi-12'
    ),
    DeviceVariant(
        DeviceModel='23113RKC6C', DeviceName='Redmi K70 Pro', ProductName='manet',
        Brand='Redmi', Board='23113RKC6C', Hardware='qcom', DeviceType='manet',
        Manufacturer='Xiaomi',
        DeviceInfo='Redmi/manet/manet:14/UKQ1.230804.001/V816.0.9.0.UNKCNXM:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='V816.0.9.0.UNKCNXM',
        BuildDisplay='V816.0.9.0.UNKCNXM release-keys', BuildTime=1703000000000, Hostname='cn-redmi-k70pro'
    ),
    DeviceVariant(
        DeviceModel='V2219A', DeviceName='vivo X90 Pro+', ProductName='PD2219',
        Brand='vivo', Board='V2219A', Hardware='qcom', DeviceType='PD2219',
        Manufacturer='vivo',
        DeviceInfo='vivo/PD2219/PD2219:13/TP1A.220624.014/PD2219_A_13.0.15.6:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='PD2219_A_13.0.15.6',
        BuildDisplay='PD2219_A_13.0.15.6 release-keys', BuildTime=1675000000000, Hostname='cn-dg-vivo-x90pp'
    ),
    DeviceVariant(
        DeviceModel='V2301A', DeviceName='iQOO 11 Pro', ProductName='PD2301',
        Brand='iQOO', Board='V2301A', Hardware='qcom', DeviceType='PD2301',
        Manufacturer='vivo',
        DeviceInfo='iQOO/PD2301/PD2301:13/TP1A.220624.014/PD2301_A_13.0.12.2:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='PD2301_A_13.0.12.2',
        BuildDisplay='PD2301_A_13.0.12.2 release-keys', BuildTime=1672000000000, Hostname='cn-dg-iqoo-11pro'
    ),
    DeviceVariant(
        DeviceModel='PGEM10', DeviceName='OPPO Find X6 Pro', ProductName='pearl',
        Brand='OPPO', Board='PGEM10', Hardware='sm8550', DeviceType='OP5949L1',
        Manufacturer='OPPO',
        DeviceInfo='OPPO/PGEM10/OP5949L1:13/TP1A.220624.014/R.1d8e2_220925:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.1d8e2_220925',
        BuildDisplay='R.1d8e2_220925 release-keys', BuildTime=1683000000000, Hostname='cn-dg-oppo-03'
    ),
    DeviceVariant(
        DeviceModel='CPH2521', DeviceName='OPPO Reno10 Pro+', ProductName='douglas',
        Brand='OPPO', Board='CPH2521', Hardware='sm7450', DeviceType='OP594DL1',
        Manufacturer='OPPO',
        DeviceInfo='OPPO/CPH2521/OP594DL1:13/TP1A.220624.014/R.21015:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.21015',
        BuildDisplay='R.21015 release-keys', BuildTime=1698000000000, Hostname='cn-dg-oppo-10'
    ),
    DeviceVariant(
        DeviceModel='PGFM10', DeviceName='OPPO Find X5 Pro', ProductName='enigma',
        Brand='OPPO', Board='PGFM10', Hardware='sm8450', DeviceType='OP5891L1',
        Manufacturer='OPPO',
        DeviceInfo='OPPO/PGFM10/OP5891L1:13/TP1A.220624.014/R.2e1f3_220502:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.2e1f3_220502',
        BuildDisplay='R.2e1f3_220502 release-keys', BuildTime=1652000000000, Hostname='cn-dg-oppo-x5p'
    ),
    DeviceVariant(
        DeviceModel='PHB110', DeviceName='OnePlus 12', ProductName='salami',
        Brand='OnePlus', Board='PHB110', Hardware='sm8550', DeviceType='OnePlusPHB110',
        Manufacturer='OnePlus',
        DeviceInfo='OnePlus/PHB110/OnePlusPHB110:13/TP1A.220905.001/R.20230401:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.20230401',
        BuildDisplay='R.20230401 release-keys', BuildTime=1681000000000, Hostname='cn-sz-oneplus-04'
    ),
    DeviceVariant(
        DeviceModel='RMX3511', DeviceName='realme C67', ProductName='rain',
        Brand='realme', Board='RMX3511', Hardware='mt6768', DeviceType='RE58BBL2',
        Manufacturer='realme',
        DeviceInfo='realme/RMX3511/RE58BBL2:13/TP1A.220624.014/R.20231215:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.20231215',
        BuildDisplay='R.20231215 release-keys', BuildTime=1702000000000, Hostname='cn-dg-realme-c67'
    ),
    DeviceVariant(
        DeviceModel='ALN-AL80', DeviceName='Huawei Mate 60 Pro', ProductName='alps',
        Brand='Huawei', Board='ALN-AL80', Hardware='kirin9000s', DeviceType='HWALN',
        Manufacturer='Huawei',
        DeviceInfo='Huawei/ALN-AL80/HWALN:12/HarmonyOS3.0/103.0.0.168:user/release-keys',
        OsVersion='12', SdkVersion='31', BuildId='103.0.0.168',
        BuildDisplay='103.0.0.168 release-keys', BuildTime=1692000000000, Hostname='cn-sz-huawei-01'
    ),ceVariant(
        DeviceModel='LIO-AL00', DeviceName='Huawei Mate 30 Pro', ProductName='lion',
        Brand='Huawei', Board='LIO-AL00', Hardware='kirin990', DeviceType='HWLIO',
        Manufacturer='Huawei',
        DeviceInfo='Huawei/LIO-AL00/HWLIO:10/HarmonyOS2.0/2.0.0.276:user/release-keys',
        OsVersion='10', SdkVersion='29', BuildId='2.0.0.276',
        BuildDisplay='2.0.0.276 release-keys', BuildTime=1612000000000, Hostname='cn-sz-huawei-m30p'
    ),
    DeviceVariant(
        DeviceModel='PGT-AN10', DeviceName='Honor Magic5 Pro', ProductName='pegasus',
        Brand='Honor', Board='PGT-AN10', Hardware='sm8550', DeviceType='HNPEGASUS',
        Manufacturer='Honor',
        DeviceInfo='Honor/PGT-AN10/HNPEGASUS:13/MagicOS7.1/7.1.0.180:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='7.1.0.180',
        BuildDisplay='7.1.0.180 release-keys', BuildTime=1685000000000, Hostname='cn-bj-honor-02'
    ),
    DeviceVariant(
        DeviceModel='REA-AN00', DeviceName='Honor 90', ProductName='rea',
        Brand='Honor', Board='REA-AN00', Hardware='sm7450', DeviceType='HNREA',
        Manufacturer='Honor',
        DeviceInfo='Honor/REA-AN00/HNREA:13/MagicOS7.1/7.1.0.156:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='7.1.0.156',
        BuildDisplay='7.1.0.156 release-keys', BuildTime=1690000000000, Hostname='cn-bj-honor-08'
    ),
    DeviceVariant(
        DeviceModel='BVL-AN00', DeviceName='Honor Magic6 Pro', ProductName='bavaria',
        Brand='Honor', Board='BVL-AN00', Hardware='sm8650', DeviceType='HNBVL',
        Manufacturer='Honor',
        DeviceInfo='Honor/BVL-AN00/HNBVL:14/MagicOS8.0/8.0.0.150:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='8.0.0.150',
        BuildDisplay='8.0.0.150 release-keys', BuildTime=1712000000000, Hostname='cn-bj-honor-magic6'
    ),
    DeviceVariant(
        DeviceModel='SM-F9460', DeviceName='Samsung Galaxy Z Fold5', ProductName='q6qkskx',
        Brand='samsung', Board='SM-F9460', Hardware='qcom', DeviceType='q6q',
        Manufacturer='samsung',
        DeviceInfo='samsung/q6qkskx/q6q:13/TP1A.220624.014/F9460ZCU1AWHA:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='F9460ZCU1AWHA',
        BuildDisplay='TP1A.220624.014 release-keys', BuildTime=1691000000000, Hostname='SEP-FOLD5'
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
        return str(uuid.uuid4())

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
        raw = f"{platform.node()}{uid}-LittlePaimon"
        md5_hash = hashlib.md5(raw.encode('utf-8')).hexdigest()
        return md5_hash[:16]
