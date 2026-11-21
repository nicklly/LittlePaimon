from __future__ import annotations

import json
import random
import re
import time
from hashlib import md5
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from LittlePaimon.utils.api import BBS_VERSION as CN_VERSION, SALTS
from LittlePaimon.utils.requests import aiorequests

PASSPORT_EXCHANGE_API = 'https://passport-api.mihoyo.com/account/ma-cn-session/app/exchange'
GAME_ROLES_BY_STOKEN_API = 'https://api-takumi.miyoushe.com/binding/api/getUserGameRolesByStoken'

LIFECYCLE_ID = str(uuid4())
DEVICE_ID_36 = str(uuid4())

TOKEN_STOKEN = 1
TOKEN_LTOKEN = 2
TOKEN_COOKIE_TOKEN = 4

_RANDOM_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789'


class SaltType:

    PROD = 'PROD'
    X4 = 'X4'
    X6 = 'X6'
    K2 = 'K2'
    LK2 = 'LK2'
    PASSPORT = 'Passport'


def _random_r(include_chars: bool) -> str:
    """Hutao DataSignOptions：r 为 6 位小写字母+数字或 6 位数字。"""
    if include_chars:
        return ''.join(random.choices(_RANDOM_CHARS, k=6))
    value = random.randint(100000, 199999)
    # Hutao 对 100000 做了特殊替换
    return '642367' if value == 100000 else str(value)


def generate_ds(
    salt: str,
    *,
    body: str = '',
    query: str = '',
    include_chars: bool = True,
    gen: int = 2,
) -> str:
    """生成 DS 头。

    :param salt: salt 值（见 ``SALTS``）
    :param body: 请求体原文，必须与实际发送的 body 完全一致
    :param query: 已排序的查询串（``k=v&k2=v2``）
    :param include_chars: r 是否包含字母
    :param gen: 1 = 仅 salt/t/r；2 = 追加 b/q
    """
    timestamp = int(time.time())
    r = _random_r(include_chars)
    if gen >= 2:
        content = f'salt={salt}&t={timestamp}&r={r}&b={body}&q={query}'
    else:
        content = f'salt={salt}&t={timestamp}&r={r}'
    return f'{timestamp},{r},{md5(content.encode("utf-8")).hexdigest()}'


def serialize_body(data: Any) -> str:
    """
    服务端校验的是实际收到的 body，因此这里生成的字符串必须直接作为请求体发送。
    """
    text = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return (
        text.replace('<', '\\u003c')
        .replace('>', '\\u003e')
        .replace('&', '\\u0026')
        .replace('=', '\\u003d')
        .replace("'", '\\u0027')
    )


def extract_mid(value: str) -> Optional[str]:
    """从 Cookie / stoken 字符串中提取 mid（兼容 stmid / ltmid_v2 等键名）。"""
    if not value:
        return None
    match = re.search(
        r'(?:^|[;,\s])(?:mid|stmid|ltmid|ltmid_v2|account_mid|account_mid_v2|login_mid)=([0-9a-zA-Z]+)',
        value,
    )
    return match.group(1) if match else None


def _passport_headers(ds: str, device_fp: Optional[str] = None) -> Dict[str, str]:

    headers = {
        'DS': ds,
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'User-Agent': f'Mozilla/5.0 (Linux; Android 12) Mobile miHoYoBBS/{CN_VERSION}',
        'x-rpc-app_id': 'bll8iq97cem8',
        'x-rpc-app_version': CN_VERSION,
        'x-rpc-client_type': '2',
        'x-rpc-device_id': DEVICE_ID_36,
        'x-rpc-device_name': '',
        'x-rpc-game_biz': 'bbs_cn',
        'x-rpc-sdk_version': '2.44.0',
        'x-rpc-account_version': '2.44.0',
        'x-rpc-sys_version': '12',
        'x-rpc-lifecycle_id': LIFECYCLE_ID,
    }
    if device_fp:
        headers['x-rpc-device_fp'] = device_fp
    return headers


async def exchange_token(
    stoken: str,
    aid: str,
    destination: int,
    mid: Optional[str] = None,
    *,
    device_fp: Optional[str] = None,
) -> Tuple[Optional[str], str]:
    """SToken 换取指定类型的 token。

    :param stoken:
    :param mid: 账号 mid；为空时尝试从 ``stoken`` 字符串中提取
    :return: ``(token, error_message)``，成功时 error_message 为空串
    """
    mid = mid or extract_mid(stoken)
    if not stoken or not mid or not aid:
        return None, 'stoken / mid / aid 不能为空'

    payload = {
        'dst_token_type': destination,
        'src_token': {'token': stoken, 'token_type': TOKEN_STOKEN},
        'mid': mid,
    }
    body = serialize_body(payload)
    ds = generate_ds(SALTS[SaltType.PASSPORT], body=body, include_chars=True, gen=2)

    try:
        response = await aiorequests.post(
            PASSPORT_EXCHANGE_API,
            headers=_passport_headers(ds, device_fp),
            data=body,
        )
        result = response.json()
    except Exception as exc:  # 网络异常/非 JSON
        return None, f'请求失败: {exc}'

    if result.get('retcode') != 0:
        message = result.get('message') or '请求失败'
        return None, f'{message} (retcode={result.get("retcode")})'

    data = result.get('data') or {}
    token = (data.get('token') or {}).get('token')
    token_type = (data.get('token') or {}).get('token_type')
    user_info = data.get('user_info') or {}
    returned_aid = str(user_info.get('aid') or user_info.get('uid') or '')

    if not token:
        return None, '响应中没有 token'
    if token_type is not None and int(token_type) != destination:
        return None, f'token_type 不匹配: {token_type}'
    if returned_aid and returned_aid != str(aid):
        return None, f'账号不匹配: {returned_aid} != {aid}'

    return str(token), ''


async def get_ltoken_by_stoken(
    stoken: str,
    aid: str,
    mid: Optional[str] = None,
    *,
    device_fp: Optional[str] = None,
) -> Tuple[Optional[str], str]:
    return await exchange_token(stoken, aid, TOKEN_LTOKEN, mid, device_fp=device_fp)


async def get_cookie_token_by_stoken(
    stoken: str,
    aid: str,
    mid: Optional[str] = None,
    *,
    device_fp: Optional[str] = None,
) -> Tuple[Optional[str], str]:
    return await exchange_token(stoken, aid, TOKEN_COOKIE_TOKEN, mid, device_fp=device_fp)


async def get_game_roles_by_stoken(
    stoken: str,
    aid: str,
    mid: Optional[str] = None,
    *,
    device_id: Optional[str] = None,
    device_fp: Optional[str] = None,
) -> Tuple[Optional[List[Dict[str, Any]]], str]:
    """通过 SToken 获取米游社绑定的游戏角色列表 """
    mid = mid or extract_mid(stoken)
    if not stoken or not mid or not aid:
        return None, 'stoken / mid / aid 不能为空'

    headers = {
        'DS': generate_ds(SALTS[SaltType.K2], include_chars=True, gen=1),
        'Cookie': f'stuid={aid};mid={mid};stoken={stoken}',
        'x-rpc-app_version': CN_VERSION,
        'x-rpc-sys_version': '12',
        'x-rpc-client_type': '2',
        'x-rpc-device_id': device_id or str(uuid4()),
        'User-Agent': f'Mozilla/5.0 (Linux; Android 12) Mobile miHoYoBBS/{CN_VERSION}',
        'Referer': 'https://app.mihoyo.com',
    }
    if device_fp:
        headers['x-rpc-device_fp'] = device_fp

    try:
        response = await aiorequests.get(GAME_ROLES_BY_STOKEN_API, headers=headers)
        result = response.json()
    except Exception as exc:
        return None, f'请求失败: {exc}'

    if result.get('retcode') != 0:
        message = result.get('message') or '请求失败'
        return None, f'{message} (retcode={result.get("retcode")})'

    data = result.get('data') or {}
    roles = data.get('list')
    if not isinstance(roles, list):
        return None, '响应中没有游戏角色列表'
    return roles, ''


def filter_genshin_roles(roles: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    """从 getUserGameRolesByStoken 的返回中筛出原神官服角色。

    该接口字段为 ``game_uid``（旧接口为 ``game_role_id``）。
    """
    result: List[Dict[str, str]] = []
    for role in roles or []:
        if str(role.get('game_biz') or '').lower() != 'hk4e_cn':
            continue
        uid = role.get('game_uid') or role.get('game_role_id')
        if not uid:
            continue
        result.append({'uid': str(uid), 'nickname': role.get('nickname') or ''})
    return result


def build_cookie(
    aid: str,
    mid: str,
    cookie_token: str,
    ltoken: Optional[str] = None,
) -> str:
    """构造兼容旧键名与 v2 键名的 Cookie 字符串。"""
    parts = [
        f'account_id={aid}',
        f'cookie_token={cookie_token}',
        f'account_id_v2={aid}',
        f'cookie_token_v2={cookie_token}',
        f'account_mid_v2={mid}',
    ]
    if ltoken:
        parts.extend([
            f'ltuid_v2={aid}',
            f'ltmid_v2={mid}',
            f'ltoken_v2={ltoken}',
        ])
    return ';'.join(parts)
