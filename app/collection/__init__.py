"""
動態主題館管理模組

提供專題館的建立、管理、排程更新等功能
"""

from flask import Blueprint

# 建立專題館藍圖
bp = Blueprint('collection', __name__, url_prefix='/collection')

# 導入路由
from . import routes
