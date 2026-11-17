"""插件管理页面。"""
from __future__ import annotations

from math import ceil
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from bootstrap_ui import (Alert, Badge, Button, Card, Col, Form, Heading, Hidden, Hr,
                          Input, Paragraph, Row, Span, Table, TableColumn, Textarea, field,
                          Checkbox, raw)

from ..ui import layout, pager
from .public_cookie import action_form, button_html, icon_button

PLUGINS_BASE = '/LittlePaimon/admin/plugins'
PLUGINS_PAGE_SIZE = 9


def _status_badge(is_load: bool, enabled: bool) -> Badge:
    if not is_load:
        return Badge(text='未加载', color='secondary')
    return Badge(text='启用' if enabled else '禁用', color='success' if enabled else 'danger')


def plugins_page(plugins: List[Dict[str, Any]], disabled: set[str],
                 notice: Optional[tuple] = None, page: int = 1) -> object:
    body = []

    total_pages = max(1, ceil(len(plugins) / PLUGINS_PAGE_SIZE))
    page = min(max(1, int(page)), total_pages)
    start = (page - 1) * PLUGINS_PAGE_SIZE
    page_plugins = plugins[start:start + PLUGINS_PAGE_SIZE]

    body.append(Heading(level=5, text='插件管理', class_name='mb-1'))
    body.append(Paragraph(muted=True, class_name='small mb-3',
                          text=f'共 {len(plugins)} 个插件，开关只影响插件是否响应消息；'
                               f'详细信息会展示在帮助图中。'))

    cards = []
    for plugin in page_plugins:
        module = plugin.get('module_name') or plugin.get('name')
        enabled = module not in disabled
        action = action_form(
            '/LittlePaimon/admin/plugins/status',
            {'module': module, 'enable': '0' if enabled else '1'},
            button_html('fa-solid fa-ban' if enabled else 'fa-solid fa-check',
                        '禁用' if enabled else '启用',
                        'danger' if enabled else 'success', outline=True),
        )
        detail = icon_button(
            'fa-solid fa-circle-info', '详情', 'primary', outline=True,
            href=f'/LittlePaimon/admin/plugins/detail/{quote(str(module))}',
        )
        cards.append(Col(md=6, xl=4, body=[Card(class_name='plugin-card', body=[
            Span(body=[
                Span(text=plugin.get('name') or module, class_name='plugin-name'),
                _status_badge(bool(plugin.get('isLoad')), enabled),
            ], class_name='d-flex justify-content-between align-items-start gap-2'),
            Paragraph(class_name='plugin-module mb-0', text=str(module)),
            Paragraph(class_name='plugin-desc',
                      text=plugin.get('description') or '暂无描述'),
            raw('<div class="plugin-actions">'), action, detail, raw('</div>'),
        ])]))

    if cards:
        body.append(Row(gutter=3, children=cards))
    else:
        body.append(Paragraph(muted=True, text='暂无插件信息'))
    body.append(pager(page, total_pages, PLUGINS_BASE))
    return layout('插件管理', body, active='/LittlePaimon/admin/plugins', toast=notice)


def plugin_detail_page(plugin: Dict[str, Any], module: str, bans: List[str],
                       notice: Optional[tuple] = None) -> object:
    body = []

    body.append(Card(title=f'插件：{plugin.get("name") or module}', body=[
        Form(
            method='post', action='/LittlePaimon/admin/plugins/detail',
            submit_label='保存修改',
            body=[
                Hidden(name='module_name', value=module),
                field('插件名称', Input(name='name', value=plugin.get('name') or module, required=True)),
                field('插件描述', Textarea(name='description', rows=3,
                                         value=plugin.get('description') or ''),
                      help='仅在本管理页面显示，不会出现在帮助图中'),
                field('使用说明', Textarea(name='usage', rows=3, value=plugin.get('usage') or ''),
                      help='该插件没有具体命令说明时，帮助图会显示这段文字'),
                field('是否展示', Checkbox(name='show', switch=True,
                                         checked=bool(plugin.get('show', True)))),
                field('展示优先级', Input(name='priority', type='number',
                                       value=plugin.get('priority', 99)),
                      help='数字越小越靠前'),
            ],
        ),
    ]))

    body.append(Card(class_name='mt-3', title='使用权限', body=[
        Paragraph(muted=True, class_name='small',
                  text='每行一条，格式：群123456789 或 群123456789.987654321 或 987654321（好友）。留空表示不限制。'),
        Form(
            method='post', action='/LittlePaimon/admin/plugins/bans',
            submit_label='保存权限',
            body=[
                Hidden(name='module_name', value=module),
                Textarea(name='bans', rows=8, value='\n'.join(bans),
                         placeholder='群123456789\n群123456789.987654321\n987654321'),
            ],
        ),
    ]))

    body.append(Paragraph(body=[Button(text='返回插件列表', href='/LittlePaimon/admin/plugins',
                                        color='secondary', outline=True, size='sm')], class_name='mt-3'))
    return layout(f'插件 {module}', body, active='/LittlePaimon/admin/plugins', toast=notice)
