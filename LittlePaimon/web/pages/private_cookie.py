"""私人 Cookie 管理页面（添加/修改使用 Bootstrap Modal）。"""
from __future__ import annotations

from typing import Any, List, Optional

from bootstrap_ui import (Alert, Card, Checkbox, Form, Hidden, Input, Modal, Paragraph,
                          Span, Table, TableColumn, Textarea, field, raw)

from ..ui import layout
from .public_cookie import action_form, button_html, cookie_tabs, icon_button, status_badge

ADD_MODAL = 'modal-private-add'


def _form_fields(cookie: Any = None) -> list:
    """添加/编辑表单的公共字段。"""
    return [
        field('QQ号', Input(name='user_id', type='number', required=True,
                            value=cookie.user_id if cookie else None)),
        field('UID', Input(name='uid', type='number', value=cookie.uid if cookie else None),
              help='强制添加时必填，普通添加留空即可'),
        field('米游社ID', Input(name='mys_id', type='number',
                              value=cookie.mys_id if cookie else None),
              help='强制添加时必填'),
        field('Cookie', Textarea(name='cookie', rows=4, required=True,
                                 value=(cookie.cookie or '') if cookie else '')),
        field('Stoken', Textarea(name='stoken', rows=2,
                                 value=(cookie.stoken or '') if cookie else '')),
        field('跳过有效性校验', Checkbox(name='force', switch=True)),
    ]


def private_cookie_page(cookies: List[Any], notice: Optional[tuple] = None) -> object:
    body = [cookie_tabs('private')]

    rows = []
    mobile_cards = []
    modals = []
    for cookie in cookies:
        edit_modal = f'edit-private-{cookie.id}'
        modals.append(Modal(
            id=edit_modal,
            scrollable=True,
            title=f'修改私人 Cookie #{cookie.id}',
            body=[Form(
                method='post', action='/LittlePaimon/admin/cookies/private/update',
                submit_label='保存修改',
                body=[Hidden(name='id', value=cookie.id), *_form_fields(cookie)],
            )],
        ))
        delete_form = action_form(
            '/LittlePaimon/admin/cookies/private/delete', {'id': cookie.id},
            button_html('fa-regular fa-trash-can', '删除', 'danger', outline=True),
            confirm='确认删除该私人 Cookie？',
        )
        rows.append({
            'id': cookie.id,
            'user_id': cookie.user_id,
            'uid': cookie.uid,
            'mys_id': cookie.mys_id,
            'status': status_badge(cookie.status),
            'actions': Span(body=[
                icon_button('fa-solid fa-pen', '编辑', 'primary', modal=edit_modal),
                delete_form,
            ], class_name='d-inline-flex gap-1'),
        })
        mobile_cards.append(Card(class_name='cookie-mobile-card', body=[
            Span(body=[
                Span(text=f'#{cookie.id} · QQ {cookie.user_id}',
                     class_name='cookie-mobile-title'),
                status_badge(cookie.status),
            ], class_name='d-flex justify-content-between align-items-center gap-2'),
            Paragraph(class_name='small text-secondary mt-2 mb-2',
                      text=f'UID：{cookie.uid or "未填写"} · 米游社ID：{cookie.mys_id or "未填写"}'),
            Span(body=[
                icon_button('fa-solid fa-pen', '编辑', 'primary', modal=edit_modal),
                delete_form,
            ], class_name='d-flex gap-2'),
        ]))

    body.append(Card(title='私人 Cookie', body=[
        Paragraph(muted=True, class_name='small mb-3',
                  text='私人 Cookie 只对绑定的 QQ 生效，普通查询会自动写入最近一次使用的账号。'),
        Paragraph(class_name='mb-3', body=[
            icon_button('fa-solid fa-plus', '添加 Cookie', 'primary', modal=ADD_MODAL),
        ]),
        raw('<div class="d-md-none">'),
        *mobile_cards,
        raw('</div>'),
        raw('<div class="d-none d-md-block">'),
        Table(
            columns=[
                TableColumn(label='ID', key='id'),
                TableColumn(label='QQ号', key='user_id'),
                TableColumn(label='UID', key='uid'),
                TableColumn(label='米游社ID', key='mys_id'),
                TableColumn(label='状态', key='status'),
                TableColumn(label='操作', key='actions', nowrap=True),
            ],
            rows=rows,
            hover=True,
            empty_text='暂无私人 Cookie',
        ),
        raw('</div>'),
    ]))

    body.append(Modal(
        id=ADD_MODAL,
        scrollable=True,
        title='添加私人 Cookie',
        body=[Form(
            method='post', action='/LittlePaimon/admin/cookies/private/add',
            submit_label='添加',
            body=_form_fields(),
        )],
    ))
    body.extend(modals)

    return layout('私人 Cookie', body, active='/LittlePaimon/admin/cookies', toast=notice)
