from faker import Faker
from faker.providers import BaseProvider
from typing import Any
import random
import hashlib

device_list = [
    ("ALI-AN00", "Huawei P60"),
    ("MNA-AL00", "Huawei P60 Pro"),
    ("ALT-AL00", "Huawei Mate 60"),
    ("ALN-AL80", "Huawei Mate 60 Pro"),
    ("ALT-AL10", "Huawei Mate X5"),
    ("ADA-AL00", "Huawei nova 12"),
    ("FIN-AL60", "Huawei nova 12 Pro"),
    ("GLA-AL00", "Huawei Pocket 2"),
    ("BVL-AN00", "Honor Magic6 Pro"),
    ("BVL-AN20", "Honor Magic6 Ultimate"),
    ("VER-AN10", "Honor Magic V2"),
    ("MAA-AN10", "Honor 100 Pro"),
    ("LRA-AN00", "Honor 90"),
    ("ALI-AN00", "Honor X50"),          # 重复型号，不同品牌
    ("2211133C", "Xiaomi 13"),
    ("2210132C", "Xiaomi 13 Pro"),
    ("2304FPN6DC", "Xiaomi 13 Ultra"),
    ("23127PN0CC", "Xiaomi 14"),
    ("23116PN5BC", "Xiaomi 14 Pro"),
    ("24030PN60C", "Xiaomi 14 Ultra"),
    ("2308CPXD0C", "Xiaomi Mix Fold 3"),
    ("23090RA98C", "Redmi Note 12 Pro"),
    ("2312DRA50C", "Redmi Note 13"),
    ("23013RK75C", "Redmi K60 / K60 Pro"),
    ("2311DRK48C", "Redmi K70"),
    ("23053RN02A", "Redmi 12C"),
    ("23124RN87C", "Redmi 13C"),
    ("V2219A", "vivo X90"),
    ("V2227A", "vivo X90 Pro+"),
    ("V2309A", "vivo X100"),
    ("V2324A", "vivo X100 Pro"),
    ("V2405A", "vivo X100 Ultra"),
    ("V2337A", "vivo X Fold3"),
    ("V2303A", "vivo X Fold3 Pro"),
    ("V2250", "vivo V29"),
    ("V2279A", "vivo Y78"),
    ("V2317", "vivo Y100"),
    ("RMX3820", "realme GT5"),
    ("RMX3851", "realme GT5 Pro"),
    ("RMX3843", "realme 12 Pro+"),
    ("RMX3902", "realme 12x"),
    ("RMX3830", "realme C67")
]
# Android 版本及其 SDK 级别
android_versions = {
    "12": "31", "12L": "32", "13": "33", "14": "34", "15": "35"
}
class AndroidDeviceProvider(BaseProvider):

    def __init__(self, generator: Any):
        super().__init__(generator)
        self.faker = Faker()
        self.devices = device_list

    def device_model(self):
        return random.choice(self.devices)[0]   # 只返回型号

    def device_name(self):
        return random.choice(self.devices)[1]   # 只返回市场名称

    def device_full_info(self):
        model, name = random.choice(self.devices)
        return model, name

    def device_id(self):
        # 模拟 16 位十六进制 Android ID
        return self.faker.hexify("^^^^^^^^^^^^^^^^", upper=False)

    def ipv4_public(self):
        return self.faker.ipv4_public()

    def android_version(self):
        version = random.choice(list(android_versions.keys()))
        return version, android_versions[version]

    def mac_address(self):
        return self.faker.mac_address()

    def locale(self):
        return self.faker.locale()

    def timezone(self):
        return self.faker.timezone()

    def google_advertising_id(self):
        # 模拟 GAID 格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        return self.faker.uuid4()

    def get_android_ua(self):
        self.faker.chrome()
        while True:
            ua = self.faker.chrome()
            if 'Android' in ua:
                return ua

    def screen_metrics(self):
        # 返回常见安卓手机分辨率及密度
        resolutions = [
            ("1080x2340", 440), ("1080x2400", 420),
            ("1440x3200", 560), ("720x1600", 320)
        ]
        res, dpi = random.choice(resolutions)
        return res, dpi

    def generator_fingerprint(self):
        mac = self.mac_address()
        ip = self.ipv4_public()
        model, name = self.device_full_info()
        user_agent = self.get_android_ua()
        android_id = self.device_id()
        locale = self.locale()
        timezone = self.timezone()
        version, sdk = self.android_version()
        resolution, dpi = self.screen_metrics()
        gaid = self.google_advertising_id()
        canvas_noise = self.faker.sha256()
        webgl_noise = self.faker.sha256()

        raw_components = [
            user_agent, model, f"Android {version} (SDK {sdk})",
            resolution, f"{dpi}dpi", mac, ip, timezone, locale,
            android_id, gaid, canvas_noise, webgl_noise
        ]
        raw_fingerprint = "|".join(raw_components)
        fingerprint_hash = hashlib.sha256(raw_fingerprint.encode()).hexdigest()

        return fingerprint_hash

