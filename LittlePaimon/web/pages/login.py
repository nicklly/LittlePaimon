"""登录页（按效果图重新设计布局）。"""
from __future__ import annotations

from html import escape as html_escape
from typing import Optional

from bootstrap_ui import Alert, Card, Form, Input, raw

from LittlePaimon.utils import __version__

from ..ui import layout

LOGO = 'https://s1.ax1x.com/2023/02/05/pS62DJK.png'
GITHUB_URL = 'https://github.com/CMHopeSunshine/LittlePaimon'
DOCS_URL = 'https://docs.paimon.cherishmoon.top'

USER_ID_TIP = '超级管理员的 QQ 号，在 .env.prod 的 SUPERUSERS 中配置'
PASSWORD_TIP = '在「配置项管理 - Web端配置」的「Web端管理员密码」中查看或修改'


def _label(text: str, tip: str) -> object:
    return raw(
        f'<div class="login-label">{html_escape(text)}<span class="req">*</span>'
        f'<span class="help-icon" data-bs-toggle="tooltip" data-bs-placement="top" '
        f'title="{html_escape(tip)}"><i class="fa-solid fa-circle-question"></i></span></div>'
    )


def login_page(error: Optional[str] = None) -> object:
    body = []
    if error:
        body.append(Alert(color='danger', body=[error]))

    body.append(Card(class_name='login-card', body=[
        raw(f'<div class="login-avatar"><img src="{LOGO}" alt="LittlePaimon"></div>'),
        raw('<div class="login-title">LittlePaimon 控制台</div>'),
        raw(f'<div class="login-version">v{__version__}</div>'),
        Form(
            action='/LittlePaimon/login',
            method='post',
            submit_label=None,
            body=[
                _label('用户ID', USER_ID_TIP),
                Input(name='user_id', required=True, placeholder='请输入用户ID',
                      class_name='login-input'),
                _label('密码', PASSWORD_TIP),
                Input(name='password', type='password', required=True,
                      placeholder='请输入管理员密码', class_name='login-input'),
                raw('<button class="login-btn" type="submit">登录</button>'),
                raw(
                    '<div class="login-footer">'
                    f'<a href="{GITHUB_URL}" target="_blank" rel="noopener">'
                    '<i class="fa-brands fa-github"></i>Github仓库</a>'
                    f'<a href="{DOCS_URL}" target="_blank" rel="noopener">'
                    '<i class="fa-solid fa-book"></i>文档</a>'
                    '</div>'
                ),
            ],
        ),
    ]))
    return layout('登录', body, auth=True)
