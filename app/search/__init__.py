#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜尋藍圖模組

遵循 .windsurfrules 規範：
- 資料庫搜尋功能
- 進階搜尋頁面
- 查詢結果顯示
- 使用者介面優化

作者：系統管理員
建立日期：2026-03-03
版本：1.0.0
"""

from flask import Blueprint

# 建立搜尋藍圖
bp = Blueprint('search', __name__)

# 匯入路由
from app.search import routes
