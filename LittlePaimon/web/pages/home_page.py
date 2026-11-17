"""首页仪表盘。"""
from __future__ import annotations

from typing import Any, Dict

from bootstrap_ui import (Alert, Badge, Button, Card, Col, Form, Heading, Hr, Input,
                          Paragraph, Row, raw)

from ..ui import layout

LOG_JS = """
async function refreshLog() {
  const levelSelect = document.getElementById('log-level');
  const box = document.getElementById('log-box');
  if (!levelSelect || !box) return;
  try {
    const resp = await fetch('/LittlePaimon/admin/logs?level=' + levelSelect.value + '&num=200',
                             {credentials: 'same-origin'});
    box.textContent = await resp.text();
    box.scrollTop = box.scrollHeight;
  } catch (err) {
    box.textContent = '日志获取失败：' + err;
  }
}
if (location.protocol === 'http:' || location.protocol === 'https:') {
  setInterval(function () {
    const auto = document.getElementById('log-auto');
    if (auto && auto.checked) refreshLog();
  }, 3000);
  refreshLog();
}
"""


def _stat_card(title: str, value: Any) -> Card:
    return Card(body=[
        Paragraph(muted=True, class_name='small mb-1', text=title),
        Heading(level=4, text=str(value if value is not None else '未知'), class_name='mb-0'),
    ])


def home_page(status: Dict[str, Any], notice: Any = None) -> object:
    body = []

    body.append(Row(gutter=3, children=[
        Col(width=6, md=3, body=[_stat_card('Bot 昵称', status.get('nickname'))]),
        Col(width=6, md=3, body=[_stat_card('Bot QQ', status.get('bot_id'))]),
        Col(width=6, md=3, body=[_stat_card('Bot 启动时间', status.get('start_time'))]),
        Col(width=6, md=3, body=[_stat_card('系统启动时间', status.get('system_start_time'))]),
    ]))
    body.append(Row(gutter=3, class_name='mt-1', children=[
        Col(width=6, md=3, body=[_stat_card('已接收消息', status.get('msg_received'))]),
        Col(width=6, md=3, body=[_stat_card('已发送消息', status.get('msg_sent'))]),
        Col(width=4, md=2, body=[_stat_card('CPU 占用', status.get('cpu_percent'))]),
        Col(width=4, md=2, body=[_stat_card('内存占用', status.get('ram_percent'))]),
        Col(width=4, md=2, body=[_stat_card('SWAP 占用', status.get('swap_percent'))]),
    ]))

    body.append(Card(class_name='mt-3', title='快捷操作', body=[
        raw("""
<div class="quick-grid">
  <form class="quick-tile" method="post" action="/LittlePaimon/admin/bot/update">
    <div class="quick-head">
      <span class="quick-icon"><i class="fa-solid fa-rotate"></i></span>
      <div>
        <div class="quick-title">检查并更新</div>
        <div class="quick-desc">检查项目更新，更新后需要重启才会生效</div>
      </div>
    </div>
    <button class="btn btn-info w-100" type="submit">
      <i class="fa-solid fa-rotate me-1"></i>检查并更新
    </button>
  </form>

  <form class="quick-tile" method="post" action="/LittlePaimon/admin/bot/restart"
        onsubmit="return confirm('确认重启 Bot？重启期间页面会暂时不可访问。')">
    <div class="quick-head">
      <span class="quick-icon"><i class="fa-solid fa-power-off"></i></span>
      <div>
        <div class="quick-title">重启 Bot</div>
        <div class="quick-desc">重启进程，页面会短暂失联</div>
      </div>
    </div>
    <button class="btn btn-danger w-100" type="submit">
      <i class="fa-solid fa-power-off me-1"></i>重启 Bot
    </button>
  </form>

  <form class="quick-tile" method="post" action="/LittlePaimon/admin/run_cmd">
    <div class="quick-head">
      <span class="quick-icon"><i class="fa-solid fa-terminal"></i></span>
      <div>
        <div class="quick-title">执行命令</div>
        <div class="quick-desc">在机器人所在主机执行 shell 命令</div>
      </div>
    </div>
    <div class="quick-control">
      <input class="form-control" type="text" name="cmd"
             placeholder="输入要执行的 shell 命令" required>
    </div>
    <button class="btn btn-warning w-100" type="submit">
      <i class="fa-solid fa-terminal me-1"></i>执行命令
    </button>
  </form>
</div>
"""),
    ]))

    body.append(Card(class_name='mt-3', title='运行日志', body=[
        raw("""
<div class="d-flex flex-wrap gap-2 align-items-center mb-3">
  <select id="log-level" class="form-select form-select-sm" style="width:auto">
    <option value="info">INFO</option>
    <option value="debug">DEBUG</option>
  </select>
  <button type="button" class="btn btn-sm btn-outline-secondary" onclick="refreshLog()">立即刷新</button>
  <div class="form-check form-switch">
    <input class="form-check-input" type="checkbox" id="log-auto" checked>
    <label class="form-check-label small" for="log-auto">自动刷新</label>
  </div>
  <span class="small text-secondary">DEBUG 日志需要 NoneBot 日志等级为 DEBUG</span>
</div>
<pre id="log-box" class="log-box border rounded p-3 small bg-body-tertiary">加载中…</pre>
"""),
    ]))

    return layout('首页', body, active='/LittlePaimon/admin', js=LOG_JS, toast=notice)
