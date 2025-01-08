import asyncio
import string
import hashlib
import time
import random
from pathlib import Path

from LittlePaimon.utils.files import load_yaml
from LittlePaimon.utils.logger import logger

from LittlePaimon.utils.requests import aiorequests

# 验证码
BBS_CAPATCH = (
    "https://bbs-api.mihoyo.com/misc/api/createVerification?is_high=true"
)
BBS_CAPTCHA_VERIFY = (
    "https://bbs-api.mihoyo.com/misc/api/verifyVerification"
)
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


def get_old_version_ds(mhy_bbs: bool = False) -> str:
    """
    生成米游社旧版本headers的ds_token
    """
    if mhy_bbs:
        s = 'N50pqm7FSy2AkFz2B3TqtuZMJ5TOl3Ep'
    else:
        s = 'z8DRIUjNDT7IT5IZXvrUAxyupA1peND9'
    t = str(int(time.time()))
    r = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
    c = md5(f"salt={s}&t={t}&r={r}")
    return f"{t},{r},{c}"


def random_text(length: int) -> str:
    """
    生成指定长度的随机字符串

    :param length: 长度
    :return: 随机字符串
    """
    return ''.join(random.sample(string.ascii_lowercase + string.digits, length))


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

    def __init__(self, user_id: str, uid: str):
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

    async def rr_ocr(self, gt: str, challenge: str, referer: str):
        """

        :param gt: gt码
        :param challenge: challenge码
        :param referer: 引用链接
        :return: 返回vaildate
        """
        logger.info('人人打码验证', '➤➤➤', {}, '正在尝试过码', False)
        params = {
            'appkey': rr.get("rr_apikey"),
            "gt": gt,
            'challenge': challenge,
            'referer': referer
        }
        try:
            response = await aiorequests.post(rr.get('rr_api'), params=params, timeout=60)
            data = response.json()
            if data['status'] != 0:
                logger.info('人人打码验证', '➤➤➤', {}, '获取 validate 失败', False)
                return None
            validate = data['data']['validate']
            logger.info('人人打码验证', '➤➤➤获取 validate 成功')
            return validate
        except Exception as e:
            return "j"

    async def get_validate(self, gt: str, challenge: str, referer: str):
        if rr.get('choose_ocr') == 'tt':
            return await self.tt_ocr(gt, challenge, referer)
        elif rr.get('choose_ocr') == 'rr':
            return await self.rr_ocr(gt, challenge, referer)
        elif rr.get('choose_ocr') == 'xhh':
            return await self.microgg_ocr(gt, challenge)

    async def get_pass_challenge(self, cookie_info):
        """

        :param cookie_info: cookie信息
        :return:
        """
        headers = {
            "DS": get_old_version_ds(mhy_bbs=False),
            "cookie": cookie_info.stoken,
            "x-rpc-client_type": "2",
            "x-rpc-app_version": "2.11.1",
            "x-rpc-sys_version": "12",
            "x-rpc-channel": "miyousheluodi",
            "x-rpc-device_id": random_hex(32),
            "x-rpc-device_name": "Honor Magic3",
            "x-rpc-device_model": "ELZ-AN00",
            "Referer": "https://app.mihoyo.com",
            "Host": "bbs-api.mihoyo.com",
            "User-Agent": "okhttp/4.8.0",
        }
        req = await aiorequests.get(url=BBS_CAPATCH, headers=headers)
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
                headers=headers,
                params={
                    "geetest_challenge": data["data"]["challenge"],
                    "geetest_seccode": f"{validate}|jordan",
                    "geetest_validate": validate,
                },
            )
            check = check_req.json()
            if check["retcode"] == 0:
                return check["data"]["challenge"]
        return None
