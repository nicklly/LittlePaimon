"""LittlePaimon Web 控制台（bootstrap_ui 版）。

页面全部服务端渲染，交互通过普通表单 POST 完成；原有 JSON API（``/LittlePaimon/api``）
保持可用，方便脚本或后续前端调用。
"""
from __future__ import annotations

import asyncio
import re
import types
import typing
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import nonebot
from bootstrap_ui import Button, Card, raw
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from html import escape
from tortoise.queryset import Q

from LittlePaimon.config import ConfigManager, PluginInfo, PluginManager
from LittlePaimon.database import CommandAlias, PluginDisable, PrivateCookie, PublicCookie
from LittlePaimon.utils import DRIVER, SUPERUSERS, logger

from .api import BaseApiRouter
from .api.bot_info import bot_restart, bot_update
from .api.cookie import (BindCookie, add_public_cookie, bind_cookie, delete_public_cookie,
                         set_public_cookie, update_cookie)
from .api.plugin import set_plugin_bans, set_plugin_detail, set_plugin_status
from .api.status import debug_logs, info_logs
from .pages import (alias_page, bind_cookie_page, blank_page, config_page, home_page,
                    login_page, plugin_detail_page, plugins_page, private_cookie_page,
                    public_cookie_page, read_env)
from .ui import (current_user, flash_redirect, guard, layout, login_response,
                 logout_response, notice, redirect, render)

PageRouter = APIRouter()

icon_path = 'https://s1.ax1x.com/2023/02/05/pS62DJK.png'


# --------------------------------------------------------------------------- 工具

async def _form(request: Request) -> Dict[str, str]:
    form = await request.form()
    return {key: str(value) for key, value in form.items()}


def _back(url: str, msg: str, kind: str = 'success') -> RedirectResponse:
    """重定向到不带任何查询参数的地址，提示通过临时 Cookie 传递。"""
    return flash_redirect(url, msg, kind)


def _result_msg(result: Any) -> tuple[str, str]:
    """把 API 返回的 dict 转成 (消息, 类型)。"""
    if isinstance(result, str):
        return result, 'danger'
    if not isinstance(result, dict):
        return '操作失败', 'danger'
    ok = result.get('status') == 0
    return str(result.get('msg') or ('操作成功' if ok else '操作失败')), 'success' if ok else 'danger'


def _admin_enabled() -> bool:
    return bool(getattr(ConfigManager.config, 'admin_enable', True))


def _discover_disabled(plugins: List[Dict[str, Any]]) -> set:
    return {plugin.get('module_name') for plugin in plugins
            if plugin.get('module_name') and not plugin.get('isLoad')}


# --------------------------------------------------------------------------- 登录

@PageRouter.get('/LittlePaimon/login', response_class=HTMLResponse)
async def login_get(request: Request):
    if not _admin_enabled():
        return render(blank_page())
    if current_user(request) is not None:
        return redirect('/LittlePaimon/admin')
    return render(login_page())


@PageRouter.post('/LittlePaimon/login')
async def login_post(request: Request):
    if not _admin_enabled():
        return render(blank_page())
    form = await _form(request)
    try:
        user_id = int(form.get('user_id', ''))
    except ValueError:
        return render(login_page('用户 ID 必须是数字'))
    password = form.get('password', '')
    if user_id not in SUPERUSERS or password != ConfigManager.config.admin_password:
        return render(login_page('登录失败，请确认用户 ID 和密码无误'))
    next_url = request.query_params.get('next') or '/LittlePaimon/admin'
    if not next_url.startswith('/LittlePaimon'):
        next_url = '/LittlePaimon/admin'
    return login_response(request, user_id, next_url)


@PageRouter.get('/LittlePaimon/logout')
async def logout():
    return logout_response()


# --------------------------------------------------------------------------- 仪表盘

@PageRouter.get('/LittlePaimon/admin', response_class=HTMLResponse)
async def admin_home(request: Request):
    if not _admin_enabled():
        return render(blank_page())
    if resp := guard(request):
        return resp
    from LittlePaimon.utils.status import get_status

    status = await get_status()
    return render(home_page(status, notice(request)))


@PageRouter.get('/LittlePaimon/admin/logs', response_class=PlainTextResponse)
async def admin_logs(request: Request):
    if guard(request):
        return PlainTextResponse('未登录', status_code=401)
    level = request.query_params.get('level', 'info')
    try:
        num = int(request.query_params.get('num', 200))
    except ValueError:
        num = 200
    logs = debug_logs if level == 'debug' else info_logs
    return PlainTextResponse('\n'.join(logs[-num:]))


@PageRouter.post('/LittlePaimon/admin/bot/update')
async def admin_bot_update(request: Request):
    if by_guard := guard(request):
        return by_guard
    msg = await bot_update()
    return _back('/LittlePaimon/admin', str(msg), 'info')


@PageRouter.post('/LittlePaimon/admin/bot/restart')
async def admin_bot_restart(request: Request):
    if by_guard := guard(request):
        return by_guard
    return await bot_restart()


@PageRouter.post('/LittlePaimon/admin/run_cmd', response_class=HTMLResponse)
async def admin_run_cmd(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    cmd = form.get('cmd', '').strip()
    if not cmd:
        return _back('/LittlePaimon/admin', '命令不能为空', 'warning')
    try:
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
    except Exception as exc:
        stdout, stderr = b'', str(exc).encode()
    output = (stdout or stderr).decode('utf-8', errors='replace') or '（无输出）'
    body = [
        Card(title=f'执行结果：{cmd}', body=[
            raw(f'<pre class="mb-0" style="white-space:pre-wrap">{escape(output)}</pre>'),
        ]),
        Button(text='返回首页', href='/LittlePaimon/admin', color='secondary', outline=True, size='sm'),
    ]
    return render(layout('命令执行结果', body, active='/LittlePaimon/admin'))


# --------------------------------------------------------------------------- 插件

@PageRouter.get('/LittlePaimon/admin/plugins', response_class=HTMLResponse)
async def plugins_get(request: Request):
    if by_guard := guard(request):
        return by_guard
    plugins = await PluginManager.get_plugin_list_for_admin()
    disabled = set(await PluginDisable.filter(global_disable=True).values_list('name', flat=True))
    return render(plugins_page(plugins, disabled, notice(request)))


@PageRouter.get('/LittlePaimon/admin/plugins/page/{page}', response_class=HTMLResponse)
async def plugins_page_get(request: Request, page: int):
    if by_guard := guard(request):
        return by_guard
    plugins = await PluginManager.get_plugin_list_for_admin()
    disabled = set(await PluginDisable.filter(global_disable=True).values_list('name', flat=True))
    return render(plugins_page(plugins, disabled, notice(request), page=page))


@PageRouter.post('/LittlePaimon/admin/plugins/status')
async def plugin_status_post(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    module = form.get('module', '')
    enable = form.get('enable') == '1'
    result = await set_plugin_status({'plugin': module, 'status': enable})
    msg, kind = _result_msg(result)
    return _back('/LittlePaimon/admin/plugins', msg, kind)


@PageRouter.get('/LittlePaimon/admin/plugins/detail', response_class=HTMLResponse)
async def plugin_detail_redirect(request: Request):
    if by_guard := guard(request):
        return by_guard
    module = request.query_params.get('module', '')
    return redirect(f'/LittlePaimon/admin/plugins/detail/{quote(module)}')


@PageRouter.get('/LittlePaimon/admin/plugins/detail/{module}', response_class=HTMLResponse)
async def plugin_detail_get(request: Request, module: str):
    if by_guard := guard(request):
        return by_guard
    info = PluginManager.plugins.get(module)
    data = info.model_dump() if info else {'name': module, 'module_name': module}
    bans = [f'群{ban.group_id}.{ban.user_id}' if ban.group_id and ban.user_id
            else f'群{ban.group_id}' if ban.group_id
            else str(ban.user_id)
            for ban in await PluginDisable.filter(name=module, global_disable=False).all()]
    return render(plugin_detail_page(data, module, bans, notice(request)))


@PageRouter.post('/LittlePaimon/admin/plugins/detail')
async def plugin_detail_post(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    module = form.get('module_name', '')
    existing = PluginManager.plugins.get(module)
    try:
        priority = int(form.get('priority') or 99)
    except ValueError:
        priority = 99
    values = {
        'name': form.get('name') or module,
        'module_name': module,
        'description': form.get('description') or None,
        'usage': form.get('usage') or None,
        'show': 'show' in form,
        'priority': priority,
    }
    if existing is not None:
        info = existing.model_copy(update=values)
    else:
        info = PluginInfo(**values)
    result = await set_plugin_detail(info)
    msg, kind = _result_msg(result)
    return _back(f'/LittlePaimon/admin/plugins/detail/{quote(module)}', msg, kind)


@PageRouter.post('/LittlePaimon/admin/plugins/bans')
async def plugin_bans_post(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    module = form.get('module_name', '')
    bans = [line.strip() for line in (form.get('bans') or '').splitlines() if line.strip()]
    result = await set_plugin_bans({'module_name': module, 'bans': bans})
    msg, kind = _result_msg(result)
    return _back(f'/LittlePaimon/admin/plugins/detail/{quote(module)}', msg, kind)


# --------------------------------------------------------------------------- Cookie

@PageRouter.get('/LittlePaimon/admin/cookies', response_class=HTMLResponse)
async def cookies_index(request: Request):
    if by_guard := guard(request):
        return by_guard
    cookies = await PublicCookie.all().order_by('id')
    return render(public_cookie_page(cookies, notice(request)))


@PageRouter.get('/LittlePaimon/admin/cookies/public', response_class=HTMLResponse)
async def public_cookies_get(request: Request):
    if by_guard := guard(request):
        return by_guard
    cookies = await PublicCookie.all().order_by('id')
    return render(public_cookie_page(cookies, notice(request)))


@PageRouter.post('/LittlePaimon/admin/cookies/public/add')
async def public_cookies_add(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    result = await add_public_cookie(
        'public', 'force' in form, BindCookie(cookie=form.get('cookie', ''))
    )
    msg, kind = _result_msg(result)
    return _back('/LittlePaimon/admin/cookies/public', msg, kind)


@PageRouter.post('/LittlePaimon/admin/cookies/public/set')
async def public_cookies_set(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    try:
        result = await set_public_cookie(int(form.get('id', 0)))
    except Exception as exc:
        result = {'status': -1, 'msg': f'操作失败：{exc}'}
    msg, kind = _result_msg(result)
    return _back('/LittlePaimon/admin/cookies/public', msg, kind)


@PageRouter.post('/LittlePaimon/admin/cookies/public/delete')
async def public_cookies_delete(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    try:
        result = await delete_public_cookie('public', int(form.get('id', 0)))
    except Exception as exc:
        result = {'status': -1, 'msg': f'删除失败：{exc}'}
    msg, kind = _result_msg(result)
    return _back('/LittlePaimon/admin/cookies/public', msg, kind)


@PageRouter.get('/LittlePaimon/admin/cookies/private', response_class=HTMLResponse)
async def private_cookies_get(request: Request):
    if by_guard := guard(request):
        return by_guard
    cookies = await PrivateCookie.all().order_by('id')
    return render(private_cookie_page(cookies, notice(request)))


@PageRouter.post('/LittlePaimon/admin/cookies/private/add')
async def private_cookies_add(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    data = BindCookie(
        user_id=form.get('user_id') or None,
        uid=form.get('uid') or None,
        mys_id=form.get('mys_id') or None,
        cookie=form.get('cookie', ''),
        stoken=form.get('stoken') or None,
    )
    result = await add_public_cookie('private', 'force' in form, data)
    msg, kind = _result_msg(result)
    return _back('/LittlePaimon/admin/cookies/private', msg, kind)


@PageRouter.get('/LittlePaimon/admin/cookies/private/edit', response_class=HTMLResponse)
async def private_cookies_edit(request: Request):
    if by_guard := guard(request):
        return by_guard
    return redirect('/LittlePaimon/admin/cookies/private')


@PageRouter.post('/LittlePaimon/admin/cookies/private/update')
async def private_cookies_update(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    data = BindCookie(
        id=form.get('id') or None,
        user_id=form.get('user_id') or None,
        uid=form.get('uid') or None,
        mys_id=form.get('mys_id') or None,
        cookie=form.get('cookie', ''),
        stoken=form.get('stoken') or None,
    )
    result = await update_cookie('force' in form, data)
    msg, kind = _result_msg(result)
    return _back('/LittlePaimon/admin/cookies/private', msg, kind)


@PageRouter.post('/LittlePaimon/admin/cookies/private/delete')
async def private_cookies_delete(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    try:
        result = await delete_public_cookie('private', int(form.get('id', 0)))
    except Exception as exc:
        result = {'status': -1, 'msg': f'删除失败：{exc}'}
    msg, kind = _result_msg(result)
    return _back('/LittlePaimon/admin/cookies/private', msg, kind)


# --------------------------------------------------------------------------- 配置

@PageRouter.get('/LittlePaimon/admin/config', response_class=HTMLResponse)
async def config_get(request: Request):
    if by_guard := guard(request):
        return by_guard
    file_name = request.query_params.get('file') or '.env'
    return render(config_page(ConfigManager.config, file_name, read_env(file_name), notice(request)))


@PageRouter.post('/LittlePaimon/admin/config')
async def config_post(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    values: Dict[str, Any] = {}
    for name, info in type(ConfigManager.config).model_fields.items():
        annotation = info.annotation
        if annotation is bool:
            values[name] = name in form
        elif annotation is int:
            raw = form.get(name)
            if raw not in (None, ''):
                try:
                    values[name] = int(raw)
                except ValueError:
                    pass
        elif typing.get_origin(annotation) is typing.Literal:
            if form.get(name):
                values[name] = form[name]
        elif typing.get_origin(annotation) in (list, List):
            raw = form.get(name, '')
            values[name] = [int(item) for item in re.split(r'[,\s]+', raw) if item.strip().isdigit()]
        else:
            if name in form:
                values[name] = form[name]
    try:
        ConfigManager.config.update(**values)
        ConfigManager.save()
        return _back('/LittlePaimon/admin/config', '配置已保存')
    except Exception as exc:
        return _back('/LittlePaimon/admin/config', f'保存失败：{exc}', 'danger')


@PageRouter.post('/LittlePaimon/admin/config/env')
async def config_env_post(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    file_name = form.get('file') or '.env'
    if file_name not in {'.env', '.env.dev', '.env.prod'}:
        return _back('/LittlePaimon/admin/config', '文件不允许编辑', 'danger')
    try:
        (Path() / file_name).write_text(form.get('content') or '', encoding='utf-8')
        return _back('/LittlePaimon/admin/config', f'{file_name} 已保存')
    except Exception as exc:
        return _back('/LittlePaimon/admin/config', f'保存失败：{exc}', 'danger')


# --------------------------------------------------------------------------- 命令别名

@PageRouter.get('/LittlePaimon/admin/alias', response_class=HTMLResponse)
async def alias_get(request: Request):
    if by_guard := guard(request):
        return by_guard
    aliases = await CommandAlias.all().order_by('priority')
    return render(alias_page(aliases, bool(ConfigManager.config.command_alias_enable), notice(request)))


@PageRouter.post('/LittlePaimon/admin/alias/add')
async def alias_add(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    try:
        await CommandAlias.create(
            alias=form.get('alias', ''),
            command=form.get('command', ''),
            mode=form.get('mode') or '前缀',
            is_regex='is_regex' in form,
            is_reverse='is_reverse' in form,
            group_id=form.get('group_id') or 'all',
            priority=int(form.get('priority') or 99),
        )
        return _back('/LittlePaimon/admin/alias', '命令别名已添加')
    except Exception as exc:
        return _back('/LittlePaimon/admin/alias', f'添加失败：{exc}', 'danger')


@PageRouter.post('/LittlePaimon/admin/alias/delete')
async def alias_delete(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    try:
        await CommandAlias.filter(id=int(form.get('id', 0))).delete()
        return _back('/LittlePaimon/admin/alias', '已删除')
    except Exception as exc:
        return _back('/LittlePaimon/admin/alias', f'删除失败：{exc}', 'danger')


@PageRouter.post('/LittlePaimon/admin/alias/toggle')
async def alias_toggle(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    ConfigManager.config.update(command_alias_enable='enable' in form)
    ConfigManager.save()
    return _back('/LittlePaimon/admin/alias', '开关已保存')


@PageRouter.post('/LittlePaimon/admin/alias/test', response_class=HTMLResponse)
async def alias_test(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    group_id = form.get('group_id') or 'all'
    message = form.get('message') or ''
    aliases = await CommandAlias.filter(Q(group_id=group_id) | Q(group_id='all')).order_by('priority')
    from LittlePaimon.config.command import modify_msg

    result = modify_msg(aliases, message)
    return render(alias_page(await CommandAlias.all().order_by('priority'),
                             bool(ConfigManager.config.command_alias_enable),
                             test_result=result))


# --------------------------------------------------------------------------- 用户绑定页

@PageRouter.get('/LittlePaimon/cookie', response_class=HTMLResponse)
async def user_cookie_get(request: Request):
    if not getattr(ConfigManager.config, 'CookieWeb_enable', True):
        return render(blank_page())
    return render(bind_cookie_page())


@PageRouter.post('/LittlePaimon/cookie', response_class=HTMLResponse)
async def user_cookie_post(request: Request):
    if not getattr(ConfigManager.config, 'CookieWeb_enable', True):
        return render(blank_page())
    form = await _form(request)
    try:
        data = BindCookie(user_id=form.get('user_id') or None, cookie=form.get('cookie', ''))
        result = await bind_cookie(data)
        msg, kind = _result_msg(result)
        return render(bind_cookie_page(msg, kind == 'success'))
    except Exception as exc:
        return render(bind_cookie_page(f'绑定失败：{exc}', False))


# --------------------------------------------------------------------------- 启动

@DRIVER.on_startup
def init_web():
    app = nonebot.get_app()
    app.include_router(BaseApiRouter)
    app.include_router(PageRouter)
    logger.info(
        'Web UI',
        f'<g>启用成功</g>，默认地址为<m>http://127.0.0.1:{DRIVER.config.port}/LittlePaimon/login</m>',
    )
