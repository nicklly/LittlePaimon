import re
import datetime
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from LittlePaimon.database import PublicCookie, PrivateCookie, LastQuery, CookieCache, Devices
from LittlePaimon.utils.api import get_bind_game_info, get_stoken_by_login_ticket
from LittlePaimon.utils.passport import (
    build_cookie,
    extract_mid,
    get_cookie_token_by_stoken,
)
from .utils import authentication

route = APIRouter()


class BindCookie(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    uid: Optional[int] = None
    mys_id: Optional[int] = None
    cookie: str
    stoken: Optional[str] = None





@route.post('/bind_cookie', response_class=JSONResponse)
async def bind_cookie(data: BindCookie):
    if mys_id := re.search(r'(?:(?:login_uid|account_mid|account_id|stmid|ltmid|stuid|ltuid)(?:_v2)?)=(\d+)',
                           data.cookie):
        mys_id = mys_id[1]
    else:
        return {'status': 200, 'msg': 'Cookie无效，缺少account_id、login_uid或stuid字段，请根据教程重新获取'}
    cookie_token_match = re.search(r'(?:cookie_token|cookie_token_v2)=([0-9a-zA-Z]+)', data.cookie)
    cookie_token = cookie_token_match[1] if cookie_token_match else None
    login_ticket_match = re.search(r'(?:login_ticket|login_ticket_v2)=([0-9a-zA-Z]+)', data.cookie)
    login_ticket = login_ticket_match[1] if login_ticket_match else None
    stoken_match = re.search(r'(?:stoken|stoken_v2)=([0-9a-zA-Z]+)', data.cookie)
    stoken = stoken_match[1] if stoken_match else None
    mid = extract_mid(data.cookie)
    if login_ticket and not stoken:
        # 如果有login_ticket但没有stoken，就通过login_ticket获取stoken
        stoken = await get_stoken_by_login_ticket(login_ticket, mys_id)
    if stoken and not cookie_token:

        cookie_token, token_err = await get_cookie_token_by_stoken(stoken, mys_id, mid)
        if not cookie_token:
            return {'status': 200, 'msg': f'获取CookieToken失败：{token_err}'}
    if not cookie_token:
        return {'status': 200, 'msg': 'Cookie无效，缺少cookie_token或login_ticket字段，请根据教程重新获取'}

    if game_info := await get_bind_game_info(f'account_id={mys_id};cookie_token={cookie_token}', mys_id):
        if not game_info['list']:
            return {'status': 200, 'msg': '该账号尚未绑定任何游戏，请确认账号无误~'}
        if not (
                genshin_games := [{'uid': game['game_role_id'], 'nickname': game['nickname']} for game in
                                  game_info['list'] if
                                  game['game_id'] == 2]):
            return {'status': 200, 'msg': '该账号尚未绑定原神，请确认账号无误~'}
        stored_cookie = build_cookie(mys_id, mid, cookie_token) if mid else f'account_id={mys_id};cookie_token={cookie_token}'
        stored_stoken = f'stuid={mys_id};stoken={stoken};' + (f'mid={mid};' if mid else '') if stoken else None
        await LastQuery.update_or_create(user_id=data.user_id,
                                         defaults={'uid':       genshin_games[0]['uid'],
                                                   'last_time': datetime.datetime.now()})
        send_msg = ''
        for info in genshin_games:
            send_msg += f'{info["nickname"]}({info["uid"]}) '
            await PrivateCookie.update_or_create(user_id=data.user_id, uid=info['uid'], mys_id=mys_id,
                                                 defaults={'cookie': stored_cookie,
                                                           'stoken': stored_stoken})
        return {'status': 0, 'msg':
                          f'QQ{data.user_id}绑定玩家{send_msg.strip()}的Cookie{"和Stoken" if stoken else ""}成功{"" if stoken else "当未能绑定Stoken"}'}
    else:
        return {'status': 200, 'msg': 'Cookie无效，请根据教程重新获取'}


@route.get('/get_public_cookies', response_class=JSONResponse, dependencies=[authentication()])
async def get_public_cookies(status: Optional[int] = None):
    if status is None:
        return await PublicCookie.all().values()
    else:
        return await PublicCookie.filter(status=status).values()


@route.post('/set_public_cookie', response_class=JSONResponse, dependencies=[authentication()])
async def set_public_cookie(id: int):
    cookie = await PublicCookie.get_or_none(id=id)
    if cookie.status != 3:
        await CookieCache.filter(cookie=cookie.cookie).delete()
        cookie.status = 3
        await cookie.save()
        return {
            'status': 0,
            'msg':    f'{id}号公共Cookie暂停使用成功'
        }
    else:
        cookie.status = 1
        await cookie.save()
        return {
            'status': 0,
            'msg':    f'{id}号公共Cookie恢复使用成功'
        }


@route.get('/get_private_cookies', response_class=JSONResponse, dependencies=[authentication()])
async def get_private_cookies(
        page: int = 1,
        perPage: int = 10,
        orderBy: str = 'id',
        orderDir: str = 'asc',
        status: Optional[int] = None,
        user_id: Optional[int] = None,
        uid: Optional[int] = None,
        mys_id: Optional[int] = None):
    orderBy = orderBy if orderDir == 'asc' else f'-{orderBy}' if orderBy else 'id'
    query = {f'{k}__contains': v for k, v in {'user_id': user_id, 'uid': uid, 'mys_id': mys_id}.items() if
             v is not None}
    if status is not None:
        query['status'] = status
    return {
        'status': 0,
        'msg':    'ok',
        'data':   {
            'items': await PrivateCookie.filter(**query).order_by(orderBy).offset((page - 1) * perPage).limit(
                perPage).values(),
            'total': await PrivateCookie.filter(**query).count()
        }
    }


@route.get('/get_private_cookie', response_class=JSONResponse, dependencies=[authentication()])
async def get_private_cookie(id: int):
    return await PrivateCookie.get_or_none(id=id).values()

@route.delete('/delete_device', response_class=JSONResponse, dependencies=[authentication()])
async def delete_device(id: int):
    await Devices.filter(id=id).delete()
    await Devices.filter(id=id).delete()
    return {'status': 0, 'msg': f'{id}号设备信息删除成功'}

@route.delete('/delete_cookie', response_class=JSONResponse, dependencies=[authentication()])
async def delete_public_cookie(cookie_type: str, id: int):
    if cookie_type == 'public':
        cookie = await PublicCookie.get(id=id)
        await CookieCache.filter(cookie=cookie.cookie).delete()
        await cookie.delete()
        return {'status': 0, 'msg': f'{id}号公共Cookie删除成功'}
    else:
        await PrivateCookie.filter(id=id).delete()
        await Devices.filter(id=id).delete()
        return {'status': 0, 'msg': f'{id}号私人Cookie和设备信息删除成功'}


@route.post('/add_cookie', response_class=JSONResponse, dependencies=[authentication()])
async def add_public_cookie(cookie_type: str, force: bool, data: BindCookie):
    if cookie_type == 'public':
        if not force:
            if mys_id := re.search(r'(?:(?:login_uid|account_mid|account_id|stmid|ltmid|stuid|ltuid)(?:_v2)?)=(\d+)',
                                   data.cookie):
                mys_id = mys_id[1]
            else:
                return {'status': 200, 'msg': 'Cookie无效，缺少account_id、login_uid或stuid字段'}
            cookie_token_match = re.search(r'(?:cookie_token|cookie_token_v2)=([0-9a-zA-Z]+)', data.cookie)
            cookie_token = cookie_token_match[1] if cookie_token_match else None
            login_ticket_match = re.search(r'(?:login_ticket|login_ticket_v2)=([0-9a-zA-Z]+)', data.cookie)
            login_ticket = login_ticket_match[1] if login_ticket_match else None
            stoken_match = re.search(r'(?:stoken|stoken_v2)=([0-9a-zA-Z]+)', data.cookie)
            stoken = stoken_match[1] if stoken_match else None
            mid = extract_mid(data.cookie)
            if login_ticket and not stoken:
                # 如果有login_ticket但没有stoken，就通过login_ticket获取stoken
                stoken = await get_stoken_by_login_ticket(login_ticket, mys_id)
            if stoken and not cookie_token:
                cookie_token, token_err = await get_cookie_token_by_stoken(stoken, mys_id, mid)
                if not cookie_token:
                    return {'status': 200, 'msg': f'获取CookieToken失败：{token_err}'}
            if not cookie_token:
                return {'status': 200, 'msg': 'Cookie无效，缺少cookie_token或login_ticket字段'}
            if await get_bind_game_info(f'account_id={mys_id};cookie_token={cookie_token}', mys_id):
                stored_cookie = build_cookie(mys_id, mid, cookie_token) if mid else f'account_id={mys_id};cookie_token={cookie_token}'
                new_cookie = await PublicCookie.create(cookie=stored_cookie)
                return {'status': 0, 'msg': f'{new_cookie.id}号公共Cookie添加成功'}
            else:
                return {'status': 200, 'msg': '该Cookie无效，请根据教程重新获取'}
        else:
            new_cookie = await PublicCookie.create(cookie=data.cookie)
            return {'status': 0, 'msg': f'{new_cookie.id}号公共Cookie添加成功'}
    else:
        if force:
            await PrivateCookie.update_or_create(user_id=data.user_id, uid=data.uid, mys_id=data.mys_id,
                                                 defaults={'cookie': data.cookie, 'stoken': data.stoken})
            return {'status': 0, 'msg': f'QQ{data.user_id}的UID{data.uid}的Cookie强制修改成功。'}
        else:
            if mys_id := re.search(r'(?:(?:login_uid|account_mid|account_id|stmid|ltmid|stuid|ltuid)(?:_v2)?)=(\d+)',
                                   data.cookie):
                mys_id = mys_id[1]
            else:
                return {'status': 200, 'msg': 'Cookie无效，缺少account_id、login_uid或stuid字段，请根据教程重新获取'}
            cookie_token_match = re.search(r'(?:cookie_token|cookie_token_v2)=([0-9a-zA-Z]+)', data.cookie)
            cookie_token = cookie_token_match[1] if cookie_token_match else None
            login_ticket_match = re.search(r'(?:login_ticket|login_ticket_v2)=([0-9a-zA-Z]+)', data.cookie)
            login_ticket = login_ticket_match[1] if login_ticket_match else None
            stoken_match = re.search(r'(?:stoken|stoken_v2)=([0-9a-zA-Z]+)', data.cookie)
            stoken = stoken_match[1] if stoken_match else None
            mid = extract_mid(data.cookie)
            if login_ticket and not stoken:
                # 如果有login_ticket但没有stoken，就通过login_ticket获取stoken
                stoken = await get_stoken_by_login_ticket(login_ticket, mys_id)
            if stoken and not cookie_token:
                cookie_token, token_err = await get_cookie_token_by_stoken(stoken, mys_id, mid)
                if not cookie_token:
                    return {'status': 200, 'msg': f'获取CookieToken失败：{token_err}'}
            if not cookie_token:
                return {'status': 200, 'msg': 'Cookie无效，缺少cookie_token或login_ticket字段，请根据教程重新获取'}

            stored_cookie = build_cookie(mys_id, mid, cookie_token) if mid else f'account_id={mys_id};cookie_token={cookie_token}'
            stored_stoken = f'stuid={mys_id};stoken={stoken};' + (f'mid={mid};' if mid else '') if stoken else None
            if game_info := await get_bind_game_info(f'account_id={mys_id};cookie_token={cookie_token}', mys_id):
                if not game_info['list']:
                    return {'status': 200, 'msg': '该账号尚未绑定任何游戏，请确认账号无误~'}
                if not (
                        genshin_games := [{'uid': game['game_role_id'], 'nickname': game['nickname']} for game in
                                          game_info['list'] if
                                          game['game_id'] == 2]):
                    return {'status': 200, 'msg': '该账号尚未绑定原神，请确认账号无误~'}
                await LastQuery.update_or_create(user_id=data.user_id,
                                                 defaults={'uid':       genshin_games[0]['uid'],
                                                           'last_time': datetime.datetime.now()})
                send_msg = ''
                for info in genshin_games:
                    send_msg += f'{info["nickname"]}({info["uid"]}) '
                    await PrivateCookie.update_or_create(user_id=data.user_id, uid=info['uid'], mys_id=mys_id,
                                                         defaults={'cookie': stored_cookie,
                                                                   'stoken': stored_stoken})
                return {'status': 0, 'msg':
                                  f'QQ{data.user_id}绑定玩家{send_msg.strip()}的Cookie{"和Stoken" if stoken else ""}成功{"" if stoken else "当未能绑定Stoken"}'}
            else:
                return {'status': 200, 'msg': 'Cookie无效，请根据教程重新获取'}


@route.post('/update_private_cookie', response_class=JSONResponse, dependencies=[authentication()])
async def update_cookie(force: bool, data: BindCookie):
    if force:
        await PrivateCookie.filter(id=data.id).update(**data.model_dump(exclude={'id'}))
        return {'status': 0, 'msg': f'QQ{data.user_id}的UID{data.uid}的Cookie强制修改成功。'}
    else:
        if mys_id := re.search(r'(?:(?:login_uid|account_mid|account_id|stmid|ltmid|stuid|ltuid)(?:_v2)?)=(\d+)',
                               data.cookie):
            mys_id = mys_id[1]
        else:
            return {'status': 200, 'msg': 'Cookie无效，缺少account_id、login_uid或stuid字段，请根据教程重新获取'}
        cookie_token_match = re.search(r'(?:cookie_token|cookie_token_v2)=([0-9a-zA-Z]+)', data.cookie)
        cookie_token = cookie_token_match[1] if cookie_token_match else None
        login_ticket_match = re.search(r'(?:login_ticket|login_ticket_v2)=([0-9a-zA-Z]+)', data.cookie)
        login_ticket = login_ticket_match[1] if login_ticket_match else None
        stoken_match = re.search(r'(?:stoken|stoken_v2)=([0-9a-zA-Z]+)', data.cookie)
        stoken = stoken_match[1] if stoken_match else None
        mid = extract_mid(data.cookie)
        if login_ticket and not stoken:
            # 如果有login_ticket但没有stoken，就通过login_ticket获取stoken
            stoken = await get_stoken_by_login_ticket(login_ticket, mys_id)
        if stoken and not cookie_token:
            cookie_token, token_err = await get_cookie_token_by_stoken(stoken, mys_id, mid)
            if not cookie_token:
                return {'status': 200, 'msg': f'获取CookieToken失败：{token_err}'}
        if not cookie_token:
            return {'status': 200, 'msg': 'Cookie无效，缺少cookie_token或login_ticket字段，请根据教程重新获取'}

        stored_cookie = build_cookie(mys_id, mid, cookie_token) if mid else f'account_id={mys_id};cookie_token={cookie_token}'
        stored_stoken = f'stuid={mys_id};stoken={stoken};' + (f'mid={mid};' if mid else '') if stoken else None
        if game_info := await get_bind_game_info(f'account_id={mys_id};cookie_token={cookie_token}', mys_id):
            if not game_info['list']:
                return {'status': 200, 'msg': '该账号尚未绑定任何游戏，请确认账号无误~'}
            if not (
                    genshin_games := [{'uid': game['game_role_id'], 'nickname': game['nickname']} for game in
                                      game_info['list'] if
                                      game['game_id'] == 2]):
                return {'status': 200, 'msg': '该账号尚未绑定原神，请确认账号无误~'}
            await LastQuery.update_or_create(user_id=data.user_id,
                                             defaults={'uid':       genshin_games[0]['uid'],
                                                       'last_time': datetime.datetime.now()})
            send_msg = ''
            for info in genshin_games:
                send_msg += f'{info["nickname"]}({info["uid"]}) '
                await PrivateCookie.update_or_create(user_id=data.user_id, uid=info['uid'], mys_id=mys_id,
                                                     defaults={'cookie': stored_cookie,
                                                               'stoken': stored_stoken})
            return {'status': 0, 'msg':
                              f'QQ{data.user_id}绑定玩家{send_msg.strip()}的Cookie{"和Stoken" if stoken else ""}成功{"" if stoken else "当未能绑定Stoken"}'}
        else:
            return {'status': 200, 'msg': 'Cookie无效，请根据教程重新获取'}
