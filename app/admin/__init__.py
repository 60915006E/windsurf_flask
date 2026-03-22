#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理藍圖模組

遵循 .windsurfrules 規範：
- 後台管理功能
- 使用者管理
- 系統監控
- 設定管理

作者：系統管理員
建立日期：2026-03-03
版本：1.0.0
"""

from flask import Blueprint

# 建立管理藍圖
bp = Blueprint('admin', __name__)

# 匯入路由
from app.admin import routes
