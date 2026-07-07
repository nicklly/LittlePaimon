import asyncio
import string
import hashlib
import time
import random
import json
from pathlib import Path
from typing import Optional, Union

from LittlePaimon.database import Devices
from LittlePaimon.utils.files import load_yaml
from LittlePaimon.utils.logger import logger
from LittlePaimon.utils.requests import aiorequests

# 验证码
BBS_VERSION = '2.109.0'
RECORD_CAPTCHA = 'https://api-takumi-record.mihoyo.com/game_record/app/card/wapi/createVerification?is_high=true'
RECORD_CAPTCHA_VERIFY = 'https://api-takumi-record.mihoyo.com/game_record/app/card/wapi/verifyVerification'
BBS_CAPTCHA = 'https://bbs-api.miyoushe.com/misc/api/createVerification?is_high=true'
BBS_CAPTCHA_VERIFY = 'https://bbs-api.miyoushe.com/misc/api/verifyVerification'

rr = load_yaml(Path() / 'config' / 'rrocr.yml')

def md5(text: str) -> str:
    """
    md5加密
    :param text: 文本
    :return: md5加密后的文本
    """
    md5_ = hashlib.md5()
    md5_.update(text.encode())
    return md5_.hexdigest()

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


def record_captcha(ds: str, cookie_info: str, devices: Devices) -> dict:
    return {
        'DS':                       ds,
        'cookie':                   cookie_info,
        'Referer':                  'https://webstatic.mihoyo.com',
        'x-rpc-client_type':        '5',
        'x-rpc-challenge_game':     '2',
        'x-rpc-challenge_path':     'https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/index',
        'x-rpc-app_version':        BBS_VERSION,
        'x-rpc-device_fp':          devices.device_fp,
        'x-rpc-device_id':          devices.device_id,
        'User-Agent':               f'Mozilla/5.0 (Linux; Android 15) Mobile miHoYoBBS/{BBS_VERSION}',
    }

def bbs_captcha(cookie_info: str, devices: Devices) -> dict:
    return {
        'DS':                                   get_old_version_ds(web=False),
        'cookie':                               cookie_info,
        'x-rpc-client_type':                    '2',
        'x-rpc-app_version':                    BBS_VERSION,
        'x-rpc-sys_version':                    '12',
        'x-rpc-channel':                        'miyousheluodi',
        'x-rpc-device_id':                      devices.device_id,
        'x-rpc-device_name':                    devices.device_name,
        'x-rpc-device_model':                   devices.device_model,
        'x-rpc-h265_supported':                 '1',
        'Referer':                              'https://app.mihoyo.com',
        'Content-Type':                         'application/json; charset=UTF-8',
        'Host':                                 'bbs-api.miyoushe.com',
        'x-rpc-verify_key':                     'bll8iq97cem8',
        'x-rpc-csm_source':                     'discussion',
        'User-Agent':                           'okhttp/4.9.3',
    }

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

class rrocr:

    def __init__(self, user_id: Optional[str] = ''):
        self.user_id = user_id
    # 打码狗


    async def dmg_ocr(self, gt: str, challenge: str):
        params: dict = {
            "userkey": rr.get('dmg_apikey'),
            "gt": gt,
            "challenge": challenge,
            "isJson": "2",
            "success": '0'
        }
        data = await aiorequests.get(rr.get('dmg_api'), params=params, timeout=60)
        data = data.json()
        if data['status'] == '0':
            return data['data']
        return 'j'
    # 小灰灰打码
    async def microgg_ocr(self, gt: str, challenge: str):
        """
        :param gt: gt码
        :param challenge: challenge码
        :return: 返回validate
        """
        try:
            params = {
                'token': rr.get('microgg_key'),
                'gt': gt,
                'challenge': challenge
            }
            response = await aiorequests.post(rr.get('microgg_api'), params=params, timeout=60)
        except Exception as e:
            logger.info('小灰灰打码验证', '➤➤➤', {}, f'请求小灰灰打码api失败 {e}', False)
            return "j"
        data = response.json()
        if response.status_code == 200:
            if data['code'] == 0:
                if data['info'] == 'success':
                    logger.info('小灰灰打码验证', '➤➤➤', {}, '请求 validate 成功', True)
                    return data['data']['validate']
                else:
                    logger.info('小灰灰打码验证', '➤➤➤', {}, '请求 validate 失败', False)
                    return 'j'
            else:
                return None
        else:
            return None
    # 套套打码
    async def tt_ocr(self, gt: str, challenge: str, referer: str):
        """
        :param gt: gt码
        :param challenge: challenge码
        :param referer: 引用链接
        :return: 返回validate
        """
        params = {
            "appkey": rr.get('tt_apikey'),
            "gt": gt,
            'challenge': challenge,
            'referer': referer,
            'itemid': 388
        }
        try:
            response = await aiorequests.post(rr.get('tt_api'), data=params, timeout=60)
            data = response.json()
        except Exception as e:
            logger.info('套套打码验证', '➤➤➤', {}, f'请求套套打码api失败 {e}', False)
            return "j"
        if data['status'] != 1:
            logger.info('套套打码验证', '➤➤➤', {}, '获取 validate 失败', False)
            return "j"

        result_id = data['resultid']
        logger.info('套套打码验证', '➤➤➤ 获取resultID成功，等待10s获取识别结果', {}, '', False)
        await asyncio.sleep(10)

        for i in range(4):
            try:
                req = await aiorequests.post(rr.get('tt_result_api'), params={
                    "appkey": rr.get('tt_apikey'),
                    "resultid": result_id,
                }, timeout=60)
            except Exception as e:
                logger.info('套套打码验证', '➤➤➤', {}, f'请求套套打码api失败 {e}', False)
                await asyncio.sleep(1.5)
                continue
            if req.status_code == 200:
                if "msg" in req.json() and req.json()['msg'] == '等待识别结果':
                    await asyncio.sleep(1.5)
                    continue
                break
            else:
                logger.info(
                "套套打码", info="➤➤", result="请求失败,可能是网络原因", result_type=False
                )
            return "j"
        res = req.json()
        # 失败返回'j' 成功返回validate
        if "data" in res and "validate" in res["data"]:
            validate = res["data"]["validate"]
            return validate
        else:
            return None

    async def get_validate(self, gt: str, challenge: str, referer: Optional[str] = ''):
        if rr.get('choose_ocr') == 'tt':
            return await self.tt_ocr(gt, challenge, referer)
        elif rr.get('choose_ocr') == 'xhh':
            return await self.microgg_ocr(gt, challenge)
        elif rr.get('choose_ocr') == 'dmg':
            return await self.dmg_ocr(gt, challenge)
        else:
            return None


    async def get_pass_challenge(self, cookie_info, user_id: str, mode: Optional[str] = 'bbs'):
        """
        :param ds:
        :param cookie_info: cookie信息
        :param mode: 验证类型
        :return:
        """
        from LittlePaimon.utils.api import get_device_info
        devices = await get_device_info(user_id)
        headers = (
            record_captcha(get_ds_x4('is_high=true', ''), cookie_info, devices = devices)
            if mode == 'game' else
            bbs_captcha(cookie_info, devices =  devices)
        )
        req = await aiorequests.get(
            url = RECORD_CAPTCHA if mode == 'game' else BBS_CAPTCHA,
            headers = headers
        )
        data = req.json()
        if data['retcode'] != 0:
            return None
        validate = await self.get_validate(
            data['data']['gt'],
            data['data']['challenge'],
            ''
        )
        if validate != 'j':
            if rr.get('choose_ocr') == 'dmg':
                result = validate.split('|')
                challenge = result[0]
                validate = result[1]
            else:
                challenge = data['data']['challenge']
            params = {
                "geetest_challenge":    challenge,
                "geetest_seccode":      f"{validate}|jordan",
                "geetest_validate":     validate,
            }
            headers2 = (
                record_captcha(ds = get_ds_x4('',params), cookie_info = cookie_info, devices = devices)
                if mode == 'game' else
                bbs_captcha(cookie_info, devices = devices)
            )
            check_req = await aiorequests.post(
                url = RECORD_CAPTCHA_VERIFY if mode == 'game' else BBS_CAPTCHA_VERIFY,
                headers = headers2,
                params = params,
            )
            check = check_req.json()
            if check["retcode"] == 0:
                return check["data"]["challenge"]
        return None
