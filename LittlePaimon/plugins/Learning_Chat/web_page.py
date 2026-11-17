"""群聊学习的 Web 管理页（bootstrap_ui 版）。

替换原先基于 amis 的页面：全部服务端渲染，操作通过表单 POST 完成。
"""
from __future__ import annotations

import datetime
import re
import typing
from math import ceil
from typing import Any, Dict, List, Optional

from bootstrap_ui import (Alert, Badge, Button, Card, Checkbox, Col, Form, Hidden, Input,
                          Paragraph, Row, Select, Span, Table, TableColumn, Textarea, field,
                          raw)
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from LittlePaimon.web import PageRouter
from LittlePaimon.web.pages.public_cookie import action_form, button_html
from LittlePaimon.web.ui import (flash_redirect, guard, layout, notice, pager, redirect,
                                 register_nav, render)

from .config import config_manager
from .models import ChatAnswer, ChatBlackList, ChatContext, ChatMessage

try:
    import jieba_fast as jieba
except ImportError:
    import jieba

router = APIRouter()
register_nav('群聊学习', '/LittlePaimon/admin/chat', 'fa-solid fa-comments')

CHAT_NAV = [
    ('配置', '/LittlePaimon/admin/chat', 'fa-solid fa-gear'),
    ('消息', '/LittlePaimon/admin/chat/messages', 'fa-solid fa-comments'),
    ('学习内容', '/LittlePaimon/admin/chat/contexts', 'fa-solid fa-book'),
    ('回复', '/LittlePaimon/admin/chat/answers', 'fa-solid fa-reply'),
    ('禁用列表', '/LittlePaimon/admin/chat/blacklist', 'fa-solid fa-ban'),
]


def _menu(active: str) -> Any:
    links = ''.join(
        f'<a class="nav-link{" active" if href == active else ""}" href="{href}">'
        f'<i class="{icon}"></i><span>{text}</span></a>'
        for text, href, icon in CHAT_NAV
    )
    return raw(f'<ul class="nav nav-pills flex-column config-menu">{links}</ul>')


def _wrap(active: str, nodes: list) -> list:
    """左侧竖排菜单 + 右侧内容，与配置页保持一致。"""
    return [raw('<div class="config-grid">'), _menu(active),
            raw('<div class="config-content">'), *nodes, raw('</div></div>')]


def _fmt_time(value: Any) -> str:
    """数据库里存的是时间戳。"""
    try:
        return datetime.datetime.fromtimestamp(int(value)).strftime('%Y-%m-%d %H:%M')
    except (TypeError, ValueError, OSError):
        return str(value or '')


def _back(url: str, msg: str, kind: str = 'success'):
    return flash_redirect(url, msg, kind)


async def _form(request: Request) -> Dict[str, str]:
    form = await request.form()
    return {key: str(value) for key, value in form.items()}


def _is_list(annotation: Any) -> bool:
    return typing.get_origin(annotation) in (list, List)


def _config_form(cfg: Any, action: str, *, percent_fields=()) -> Form:
    children = []
    for name, info in type(cfg).model_fields.items():
        if name == 'group_config':
            continue
        label = info.alias or name
        annotation = info.annotation
        value = getattr(cfg, name, None)
        if annotation is bool:
            control = Checkbox(name=name, switch=True, checked=bool(value))
        elif annotation is int:
            control = Input(name=name, type='number', value=value)
        elif annotation is float:
            shown = value * 100 if name in percent_fields else value
            control = Input(name=name, type='number', step='0.01', value=shown)
        elif _is_list(annotation):
            control = Input(name=name, value=','.join(str(item) for item in value or []),
                            placeholder='英文逗号分隔')
        else:
            control = Input(name=name, value='' if value is None else str(value))
        children.append(Col(md=6, body=[field(label, control)]))
    return Form(action=action, method='post', submit_label='保存',
                body=[Row(gutter=3, children=children)])


def _parse(cfg: Any, form: Dict[str, str], *, percent_fields=(), skip=('group_config',)) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for name, info in type(cfg).model_fields.items():
        if name in skip:
            continue
        annotation = info.annotation
        if annotation is bool:
            values[name] = name in form
        elif annotation is int:
            raw = form.get(name)
            if raw not in (None, ''):
                try:
                    values[name] = int(float(raw))
                except ValueError:
                    pass
        elif annotation is float:
            raw = form.get(name)
            if raw not in (None, ''):
                try:
                    number = float(raw)
                except ValueError:
                    continue
                values[name] = number / 100 if name in percent_fields else number
        elif _is_list(annotation):
            raw = form.get(name, '')
            items = [item.strip() for item in re.split(r'[,\s]+', raw) if item.strip()]
            origin = typing.get_origin(annotation)
            args = typing.get_args(annotation)
            if args and args[0] is int:
                values[name] = [int(item) for item in items if item.isdigit()]
            else:
                values[name] = items
        else:
            if name in form:
                values[name] = form[name]
    return values


def chat_config_page(notice_data: Optional[tuple] = None) -> object:
    cfg = config_manager.config
    body = []
    body.append(Card(title='全局配置', body=[
        Paragraph(muted=True, class_name='small',
                  text='关闭总开关后全局都不再学习和回复；屏蔽词/用户用英文逗号分隔。'),
        _config_form(cfg, '/LittlePaimon/admin/chat/config'),
    ]))

    groups = sorted(cfg.group_config.keys())
    options = ''.join(f'<option value="{g}">{g}</option>' for g in groups)
    if not options:
        options = "<option value=''>暂无分群配置</option>"
    disabled = ' disabled' if not groups else ''
    body.append(Card(class_name='mt-3', title='分群配置', body=[
        raw(
            '<form class="d-flex flex-wrap gap-2 align-items-center" '
            'onsubmit="location.href=\'/LittlePaimon/admin/chat/group/\' + '
            'this.group_id.value; return false;">'
            f'<select class="form-select" name="group_id" style="max-width:240px"{disabled}>'
            f'{options}</select>'
            f'<button class="btn btn-secondary btn-sm" type="submit"{disabled}>'
            '编辑该群配置</button>'
            '</form>'
        ),
    ]))
    return layout('群聊学习', _wrap('/LittlePaimon/admin/chat', body),
                  active='/LittlePaimon/admin/chat', toast=notice_data)


def chat_group_page(group_id: int, notice_data: Optional[tuple] = None) -> object:
    cfg = config_manager.get_group_config(group_id)
    body = []
    body.append(Card(title=f'群 {group_id} 配置', body=[
        Paragraph(muted=True, class_name='small',
                  text='概率类配置以百分比填写（0-100）。'),
        _config_form(cfg, f'/LittlePaimon/admin/chat/group/{group_id}',
                     percent_fields=('break_probability', 'speak_continuously_probability',
                                     'speak_poke_probability')),
    ]))
    return layout(f'群 {group_id} 配置', _wrap('/LittlePaimon/admin/chat', body),
                  active='/LittlePaimon/admin/chat', toast=notice_data)


def _table_card(title: str, columns: List[TableColumn], rows: List[dict], empty: str) -> Card:
    return Card(title=title, body=[Table(columns=columns, rows=rows, hover=True, empty_text=empty)])


CHAT_PAGE_SIZE = 10


def _del_form(action: str, page: Optional[int] = None, **hidden) -> Any:
    if page and page > 1:
        hidden['page'] = page
    return action_form(
        action, hidden,
        button_html('fa-regular fa-trash-can', '删除', 'danger', outline=True),
        confirm='确认删除？',
    )


def _ban_form(kind: str, id_: Any, page: Optional[int] = None) -> Any:
    fields = {'type': kind, 'id': id_}
    if page and page > 1:
        fields['page'] = page
    return action_form(
        '/LittlePaimon/admin/chat/ban', fields,
        button_html('fa-solid fa-ban', '禁用', 'warning', outline=True),
        confirm='确认禁用该内容？',
    )


async def _paginate(model: Any, order_by: str, page: int):
    total = await model.all().count()
    total_pages = max(1, ceil(total / CHAT_PAGE_SIZE))
    page = min(max(1, int(page)), total_pages)
    items = await (model.all().order_by(order_by)
                   .offset((page - 1) * CHAT_PAGE_SIZE).limit(CHAT_PAGE_SIZE))
    return items, page, total_pages, total


async def chat_messages_page(notice_data: Optional[tuple] = None, page: int = 1) -> object:
    items, page, total_pages, total = await _paginate(ChatMessage, '-id', page)
    rows = []
    for item in items:
        rows.append({
            'id': item.id,
            'group': item.group_id,
            'user': item.user_id,
            'message': (item.raw_message or '')[:60],
            'time': _fmt_time(item.time),
            'actions': Span(body=[_ban_form('message', item.id, page),
                                  _del_form('/LittlePaimon/admin/chat/delete', page,
                                            type='message', id=item.id)]),
        })
    body = []
    body.append(_table_card(f'聊天记录（第 {page}/{total_pages} 页，共 {total} 条）', [
        TableColumn(label='ID', key='id'),
        TableColumn(label='群', key='group'),
        TableColumn(label='用户', key='user'),
        TableColumn(label='消息', key='message'),
        TableColumn(label='时间', key='time'),
        TableColumn(label='操作', key='actions', nowrap=True),
    ], rows, '暂无聊天记录'))
    body.append(pager(page, total_pages, '/LittlePaimon/admin/chat/messages'))
    return layout('群聊消息', _wrap('/LittlePaimon/admin/chat/messages', body),
                  active='/LittlePaimon/admin/chat/messages', toast=notice_data)


async def chat_contexts_page(notice_data: Optional[tuple] = None, page: int = 1) -> object:
    items, page, total_pages, total = await _paginate(ChatContext, '-time', page)
    rows = []
    for item in items:
        rows.append({
            'id': item.id,
            'keywords': (item.keywords or '')[:60],
            'count': item.count,
            'time': _fmt_time(item.time),
            'actions': Span(body=[_ban_form('context', item.id, page),
                                  _del_form('/LittlePaimon/admin/chat/delete', page,
                                            type='context', id=item.id)]),
        })
    body = []
    body.append(_table_card(f'学习内容（第 {page}/{total_pages} 页，共 {total} 条）', [
        TableColumn(label='ID', key='id'),
        TableColumn(label='内容/关键词', key='keywords'),
        TableColumn(label='已学次数', key='count'),
        TableColumn(label='最后学习', key='time'),
        TableColumn(label='操作', key='actions', nowrap=True),
    ], rows, '暂无学习内容'))
    body.append(pager(page, total_pages, '/LittlePaimon/admin/chat/contexts'))
    return layout('学习内容', _wrap('/LittlePaimon/admin/chat/contexts', body),
                  active='/LittlePaimon/admin/chat/contexts', toast=notice_data)


async def chat_answers_page(notice_data: Optional[tuple] = None, page: int = 1) -> object:
    items, page, total_pages, total = await _paginate(ChatAnswer, '-count', page)
    rows = []
    for item in items:
        rows.append({
            'id': item.id,
            'context': item.context_id,
            'keywords': (item.keywords or '')[:60],
            'count': item.count,
            'actions': Span(body=[_ban_form('answer', item.id, page),
                                  _del_form('/LittlePaimon/admin/chat/delete', page,
                                            type='answer', id=item.id)]),
        })
    body = []
    body.append(_table_card(f'已学回复（第 {page}/{total_pages} 页，共 {total} 条）', [
        TableColumn(label='ID', key='id'),
        TableColumn(label='内容ID', key='context'),
        TableColumn(label='关键词', key='keywords'),
        TableColumn(label='次数', key='count'),
        TableColumn(label='操作', key='actions', nowrap=True),
    ], rows, '暂无已学回复'))
    body.append(pager(page, total_pages, '/LittlePaimon/admin/chat/answers'))
    return layout('已学回复', _wrap('/LittlePaimon/admin/chat/answers', body),
                  active='/LittlePaimon/admin/chat/answers', toast=notice_data)


async def chat_blacklist_page(notice_data: Optional[tuple] = None, page: int = 1) -> object:
    items, page, total_pages, total = await _paginate(ChatBlackList, 'id', page)
    rows = []
    for item in items:
        bans = '全局禁用' if getattr(item, 'global_ban', False) else ', '.join(
            str(g) for g in (item.ban_group_id or []))
        rows.append({
            'id': item.id,
            'keywords': (item.keywords or '')[:60],
            'bans': bans,
            'actions': _del_form('/LittlePaimon/admin/chat/delete', page,
                                 type='blacklist', id=item.id),
        })
    body = []
    body.append(_table_card(f'禁用列表（第 {page}/{total_pages} 页，共 {total} 条）', [
        TableColumn(label='ID', key='id'),
        TableColumn(label='内容/关键词', key='keywords'),
        TableColumn(label='禁用范围', key='bans'),
        TableColumn(label='操作', key='actions', nowrap=True),
    ], rows, '暂无禁用记录'))
    body.append(pager(page, total_pages, '/LittlePaimon/admin/chat/blacklist'))
    return layout('禁用列表', _wrap('/LittlePaimon/admin/chat/blacklist', body),
                  active='/LittlePaimon/admin/chat/blacklist', toast=notice_data)


# --------------------------------------------------------------------------- 路由

@router.get('/LittlePaimon/admin/chat', response_class=HTMLResponse)
async def chat_config_get(request: Request):
    if by_guard := guard(request):
        return by_guard
    group_id = request.query_params.get('group_id')
    if group_id:
        # 兼容旧链接，跳转到不带查询参数的路径
        return redirect(f'/LittlePaimon/admin/chat/group/{group_id}')
    return render(chat_config_page(notice(request)))


@router.get('/LittlePaimon/admin/chat/group/{group_id}', response_class=HTMLResponse)
async def chat_group_get(request: Request, group_id: int):
    if by_guard := guard(request):
        return by_guard
    return render(chat_group_page(group_id, notice(request)))


@router.post('/LittlePaimon/admin/chat/config')
async def chat_config_post(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    values = _parse(config_manager.config, form)
    config_manager.config.update(**values)
    config_manager.save()
    jieba.load_userdict(config_manager.config.dictionary)
    return _back('/LittlePaimon/admin/chat', '全局配置已保存')


@router.post('/LittlePaimon/admin/chat/group/{group_id}')
async def chat_group_post(request: Request, group_id: int):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    cfg = config_manager.get_group_config(group_id)
    values = _parse(cfg, form, percent_fields=(
        'break_probability', 'speak_continuously_probability', 'speak_poke_probability'))
    cfg.update(**values)
    config_manager.save()
    return _back(f'/LittlePaimon/admin/chat/group/{group_id}', '群配置已保存')


@router.get('/LittlePaimon/admin/chat/messages', response_class=HTMLResponse)
async def chat_messages_get(request: Request):
    if by_guard := guard(request):
        return by_guard
    return render(await chat_messages_page(notice(request)))


@router.get('/LittlePaimon/admin/chat/messages/page/{page}', response_class=HTMLResponse)
async def chat_messages_page_get(request: Request, page: int):
    if by_guard := guard(request):
        return by_guard
    return render(await chat_messages_page(notice(request), page))


@router.get('/LittlePaimon/admin/chat/contexts', response_class=HTMLResponse)
async def chat_contexts_get(request: Request):
    if by_guard := guard(request):
        return by_guard
    return render(await chat_contexts_page(notice(request)))


@router.get('/LittlePaimon/admin/chat/contexts/page/{page}', response_class=HTMLResponse)
async def chat_contexts_page_get(request: Request, page: int):
    if by_guard := guard(request):
        return by_guard
    return render(await chat_contexts_page(notice(request), page))


@router.get('/LittlePaimon/admin/chat/answers', response_class=HTMLResponse)
async def chat_answers_get(request: Request):
    if by_guard := guard(request):
        return by_guard
    return render(await chat_answers_page(notice(request)))


@router.get('/LittlePaimon/admin/chat/answers/page/{page}', response_class=HTMLResponse)
async def chat_answers_page_get(request: Request, page: int):
    if by_guard := guard(request):
        return by_guard
    return render(await chat_answers_page(notice(request), page))


@router.get('/LittlePaimon/admin/chat/blacklist', response_class=HTMLResponse)
async def chat_blacklist_get(request: Request):
    if by_guard := guard(request):
        return by_guard
    return render(await chat_blacklist_page(notice(request)))


@router.get('/LittlePaimon/admin/chat/blacklist/page/{page}', response_class=HTMLResponse)
async def chat_blacklist_page_get(request: Request, page: int):
    if by_guard := guard(request):
        return by_guard
    return render(await chat_blacklist_page(notice(request), page))


def _page_url(base: str, page: int) -> str:
    return f'{base}/page/{page}' if page and page > 1 else base


@router.post('/LittlePaimon/admin/chat/delete')
async def chat_delete(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    kind = form.get('type', '')
    id_ = int(form.get('id') or 0)
    page = int(form.get('page') or 1)
    page_map = {'message': 'messages', 'context': 'contexts', 'answer': 'answers',
                'blacklist': 'blacklist'}
    try:
        if kind == 'message':
            await ChatMessage.filter(id=id_).delete()
        elif kind == 'context':
            context = await ChatContext.get_or_none(id=id_)
            if context:
                await ChatAnswer.filter(context=context).delete()
                await context.delete()
        elif kind == 'answer':
            await ChatAnswer.filter(id=id_).delete()
        elif kind == 'blacklist':
            await ChatBlackList.filter(id=id_).delete()
        base = f'/LittlePaimon/admin/chat/{page_map.get(kind, "messages")}'
        return _back(_page_url(base, page), '删除成功')
    except Exception as exc:
        return _back('/LittlePaimon/admin/chat', f'删除失败：{exc}', 'danger')


@router.post('/LittlePaimon/admin/chat/ban')
async def chat_ban(request: Request):
    if by_guard := guard(request):
        return by_guard
    form = await _form(request)
    kind = form.get('type', '')
    id_ = int(form.get('id') or 0)
    page = int(form.get('page') or 1)
    try:
        from .handler import LearningChat

        data = await ChatMessage.get_or_none(id=id_) if kind == 'message' else \
            await ChatContext.get_or_none(id=id_) if kind == 'context' else \
            await ChatAnswer.get_or_none(id=id_)
        if data:
            await LearningChat.add_ban(data)
        return _back(_page_url('/LittlePaimon/admin/chat/contexts', page), '已禁用')
    except Exception as exc:
        return _back('/LittlePaimon/admin/chat', f'禁用失败：{exc}', 'danger')


PageRouter.include_router(router)
