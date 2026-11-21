from __future__ import annotations
from typing import Optional, Any, List

from LittlePaimon.web.pages.public_cookie import cookie_tabs, icon_button, action_form, button_html
from bootstrap_ui import Card, Paragraph, raw, Table, TableColumn, Span, Form, Modal, Hidden, field, Input, Textarea, \
    Button, Small
from LittlePaimon.web.ui import layout

def _form_fields(devices: Any = None) -> list:
    """添加/编辑表单的公共字段。"""
    return [
        field('QQ号', Input(
                name='user_id',
                type='number',
                required=True,
                value=devices.user_id if devices else None
            )
        ),
        field('UID', Input(
                name='uid',
                type='number',
                value=devices.uid if devices else None
            ),
            help='强制添加时必填，普通添加留空即可'
        ),
        field('设备ID', Input(
                name='mys_id',
                type='text',
                value=devices.device_id if devices else None
            ),
            help='强制添加时必填'
        ),
        field('设备名字', Input(
                name='name',
                required=True,
                value=(devices.device_name or '') if devices else ''
            )
        ),
        field('设备型号', Input(
                name='model',
                required=True,
                value=(devices.device_model or '') if devices else ''
            )
        ),
        field('设备fp（设备指纹）', Input(
                name='model',
                required=True,
                value=(devices.device_fp or '') if devices else ''
            )
        )
    ]


def user_devices_page(devices: List[Any], notice: Optional[tuple] = None) -> object:
    body = [cookie_tabs('devices')]
    rows = []
    modals = []
    mobile_cards = []
    for device in devices:
        delete_form = action_form(
            '/LittlePaimon/admin/cookies/device/delete', {'id': device.id},
            button_html('fa-regular fa-trash-can', '删除', 'danger', outline=True),
            confirm='确认删除该设备信息？删除设备信息会连同cookie信息一并删除哦',
        )
        mobile_cards.append(
            Card(
                class_name = 'cookie-mobile-card',
                body = [
                    Span(
                        body = [
                            Span(
                                text = f'#{device.id} · QQ {device.user_id}',
                                class_name = 'cookie-mobile-title'),
                        ],
                        class_name = 'd-flex justify-content-between align-items-center gap-2'),
                    Paragraph(
                        class_name = 'small text-secondary mt-2 mb-2',
                        text = f'UID：{device.uid or "未填写"} · {device.device_name} / {device.device_model}',
                    ),
                    Small(
                        class_name = 'small text-secondary mt-2 mb-2',
                        text = f'设备ID：{device.device_id}',
                    )
                ]
            )
        ),
        rows.append({
            'id': device.id,
            'user_id': device.user_id,
            'uid': device.uid,
            'device_id': device.device_id,
            'device_name': device.device_name,
            'device_model': device.device_model,
            'device_fp': device.device_fp
        })

    body.append(
        Card(
            title = '用户设备 Devices',
            body = [
                Paragraph(
                    muted = True,
                    class_name = 'small mb-3',
                    text = '拟真设备信息，只对绑定的QQ生效，用于验证部分mihoyo接口'
                ),
                raw('<div class="d-md-none">'),
                *mobile_cards,
                raw('</div>'),
                raw('<div class="d-none d-md-block">'),
                Table(
                    columns=[
                        TableColumn(label = 'ID', key = 'id', width = 10),
                        TableColumn(label = 'QQ号', key = 'user_id', width = 30),
                        TableColumn(label = 'UID', key = 'uid', width = 30),
                        TableColumn(label = '设备ID', key = 'device_id', width = 350),
                        TableColumn(label = '设备名', key = 'device_name', width = 180),
                        TableColumn(label = '设备型号', key = 'device_model', width = 120),
                        TableColumn(label = '设备fp', key = 'device_fp')
                    ],
                    rows=rows,
                    hover=True,
                    empty_text = '暂无用户设备 Devices',
                ),
                raw('</div>'),
            ])
    )

    body.extend(modals)
    return layout('私人 Cookie', body, active= '/LittlePaimon/admin/cookies', toast = notice)

