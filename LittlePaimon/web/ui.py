"""bootstrap_ui 版 Web 控制台的公共组件、主题与鉴权工具。"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from html import escape as html_escape
from typing import Any, Optional
from urllib.parse import quote

from bootstrap_ui import Page, Paragraph, raw
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jose import JWTError, jwt

from LittlePaimon.config import config
from LittlePaimon.utils import SUPERUSERS, __version__

from .api.utils import ALGORITHM, SECRET_KEY, TOKEN_EXPIRE_MINUTES

TOKEN_COOKIE = 'paimon_token'
FLASH_COOKIE = 'paimon_flash'

FA_CSS = 'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/css/all.min.css'

#: 主题 key -> 显示名称
THEMES = {
    'morandi-green': '莫兰迪绿',
    'morandi-blue': '莫兰迪蓝',
    'morandi-magenta': '莫兰迪品红',
    'morandi-yellow': '莫兰迪黄',
    'morandi-sky': '莫兰迪天蓝',
    'dark': '暗色',
}

#: 旧版本保存的主题值，统一回落到莫兰迪绿
LEGACY_THEMES = {'default': 'morandi-green', 'antd': 'morandi-green', 'ang': 'morandi-green'}

#: 顶部（左侧）导航：(标题, 路径, font-awesome 图标 class)
NAV = [
    ('首页', '/LittlePaimon/admin', 'fa-solid fa-house'),
    ('插件', '/LittlePaimon/admin/plugins', 'fa-solid fa-cubes'),
    ('Cookie', '/LittlePaimon/admin/cookies', 'fa-solid fa-key'),
    ('配置', '/LittlePaimon/admin/config', 'fa-solid fa-sliders'),
    ('命令别名', '/LittlePaimon/admin/alias', 'fa-solid fa-font'),
]

#: 插件可在启动时追加的导航项
EXTRA_NAV: list = []


def register_nav(text: str, href: str, icon: str = 'fa-solid fa-puzzle-piece') -> None:
    """让插件把自己的管理页面挂到左侧导航。"""
    if all(item[1] != href for item in EXTRA_NAV):
        EXTRA_NAV.append((text, href, icon))


def resolve_theme() -> str:
    """当前主题 key（兼容旧配置值）。"""
    value = str(getattr(config, 'admin_theme', 'morandi-green') or 'morandi-green')
    value = LEGACY_THEMES.get(value, value)
    return value if value in THEMES else 'morandi-green'


def theme_options() -> list[tuple[str, str]]:
    return [(label, key) for key, label in THEMES.items()]


# --------------------------------------------------------------------------- 样式

THEME_CSS = r"""
:root {
  --radius-xl: 22px;
  --radius-lg: 18px;
  --radius-md: 13px;
  --radius-sm: 10px;
  --shadow-card: 0 10px 30px rgba(64, 76, 66, .06);
  --shadow-float: 0 18px 45px rgba(64, 76, 66, .10);
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;
}

/* ------------------------- 莫兰迪主题色板 ------------------------- */
.theme-morandi-green {
  --bg: #f1f4f1; --surface: #fbfcfa; --sidebar: #e9efea; --line: #e4eae5;
  --primary: #7f9c88; --primary-strong: #6c8a76; --primary-soft: #e3ece5;
  --text: #3a443d; --muted: #8b968e; --accent: #b8cabb;
}
.theme-morandi-blue {
  --bg: #eff2f6; --surface: #fafbfd; --sidebar: #e6ecf3; --line: #e1e7ee;
  --primary: #7f95ad; --primary-strong: #6b829c; --primary-soft: #e3eaf2;
  --text: #39424d; --muted: #8a94a0; --accent: #b6c4d4;
}
.theme-morandi-magenta {
  --bg: #f5f0f3; --surface: #fcfafb; --sidebar: #f0e6eb; --line: #ece1e7;
  --primary: #a87f95; --primary-strong: #946b82; --primary-soft: #f0e4ea;
  --text: #463a40; --muted: #9b8a92; --accent: #d3b8c5;
}
.theme-morandi-yellow {
  --bg: #f6f2ea; --surface: #fdfbf7; --sidebar: #f1ebdf; --line: #ece4d5;
  --primary: #b99f66; --primary-strong: #a68b52; --primary-soft: #f2ead9;
  --text: #474135; --muted: #9c937f; --accent: #dccba2;
}
.theme-morandi-sky {
  --bg: #eef4f6; --surface: #fafcfd; --sidebar: #e6f0f3; --line: #dfeaee;
  --primary: #7ba2b3; --primary-strong: #67909f; --primary-soft: #e2eef2;
  --text: #36444a; --muted: #86979e; --accent: #b3cdd6;
}
.theme-dark {
  --bg: #22262a; --surface: #2a2f34; --sidebar: #24292e; --line: #3a4148;
  --primary: #8aa88f; --primary-strong: #7a9a80; --primary-soft: #33403a;
  --text: #e8ecee; --muted: #9aa5ad; --accent: #54705c;
}

/* ------------------------- 基础 ------------------------- */
html, body { min-height: 100%; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 14.5px;
  letter-spacing: .01em;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--primary); text-decoration: none; }
a:hover { color: var(--primary-strong); }
h1, h2, h3, h4, h5, h6 { color: var(--text); font-weight: 600; }
.text-secondary, .text-muted { color: var(--muted) !important; }
hr { border-color: var(--line); opacity: 1; }

/* ------------------------- 顶栏 + 左侧导航 ------------------------- */
.app-shell { display: flex; flex-direction: column; min-height: 100vh; background: var(--bg); }
.topbar {
  display: flex; align-items: center; gap: 14px; padding: 10px 18px;
  background: var(--surface); position: sticky; top: 0; z-index: 1040;
  box-shadow: 0 4px 18px rgba(64, 76, 66, .05);
}
.menu-toggle {
  display: none; width: 38px; height: 38px; border: 0; border-radius: 12px;
  background: var(--primary-soft); color: var(--primary-strong);
  align-items: center; justify-content: center; font-size: 15px;
  transition: background .18s, color .18s;
}
.menu-toggle:hover { background: var(--primary); color: #fff; }
.topbar-brand {
  display: flex; align-items: center; gap: 10px;
  font-weight: 700; font-size: 15px; color: var(--text);
}
.topbar-brand:hover { color: var(--text); }
.topbar-logo { width: 28px; height: 28px; border-radius: 9px; object-fit: cover; }
.app-body { display: flex; flex: 1; align-items: flex-start; }
.sidebar {
  width: 240px; flex: 0 0 240px; position: sticky; top: 58px;
  height: calc(100vh - 58px); background: var(--sidebar);
  padding: 20px 14px 16px; display: flex; flex-direction: column;
}
.app-shell.sidebar-collapsed .sidebar { display: none; }
.sidebar-backdrop { display: none; }
.side-nav { display: flex; flex-direction: column; gap: 4px; }
.side-link {
  display: flex; align-items: center; gap: 12px;
  padding: 11px 14px; border-radius: var(--radius-md);
  color: var(--muted); font-size: 14px; transition: all .18s ease;
}
.side-link i { width: 18px; text-align: center; font-size: 15px; }
.side-link:hover { background: var(--primary-soft); color: var(--text); }
.side-link.active { background: var(--primary); color: #fff; box-shadow: 0 8px 20px rgba(64, 76, 66, .16); }
.side-link.active:hover { background: var(--primary); color: #fff; }
.side-foot { margin-top: auto; display: flex; flex-direction: column; gap: 6px; }
.side-ver { font-size: 11px; color: var(--muted); padding: 8px 14px 0; letter-spacing: .03em; }

/* ------------------------- 主内容 ------------------------- */
.app-main { flex: 1; display: flex; padding: 24px 28px; min-width: 0; }
.app-content {
  width: 100%; max-width: 1280px;
  display: flex; flex-direction: column;
}

/* ------------------------- 卡片：扁平、无边框 ------------------------- */
.card {
  border: 0 !important; border-radius: var(--radius-xl); height: auto !important;
  background: var(--surface); box-shadow: var(--shadow-card);
  overflow: hidden;
}
.card-body { border: 0 !important; padding: 24px 26px; }
.card-header {
  border: 0 !important; background: transparent; padding: 20px 26px 0;
  font-weight: 600; font-size: 15px;
}
.card-footer { border: 0 !important; background: transparent; padding: 0 26px 20px; }

/* ------------------------- 按钮 ------------------------- */
.btn {
  border-radius: var(--radius-md); border: 0; font-weight: 500;
  padding: .52rem 1.05rem; transition: all .18s ease; box-shadow: none !important;
}
.btn-sm { border-radius: var(--radius-sm); padding: .3rem .7rem; font-size: 13px; }
.btn-primary { background: var(--primary); color: #fff; }
.btn-primary:hover, .btn-primary:focus { background: var(--primary-strong); color: #fff; }
.btn-secondary { background: var(--accent); color: #fff; }
.btn-secondary:hover { background: var(--primary); color: #fff; }
.btn-outline-primary { border: 1px solid var(--primary); color: var(--primary); background: transparent; }
.btn-outline-primary:hover { background: var(--primary); color: #fff; }
.btn-outline-secondary { border: 1px solid var(--line); color: var(--muted); background: transparent; }
.btn-outline-secondary:hover { background: var(--primary-soft); color: var(--text); }
.btn-outline-danger { border: 1px solid #d8b3b3; color: #b57c7c; background: transparent; }
.btn-outline-danger:hover { background: #b57c7c; color: #fff; }
.btn-outline-success { border: 1px solid var(--primary); color: var(--primary); background: transparent; }
.btn-outline-success:hover { background: var(--primary); color: #fff; }
.btn-outline-warning { border: 1px solid #d9c39a; color: #b39557; background: transparent; }
.btn-outline-warning:hover { background: #b39557; color: #fff; }
.btn-outline-info { border: 1px solid var(--accent); color: var(--muted); background: transparent; }
.btn-info { background: #9fb3c8; color: #fff; }
.btn-info:hover, .btn-info:focus { background: #8aa0b8; color: #fff; }
.btn-danger { background: #b57c7c; color: #fff; }
.btn-danger:hover, .btn-danger:focus { background: #a76e6e; color: #fff; }
.btn-warning { background: #c8ad78; color: #fff; }
.btn-warning:hover, .btn-warning:focus { background: #b99c65; color: #fff; }
.btn-success { background: var(--primary); color: #fff; }
.btn-success:hover { background: var(--primary-strong); color: #fff; }

/* ------------------------- 表单 ------------------------- */
.form-label { font-weight: 500; font-size: 13.5px; color: var(--text); margin-bottom: .45rem; }
.form-control, .form-select {
  border: 1px solid var(--line); border-radius: var(--radius-md);
  background-color: #fff; padding: .6rem .85rem; font-size: 14px; color: var(--text);
  box-shadow: none !important;
}
.theme-dark .form-control, .theme-dark .form-select { background-color: #2f353b; border-color: var(--line); color: var(--text); }
.form-control:focus, .form-select:focus {
  border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-soft) !important;
}
.form-control::placeholder { color: var(--muted); opacity: .8; }
.form-check-input { border-color: var(--line); }
.form-check-input:checked { background-color: var(--primary); border-color: var(--primary); }
.form-check-input:focus { box-shadow: 0 0 0 3px var(--primary-soft); }
.form-text, .help-block { color: var(--muted); font-size: 12.5px; }

/* ------------------------- 表格 ------------------------- */
.table { --bs-table-bg: transparent; margin-bottom: 0; color: var(--text); }
.table > :not(caption) > * > * { border-color: var(--line); padding: .9rem .75rem; }
.table thead th {
  border-bottom: 1px solid var(--line); color: var(--muted);
  font-size: 12px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
}
.table-hover > tbody > tr:hover > * { background: var(--primary-soft); }
.table form { display: inline-block; margin: 0; }

/* ------------------------- 徽章 / 提示 ------------------------- */
.badge { border-radius: var(--radius-sm); font-weight: 600; padding: .42em .7em; letter-spacing: .02em; }
.badge.text-bg-success { background: #cfe0d4 !important; color: #4f6b57 !important; }
.badge.text-bg-danger { background: #eed6d6 !important; color: #9a5f5f !important; }
.badge.text-bg-warning { background: #f0e4c8 !important; color: #8a713c !important; }
.badge.text-bg-secondary { background: #e5e8e5 !important; color: #6f7a72 !important; }
.badge.text-bg-info { background: #dde8f1 !important; color: #4f6b85 !important; }
.alert { border: 0; border-radius: var(--radius-lg); box-shadow: var(--shadow-card); }
.alert-success { background: var(--primary-soft); color: var(--primary-strong); }
.alert-info { background: #e8eef5; color: #5f728a; }
.alert-warning { background: #f5eddb; color: #927a45; }
.alert-danger { background: #f3e2e2; color: #9a5f5f; }

/* ------------------------- 登录 / 绑定页 ------------------------- */
.auth-shell {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 28px; background: var(--bg);
}
.auth-card { width: min(440px, 100%); }
.auth-logo {
  width: 64px; height: 64px; border-radius: 20px; background: var(--primary);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 28px; margin: 0 auto 18px;
}

/* 登录卡片（按效果图） */
.login-card { border-radius: 24px !important; box-shadow: 0 20px 50px rgba(60, 70, 85, .10); }
.login-card .card-body { padding: 38px 36px 26px; }
.login-avatar { display: flex; justify-content: center; margin-bottom: 18px; }
.login-avatar img {
  width: 96px; height: 96px; border-radius: 50%; object-fit: cover;
  border: 3px solid #d97b7b; padding: 3px; background: #fff;
}
.login-title { text-align: center; font-size: 22px; font-weight: 700; letter-spacing: .01em; }
.login-version { text-align: center; font-size: 12.5px; color: var(--muted); margin: 4px 0 26px; }
.login-label {
  display: flex; align-items: center; font-size: 14px; font-weight: 600;
  margin-bottom: 8px; color: var(--text);
}
.login-label .req { color: #d9534f; margin-left: 3px; font-weight: 700; }
.login-label .help-icon { color: #b9c0c4; font-size: 13px; margin-left: 4px; }
.login-card .login-input {
  background: #f6f7f7; border: 1px solid #e9ebeb; height: 46px;
  border-radius: 11px; margin-bottom: 18px; font-size: 14px;
}
.login-card .login-input:focus { background: #fff; }
.login-btn {
  width: 100%; height: 46px; border: 0; border-radius: 11px;
  background: var(--primary-strong); color: #fff; font-weight: 600;
  font-size: 15px; letter-spacing: .05em; transition: background .18s;
}
.login-btn:hover { background: var(--primary); }
.login-footer { display: flex; justify-content: center; gap: 26px; margin-top: 22px; }
.login-footer a {
  color: var(--muted); font-size: 13px;
  display: inline-flex; align-items: center; gap: 6px;
}
.login-footer a:hover { color: var(--primary); }
.help-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 16px; height: 16px; margin-left: 3px; color: var(--muted);
  cursor: help; font-size: 12.5px; vertical-align: -2px;
}
.help-icon:hover { color: var(--primary); }

/* ------------------------- 页面标题 ------------------------- */
.page-head {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 16px; flex-wrap: wrap; margin-bottom: 14px;
}
.page-title { font-size: 26px; font-weight: 700; }
.page-hint { color: var(--muted); font-size: 13px; }

/* ------------------------- 配置页：顶部横向选项卡 ------------------------- */
.config-tabs {
  display: flex; flex-wrap: wrap; align-items: center; gap: 6px;
  background: var(--surface); padding: 8px; border-radius: 16px;
  box-shadow: var(--shadow-card); margin-bottom: 18px;
}
.config-tabs .nav-link {
  display: flex; align-items: center; gap: 8px; border: 0; background: transparent;
  color: var(--muted); padding: 9px 16px; border-radius: 12px; font-size: 13.5px;
}
.config-tabs .nav-link i { font-size: 13px; }
.config-tabs .nav-link:hover { background: var(--primary-soft); color: var(--text); }
.config-tabs .nav-link.active {
  background: var(--primary-soft); color: var(--primary-strong); font-weight: 600;
}
.config-tabs .nav-item.ms-auto { margin-left: auto; }
.tab-bell {
  border: 0; background: transparent; color: var(--muted);
  padding: 9px 14px; border-radius: 12px; font-size: 15px;
}
.tab-bell:hover { background: var(--primary-soft); color: var(--text); }

/* ------------------------- 配置页：竖排选项卡 ------------------------- */
.config-grid { display: grid; grid-template-columns: 196px minmax(0, 1fr); gap: 20px; align-items: start; }
.config-menu {
  position: sticky; top: 24px; display: flex; flex-direction: column; gap: 4px;
  background: var(--surface); border-radius: var(--radius-lg); padding: 10px;
  box-shadow: var(--shadow-card);
}
.config-menu .nav-link,
.config-menu a {
  display: flex; align-items: center; gap: 10px; padding: 9px 12px; width: 100%;
  border: 0; border-radius: var(--radius-sm); background: transparent;
  color: var(--muted); font-size: 13.5px; text-align: left;
}
.config-menu .nav-link i,
.config-menu a i { width: 16px; text-align: center; }
.config-menu .nav-link:hover,
.config-menu a:hover { background: var(--primary-soft); color: var(--text); }
.config-menu .nav-link.active,
.config-menu a.active { background: var(--primary); color: #fff; }
.config-content { min-width: 0; }
.config-content .tab-pane > .card,
.config-content > .card { margin-bottom: 0; }
.config-section { scroll-margin-top: 24px; margin-bottom: 0; }
.section-title { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; font-size: 15px; font-weight: 600; }
.section-title i { color: var(--primary); }

/* ------------------------- 模态框 ------------------------- */
.modal-content { border: 0; border-radius: var(--radius-xl); background: var(--surface); box-shadow: var(--shadow-float); }
.modal-header { border: 0; padding: 22px 26px 6px; }
.modal-title { font-size: 16px; font-weight: 600; }
.modal-body { padding: 14px 26px 4px; }
.modal-footer { border: 0; padding: 16px 26px 24px; }
.modal-backdrop.show { opacity: .28; }

/* 模态框内表单紧凑排版，尽量避免出现内部滚动条 */
.modal .modal-header { padding: 18px 24px 4px; }
.modal .modal-body { padding: 10px 24px 20px; }
.modal .modal-footer { padding: 10px 24px 18px; }
.modal .form-label { margin-bottom: .35rem; font-size: 13px; }
.modal .form-control, .modal .form-select {
  padding: .45rem .7rem; font-size: 13.5px; border-radius: 10px;
}
.modal .mb-3 { margin-bottom: .85rem !important; }
.modal .form-text { font-size: 11.5px; margin-top: .15rem; }
.modal .form-check-input { margin-top: .15em; }
.modal .row.g-3 { --bs-gutter-y: .35rem; }
/* 保存按钮统一放到 Modal 右下角，并与底部留出间距 */
.modal .modal-body form > .d-flex.gap-2.mt-4 {
  justify-content: flex-end; margin-top: 1.35rem !important; margin-bottom: .45rem;
}
.modal .modal-body form > .d-flex.gap-2.mt-4 .btn { min-width: 86px; }

/* ------------------------- 快捷操作：三等分等高卡片 ------------------------- */
.quick-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.quick-tile {
  display: flex; flex-direction: column; justify-content: space-between; gap: 14px;
  margin: 0; padding: 16px; border-radius: var(--radius-lg); background: var(--bg);
}
.quick-head { display: flex; gap: 12px; align-items: flex-start; }
.quick-icon {
  width: 34px; height: 34px; flex: 0 0 34px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  background: var(--primary-soft); color: var(--primary);
}
.quick-title { font-weight: 600; font-size: 14px; }
.quick-desc { font-size: 12.5px; color: var(--muted); margin-top: 2px; line-height: 1.5; }
.quick-tile .btn { margin-top: auto; }
.quick-control { margin-top: auto; }

/* ------------------------- 插件卡片 ------------------------- */
.plugin-card { height: 100% !important; display: flex; flex-direction: column; }
.plugin-card .card-body { display: flex; flex-direction: column; height: 100%; gap: 6px; }
.plugin-name { font-weight: 600; font-size: 15px; }
.plugin-module { font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 12px; color: var(--muted); }
.plugin-desc { font-size: 13px; color: var(--muted); min-height: 40px; margin-bottom: 0; }
.plugin-actions { display: flex; gap: 8px; margin-top: auto; padding-top: 12px; }

/* ------------------------- Cookie 子导航 ------------------------- */
.cookie-tabs {
  display: inline-flex; align-self: flex-start; gap: 6px; padding: 6px; border-radius: 16px;
  background: var(--surface); box-shadow: var(--shadow-card); margin-bottom: 18px;
}
.cookie-tab {
  display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px;
  border-radius: 12px; color: var(--muted); font-size: 13.5px;
}
.cookie-tab:hover { background: var(--primary-soft); color: var(--text); }
.cookie-tab.active { background: var(--primary); color: #fff; }

/* ------------------------- 右下角提示 Toast ------------------------- */
.toast-container { z-index: 1090; }
.toast-msg {
  border: 0 !important; border-radius: 14px; min-width: 260px;
  background: var(--surface); color: var(--text); box-shadow: var(--shadow-float);
}
.toast-msg .toast-body { font-size: 13.5px; font-weight: 500; padding: 12px 14px; }
.toast-msg.toast-success { background: #eef5f0; }
.toast-msg.toast-success i { color: #5f8a6b; }
.toast-msg.toast-danger { background: #f7eaea; }
.toast-msg.toast-danger i { color: #a76e6e; }
.toast-msg.toast-warning { background: #f8f1e2; }
.toast-msg.toast-warning i { color: #a68b52; }
.toast-msg.toast-info { background: #eaf1f7; }
.toast-msg.toast-info i { color: #5f7d99; }

/* ------------------------- 分页 ------------------------- */
.pager { display: flex; justify-content: center; margin-top: 18px; }
.pager .pagination { gap: 6px; margin: 0; }
.pager .page-link {
  border: 0; border-radius: 10px; background: transparent; color: var(--muted);
  padding: .4rem .8rem; font-size: 13.5px;
}
.pager .page-link:hover { background: var(--primary-soft); color: var(--text); }
.pager .page-item.active .page-link { background: var(--primary); color: #fff; }
.pager .page-item.disabled .page-link { opacity: .45; pointer-events: none; }

/* ------------------------- 其他 ------------------------- */
pre, .font-monospace { font-family: "JetBrains Mono", "Cascadia Code", Consolas, monospace; }
pre { background: var(--primary-soft); border: 0 !important; border-radius: var(--radius-lg); color: var(--text); }
.log-box { height: 420px; overflow: auto; white-space: pre-wrap; margin-bottom: 0; }
.list-group-item { border-color: var(--line); background: transparent; }
.accordion-item { border: 0; background: transparent; }
.accordion-button { background: var(--surface); color: var(--text); box-shadow: none; border-radius: var(--radius-md) !important; }
.accordion-button:not(.collapsed) { background: var(--primary-soft); color: var(--text); }
.dropdown-menu { border: 0; border-radius: var(--radius-md); box-shadow: var(--shadow-float); }

/* 私人 Cookie 手机端卡片 */
.cookie-mobile-card { margin-bottom: 10px; }
.cookie-mobile-card .card-body { padding: 14px 16px; }
.cookie-mobile-title { font-weight: 600; font-size: 14px; }

@media (max-width: 992px) {
  .app-main { padding: 20px; }
  .config-grid { grid-template-columns: 1fr; }
  .config-menu { position: static; flex-direction: row; flex-wrap: wrap; }
  .quick-grid { grid-template-columns: 1fr; }
}

/* 手机端：侧边栏变为抽屉，由顶栏的菜单按钮控制 */
@media (max-width: 768px) {
  .menu-toggle { display: flex; }
  .sidebar {
    position: fixed; top: 58px; bottom: 0; left: 0; height: auto;
    width: 240px; flex-basis: 240px; z-index: 1050;
    transform: translateX(-100%); transition: transform .22s ease;
    box-shadow: 14px 0 40px rgba(40, 45, 42, .16);
    overflow-y: auto;
  }
  .app-shell.drawer-open .sidebar { transform: translateX(0); }
  .app-shell.drawer-open .sidebar-backdrop {
    display: block; position: fixed; inset: 58px 0 0 0;
    background: rgba(40, 45, 42, .30); z-index: 1045;
  }
  .app-shell.sidebar-collapsed .sidebar { display: flex; transform: translateX(-100%); }
  .app-main { padding: 14px; }
  .app-content { min-height: auto; }
  .log-box { height: 260px; }
  .card-body { padding: 18px 16px; }
  .login-card .card-body { padding: 28px 22px 20px; }
}
"""

BASE_JS = """
document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
  new bootstrap.Tooltip(el);
});

function toggleSidebar() {
  var shell = document.querySelector('.app-shell');
  if (!shell) return;
  if (window.innerWidth <= 768) {
    shell.classList.toggle('drawer-open');
  } else {
    shell.classList.toggle('sidebar-collapsed');
  }
}

function closeSidebar() {
  var shell = document.querySelector('.app-shell');
  if (shell) shell.classList.remove('drawer-open');
}
"""

LOGO_URL = 'https://s1.ax1x.com/2023/02/05/pS62DJK.png'


# --------------------------------------------------------------------------- 布局

def _topbar() -> Any:
    return raw(
        '<header class="topbar">'
        '<button class="menu-toggle" type="button" onclick="toggleSidebar()" '
        'aria-label="菜单"><i class="fa-solid fa-bars"></i></button>'
        '<a class="topbar-brand" href="/LittlePaimon/admin">'
        f'<img class="topbar-logo" src="{LOGO_URL}" alt="LittlePaimon">'
        '<span>LittlePaimon</span></a>'
        '</header>'
    )


def _sidebar(active: str) -> Any:
    links = []
    for text, href, icon in [*NAV, *EXTRA_NAV]:
        is_active = active == href or (href != '/LittlePaimon/admin' and active.startswith(href))
        links.append(
            f'<a class="side-link{" active" if is_active else ""}" href="{html_escape(href)}">'
            f'<i class="{icon}"></i><span>{html_escape(text)}</span></a>'
        )
    return raw(
        '<aside class="sidebar">'
        f'<nav class="side-nav">{"".join(links)}</nav>'
        '<div class="side-foot">'
        '<a class="side-link" href="/LittlePaimon/logout">'
        '<i class="fa-solid fa-arrow-right-from-bracket"></i><span>退出登录</span></a>'
        f'<div class="side-ver">v{__version__} · bootstrap-python</div>'
        '</div></aside>'
    )


TOAST_ICONS = {
    'success': 'fa-solid fa-circle-check',
    'danger': 'fa-solid fa-circle-exclamation',
    'warning': 'fa-solid fa-triangle-exclamation',
    'info': 'fa-solid fa-circle-info',
}


def toast_message(tone: str, message: str) -> Any:
    """右下角自动消失的提示条。"""
    tone = tone if tone in TOAST_ICONS else 'info'
    icon = TOAST_ICONS[tone]
    return raw(
        '<div class="toast-container position-fixed bottom-0 end-0 p-3">'
        f'<div class="toast toast-msg toast-{tone}" role="status" aria-live="polite" '
        'aria-atomic="true" data-bs-delay="4000">'
        '<div class="d-flex align-items-center">'
        f'<div class="toast-body d-flex align-items-center gap-2">'
        f'<i class="{icon}"></i><span>{html_escape(str(message))}</span></div>'
        '<button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" '
        'aria-label="关闭"></button>'
        '</div></div></div>'
    )


def layout(title: str, body: Any, *, active: str = '', js: Optional[str] = None,
           auth: bool = False, toast: Optional[tuple[str, str]] = None) -> Page:
    """生成整页：管理页带左侧栏，登录/绑定页居中。"""
    if not isinstance(body, (list, tuple)):
        body = [body]
    if auth:
        content = [raw('<div class="auth-shell"><div class="auth-card">'), *body, raw('</div></div>')]
    else:
        content = [
            raw('<div class="app-shell">'),
            _topbar(),
            raw('<div class="app-body">'),
            _sidebar(active),
            raw('<main class="app-main"><div class="app-content">'),
            *body,
            raw('</div></main>'),
            raw('</div>'),
            raw('<div class="sidebar-backdrop" onclick="closeSidebar()"></div>'),
            raw('</div>'),
        ]
    if toast:
        content.append(toast_message(toast[0], toast[1]))
    return Page(
        title=f'{title} | LittlePaimon',
        lang='zh-CN',
        body=list(content),
        container=False,
        icons=False,
        css=[FA_CSS],
        custom_css=THEME_CSS,
        custom_js=BASE_JS + (js or ''),
        body_class=f'theme-{resolve_theme()}',
    )


def field_with_help(label: str, control: Any, tip: str) -> Any:
    """带 ? 图标提示的表单项。"""
    return raw(
        f'<div class="mb-3">'
        f'<label class="form-label">{html_escape(label)}'
        f'<span class="help-icon" data-bs-toggle="tooltip" data-bs-placement="top" '
        f'title="{html_escape(tip)}"><i class="fa-regular fa-circle-question"></i></span>'
        f'</label>{control.render()}</div>'
    )


def pager(current: int, total: int, base: str) -> Any:
    """Bootstrap 分页控件；页码走路径（``/base/page/N``），不产生查询参数。"""
    total = max(1, int(total))
    current = min(max(1, int(current)), total)
    if total <= 1:
        return raw('')

    def link(number: int, label: Optional[str] = None, *, active: bool = False,
             disabled: bool = False) -> str:
        classes = 'page-item'
        if active:
            classes += ' active'
        if disabled:
            classes += ' disabled'
        return (f'<li class="{classes}"><a class="page-link" '
                f'href="{base}/page/{number}">{label or number}</a></li>')

    items: list[str] = []
    items.append(link(current - 1, '‹', disabled=current <= 1) if current > 1
                 else '<li class="page-item disabled"><span class="page-link">‹</span></li>')

    start = max(1, current - 2)
    end = min(total, start + 4)
    start = max(1, end - 4)
    if start > 1:
        items.append(link(1))
        if start > 2:
            items.append('<li class="page-item disabled"><span class="page-link">…</span></li>')
    for number in range(start, end + 1):
        items.append(link(number, active=number == current))
    if end < total:
        if end < total - 1:
            items.append('<li class="page-item disabled"><span class="page-link">…</span></li>')
        items.append(link(total))

    items.append(link(current + 1, '›', disabled=current >= total) if current < total
                 else '<li class="page-item disabled"><span class="page-link">›</span></li>')
    return raw(f'<nav class="pager"><ul class="pagination">{"".join(items)}</ul></nav>')


def render(page: Page) -> HTMLResponse:
    resp = HTMLResponse(page.render())
    # 一次性提示读完即删，避免刷新后重复出现
    resp.delete_cookie(FLASH_COOKIE, path='/LittlePaimon')
    return resp


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def flash_redirect(url: str, msg: str, kind: str = 'success') -> RedirectResponse:
    """操作完成后重定向到干净的 URL，提示信息通过临时 Cookie 传递。"""
    resp = redirect(url)
    payload = base64.urlsafe_b64encode(
        json.dumps({'msg': msg, 'kind': kind}, ensure_ascii=False).encode('utf-8')
    ).decode('ascii')
    resp.set_cookie(FLASH_COOKIE, payload, max_age=30, httponly=True, samesite='lax',
                    path='/LittlePaimon')
    return resp


# ---------------------------------------------------------------- 鉴权

def _decode(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get('user_id'))
    except (JWTError, TypeError, ValueError, KeyError):
        return None
    return user_id if user_id in SUPERUSERS else None


def current_user(request: Request) -> Optional[int]:
    """从 Cookie 中解析当前登录的超级用户。"""
    token = request.cookies.get(TOKEN_COOKIE)
    return _decode(token) if token else None


def guard(request: Request) -> Optional[RedirectResponse]:
    """页面用鉴权：未登录则跳转登录页。"""
    if current_user(request) is None:
        target = request.url.path
        return redirect(f'/LittlePaimon/login?next={quote(target)}')
    return None


def login_response(request: Request, user_id: int, next_url: Optional[str] = None) -> RedirectResponse:
    token = jwt.encode(
        {
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    resp = redirect(next_url or '/LittlePaimon/admin')
    resp.set_cookie(TOKEN_COOKIE, token, max_age=TOKEN_EXPIRE_MINUTES * 60,
                    httponly=True, samesite='lax')
    return resp


def logout_response() -> RedirectResponse:
    resp = redirect('/LittlePaimon/login')
    resp.delete_cookie(TOKEN_COOKIE)
    return resp


def notice(request: Request) -> Optional[tuple[str, str]]:
    """读取一次性提示（临时 Cookie），返回 (bootstrap 颜色, 文本)。"""
    token = request.cookies.get(FLASH_COOKIE)
    if not token:
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(token.encode('ascii')).decode('utf-8'))
    except (ValueError, TypeError):
        return None
    msg = str(data.get('msg') or '')
    if not msg:
        return None
    kind = data.get('kind') or 'success'
    if kind not in {'success', 'danger', 'warning', 'info'}:
        kind = 'success'
    return kind, msg
