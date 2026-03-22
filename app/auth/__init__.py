#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
認證藍圖模組

遵循 .windsurfrules 規範：
- 使用者登入系統
- Session 機制管理
- 存取日誌記錄
- 管理員驗證

作者：系統管理員
建立日期：2026-03-03
版本：1.0.0
"""

from flask import Blueprint

# 建立認證藍圖
bp = Blueprint('auth', __name__)

# 匯入路由
from app.auth import routes
