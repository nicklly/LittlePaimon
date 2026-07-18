import contextlib
import hashlib
import json
import random
import string
import asyncio
import time

from typing import Optional, Literal, Union, Tuple
from nonebot import logger as nb_logger
from tortoise.queryset import Q
from LittlePaimon.config import config
from LittlePaimon.database import PublicCookie, PrivateCookie, CookieCache, Devices
from LittlePaimon.utils.captcha import rrocr
from LittlePaimon.utils import logger
from .devices import DeviceProvider
from .requests import aiorequests

# MIHOYO_API = 'https://api-takumi-record.mihoyo.com/'
# MIHOYO_API_OLD = 'https://api-takumi.mihoyo.com/'
ABYSS_API = 'https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/spiralAbyss'
HARD_CHALLENGE_API = 'https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/hard_challenge'
ROLE_COMBAT_API = 'https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/role_combat'
PLAYER_CARD_API = 'https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/index'
CHARACTER_DETAIL_API = 'https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/character'
CHARACTER_SKILL_API = 'https://api-takumi.mihoyo.com/event/e20200928calculate/v1/sync/avatar/detail'
MONTH_INFO_API = 'https://act-hk4e-api.mihoyo.com/event/ys_ledger/monthInfo'
# DAILY_NOTE_API = 'https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/dailyNote'
GAME_RECORD_API = 'https://api-takumi-record.mihoyo.com/game_record/card/wapi/getGameRecordCard'
SIGN_INFO_API = 'https://api-takumi.mihoyo.com/event/luna/hk4e/info'
SIGN_REWARD_API = 'https://api-takumi.mihoyo.com/event/luna/home'
SIGN_ACTION_API = 'https://api-takumi.mihoyo.com/event/luna/sign'
AUTHKEY_API = 'https://api-takumi.mihoyo.com/binding/api/genAuthKey'
STOKEN_API = 'https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket'
COOKIE_TOKEN_API = 'https://api-takumi.mihoyo.com/auth/api/getCookieAccountInfoBySToken'
SCAN_STATUS_API = 'https://passport-api.mihoyo.com/account/ma-cn-passport/app/scanQRLogin'
CONFIRM_STATUS_API = 'https://passport-api.mihoyo.com/account/ma-cn-passport/app/confirmQRLogin'
LOGIN_TICKET_INFO_API = 'https://webapi.account.mihoyo.com/Api/cookie_accountinfo_by_loginticket'
WIDGET_URL = 'https://api-takumi-record.mihoyo.com/game_record/app/genshin/aapi/widget/v2?game_id=2'
GET_EXT_LIST_URL = "https://public-data-api.mihoyo.com/device-fp/api/getExtList"
GET_FP_URL = 'https://public-data-api.mihoyo.com/device-fp/api/getFp'
BBS_VERSION = '2.109.0'


def md5(text: str) -> str:
    """
    md5加密
    :param text: 文本
    :return: md5加密后的文本
    """
    md5_ = hashlib.md5()
    md5_.update(text.encode())
    return md5_.hexdigest()

def random_hex(length: int) -> str:
    """
    生成指定长度的随机字符串
    :param length: 长度
    :return: 随机字符串
    """
    result = hex(random.randint(0, 16 ** length)).replace('0x', '').upper()
    if len(result) < length:
        result = '0' * (length - len(result)) + result
    return result

def random_text(length: int) -> str:
    """
    生成指定长度的随机字符串
    :param length: 长度
    :return: 随机字符串
    """
    return ''.join(random.sample(string.ascii_lowercase + string.digits, length))

def get_ds(q: str = '', b: dict = None) -> str:
    """
    生成米游社headers的ds_token
    :param q: 查询
    :param b: 请求体
    :return: ds_token
    """
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    br = json.dumps(b) if b else ''
    t = str(int(time.time()))
    r = ''.join(random.choices(chars, k=6))
    c = md5(f'salt=dDIQHbKOdaPaLuvQKVzUzqdeCaxjtaPV&t={t}&r={r}&b={br}&q={q}')
    return f'{t},{r},{c}'

def get_ds_x4(q: str = '', b: dict = None) -> str:
    """
    生成米游社headers的ds_token
    :param q: 查询
    :param b: 请求体
    :return: ds_token
    """
    br = json.dumps(b) if b else ''

    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = md5(f'salt=xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs&t={t}&r={r}&b={br}&q={q}')
    return f'{t},{r},{c}'

def get_ds_x6(q: str = '', b: str = None) -> str:
    """
    生成米游社headers的ds_token
    :param q: 查询
    :param b: 请求体
    :return: ds_token
    """
    br = json.dumps(b) if b else ''
    t = str(int(time.time()))
    r = str(random.randint(100001, 200000))
    c = md5(f'salt=t0qEgfub6cvueAPgR5m9aQWWVciEer7v&t={t}&r={r}&b={br}&q={q}')
    return f'{t},{r},{c}'

def get_old_version_ds(web: bool = False) -> str:
    """
    生成米游社旧版本headers的ds_token
    """
    if web:
        # s = 'G1ktdwFL4IyGkHuuWSmz0wUe9Db9scyK'.
        s = 'd9200c846b10886e8c874fc33c8f308b'
    else:
        # s = 'idMMaGYmVgPzh3wxmWudUXKUPGidO7GM'
        s = '47f15f1b66bee46b816115d8e8e6ebb6'
    t = str(int(time.time()))
    r = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
    c = md5(f"salt={s}&t={t}&r={r}")
    return f"{t},{r},{c}"

def qrcode_permission_headers(cookies: Optional[str], user_id: Optional[str]):

    devices = asyncio.run(get_device_info(user_id))
    headers = {
        'DS':                   get_old_version_ds(web=False),
        'cookie':               cookies,
        'x-rpc-client_type':    '2',
        'x-rpc-app_version':    BBS_VERSION,
        'x-rpc-sys_version':    '12',
        'x-rpc-channel':        'miyousheluodi',
        'x-rpc-device_id':      'FF8F93BE-8791-4263-AA15-F96A60CA22F6',
        'x-rpc-device_name':    'OPPO Find X7',
        'x-rpc-device_model':   'PHZ110',
        'x-rpc-h265_supported': '1',
        'x-rpc-csm_source':     'discussion',
        'x-rpc-verify_key':     'bll8iq97cem8',
        'referer':              'https://app.mihoyo.com',
        'Host':                 'bbs-api.miyoushe.com',
        'user-agent':           'okhttp/4.9.3'
    }
    if user_id is not None:
        headers.update({
            'x-rpc-device_id':      devices.device_id ,
            'x-rpc-device_name':    devices.device_name,
            'x-rpc-device_model':   devices.device_model
        })
    return headers

def login_permission_headers(ticket: Optional[dict] = None, auth_cookie: Optional[str] = '', referer: Optional[str] = '') -> dict:
    return {
        'Accept-Language':          'zh-cn',
        'Content-Type':             'application/json; charset=UTF-8',
        'Accept':                   '*/*',
        'Cookie':                   auth_cookie,
        'DS':                       get_ds('', ticket),
        'referer':                  referer if referer is not None else '',
        'x-rpc-app_version':        BBS_VERSION,
        'x-rpc-app_id':             'bll8iq97cem8',
        'x-rpc-sdk_version':        BBS_VERSION,
        'x-rpc-client_type':        '2',
        'x-rpc-device_name':        'OPPO Find X7',
        'x-rpc-device_fp':          '38d81926460a0',
        'x-rpc-device_id':          'FF8F93BE-8791-4263-AA15-F96A60CA22F6',
        'x-rpc-device_model':       'PHZ110',
        'x-rpc-game_biz':           'bbs_cn',
        'x-rpc-account_version':    BBS_VERSION,
        'User-Agent':               f'Mozilla/5.0 miHoYoBBS/{BBS_VERSION} Capture/2.2.0'
    }

async def check_qrcode_status(url: str, ticket: str, auth_cookie:str, referer: str = '') -> bool:
    tickets = {'ticket': ticket, 'token_types': ["4"]}
    body = json.dumps(tickets, ensure_ascii=False)

    req = await aiorequests.post(
        url = url,
        headers = login_permission_headers(tickets, auth_cookie, referer),
        data = body # type: ignore
    )
    try:
        result = req.json()
        return result["retcode"] == 0
    except Exception as e:
        return False

def mihoyo_headers(cookie, q = '', b = None, devices: Optional[Devices] = None) -> dict:
    """
    生成米游社headers
        :param devices:
        :param cookie: cookie
        :param q: 查询
        :param b: 请求体
        :return: headers
    """
    headers = {
        'Host':                 'api-takumi-record.mihoyo.com',
        'Accept':               'application/json, text/plain, */*',
        'Origin':               'https://webstatic.mihoyo.com',
        'x-rpc-page':           'v6.6.1-gr-cn_#/ys',
        'x-rpc-tool_verison':   'v6.6.1-gr-cn',
        'x-rpc-app_version':    BBS_VERSION,
        'x-rpc-device_fp':      '38d81926460a0',
        'x-rpc-device_name':    'OPPO Find X7',
        'x-rpc-device_id':      'FF8F93BE-8791-4263-AA15-F96A60CA22F6',
        'x-rpc-client_type':    '5',
        'x-rpc-sys_version':    '12',
        'X-Requested-With':     'com.mihoyo.hyperion',
        'x-rpc-challenge':      '',
        'User-Agent':           f'Mozilla/5.0 (Linux; Android 13; Pixel 5 Build/TQ3A.230901.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/118.0.0.0 Mobile Safari/537.36 miHoYoBBS/{BBS_VERSION}',
        'Referer':              'https://webstatic.mihoyo.com/',
        'Cookie':               cookie,
        'DS':                   get_ds_x4(q, b),
    }
    if devices is not None:
        headers.update({
            'x-rpc-device_fp':      devices.device_fp,
            'x-rpc-device_name':    devices.device_name,
            'x-rpc-device_id':      devices.device_id
        })
    return headers


def mihoyo_sign_headers(cookie: str, extra_headers: Optional[dict] = None) -> dict:
    """
    生成米游社签到headers
        :param mhy_bbs:
        :param q:
        :param b:
        :param cookie: cookie
        :param extra_headers: 额外的headers参数
        :return: headers
    """
    header = {
        'User-Agent':           'okhttp/4.9.3',
        'x-rpc-device_name':    'Vivo V2309A',
        'x-rpc-device_model':   'V2309A',
        'x-rpc-device_id':      '129ec7b8-f825-3c0b-8a2f-94c0d977ad8a',
        'x-rpc-device_fp':      '38d8191ad9596',
        'x-rpc-client_type':    '2',
        'x-rpc-channel':        'miyousheluodi',
        'x-rpc-csm_source':     'discussion',
        'x-rpc-app_version':    BBS_VERSION,
        'x-rpc-sys_version':    '12',
        'Referer':              'https://app.mihoyo.com',
        'Host':                 'bbs-api.miyoushe.com',
        "Content-Type":         "application/json; charset=UTF-8",
        'Cookie':               cookie,
        'DS':                   get_old_version_ds(web=False),
    }
    if extra_headers:
        header.update(extra_headers)
    return header


async def check_retcode(data: dict, cookie_info, user_id: str, uid: str) -> bool:
    """
    检查数据响应状态冰进行响应处理
        :param data: 数据
        :param cookie_info: cookie信息
        :param user_id: 用户id
        :param uid: 原神uid
        :return: 数据是否有效
    """
    if not data:
        return False
    if data['retcode'] in [10001, -100]:
        if isinstance(cookie_info, PrivateCookie):
            if cookie_info.status == 1:
                cookie_info.status = 0
                await cookie_info.save()
                logger.info('原神Cookie', f'用户<m>{user_id}</m>的私人cookie<m>{uid}</m>疑似失效')
            elif cookie_info.status == 0:
                await cookie_info.delete()
                logger.info(
                    '原神Cookie',
                    f'用户<m>{user_id}</m>的私人cookie<m>{uid}</m>连续失效，<r>已删除</r>',
                )
        elif isinstance(cookie_info, PublicCookie):
            await CookieCache.filter(cookie=cookie_info.cookie).delete()
            await cookie_info.delete()
            logger.info('原神Cookie', f'<m>{cookie_info.id}</m>号公共cookie已失效，<r>已删除</r>')
        else:
            await PublicCookie.filter(cookie=cookie_info.cookie).delete()
            await cookie_info.delete()
            logger.info(
                '原神Cookie', f'UID<m>{cookie_info.uid}</m>使用的缓存cookie已失效，<r>已删除</r>'
            )
        return False
    elif data['retcode'] == 10101:
        cookie_info.status = 2
        if isinstance(cookie_info, PrivateCookie):
            cookie_info.status = 2
            await cookie_info.save()
            logger.info(
                '原神Cookie', f'用户<m>{user_id}</m>的私人cookie<m>{uid}</m>已达到每日30次查询上限'
            )
        elif isinstance(cookie_info, PublicCookie):
            cookie_info.status = 2
            await cookie_info.save()
            logger.info('原神Cookie', f'<m>{cookie_info.id}</m>号公共cookie已达到每日30次查询上限')
        else:
            await PublicCookie.filter(cookie=cookie_info.cookie).update(status=2)
            await cookie_info.delete()
            logger.info(
                '原神Cookie', f'UID<m>{cookie_info.uid}</m>使用的缓存cookie已达到每日30次查询上限'
            )
        return False
    else:
        if isinstance(cookie_info, PublicCookie) and data['retcode'] != 1034:
            await CookieCache.update_or_create(
                uid=uid, defaults={'cookie': cookie_info.cookie}
            )
        return True

async def get_device_info(user_id: str) -> Union[None, Devices]:
    if device_info := await Devices.filter(Q(user_id=user_id)).first():
        return device_info
    else:
        return None

async def get_cookie(
        user_id: str, uid: str, check: bool = True, own: bool = False
) -> Union[None, PrivateCookie, PublicCookie, CookieCache]:
    """
    获取可用的cookie
        :param user_id: 用户id
        :param uid: 原神uid
        :param check: 是否获取疑似失效的cookie
        :param own: 是否只获取和uid对应的cookie
    """
    query = Q(status=1) | Q(status=0) if check else Q(status=1)
    if private_cookie := await PrivateCookie.filter(
            Q(Q(query) & Q(user_id=user_id) & Q(uid=uid))
    ).first():
        return private_cookie
    elif not own:
        if cache_cookie := await CookieCache.get_or_none(uid=uid):
            return cache_cookie
        elif private_cookie := await PrivateCookie.filter(
                Q(Q(query) & Q(user_id=user_id))
        ).first():
            return private_cookie
        else:
            return await PublicCookie.filter(Q(query)).first()
    else:
        return None

async def get_ext_list():
    try:
        req = await aiorequests.get(
            url = f'{GET_EXT_LIST_URL}?platform=2&app_name=bbs_cn',
            headers = {
                'User-Agent':       'okhttp/4.9.3'
            }
        )
        req = req.json()
        if req['data'] and 'ext_list' in req['data']:
            ext_list = req['data']['ext_list']
            if isinstance(ext_list, list):
                return {item for item in ext_list if isinstance(item, str)}
    except Exception as ex:
        return ex

    return {
        'oaid', 'vaid', 'aaid', 'board', 'brand', 'hardware', 'cpuType', 'deviceType',
        'display', 'hostname', 'manufacturer', 'productName', 'model', 'deviceInfo',
        'sdkVersion', 'osVersion', 'devId', 'buildTags', 'buildType', 'buildUser',
        'buildTime', 'screenSize', 'vendor', 'romCapacity', 'romRemain', 'ramCapacity',
        'ramRemain', 'appMemory', 'accelerometer', 'gyroscope', 'magnetometer', 'isRoot',
        'debugStatus', 'proxyStatus', 'emulatorStatus', 'isTablet', 'simState', 'ui_mode',
        'sdCapacity', 'sdRemain', 'hasKeyboard', 'isMockLocation', 'ringMode', 'isAirMode',
        'batteryStatus', 'chargeStatus', 'deviceName', 'appInstallTimeDiff',
        'appUpdateTimeDiff', 'packageName', 'packageVersion', 'networkType'
    }

async def get_Fp(uid: str):
    fp = DeviceProvider()
    default_fp = fp.generate_default_device_id()
    error_fp = fp.generate_error_device_id()
    seedId, seedTime = fp.device_seed()
    variant = fp.select_variant(uid)
    extList = await get_ext_list()
    allFields = fp.build_ext_fields(variant)
    filtered = {k: v for k, v in allFields.items() if k in extList}

    body = json.dumps({
        'device_id':             str(fp.get_device_id_for_account(uid)),
        'seed_id':               seedId,
        'seed_time':             seedTime,
        'platform':              '2',
        'device_fp':             default_fp,
        'app_name':              'bbs_cn',
        'ext_fields':            json.dumps(filtered),
        'bbs_device_id':         str(fp.device_id())
    })
    req = await aiorequests.post(
        url = GET_FP_URL,
        headers = {
            'User-Agent': 'okhttp/4.9.3'
        },
        data = body,
    )
    req = req.json()
    if req['retcode'] == 0:
        return req['data']['device_fp']
    return None

async def get_bind_game_info(cookie: str, mys_id: str):
    """
    通过cookie，获取米游社绑定的原神游戏信息
    :param cookie: cookie
    :param mys_id: 米游社id
    :return: 原神信息
    """
    with contextlib.suppress(Exception):
        data = await aiorequests.get(
            url = GAME_RECORD_API,
            headers = mihoyo_headers(cookie, f'uid={mys_id}'),
            params = {'uid': mys_id},
        )
        data = data.json()
        nb_logger.debug(data)
        if data['retcode'] == 0:
            return data['data']
    return None


async def get_Abyss2_info(
        uid: str,
        user_id: Optional[str],
):
    cookie_info = await get_cookie(user_id, uid, True)
    device_info = await get_device_info(user_id)
    if not cookie_info:
        return '当前没有可使用的cookie，请使用命令[原神扫码绑定]/[ysb]绑定私人cookie或联系超级管理员添加公共cookie，'
    server_id = 'cn_qd01' if uid[0] == '5' else 'cn_gf01'
    headers = mihoyo_headers(
        q = f'role_id={uid}&need_detail=True&server={server_id}',
        cookie = cookie_info.cookie,
        devices = device_info
    )
    data: dict = (
        await aiorequests.get(
            url=HARD_CHALLENGE_API,
            headers=headers,
            params={
                "role_id": uid,
                "server": server_id,
                "need_detail": True,
            }
        )
    ).json()
    return data

async def get_abyss_info(
        uid: str,
        user_id: Optional[str],
        schedule_type: Optional[str] = "1",
):
    server_id = 'cn_qd01' if uid[0] == '5' else 'cn_gf01'
    cookie_info = await get_cookie(user_id, uid, True)
    device_info = await get_device_info(user_id)
    ocr = rrocr(user_id)
    if not cookie_info:
        return '当前没有可使用的cookie，请使用命令[原神扫码绑定]/[ysb]绑定私人cookie或联系超级管理员添加公共cookie，'
    headers = mihoyo_headers(
        q = f'role_id={uid}&schedule_type={schedule_type}&server={server_id}',
        cookie = cookie_info.cookie,
        devices = device_info
    )

    data = await aiorequests.get(
            url = ABYSS_API,
            headers = headers,
            params = {
                "schedule_type": schedule_type,
                "role_id": uid,
                "server": server_id,
            }
    )
    data = data.json()
    if data['retcode'] == 0:
        logger.info('原神深渊战报', "获取数据成功")
        return data
    elif data['retcode'] == data['retcode'] == 5003:
        logger.warning('原神深渊战报', "账号异常，未能获取数据")
        return '帐号异常，获取数据失败'
    elif data['retcode'] == 1034:
        logger.warning('原神深渊战报', '遭遇验证码，正尝试过码')
        for i in range(1, 4):
            logger.info('原神深渊战报', f'触发验证码，即将进行第{i}次重试，最多3次')
            challenge = await ocr.get_pass_challenge(cookie_info.extra_cookie, user_id = user_id, mode = 'game')
            if challenge is not None:
                headers.update({"x-rpc-challenge": challenge})
                req = await aiorequests.get(
                    url = ABYSS_API,
                    headers = headers,
                    params = {
                        "schedule_type": schedule_type,
                        "role_id": uid,
                        "server": server_id,
                    }
                )
                req = req.json()
                if req['retcode'] == 0:
                    logger.success('原神深渊战报', "打码成功，获取数据成功")
                    return req
                elif req['retcode'] == 10034:
                    logger.warning('原神深渊战报', "打码失败，无法获取数据")
                    return '打码失败，无法获取数据'
            else:
                logger.info('原神深渊战报', '过码失败')
                return "遇到验证码，但是过码失败"
    else:
        logger.warning('原神深渊战报', "未知错误")
        return '未知错误'
    return data['message']

async def get_role_combat_info(
        uid: str,
        user_id: Optional[str]
):
    cookie_info = await get_cookie(user_id, uid, True)
    device_info = await get_device_info(user_id)
    if not cookie_info:
        return '当前没有可使用的cookie，请使用命令[原神扫码绑定]/[ysb]绑定私人cookie或联系超级管理员添加公共cookie，'
    server_id = 'cn_qd01' if uid[0] == '5' else 'cn_gf01'
    headers = mihoyo_headers(
        q=f'role_id={uid}&need_detail=True&server={server_id}&active=1',
        cookie = cookie_info.cookie,
        devices = device_info
    )
    data: dict = (
        await aiorequests.get(
            url = ROLE_COMBAT_API,
            headers = headers,
            params = {
                "role_id": uid,
                "server": server_id,
                "active": 1,
                "need_detail": True,
            }
        )
    ).json()
    return data

async def get_mihoyo_public_data(
        uid: str,
        user_id: Optional[str],
        mode: Literal['player_card', 'role_detail'],
):
    server_id = 'cn_qd01' if uid[0] == '5' else 'cn_gf01'
    check = True
    ocr = rrocr(user_id)

    cookie_info = await get_cookie(user_id, uid, check)
    device_info = await get_device_info(user_id)
    if not cookie_info:
         return '当前没有可使用的cookie，请使用命令[原神扫码绑定]/[ysb]绑定私人cookie或联系超级管理员添加公共cookie，'
    elif mode == 'player_card':
        headers = mihoyo_headers(
            q = f'role_id={uid}&server={server_id}&avatar_list_type=1',
            cookie = cookie_info.cookie,
            devices = device_info
        )
        ds = get_ds_x4(q = f'role_id={uid}&server={server_id}&avatar_list_type=1')
        data = await aiorequests.get(
            url = PLAYER_CARD_API,
            headers = headers,
            params = {'server': server_id, 'role_id': uid, 'avatar_list_type': '1'},
        )
        data = data.json()
        if data['retcode'] == 0:
            logger.info('原神信息查询', "获取数据成功")
            if await check_retcode(data, cookie_info, user_id, uid):
                return data
        elif data['retcode'] == 5003:
            logger.warning('原神信息查询', "获取数据失败")
            return '账号异常，获取数据失败'
        elif data['retcode'] == 1034:
            for i in range(1, 3):
                logger.info('原神信息查询', f'➤ 触发验证码，即将进行第{i}次重试，最多3次')
                challenge = await ocr.get_pass_challenge(cookie_info.extra_cookie, user_id,'game')
                if challenge is not None:
                    headers.update({
                        'DS':                   ds,
                        "x-rpc-challenge":      challenge,
                    })
                    result = await aiorequests.get(
                        url = PLAYER_CARD_API,
                        headers = headers,
                        params = {'server': server_id, 'role_id': uid, 'avatar_list_type': '1'},
                    )
                    result = result.json()
                    if result['retcode'] == 0:
                        logger.success('原神信息查询', '打码成功,数据获取成功')
                        return result
                    elif result['retcode'] == 1034:
                        logger.warning('原神信息查询','打码成功,但数据获取失败')
                        return result
                else:
                    logger.info('原神信息查询', '过码失败')
                    return "遇到验证码，但是过码失败"
        else:
            return '未知错误'
    elif mode == 'role_detail':
        json_data = {"server": server_id, "role_id": uid, "character_ids": []}
        data = await aiorequests.post(
            url = CHARACTER_DETAIL_API,
            headers = mihoyo_headers(b = json_data, cookie = cookie_info.cookie),
            json = json_data,
        )
        data = data.json() if data else {'retcode': 999}
        if await check_retcode(data, cookie_info, user_id, uid):
            return data
    else:
        return None

async def get_mihoyo_private_data(
        uid: str,
        user_id: Optional[str],
        mode: Literal['role_skill', 'month_info', 'daily_note', 'sign_info', 'sign_action'],
        role_id: Optional[str] = None,
        month: Optional[str] = None,
):
    server_id = 'cn_qd01' if uid[0] == '5' else 'cn_gf01'
    cookie_info = await get_cookie(user_id, uid, True, True)
    if not cookie_info:
        return (
                '未绑定私人cookie，绑定方法二选一：\n1.通过米游社扫码绑定：\n请发送指令[原神扫码绑定]\n2.获取cookie的教程：\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1\n获取后，使用[ysb cookie]指令绑定'
                + (f'或前往{config.CookieWeb_url}网页添加绑定' if config.CookieWeb_enable else '')
        )
    if mode == 'role_skill':
        data = await aiorequests.get(
            url = CHARACTER_SKILL_API,
            headers = mihoyo_headers(
                q = f'uid={uid}&region={server_id}&avatar_id={role_id}',
                cookie = cookie_info.cookie,
            ),
            params = {
                "region":       server_id,
                "uid":          uid,
                "avatar_id":    role_id
            },
        )
    elif mode == 'month_info':
        headers = {
            'Host':                     'act-hk4e-api.mihoyo.com',
            'Cookie':                   cookie_info.cookie,
            'origin':                   'https://webstatic.mihoyo.com',
            'referer':                  'https://webstatic.mihoyo.com/',
            'x-requested-with':         'com.mihoyo.hyperion',
            'user-agent':               f'Mozilla/5.0 (Linux; Android 12; V2309A Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/110.0.5481.154 Safari/537.36 miHoYoBBS/{BBS_VERSION}'
        }
        data = await aiorequests.get(
            url = MONTH_INFO_API,
            headers = headers,
            params = {
                "month":                    month,
                "bind_uid":                 uid,
                "bind_region":              server_id
            },
        )
    elif mode == 'daily_note':
        headers = mihoyo_headers(
            q=f'role_id={uid}&server={server_id}', cookie=cookie_info.stoken
        )
        data = await aiorequests.get(
            url = WIDGET_URL,
            headers = headers,
            params = {
                "server":   server_id,
                "role_id":  uid
            },
        )
    elif mode == 'sign_info':
        data = await aiorequests.get(
            url=SIGN_INFO_API,
            headers = {
                'Cookie':           cookie_info.cookie,
                'x-rpc-signgame':   'hk4e',
                'x-Requested-With': 'com.mihoyo.hyperion',
                'Origin':           'https://act.mihoyo.com',
                'Referer':          'https://act.mihoyo.com/',
                'User-Agent':       'Mozilla/5.0 (Linux; Android 12; V2309A Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/110.0.5481.154 Safari/537.36 miHoYoBBS/2.99.1',
            },
            params = {
                'lang':         'zh-cn',
                'act_id':       'e202311201442471',
                'region':       server_id,
                'uid':          uid
            },
        )
    elif mode == 'sign_action':
        data = await aiorequests.post(
            url = SIGN_ACTION_API,
            headers = mihoyo_sign_headers(cookie_info.cookie),
            json = {
                'act_id':       'e202009291139501',
                'uid':          uid,
                'region':       server_id
            },
        )
    else:
        data = None
    data = data.json() if data else {'retcode': 999}
    nb_logger.debug(data)
    if await check_retcode(data, cookie_info, user_id, uid):
        return data
    else:
        return f'你的UID{uid}的cookie疑似失效了'


async def get_sign_reward_list() -> dict:
    headers = {
        'x-rpc-app_version':        BBS_VERSION,
        'x-rpc-signgame':           'hk4e',
        'User-Agent':               'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.99.1',
        'Referer':                  'https://act.mihoyo.com/'
    }
    resp = await aiorequests.get(
        url = SIGN_REWARD_API,
        headers = headers,
        params = {
            'act_id': 'e202311201442471'
        }
    )
    data = resp.json()
    nb_logger.debug(data)
    return data


async def get_stoken_by_login_ticket(login_ticket: str, mys_id: str) -> Optional[str]:
    with contextlib.suppress(Exception):
        data = await aiorequests.get(
            STOKEN_API,
            headers={
                'x-rpc-app_version':    BBS_VERSION,
                'User-Agent':           'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.60.1',
                'x-rpc-client_type':    '5',
                'Referer':              'https://webstatic.mihoyo.com/',
                'Origin':               'https://webstatic.mihoyo.com',
            },
            params = {
                'token_types':      '3',
                'login_ticket':     login_ticket,
                'uid':              mys_id
            },
        )
        data = data.json()
        return data['data']['list'][0]['token']
    return None


async def get_cookie_token_by_stoken(stoken: str, mys_id: str) -> Optional[str]:
    with contextlib.suppress(Exception):
        data = await aiorequests.get(
            COOKIE_TOKEN_API,
            headers = {
                'x-rpc-app_version':        BBS_VERSION,
                'User-Agent':               'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.60.1',
                'x-rpc-client_type':        '5',
                'Referer':                  'https://webstatic.mihoyo.com/',
                'Origin':                   'https://webstatic.mihoyo.com',
                'Cookie':                   f'stuid={mys_id};stoken={stoken}',
            },
            params = {
                'uid':      mys_id,
                'stoken':   stoken
            },
        )
        data = data.json()
        return data['data']['cookie_token']
    return None


async def get_authkey_by_stoken(
        user_id: str, uid: str
) -> Tuple[Optional[str], bool, Optional[PrivateCookie]]:
    """
    根据stoken获取authkey

    :param user_id: 用户id
    :param uid: 原神uid
    :return: authkey
    """
    server_id = 'cn_qd01' if uid[0] == '5' else 'cn_gf01'
    cookie_info = await get_cookie(user_id, uid, True, True)
    device_info = await get_device_info(user_id)
    if not cookie_info:
        return (
            '未绑定私人cookie，绑定方法二选一：\n1.通过米游社扫码绑定：\n请发送指令[原神扫码绑定]\n2.获取cookie的教程：\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1\n获取后，使用[ysb cookie]指令绑定'
            + (f'或前往{config.CookieWeb_url}网页添加绑定' if config.CookieWeb_enable else ''),
            False,
            cookie_info,
        )
    if not cookie_info.stoken:
        return 'cookie中没有stoken字段，请重新绑定', False, cookie_info

    headers = {
        "Cookie":                       cookie_info.stoken,
        "DS":                           get_old_version_ds(True),
        "User-Agent":                   "okhttp/4.8.0",
        "x-rpc-app_version":            BBS_VERSION,
        "x-rpc-sys_version":            "12",
        "x-rpc-client_type":            "5",
        "x-rpc-channel":                "mihoyo",
        "x-rpc-device_id":              device_info.device_id,
        "x-rpc-device_name":            device_info.device_name,
        "x-rpc-device_model":           device_info.device_model,
        "Referer":                      "https://app.mihoyo.com",
        "Host":                         "api-takumi.mihoyo.com",
    }
    data = await aiorequests.post(
        url = AUTHKEY_API,
        headers = headers,
        json = {
            'auth_appid':       'webview_gacha',
            'game_biz':         'hk4e_cn',
            'game_uid':         uid,
            'region':           server_id,
        },
    )
    data = data.json()
    if data.get('data') is not None and 'authkey' in data['data']:
        return data['data']['authkey'], True, cookie_info
    else:
        return None, False, cookie_info


async def get_enka_data(uid: str):
    urls = [
        'https://enka.network/api/uid/{uid}',
        'https://profile.microgg.cn/api/uid/{uid}',  # 以下两个api由小灰灰提供
        'https://enka.microgg.cn/api/uid/{uid}',
    ]
    for url in urls:
        with contextlib.suppress(Exception):
            resp = await aiorequests.get(
                url = url.format(uid=uid),
                headers = {
                    'User-Agent': 'LittlePaimon/3.0'
                },
                follow_redirects = True,
            )
            data = resp.json()
            nb_logger.debug(data)
            if 'playerInfo' in data:
                return data
