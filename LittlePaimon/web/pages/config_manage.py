"""配置管理页面：表单由 ConfigModel 自动生成，左侧为竖排功能菜单。"""
from __future__ import annotations

import typing
from pathlib import Path
from typing import Any, Dict, List, Optional

from bootstrap_ui import (Alert, Button, Card, Checkbox, Col, Form, Heading, Input,
                          Paragraph, Row, Select, Textarea, field, raw)

from ..ui import layout, resolve_theme, theme_options

ENV_FILES = ['.env', '.env.dev', '.env.prod']

#: 配置分组：(key, 标题, 图标, 字段名列表)
SECTIONS = [
    ('web', 'Web 端配置', 'fa-solid fa-globe', [
        'CookieWeb_enable', 'CookieWeb_url', 'qrcode_bind_use_url',
        'admin_enable', 'admin_password', 'secret_key', 'admin_theme', 'browser_type',
    ]),
    ('gacha', '模拟抽卡', 'fa-solid fa-dice', [
        'sim_gacha_cd_group', 'sim_gacha_cd_member', 'sim_gacha_max',
    ]),
    ('sign', '米游社签到', 'fa-solid fa-calendar-check', [
        'auto_sign_enable', 'auto_sign_hour', 'auto_sign_minute',
        'auto_myb_enable', 'auto_myb_hour', 'auto_myb_minute',
    ]),
    ('note', '实时便签', 'fa-solid fa-bell', [
        'ssbq_enable', 'ssbq_begin', 'ssbq_end', 'ssbq_check',
    ]),
    ('cloud', '云原神', 'fa-solid fa-cloud', [
        'cloud_genshin_enable', 'cloud_genshin_hour',
    ]),
    ('notice', '通知与好友', 'fa-solid fa-user-group', [
        'request_event', 'auto_add_friend', 'auto_add_group', 'notice_event',
    ]),
    ('misc', '其他设置', 'fa-solid fa-gear', [
        'reboot_card_enable', 'img_use_cache', 'screenshot_enable', 'guess_voice_time',
        'ys_auto_update', 'ysa_auto_update', 'ysd_auto_update', 'morning_news',
        'github_proxy', 'command_alias_enable',
    ]),
]

#: 需要下拉选择的字段
SELECT_FIELDS = {
    'admin_theme': lambda: theme_options(),
    'browser_type': lambda: [('Chromium', 'chromium'), ('Firefox', 'firefox'), ('WebKit', 'webkit')],
}


def _is_list(annotation: Any) -> bool:
    return typing.get_origin(annotation) in (list, List)


def _control(name: str, annotation: Any, value: Any) -> Any:
    if name in SELECT_FIELDS:
        options = SELECT_FIELDS[name]()
        current = resolve_theme() if name == 'admin_theme' else str(value)
        return Select(name=name, options=options, value=current)
    if annotation is bool:
        return Checkbox(name=name, switch=True, checked=bool(value))
    if _is_list(annotation):
        text = ','.join(str(item) for item in value or [])
        return Input(name=name, value=text, placeholder='英文逗号分隔，如 123,456')
    if annotation is int:
        return Input(name=name, type='number', value=value)
    return Input(name=name, type='text', value='' if value is None else str(value))


def _section_card(key: str, title: str, icon: str, fields: Dict[str, Any], cfg: Any) -> Card:
    children = []
    for name in fields:
        info = type(cfg).model_fields[name]
        label = info.alias or name
        value = getattr(cfg, name, None)
        children.append(Col(md=6, body=[field(label, _control(name, info.annotation, value))]))
    return Card(
        id=f'sec-{key}',
        class_name='config-section',
        body=[
            raw(f'<div class="section-title"><i class="{icon}"></i><span>{title}</span></div>'),
            Row(gutter=3, children=children),
        ],
    )


def config_page(cfg: Any, env_file: str = '.env', env_content: str = '',
                notice: Optional[tuple] = None) -> object:
    body = []

    all_fields = dict(type(cfg).model_fields)
    used: set[str] = set()
    sections = []
    for key, title, icon, names in SECTIONS:
        names = [name for name in names if name in all_fields]
        if not names:
            continue
        used.update(names)
        sections.append((key, title, icon, names))
    leftovers = [name for name in all_fields if name not in used]
    if leftovers:
        sections.append(('other', '未分类', 'fa-solid fa-ellipsis', leftovers))

    nav = ['<ul class="nav nav-pills config-tabs" id="config-tabs" role="tablist">']
    panes = []
    for index, (key, title, icon, names) in enumerate(sections):
        active = index == 0
        nav.append(
            '<li class="nav-item" role="presentation">'
            f'<button class="nav-link{" active" if active else ""}" type="button" role="tab" '
            f'data-bs-toggle="pill" data-bs-target="#pane-{key}" aria-controls="pane-{key}" '
            f'aria-selected="{"true" if active else "false"}">'
            f'<i class="{icon}"></i><span>{title}</span></button></li>'
        )
        panes.append(raw(f'<div class="tab-pane fade{" show active" if active else ""}" '
                         f'id="pane-{key}" role="tabpanel">'))
        panes.append(_section_card(key, title, icon, names, cfg))
        panes.append(raw('</div>'))
    if any(key == 'notice' for key, _, _, _ in sections):
        nav.append(
            '<li class="nav-item ms-auto"><button class="tab-bell" type="button" '
            'role="tab" data-bs-toggle="pill" data-bs-target="#pane-notice" '
            'title="通知与好友"><i class="fa-solid fa-bell"></i></button></li>'
        )
    nav.append('</ul>')

    body.append(raw(
        '<div class="page-head">'
        '<div class="page-title">配置项管理</div>'
        '<div class="page-hint">修改后部分配置需要重启 Bot 才会生效</div>'
        '</div>'
    ))
    body.append(Form(
        action='/LittlePaimon/admin/config', method='post', submit_label=None,
        body=[
            raw(''.join(nav)),
            raw('<div class="tab-content config-content">'),
            *panes,
            raw('<div class="d-flex justify-content-end mt-3">'
                '<button class="btn btn-primary" type="submit">'
                '<i class="fa-solid fa-floppy-disk me-1"></i>保存全部配置</button></div>'),
            raw('</div>'),
        ],
    ))

    env_buttons = [
        Button(text=name, size='sm', color='secondary', outline=name != env_file,
               href=f'/LittlePaimon/admin/config?file={name}')
        for name in ENV_FILES
    ]
    body.append(Card(class_name='mt-3', title='环境变量文件', body=[
        Paragraph(body=env_buttons, class_name='mb-3 d-flex flex-wrap gap-2'),
        Paragraph(class_name='small text-secondary',
                  text='保存后会立即写入文件，部分配置需要重启 NoneBot 生效。'),
        Form(method='post', action='/LittlePaimon/admin/config/env', submit_label='保存文件',
             body=[
                 Input(name='file', value=env_file, type='hidden'),
                 Textarea(name='content', rows=16, value=env_content, class_name='font-monospace'),
             ]),
    ]))

    return layout('配置管理', body, active='/LittlePaimon/admin/config', toast=notice)


def read_env(file_name: str) -> str:
    if file_name not in ENV_FILES:
        return ''
    path = Path() / file_name
    return path.read_text(encoding='utf-8') if path.exists() else ''
