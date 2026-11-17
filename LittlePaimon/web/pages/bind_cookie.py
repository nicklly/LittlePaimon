"""面向普通用户的 Cookie 绑定页面。"""
from __future__ import annotations

from typing import Optional

from bootstrap_ui import (Accordion, AccordionItem, Alert, Card, Form, Heading, Input,
                          Paragraph, Textarea, field, raw)

from ..ui import layout


def bind_cookie_page(result: Optional[str] = None, ok: bool = True) -> object:
    body = []
    if result:
        body.append(Alert(color='success' if ok else 'danger', body=[result]))

    body.append(Card(body=[
        raw('<div class="auth-logo"><i class="fa-solid fa-link"></i></div>'),
        Heading(level=4, text='绑定米游社 Cookie', class_name='text-center mb-1'),
        Paragraph(muted=True, class_name='text-center small mb-4',
                  text='绑定后机器人可以免密码查询你的原神数据'),
        Accordion(class_name='mb-4', items=[
            AccordionItem(title='Cookie 安全说明与获取方法', body=[
                Paragraph(text='Cookie 的作用相当于账号密码，请仅在你信任的机器人上绑定。'),
                Paragraph(muted=True, class_name='small',
                          text='获取方法：浏览器登录米游社后，从开发者工具中复制完整 Cookie 字符串。'),
                Paragraph(muted=True, class_name='small mb-0',
                          text='绑定成功后 Cookie 会保存在机器人数据库中，可随时联系管理员删除。'),
            ]),
        ]),
        Form(
            action='/LittlePaimon/cookie',
            method='post',
            submit_label='绑 定',
            body=[
                field('QQ号', Input(name='user_id', required=True, placeholder='你的 QQ 号')),
                field('Cookie', Textarea(name='cookie', rows=5, required=True,
                                         placeholder='粘贴完整的 Cookie 字符串')),
            ],
        ),
    ]))
    return layout('绑定 Cookie', body, auth=True)
