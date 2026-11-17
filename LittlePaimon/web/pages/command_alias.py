"""命令别名管理页面。"""
from __future__ import annotations

from typing import Any, List, Optional

from bootstrap_ui import (Alert, Badge, Button, Card, Checkbox, Form, Hidden, Input,
                          Paragraph, Row, Col, Select, Span, Table, TableColumn, field)

from ..ui import layout
from .public_cookie import action_form, button_html

MODE_OPTIONS = [('前缀', '前缀'), ('后缀', '后缀'), ('全匹配', '全匹配')]


def alias_page(aliases: List[Any], enabled: bool, notice: Optional[tuple] = None,
               test_result: Optional[str] = None) -> object:
    body = []

    rows = []
    for alias in aliases:
        delete_form = action_form(
            '/LittlePaimon/admin/alias/delete', {'id': alias.id},
            button_html('fa-regular fa-trash-can', '删除', 'danger', outline=True),
            confirm='确认删除该命令别名？',
        )
        rows.append({
            'id': alias.id,
            'alias': alias.alias,
            'command': alias.command,
            'mode': '正则' if alias.is_regex else alias.mode,
            'reverse': '是' if alias.is_reverse else '否',
            'group': '全群' if str(alias.group_id) == 'all' else alias.group_id,
            'priority': alias.priority,
            'actions': Span(body=[delete_form]),
        })

    toggle_form = Form(
        method='post', action='/LittlePaimon/admin/alias/toggle', submit_label='保存开关',
        body=[field('功能开关', Checkbox(name='enable', switch=True, checked=enabled))],
    )

    body.append(Card(title='命令别名', body=[
        Paragraph(muted=True, class_name='small',
                  text='把消息中的文本替换成另一个命令；正则模式下按正则替换。'),
        toggle_form,
        Table(
            columns=[
                TableColumn(label='ID', key='id'),
                TableColumn(label='别名', key='alias'),
                TableColumn(label='原命令', key='command'),
                TableColumn(label='匹配模式', key='mode'),
                TableColumn(label='反转', key='reverse', align='center'),
                TableColumn(label='生效群', key='group'),
                TableColumn(label='优先级', key='priority', align='center'),
                TableColumn(label='操作', key='actions', nowrap=True),
            ],
            rows=rows,
            hover=True,
            empty_text='暂无命令别名',
        ),
    ]))

    body.append(Card(class_name='mt-3', title='添加命令别名', body=[
        Form(
            method='post', action='/LittlePaimon/admin/alias/add', submit_label='添加',
            body=[
                Row(gutter=3, children=[
                    Col(md=6, body=[field('命令别名', Input(name='alias', required=True))]),
                    Col(md=6, body=[field('原命令', Input(name='command', required=True))]),
                    Col(md=4, body=[field('匹配模式', Select(name='mode', options=MODE_OPTIONS,
                                                        value='前缀'))]),
                    Col(md=4, body=[field('生效群', Input(name='group_id', value='all'),
                                          help='填 all 表示所有群')]),
                    Col(md=4, body=[field('优先级', Input(name='priority', type='number', value=99))]),
                    Col(md=6, body=[field('正则匹配', Checkbox(name='is_regex', switch=True))]),
                    Col(md=6, body=[field('是否反转', Checkbox(name='is_reverse', switch=True))]),
                ]),
            ],
        ),
    ]))

    test_card_body = [
        Form(
            method='post', action='/LittlePaimon/admin/alias/test', submit_label='测试',
            body=[
                Row(gutter=3, children=[
                    Col(md=4, body=[field('测试群', Input(name='group_id', value='all'))]),
                    Col(md=8, body=[field('测试消息', Input(name='message', required=True))]),
                ]),
            ],
        ),
    ]
    if test_result is not None:
        test_card_body.append(Alert(color='info', class_name='mt-3', body=[
            Paragraph(class_name='mb-1', text='替换后的消息：'),
            Paragraph(class_name='mb-0 font-monospace', text=test_result),
        ]))
    body.append(Card(class_name='mt-3', title='测试', body=test_card_body))

    return layout('命令别名', body, active='/LittlePaimon/admin/alias', toast=notice)
