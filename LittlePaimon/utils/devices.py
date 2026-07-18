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
        DeviceModel='23127PN0CC', DeviceName='Xiaomi 13 Ultra', ProductName='shennong',
        Brand='Xiaomi', Board='23127PN0CC', Hardware='qcom', DeviceType='shennong',
        Manufacturer='Xiaomi',
        DeviceInfo='Xiaomi/shennong/shennong:15/AP3A.240805.005/18.6.10:user/release-keys',
        OsVersion='15', SdkVersion='35', BuildId='AP3A.240805.005',
        BuildDisplay='AP3A.240805.005 release-keys', BuildTime=1720000000000, Hostname='6b29a8384f29'
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
        DeviceModel='2304FPN6DC', DeviceName='Xiaomi 13T Pro', ProductName='ishtar',
        Brand='Xiaomi', Board='2304FPN6DC', Hardware='qcom', DeviceType='ishtar',
        Manufacturer='Xiaomi',
        DeviceInfo='Xiaomi/ishtar/ishtar:13/TKQ1.220829.002/V14.0.8.0:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='V14.0.8.0',
        BuildDisplay='V14.0.8.0 release-keys', BuildTime=1685000000000, Hostname='cn-bj-xiaomi-11'
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
        DeviceModel='23090RA98C', DeviceName='Redmi Note 13 Pro+', ProductName='garnet',
        Brand='Redmi', Board='23090RA98C', Hardware='mt6895', DeviceType='garnet',
        Manufacturer='Xiaomi',
        DeviceInfo='Redmi/garnet/garnet:13/TP1A.220624.014/V14.0.12.0.TMRCNXM:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='V14.0.12.0.TMRCNXM',
        BuildDisplay='V14.0.12.0.TMRCNXM release-keys', BuildTime=1693000000000, Hostname='cn-xiaomi-redmi13'
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
        DeviceModel='23054RA19C', DeviceName='Redmi Note 12 Turbo', ProductName='marble',
        Brand='Redmi', Board='marble', Hardware='qcom', DeviceType='marble',
        Manufacturer='Xiaomi',
        DeviceInfo='Redmi/marble/marble:13/TP1A.220624.014/V14.0.22.0.TMRCNXM:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='V14.0.22.0.TMRCNXM',
        BuildDisplay='V14.0.22.0.TMRCNXM release-keys', BuildTime=1686000000000, Hostname='cn-redmi-note12t'
    ),
    DeviceVariant(
        DeviceModel='23124RN87G', DeviceName='Redmi 13C', ProductName='gale',
        Brand='Redmi', Board='gale', Hardware='mt6769', DeviceType='gale',
        Manufacturer='Xiaomi',
        DeviceInfo='Redmi/gale/gale:13/TP1A.220624.014/V14.0.8.0.TGCMIXM:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='V14.0.8.0.TGCMIXM',
        BuildDisplay='V14.0.8.0.TGCMIXM release-keys', BuildTime=1701000000000, Hostname='cn-redmi-13c'
    ),
    DeviceVariant(
        DeviceModel='23078RB5BC', DeviceName='Redmi K60', ProductName='mondrian',
        Brand='Redmi', Board='mondrian', Hardware='qcom', DeviceType='mondrian',
        Manufacturer='Xiaomi',
        DeviceInfo='Redmi/mondrian/mondrian:13/TKQ1.220829.002/V14.0.23.0.TMNCNXM:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='V14.0.23.0.TMNCNXM',
        BuildDisplay='V14.0.23.0.TMNCNXM release-keys', BuildTime=1678000000000, Hostname='cn-redmi-k60'
    ),
    DeviceVariant(
        DeviceModel='V2366GA', DeviceName='vivo X100 Pro', ProductName='PD2366',
        Brand='vivo', Board='V2366GA', Hardware='vivo', DeviceType='PD2366',
        Manufacturer='vivo',
        DeviceInfo='vivo/PD2366/PD2366:12/V417IR/1747:user/release-keys',
        OsVersion='12', SdkVersion='32', BuildId='V417IR',
        BuildDisplay='V417IR release-keys', BuildTime=1779448087000, Hostname='6b29a8384f29'
    ),
    DeviceVariant(
        DeviceModel='V2309A', DeviceName='vivo X90s', ProductName='vivoX100Pro',
        Brand='vivo', Board='V2309A', Hardware='mt6989', DeviceType='PD2309',
        Manufacturer='vivo',
        DeviceInfo='vivo/V2309A/PD2309:14/UP1A.231005.007/compiler1205:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='compiler1205',
        BuildDisplay='compiler1205 release-keys', BuildTime=1703000000000, Hostname='cn-dg-vivo-09'
    ),
    DeviceVariant(
        DeviceModel='V2324A', DeviceName='vivo X100', ProductName='PD2324',
        Brand='vivo', Board='V2324A', Hardware='mt6989', DeviceType='PD2324',
        Manufacturer='vivo',
        DeviceInfo='vivo/PD2324/PD2324:14/UP1A.231005.007/PD2324_A_14.1.6.3:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='PD2324_A_14.1.6.3',
        BuildDisplay='PD2324_A_14.1.6.3 release-keys', BuildTime=1707000000000, Hostname='cn-dg-vivo-x100'
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
        DeviceModel='V2338A', DeviceName='vivo S18 Pro', ProductName='PD2338',
        Brand='vivo', Board='V2338A', Hardware='mt6989', DeviceType='PD2338',
        Manufacturer='vivo',
        DeviceInfo='vivo/PD2338/PD2338:14/UP1A.231005.007/PD2338_A_14.0.10.2:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='PD2338_A_14.0.10.2',
        BuildDisplay='PD2338_A_14.0.10.2 release-keys', BuildTime=1709000000000, Hostname='cn-dg-vivo-s18'
    ),
    DeviceVariant(
        DeviceModel='V2166A', DeviceName='vivo X80 Pro', ProductName='PD2166',
        Brand='vivo', Board='V2166A', Hardware='qcom', DeviceType='PD2166',
        Manufacturer='vivo',
        DeviceInfo='vivo/PD2166/PD2166:12/SP1A.210812.016/PD2166_A_12.0.20.5:user/release-keys',
        OsVersion='12', SdkVersion='31', BuildId='PD2166_A_12.0.20.5',
        BuildDisplay='PD2166_A_12.0.20.5 release-keys', BuildTime=1654000000000, Hostname='cn-dg-vivo-x80'
    ),
    DeviceVariant(
        DeviceModel='V2339A', DeviceName='iQOO 12', ProductName='PD2339',
        Brand='iQOO', Board='V2339A', Hardware='qcom', DeviceType='PD2339',
        Manufacturer='vivo',
        DeviceInfo='iQOO/PD2339/PD2339:14/UKQ1.231003.002/PD2339_A_14.1.10.2:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='PD2339_A_14.1.10.2',
        BuildDisplay='PD2339_A_14.1.10.2 release-keys', BuildTime=1710000000000, Hostname='cn-dg-iqoo-12'
    ),
    DeviceVariant(
        DeviceModel='V2318A', DeviceName='iQOO Neo8 Pro', ProductName='PD2318',
        Brand='iQOO', Board='V2318A', Hardware='mt6895', DeviceType='PD2318',
        Manufacturer='vivo',
        DeviceInfo='iQOO/PD2318/PD2318:13/TP1A.220624.014/PD2318_A_13.0.7.0:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='PD2318_A_13.0.7.0',
        BuildDisplay='PD2318_A_13.0.7.0 release-keys', BuildTime=1688000000000, Hostname='cn-dg-iqoo-neo8'
    ),
    DeviceVariant(
        DeviceModel='V2336A', DeviceName='iQOO 12 Pro', ProductName='PD2336',
        Brand='iQOO', Board='V2336A', Hardware='qcom', DeviceType='PD2336',
        Manufacturer='vivo',
        DeviceInfo='iQOO/PD2336/PD2336:14/UKQ1.231003.002/PD2336_A_14.1.12.3:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='PD2336_A_14.1.12.3',
        BuildDisplay='PD2336_A_14.1.12.3 release-keys', BuildTime=1712000000000, Hostname='cn-dg-iqoo-12pro'
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
        DeviceModel='V2241A', DeviceName='iQOO 10 Pro', ProductName='PD2241',
        Brand='iQOO', Board='V2241A', Hardware='qcom', DeviceType='PD2241',
        Manufacturer='vivo',
        DeviceInfo='iQOO/PD2241/PD2241:12/SP1A.210812.016/PD2241_A_12.0.18.3:user/release-keys',
        OsVersion='12', SdkVersion='31', BuildId='PD2241_A_12.0.18.3',
        BuildDisplay='PD2241_A_12.0.18.3 release-keys', BuildTime=1660000000000, Hostname='cn-dg-iqoo-10pro'
    ),
    DeviceVariant(
        DeviceModel='V2352A', DeviceName='iQOO Z9 Turbo', ProductName='PD2352',
        Brand='iQOO', Board='V2352A', Hardware='qcom', DeviceType='PD2352',
        Manufacturer='vivo',
        DeviceInfo='iQOO/PD2352/PD2352:14/UP1A.231005.007/PD2352_A_14.0.5.3:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='PD2352_A_14.0.5.3',
        BuildDisplay='PD2352_A_14.0.5.3 release-keys', BuildTime=1713000000000, Hostname='cn-dg-iqoo-z9t'
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
        DeviceModel='CPH2557', DeviceName='OPPO Find N3', ProductName='stanford',
        Brand='OPPO', Board='CPH2557', Hardware='sm8550', DeviceType='OP5961L1',
        Manufacturer='OPPO',
        DeviceInfo='OPPO/CPH2557/OP5961L1:14/UKQ1.230804.001/R.1f80e_240125:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='R.1f80e_240125',
        BuildDisplay='R.1f80e_240125 release-keys', BuildTime=1707000000000, Hostname='cn-dg-oppo-n3'
    ),
    DeviceVariant(
        DeviceModel='PHY110', DeviceName='OPPO Find X7 Ultra', ProductName='alexandrite',
        Brand='OPPO', Board='PHY110', Hardware='sm8650', DeviceType='OP596EL1',
        Manufacturer='OPPO',
        DeviceInfo='OPPO/PHY110/OP596EL1:14/UKQ1.231003.002/R.1a2b3_240110:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='R.1a2b3_240110',
        BuildDisplay='R.1a2b3_240110 release-keys', BuildTime=1705000000000, Hostname='cn-dg-oppo-x7u'
    ),
    DeviceVariant(
        DeviceModel='CPH2609', DeviceName='OPPO Reno11 Pro', ProductName='oscar',
        Brand='OPPO', Board='CPH2609', Hardware='mt6889', DeviceType='OP596CL1',
        Manufacturer='OPPO',
        DeviceInfo='OPPO/CPH2609/OP596CL1:14/UP1A.231005.007/R.120_240320:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='R.120_240320',
        BuildDisplay='R.120_240320 release-keys', BuildTime=1711000000000, Hostname='cn-dg-oppo-r11p'
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
        DeviceModel='CPH2449', DeviceName='OnePlus Nord 3', ProductName='larry',
        Brand='OnePlus', Board='CPH2449', Hardware='mt6895', DeviceType='OP5B78L1',
        Manufacturer='OnePlus',
        DeviceInfo='OnePlus/CPH2449/OP5B78L1:13/TP1A.220905.001/R.120:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.120',
        BuildDisplay='R.120 release-keys', BuildTime=1689000000000, Hostname='cn-sz-oneplus-13'
    ),
    DeviceVariant(
        DeviceModel='CPH2611', DeviceName='OnePlus Ace 3', ProductName='aston',
        Brand='OnePlus', Board='CPH2611', Hardware='sm8550', DeviceType='OP5A04L1',
        Manufacturer='OnePlus',
        DeviceInfo='OnePlus/CPH2611/OP5A04L1:14/UKQ1.230804.001/R.20240301:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='R.20240301',
        BuildDisplay='R.20240301 release-keys', BuildTime=1709000000000, Hostname='cn-sz-oneplus-ace3'
    ),
    DeviceVariant(
        DeviceModel='CPH2451', DeviceName='OnePlus 11', ProductName='pancetta',
        Brand='OnePlus', Board='CPH2451', Hardware='sm8550', DeviceType='OP594BL1',
        Manufacturer='OnePlus',
        DeviceInfo='OnePlus/CPH2451/OP594BL1:13/TP1A.220905.001/R.20230101:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.20230101',
        BuildDisplay='R.20230101 release-keys', BuildTime=1673000000000, Hostname='cn-sz-oneplus-11'
    ),
    DeviceVariant(
        DeviceModel='NE2210', DeviceName='OnePlus 10 Pro', ProductName='negroni',
        Brand='OnePlus', Board='NE2210', Hardware='sm8450', DeviceType='OP516FL1',
        Manufacturer='OnePlus',
        DeviceInfo='OnePlus/NE2210/OP516FL1:13/TP1A.220624.014/R.20220915:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.20220915',
        BuildDisplay='R.20220915 release-keys', BuildTime=1663000000000, Hostname='cn-sz-oneplus-10pro'
    ),
    DeviceVariant(
        DeviceModel='CPH2605', DeviceName='OnePlus Ace 2 Pro', ProductName='martini',
        Brand='OnePlus', Board='CPH2605', Hardware='sm8475', DeviceType='OP5A20L1',
        Manufacturer='OnePlus',
        DeviceInfo='OnePlus/CPH2605/OP5A20L1:13/TP1A.220905.001/R.20230820:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.20230820',
        BuildDisplay='R.20230820 release-keys', BuildTime=1692000000000, Hostname='cn-sz-oneplus-ace2p'
    ),
    DeviceVariant(
        DeviceModel='RMX3888', DeviceName='realme GT5 Pro', ProductName='titan',
        Brand='realme', Board='RMX3888', Hardware='sm8550', DeviceType='RE58BAL1',
        Manufacturer='realme',
        DeviceInfo='realme/RMX3888/RE58BAL1:14/UKQ1.230804.001/R.20240115:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='R.20240115',
        BuildDisplay='R.20240115 release-keys', BuildTime=1705000000000, Hostname='cn-dg-realme-05'
    ),
    DeviceVariant(
        DeviceModel='RMX3706', DeviceName='realme GT Neo5 SE', ProductName='hotdog',
        Brand='realme', Board='RMX3706', Hardware='sm7475', DeviceType='RE58BBL1',
        Manufacturer='realme',
        DeviceInfo='realme/RMX3706/RE58BBL1:13/TP1A.220905.001/R.20230522:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.20230522',
        BuildDisplay='R.20230522 release-keys', BuildTime=1685000000000, Hostname='cn-dg-realme-neo5se'
    ),
    DeviceVariant(
        DeviceModel='RMX3800', DeviceName='realme GT6', ProductName='hercules',
        Brand='realme', Board='RMX3800', Hardware='sm8550', DeviceType='RE58C2',
        Manufacturer='realme',
        DeviceInfo='realme/RMX3800/RE58C2:14/UKQ1.231003.002/R.20240327:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='R.20240327',
        BuildDisplay='R.20240327 release-keys', BuildTime=1711000000000, Hostname='cn-dg-realme-gt6'
    ),
    DeviceVariant(
        DeviceModel='RMX3840', DeviceName='realme 12 Pro+', ProductName='salvia',
        Brand='realme', Board='RMX3840', Hardware='sm6450', DeviceType='RE58DAL1',
        Manufacturer='realme',
        DeviceInfo='realme/RMX3840/RE58DAL1:14/UP1A.231005.007/R.20240105:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='R.20240105',
        BuildDisplay='R.20240105 release-keys', BuildTime=1704000000000, Hostname='cn-dg-realme-12p'
    ),
    DeviceVariant(
        DeviceModel='RMX3770', DeviceName='realme 11 Pro+', ProductName='lychee',
        Brand='realme', Board='RMX3770', Hardware='mt6877', DeviceType='RE547AL1',
        Manufacturer='realme',
        DeviceInfo='realme/RMX3770/RE547AL1:13/TP1A.220624.014/R.20230510:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='R.20230510',
        BuildDisplay='R.20230510 release-keys', BuildTime=1684000000000, Hostname='cn-dg-realme-11p'
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
    ),
    DeviceVariant(
        DeviceModel='MNA-AL00', DeviceName='Huawei P60', ProductName='mona',
        Brand='Huawei', Board='MNA-AL00', Hardware='sm8475', DeviceType='HWMNA',
        Manufacturer='Huawei',
        DeviceInfo='Huawei/MNA-AL00/HWMNA:13/HarmonyOS4.0/4.0.0.120:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='4.0.0.120',
        BuildDisplay='4.0.0.120 release-keys', BuildTime=1702000000000, Hostname='cn-sz-huawei-07'
    ),
    DeviceVariant(
        DeviceModel='ALT-AL10', DeviceName='Huawei P70 Pro', ProductName='altair',
        Brand='Huawei', Board='ALT-AL10', Hardware='kirin9010', DeviceType='HWALT',
        Manufacturer='Huawei',
        DeviceInfo='Huawei/ALT-AL10/HWALT:12/HarmonyOS4.2/4.2.0.130:user/release-keys',
        OsVersion='12', SdkVersion='31', BuildId='4.2.0.130',
        BuildDisplay='4.2.0.130 release-keys', BuildTime=1714000000000, Hostname='cn-sz-huawei-p70'
    ),
    DeviceVariant(
        DeviceModel='DCO-AL00', DeviceName='Huawei Mate 50 Pro', ProductName='davinci',
        Brand='Huawei', Board='DCO-AL00', Hardware='sm8475', DeviceType='HWDCO',
        Manufacturer='Huawei',
        DeviceInfo='Huawei/DCO-AL00/HWDCO:12/HarmonyOS3.0/3.0.0.200:user/release-keys',
        OsVersion='12', SdkVersion='31', BuildId='3.0.0.200',
        BuildDisplay='3.0.0.200 release-keys', BuildTime=1662000000000, Hostname='cn-sz-huawei-m50p'
    ),
    DeviceVariant(
        DeviceModel='ADA-AL00', DeviceName='Huawei nova 12 Pro', ProductName='ada',
        Brand='Huawei', Board='ADA-AL00', Hardware='kirin8000', DeviceType='HWADA',
        Manufacturer='Huawei',
        DeviceInfo='Huawei/ADA-AL00/HWADA:12/HarmonyOS4.0/4.0.0.122:user/release-keys',
        OsVersion='12', SdkVersion='31', BuildId='4.0.0.122',
        BuildDisplay='4.0.0.122 release-keys', BuildTime=1708000000000, Hostname='cn-sz-huawei-nova12'
    ),
    DeviceVariant(
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
        DeviceModel='ANY-AN00', DeviceName='Honor 100 Pro', ProductName='anya',
        Brand='Honor', Board='ANY-AN00', Hardware='sm8475', DeviceType='HNANYA',
        Manufacturer='Honor',
        DeviceInfo='Honor/ANY-AN00/HNANYA:14/MagicOS8.0/8.0.0.115:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='8.0.0.115',
        BuildDisplay='8.0.0.115 release-keys', BuildTime=1710000000000, Hostname='cn-bj-honor-100p'
    ),
    DeviceVariant(
        DeviceModel='VER-AN10', DeviceName='Honor Magic V2', ProductName='verona',
        Brand='Honor', Board='VER-AN10', Hardware='sm8550', DeviceType='HNVERONA',
        Manufacturer='Honor',
        DeviceInfo='Honor/VER-AN10/HNVERONA:13/MagicOS7.2/7.2.0.118:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='7.2.0.118',
        BuildDisplay='7.2.0.118 release-keys', BuildTime=1696000000000, Hostname='cn-bj-honor-v2'
    ),
    DeviceVariant(
        DeviceModel='FNE-AN00', DeviceName='Honor X50', ProductName='finley',
        Brand='Honor', Board='FNE-AN00', Hardware='sm4350', DeviceType='HNFNE',
        Manufacturer='Honor',
        DeviceInfo='Honor/FNE-AN00/HNFNE:13/MagicOS7.1/7.1.0.178:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='7.1.0.178',
        BuildDisplay='7.1.0.178 release-keys', BuildTime=1694000000000, Hostname='cn-bj-honor-x50'
    ),
    DeviceVariant(
        DeviceModel='M391Q', DeviceName='Meizu 20 Pro', ProductName='meizu20pro',
        Brand='Meizu', Board='M391Q', Hardware='sm8550', DeviceType='meizu_M391Q',
        Manufacturer='Meizu',
        DeviceInfo='Meizu/M391Q/meizu_M391Q:13/TP1A.220624.014/Flyme10.0.0.0:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='Flyme10.0.0.0',
        BuildDisplay='Flyme10.0.0.0 release-keys', BuildTime=1679000000000, Hostname='cn-zh-meizu-06'
    ),
    DeviceVariant(
        DeviceModel='M461H', DeviceName='Meizu 21', ProductName='meizu21',
        Brand='Meizu', Board='M461H', Hardware='sm8650', DeviceType='meizu_M461H',
        Manufacturer='Meizu',
        DeviceInfo='Meizu/M461H/meizu_M461H:14/UP1A.231005.007/Flyme11.0.0.0:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='Flyme11.0.0.0',
        BuildDisplay='Flyme11.0.0.0 release-keys', BuildTime=1712000000000, Hostname='cn-zh-meizu-21'
    ),
    DeviceVariant(
        DeviceModel='M381Q', DeviceName='Meizu 20', ProductName='meizu20',
        Brand='Meizu', Board='M381Q', Hardware='sm8550', DeviceType='meizu_M381Q',
        Manufacturer='Meizu',
        DeviceInfo='Meizu/M381Q/meizu_M381Q:13/TP1A.220624.014/Flyme10.0.3.0:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='Flyme10.0.3.0',
        BuildDisplay='Flyme10.0.3.0 release-keys', BuildTime=1680000000000, Hostname='cn-zh-meizu-20'
    ),
    DeviceVariant(
        DeviceModel='M191Q', DeviceName='Meizu 18 Pro', ProductName='meizu18pro',
        Brand='Meizu', Board='M191Q', Hardware='sm8350', DeviceType='meizu_M191Q',
        Manufacturer='Meizu',
        DeviceInfo='Meizu/M191Q/meizu_M191Q:11/RP1A.200720.001/Flyme9.2.0.0A:user/release-keys',
        OsVersion='11', SdkVersion='30', BuildId='Flyme9.2.0.0A',
        BuildDisplay='Flyme9.2.0.0A release-keys', BuildTime=1618000000000, Hostname='cn-zh-meizu-18p'
    ),
    DeviceVariant(
        DeviceModel='M081Q', DeviceName='Meizu 17 Pro', ProductName='meizu17pro',
        Brand='Meizu', Board='M081Q', Hardware='sm8250', DeviceType='meizu_M081Q',
        Manufacturer='Meizu',
        DeviceInfo='Meizu/M081Q/meizu_M081Q:10/QKQ1.200512.002/Flyme8.10.5.0A:user/release-keys',
        OsVersion='10', SdkVersion='29', BuildId='Flyme8.10.5.0A',
        BuildDisplay='Flyme8.10.5.0A release-keys', BuildTime=1598000000000, Hostname='cn-zh-meizu-17p'
    ),
    DeviceVariant(
        DeviceModel='M971Q', DeviceName='Meizu 16s Pro', ProductName='meizu16spro',
        Brand='Meizu', Board='M971Q', Hardware='sm8150', DeviceType='meizu_M971Q',
        Manufacturer='Meizu',
        DeviceInfo='Meizu/M971Q/meizu_M971Q:9/PKQ1.190118.001/Flyme8.0.0.0A:user/release-keys',
        OsVersion='9', SdkVersion='28', BuildId='Flyme8.0.0.0A',
        BuildDisplay='Flyme8.0.0.0A release-keys', BuildTime=1566000000000, Hostname='cn-zh-meizu-16sp'
    ),
    DeviceVariant(
        DeviceModel='SM-S9080', DeviceName='Samsung Galaxy S22 Ultra', ProductName='b0s',
        Brand='samsung', Board='SM-S9080', Hardware='qcom', DeviceType='b0s',
        Manufacturer='samsung',
        DeviceInfo='samsung/b0s/b0s:12/SP1A.210812.016/S9080ZHU2AVE4:user/release-keys',
        OsVersion='12', SdkVersion='31', BuildId='S9080ZHU2AVE4',
        BuildDisplay='SP1A.210812.016 release-keys', BuildTime=1654000000000, Hostname='SEP-72'
    ),
    DeviceVariant(
        DeviceModel='SM-S9210', DeviceName='Samsung Galaxy S24', ProductName='e2qkskx',
        Brand='samsung', Board='SM-S9210', Hardware='exynos2400', DeviceType='e2q',
        Manufacturer='samsung',
        DeviceInfo='samsung/e2qkskx/e2q:14/UP1A.231005.007/S9210ZCU1AXBA:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='S9210ZCU1AXBA',
        BuildDisplay='UP1A.231005.007 release-keys', BuildTime=1708000000000, Hostname='SAMSUNG-S24-CN'
    ),
    DeviceVariant(
        DeviceModel='SM-F9460', DeviceName='Samsung Galaxy Z Fold5', ProductName='q6qkskx',
        Brand='samsung', Board='SM-F9460', Hardware='qcom', DeviceType='q6q',
        Manufacturer='samsung',
        DeviceInfo='samsung/q6qkskx/q6q:13/TP1A.220624.014/F9460ZCU1AWHA:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='F9460ZCU1AWHA',
        BuildDisplay='TP1A.220624.014 release-keys', BuildTime=1691000000000, Hostname='SEP-FOLD5'
    ),
    DeviceVariant(
        DeviceModel='SM-S9180', DeviceName='Samsung Galaxy S23 Ultra', ProductName='dm3qkskx',
        Brand='samsung', Board='SM-S9180', Hardware='qcom', DeviceType='dm3q',
        Manufacturer='samsung',
        DeviceInfo='samsung/dm3qkskx/dm3q:13/TP1A.220624.014/S9180ZCU1AWD3:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='S9180ZCU1AWD3',
        BuildDisplay='TP1A.220624.014 release-keys', BuildTime=1675000000000, Hostname='SEP-S23U'
    ),
    DeviceVariant(
        DeviceModel='SM-F7310', DeviceName='Samsung Galaxy Z Flip5', ProductName='b6qkskx',
        Brand='samsung', Board='SM-F7310', Hardware='qcom', DeviceType='b6q',
        Manufacturer='samsung',
        DeviceInfo='samsung/b6qkskx/b6q:13/TP1A.220624.014/F7310ZCU1AWH3:user/release-keys',
        OsVersion='13', SdkVersion='33', BuildId='F7310ZCU1AWH3',
        BuildDisplay='TP1A.220624.014 release-keys', BuildTime=1693000000000, Hostname='SEP-FLIP5'
    ),
    DeviceVariant(
        DeviceModel='SM-A5560', DeviceName='Samsung Galaxy A55 5G', ProductName='a55xkskx',
        Brand='samsung', Board='SM-A5560', Hardware='exynos1480', DeviceType='a55x',
        Manufacturer='samsung',
        DeviceInfo='samsung/a55xkskx/a55x:14/UP1A.231005.007/A5560ZCU1AXC1:user/release-keys',
        OsVersion='14', SdkVersion='34', BuildId='A5560ZCU1AXC1',
        BuildDisplay='UP1A.231005.007 release-keys', BuildTime=1712000000000, Hostname='SAMSUNG-A55'
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
