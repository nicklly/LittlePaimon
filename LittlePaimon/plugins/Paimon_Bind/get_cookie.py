# main code from lulu: https://github.com/lulu666lulu
import asyncio
import contextlib
import datetime
import json
import random
import time
import base64
from hashlib import md5
from io import BytesIO
from string import ascii_letters
from string import digits
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from nonebot import on_command, get_bot, get_app
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, MessageEvent, GroupMessageEvent
from LittlePaimon.config import config
from LittlePaimon.database.models import PrivateCookie, LastQuery, Devices
from LittlePaimon.utils import NICKNAME, logger
from LittlePaimon.utils.qrcode import generate_qrcode
from LittlePaimon.utils.requests import aiorequests
from LittlePaimon.utils.scheduler import scheduler
from LittlePaimon.utils.api import login_permission_headers, check_qrcode_status, SCAN_STATUS_API, \
    CONFIRM_STATUS_API, get_Fp
from LittlePaimon.utils.passport import (
    build_cookie,
    filter_genshin_roles,
    get_cookie_token_by_stoken,
    get_game_roles_by_stoken,
    get_ltoken_by_stoken,
)
from LittlePaimon.utils.message import fullmatch_rule
from LittlePaimon.utils.devices import DeviceProvider

device_id = "".join(random.choices((ascii_letters + digits), k=64))


bind_tips = '绑定方法二选一：\n1.通过米游社扫码绑定：\n请发送指令[原神扫码绑定]\n2.通过Cookie绑定：获取教程\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1\n获取后，使用[ysb cookie]指令绑定'
bind_tips_web = '绑定方法二选一：\n1.通过米游社扫码绑定：\n请发送指令[原神扫码绑定]\n2.通过Cookie绑定：获取教程\ndocs.qq.com/doc/DQ3JLWk1vQVllZ2Z1\n获取后，使用[ysb cookie]指令绑定或前往{cookie_web_url}网页添加绑定'

running_login_data = {}

def md5_(self) -> str:
    return md5(self.encode()).hexdigest()

async def create_login_data():
    headers = login_permission_headers()
    headers.update({
        'x-rpc-client_type':    '3',
        # 'x-rpc-app_id':         'ddxf5dufpuyo'
    })
    res = await aiorequests.post(
        url = 'https://passport-api.mihoyo.com/account/ma-cn-passport/app/createQRLogin',
        headers = headers
    )
    result = res.json()
    url = result['data']['url']
    ticket = result['data']['ticket']
    return {
        'ticket': ticket,
        'url':    url
    }

async def create_extra_login_data():

    res = await aiorequests.post(
        url = 'https://passport-api.mihoyo.com/account/ma-cn-passport/web/createQRLogin',
        headers = login_permission_headers()
    )
    result = res.json()
    url = result['data']['url']
    ticket = result['data']['ticket']
    return {
        'ticket': ticket,
        'url':    url
    }


async def check_login(login_data: dict):
    headers = login_permission_headers()
    headers.update({
        'x-rpc-client_type':    '3',
        'x-rpc-app_id':         'ddxf5dufpuyo'
    })
    res = await aiorequests.post(
        url = 'https://passport-api.mihoyo.com/account/ma-cn-passport/app/queryQRLoginStatus',
        headers = headers,
        json = {
            'ticket': login_data['ticket']
        }
    )
    return res

async def get_extra_cookie(tickets: str):

    res = await aiorequests.post(
        url = 'https://passport-api.mihoyo.com/account/ma-cn-passport/web/queryQRLoginStatus',
        headers = login_permission_headers(),
        json = {
            'ticket': tickets
        }
    )
    result = res.json()
    for i in range(3):
        if result['retcode'] == 0:
            if result['data']['status'] == 'Confirmed':
                cookies = dict(res.cookies)
                cookies.pop('aliyungf_tc', None)
                return '; '.join(f'{k}={v}' for k, v in cookies.items())
    return None

qrcode_bind = on_command('原神扫码绑定', aliases={'原神扫码登录', '原神扫码登陆'}, priority=1, block=True,
                         rule=fullmatch_rule,
                         state={
                             'pm_name':        '原神扫码绑定',
                             'pm_description': '通过米游社扫码的方式绑定原神Cookie',
                             'pm_usage':       '原神扫码绑定',
                             'pm_priority':    1
                         })


@qrcode_bind.handle()
async def _(event: MessageEvent):  # sourcery skip: use-fstring-for-concatenation

    from LittlePaimon.utils.api import get_device_info

    devices = await get_device_info(str(event.user_id))
    if devices is not None:
        logger.warning('原神扫码绑定', f'{event.user_id}已有绑定信息，正在移除....,移除后开始新一轮信息绑定')
        await devices.delete()
    if str(event.user_id) in running_login_data:
        await qrcode_bind.finish('你已经在绑定中了，请扫描上一次的二维码')
    login_data = await create_login_data()
    running_login_data[str(event.user_id)] = login_data
    img_b64 = generate_qrcode(url=login_data['url'], icon_scale=0.15)
    running_login_data[str(event.user_id)]['img_b64'] = img_b64
    img = f'二维码链接：{config.CookieWeb_url}/qrcode?user_id={event.user_id}' if config.qrcode_bind_use_url else MessageSegment.image(img_b64)
    msg_data = await qrcode_bind.send(
        img + f'\n请在3分钟内使用米游社扫码并确认进行绑定。\n注意：1.扫码即代表你同意将Cookie信息授权给{NICKNAME}\n2.扫码时会提示登录原神，实际不会把你顶掉原神\n3.其他人请不要乱扫，否则会将你的账号绑到TA身上！',
        at_sender=True)
    running_login_data[str(event.user_id)]['msg_id'] = msg_data['message_id']
    if isinstance(event, GroupMessageEvent):
        running_login_data[str(event.user_id)]['group_id'] = event.group_id
    elif event.message_type == 'guild':
        running_login_data[str(event.user_id)]['guild_id'] = event.guild_id
        running_login_data[str(event.user_id)]['channel_id'] = event.channel_id
    running_login_data[str(event.user_id)]['bot_id'] = event.self_id
    running_login_data[str(event.user_id)]['nickname'] = event.sender.card or event.sender.nickname


@scheduler.scheduled_job('cron', second='*/10', misfire_grace_time=10)
async def check_qrcode():
    with contextlib.suppress(RuntimeError):
        for user_id, data in running_login_data.items():
            send_msg = None
            result = await check_login(data)
            status_data = result.json()

            if status_data['retcode'] != 0:
                send_msg = status_data['message']
                running_login_data.pop(user_id)
            elif status_data['data']['status'] == 'Scanned':
                logger.info('原神扫码绑定','➤➤ 已扫码，请在手机端确认登录...')
            elif status_data['data']['status'] == 'Confirmed':
                logger.info('原神扫码绑定','➤➤ 扫码成功，正在获取相关数据')
                game_token = status_data['data']
                running_login_data.pop(user_id)

                tokens = game_token.get('tokens') or []
                stoken_token = next(
                    (token for token in tokens if int(token.get('token_type') or 0) == 1),
                    tokens[0] if tokens else {},
                )
                stoken_value = stoken_token.get('token', '')
                aid = str(game_token['user_info']['aid'])
                mid = str(game_token['user_info']['mid'])
                stoken = f'stoken={stoken_value};stuid={aid};mid={mid};'

                cookie_token, cookie_token_err = await get_cookie_token_by_stoken(stoken_value, aid, mid)
                if not cookie_token:
                    send_msg = f'获取CookieToken失败：{cookie_token_err}'
                else:
                    ltoken, ltoken_err = await get_ltoken_by_stoken(stoken_value, aid, mid)
                    if not ltoken:
                        logger.warning('原神扫码绑定', f'➤➤ 获取LToken失败：{ltoken_err}')

                    auth_cookie = f"stoken={stoken_value};mid={mid};"
                    result = await create_extra_login_data()
                    scan_result = await check_qrcode_status(SCAN_STATUS_API, result['ticket'], auth_cookie)
                    confirm_result = await check_qrcode_status(CONFIRM_STATUS_API, result['ticket'], auth_cookie)

                    if None in (scan_result, confirm_result):
                        logger.warning('原神扫码绑定','➤➤','请求被拒绝')

                    extra_cookie = await get_extra_cookie(result['ticket'])

                    roles, roles_err = await get_game_roles_by_stoken(stoken_value, aid, mid)
                    if roles is None:
                        send_msg = f'获取游戏角色失败：{roles_err}'
                    elif not roles:
                        send_msg = '该账号尚未绑定任何游戏，请确认扫码的账号无误'
                    else:
                        genshin_games = filter_genshin_roles(roles)
                        if not genshin_games:
                            send_msg = '该账号尚未绑定原神，请确认扫码的账号无误'
                        else:
                            cookie = build_cookie(aid, mid, cookie_token, ltoken)
                            send_msg = '成功绑定原神账号：'
                            for info in genshin_games:
                                send_msg += f'{info["nickname"]}({info["uid"]}) '
                                devices = DeviceProvider()
                                fingerprint = await get_Fp(info['uid'])

                                await Devices.update_or_create(
                                    user_id = user_id,
                                    uid = info['uid'],
                                    device_id = devices.device_id(),
                                    device_name = devices.select_variant(info['uid']).DeviceName,
                                    device_model = devices.select_variant(info['uid']).DeviceModel,
                                    device_fp = fingerprint,
                                )
                                await PrivateCookie.update_or_create(
                                    user_id = user_id,
                                    uid = info['uid'],
                                    mys_id = aid,
                                    defaults = {
                                        'cookie': cookie,
                                        'stoken': stoken,
                                        'extra_cookie': extra_cookie
                                    }
                                )
                            send_msg = send_msg.strip()
                            await LastQuery.update_or_create(
                                user_id = user_id,
                                defaults = {
                                    'uid':       genshin_games[0]['uid'],
                                    'last_time': datetime.datetime.now()
                                }
                            )
            if send_msg:
                bot: Bot = get_bot(str(data['bot_id']))
                if 'group_id' in data:
                    await bot.send_group_msg(group_id=data['group_id'],
                                             message=MessageSegment.reply(data['msg_id']) + MessageSegment.at(
                                                 int(user_id)) + send_msg)
                elif 'guild_id' in data:
                    await bot.send_guild_channel_msg(guild_id=data['guild_id'], channel_id=data['channel_id'],
                                                     message=MessageSegment.at(int(user_id)) + send_msg)
                else:
                    await bot.send_private_msg(user_id=int(user_id),
                                               message=MessageSegment.reply(data['msg_id']) + send_msg)
            if not running_login_data:
                break
            await asyncio.sleep(1)


app: FastAPI = get_app()


@app.get('/LittlePaimon/cookie/qrcode')
async def qrcode_img_url(user_id: str):
    if not config.qrcode_bind_use_url:
        return {'status': 'error', 'msg': '请在QQ内查看二维码'}
    if user_id not in running_login_data:
        return {'status': 'error', 'msg': '二维码不存在'}
    img_base64 = running_login_data[user_id]['img_b64'].lstrip('base64://')
    return StreamingResponse(BytesIO(base64.b64decode(img_base64)), media_type='image/png')
