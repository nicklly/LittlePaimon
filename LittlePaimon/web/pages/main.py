"""未开启页等公共页面。"""
from __future__ import annotations

from bootstrap_ui import Alert

from ..ui import layout


def blank_page(message: str = '该页面未开启或不存在') -> object:
    return layout('提示', [Alert(color='warning', body=[message])], auth=True)
