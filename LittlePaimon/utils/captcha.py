import asyncio
import string
import hashlib
import time
import random
from pathlib import Path
from typing import Optional

from LittlePaimon.utils.files import load_yaml
from LittlePaimon.utils.logger import logger

from LittlePaimon.utils.requests import aiorequests

# 验证码
BBS_VERSION = '2.90.1'
BBS_CAPATCH = 'https://api-takumi-record.mihoyo.com/game_record/app/card/wapi/createVerification?is_high=true'
    # "https://bbs-api.mihoyo.com/misc/api/createVerification?is_high=true"
BBS_CAPTCHA_VERIFY = 'https://api-takumi-record.mihoyo.com/game_record/app/card/wapi/verifyVerification'
    # https://bbs-api.mihoyo.com/misc/api/verifyVerification"
rr = load_yaml(Path() / 'config' / 'rrocr.yml')


captcha_headers = {
    'Host':                     'api-takumi-record.mihoyo.com',
    'Origin':                   'https://webstatic.mihoyo.com',
    'Referer':                  'https://webstatic.mihoyo.com/',
    'User-Agent':               f'Mozilla/5.0 (Linux; Android 13; Pixel 5 Build/TQ3A.230901.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/118.0.0.0 Mobile Safari/537.36 miHoYoBBS/{BBS_VERSION}',
    'x-rpc-challenge_game':     '2',
    'x-rpc-app_version':        f'{BBS_VERSION}',
    'x-rpc-device_fp':          '38d819850c101',
    'x-rpc-device_type':        '5',
    'x-rpc-tool_verison':       'v6.6.1-gr-cn',
    'x-rpc-page':               'v6.6.1-gr-cn_#/ys',
    'x-rpc-sys_version':        ''

}

def md5(text: str) -> str:
    """
    md5加密
    :param text: 文本
    :return: md5加密后的文本
    """
    md5_ = hashlib.md5()
    md5_.update(text.encode())
    return md5_.hexdigest()

def get_old_version_ds(web: bool = False) -> str:
    """
    生成米游社旧版本headers的ds_token
    """
    if web:
        s = 'G1ktdwFL4IyGkHuuWSmz0wUe9Db9scyK'
    else:
        s = 'idMMaGYmVgPzh3wxmWudUXKUPGidO7GM'
    t = str(int(time.time()))
    r = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
    c = md5(f"salt={s}&t={t}&r={r}")
    return f"{t},{r},{c}"


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

    def __init__(self, user_id: Optional[str] = '', uid: Optional[str] = ''):
        self.uid = uid
        self.user_id = user_id

    async def microgg_ocr(self, gt: str, challenge: str):
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

    async def tt_ocr(self, gt: str, challenge: str, referer: str):
        """

        :param gt: gt码
        :param challenge: challenge码
        :param referer: 引用链接
        :return: 返回vaildate
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

    async def get_validate(self, gt: str, challenge: str, referer: str):
        if rr.get('choose_ocr') == 'tt':
            return await self.tt_ocr(gt, challenge, referer)
        # elif rr.get('choose_ocr') == 'rr':
        #     return await self.rr_ocr(gt, challenge, referer)
        elif rr.get('choose_ocr') == 'xhh':
            return await self.microgg_ocr(gt, challenge)

    async def get_pass_challenge(self, cookie_info):
        """

        :param cookie_info: cookie信息
        :return:
        """
        req = await aiorequests.get(
            url = BBS_CAPATCH,
            headers = captcha_headers.update({
                'cookie':                   cookie_info,
                'x-rpc-device_id':          'FF8F93BE-8791-4263-AA15-F96A60CA22F6',
            })
        )
        data = req.json()
        if data['retcode'] != 0:
            return None
        validate = await self.get_validate(
            data['data']['gt'],
            data['data']['challenge'],
            "https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html?bbs_auth_required=true&act_id"
            "=e202009291139501&utm_source=bbs&utm_medium=mys&utm_campaign=icon"
        )
        if validate != 'j':
            check_req = await aiorequests.post(
                url=BBS_CAPTCHA_VERIFY,
                headers = captcha_headers.update({
                    'cookie':                   cookie_info,
                    'x-rpc-device_id':          'FF8F93BE-8791-4263-AA15-F96A60CA22F6',
                }),
                params = {
                    "geetest_challenge": data["data"]["challenge"],
                    "geetest_seccode": f"{validate}|jordan",
                    "geetest_validate": validate,
                },
            )
            check = check_req.json()
            if check["retcode"] == 0:
                return check["data"]["challenge"]
        return None
