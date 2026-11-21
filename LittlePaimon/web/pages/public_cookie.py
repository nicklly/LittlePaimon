"""公共 Cookie 管理页面（添加使用 Bootstrap Modal）。"""
from __future__ import annotations

from html import escape as html_escape
from typing import Any, Dict, List, Optional

from bootstrap_ui import (Alert, Badge, Card, Checkbox, Form, Modal, Paragraph, Span,
                          Table, TableColumn, Textarea, field, raw)

from ..ui import layout
from .constants import status_map

COLORS = {0: 'danger', 1: 'success', 2: 'warning', 3: 'secondary'}
ADD_MODAL = 'modal-public-add'


def status_badge(status: Any) -> Badge:
    return Badge(text=status_map.get(status, '未知'), color=COLORS.get(status, 'secondary'))


def cookie_tabs(active: str) -> Any:
    """公共 / 私人 Cookie 子导航。"""
    items = [
        ('public', '公共 Cookie', 'fa-solid fa-globe', '/LittlePaimon/admin/cookies/public'),
        ('private', '私人 Cookie', 'fa-solid fa-user', '/LittlePaimon/admin/cookies/private'),
        ('devices', '用户设备 Devices', 'fa-solid fa-mobile-screen-button', '/LittlePaimon/admin/cookies/device'),
    ]
    links = ''.join(
        f'<a class="cookie-tab{" active" if key == active else ""}" href="{href}">'
        f'<i class="{icon}"></i><span>{label}</span></a>'
        for key, label, icon, href in items
    )
    return raw(f'<div class="cookie-tabs">{links}</div>')


def _cookie_text(cookie: str, limit: int = 90) -> str:
    if len(cookie) <= limit:
        return cookie
    return cookie[:limit] + '…'


def button_html(icon: str, text: str, color: str = 'primary', *, modal: Optional[str] = None,
                href: Optional[str] = None, outline: bool = False, title: str = '', onclick: Optional[str] = None) -> str:
    """带 font-awesome 图标的小按钮（返回 HTML 字符串）。"""
    classes = f'btn btn-sm btn-{"outline-" if outline else ""}{color}'
    attrs = f' title="{html_escape(title)}"' if title else ''
    label = f'<i class="{icon} me-1"></i>{html_escape(text)}' if text else f'<i class="{icon}"></i>'
    if onclick:                                  # ← 新增
        attrs += f' onclick="{html_escape(onclick)}"'
    if modal:
        return (f'<button type="button" class="{classes}"{attrs} data-bs-toggle="modal" '
                f'data-bs-target="#{modal}">{label}</button>')
    if href:
        return f'<a class="{classes}"{attrs} href="{html_escape(href)}">{label}</a>'
    return f'<button type="submit" class="{classes}"{attrs}>{label}</button>'


def icon_button(*args, **kwargs) -> Any:
    return raw(button_html(*args, **kwargs))


def action_form(action: str, fields: Dict[str, Any], button: str,
                confirm: Optional[str] = None) -> Any:
    """表格行内的迷你表单（提交按钮用 ``button_html`` 生成）。"""
    hidden = ''.join(
        f'<input type="hidden" name="{html_escape(str(key))}" value="{html_escape(str(value))}">'
        for key, value in fields.items()
    )
    onsubmit = f' onsubmit="return confirm(\'{html_escape(confirm)}\')"' if confirm else ''
    return raw(f'<form method="post" action="{action}" class="d-inline"{onsubmit}>{hidden}{button}</form>')


def public_cookie_page(cookies: List[Any], notice: Optional[tuple] = None) -> object:
    body = [cookie_tabs('public')]

    rows = []
    for cookie in cookies:
        running = cookie.status != 3
        set_form = action_form(
            '/LittlePaimon/admin/cookies/public/set', {'id': cookie.id},
            button_html('fa-solid fa-pause' if running else 'fa-solid fa-play',
                        '暂停' if running else '恢复', 'warning', outline=True),
        )
        delete_form = action_form(
            '/LittlePaimon/admin/cookies/public/delete', {'id': cookie.id},
            button_html('fa-regular fa-trash-can', '删除', 'danger', outline=True),
            confirm='确认删除该公共 Cookie？',
        )
        rows.append({
            'id': cookie.id,
            'cookie': _cookie_text(cookie.cookie or ''),
            'status': status_badge(cookie.status),
            'actions': Span(body=[set_form, delete_form], class_name='d-inline-flex gap-1'),
        })

    body.append(Card(title='公共 Cookie', body=[
        Paragraph(muted=True, class_name='small mb-3',
                  text='公共 Cookie 会在所有用户查询时轮流使用；添加时会校验有效性。'),
        Paragraph(class_name='mb-3', body=[
            icon_button('fa-solid fa-plus', '添加 Cookie', 'primary', modal=ADD_MODAL),
        ]),
        Table(
            columns=[
                TableColumn(label='ID', key='id'),
                TableColumn(label='Cookie', key='cookie'),
                TableColumn(label='状态', key='status', align='center'),
                TableColumn(label='操作', key='actions', nowrap=True),
            ],
            rows=rows,
            hover=True,
            empty_text='暂无公共 Cookie',
        ),
    ]))

    body.append(Modal(
        id=ADD_MODAL,
        scrollable=True,
        title='添加公共 Cookie',
        body=[
            Form(
                method='post', action='/LittlePaimon/admin/cookies/public/add',
                submit_label='添加',
                body=[
                    field('Cookie', Textarea(name='cookie', rows=5, required=True,
                                             placeholder='粘贴完整的 Cookie 字符串')),
                    field('跳过有效性校验', Checkbox(name='force', switch=True),
                          help='强制添加不会校验 Cookie 是否有效，请确认无误后再使用'),
                ],
            ),
        ],
    ))

    return layout('公共 Cookie', body, active='/LittlePaimon/admin/cookies', toast=notice)
