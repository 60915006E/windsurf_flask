#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask 應用程式入口點

遵循 .windsurfrules 規範：
- 應用程式工廠模式
- 開發與生產環境配置
- 除錯模式設定
- 安全性配置

作者：系統管理員
建立日期：2026-03-03
版本：1.0.0
"""

import os
import sys
from app import create_app

def check_environment():
    """檢查運行環境"""
    print("🔍 檢查運行環境...")
    
    # 檢查 Python 版本
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 版本過低: {version.major}.{version.minor}.{version.micro}")
        print("   建議使用 Python 3.8 或更高版本")
        return False
    
    print(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    # 檢查必要檔案
    required_files = ['app', 'config.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要檔案: {file}")
            return False
    
    print("✅ 必要檔案檢查通過")
    return True

def main():
    """
    主函數 - 啟動 Flask 應用程式
    
    根據環境變數設定不同的運行模式：
    - 開發環境：啟用除錯模式
    - 生產環境：關閉除錯模式，設定安全配置
    """
    # 檢查環境
    if not check_environment():
        print("❌ 環境檢查失敗，無法啟動應用程式")
        sys.exit(1)
    
    # 取得環境配置
    env = os.environ.get('FLASK_ENV', 'development')
    
    try:
        # 建立應用程式實例
        app = create_app(env)
        print("✅ Flask 應用程式建立成功")
    except Exception as e:
        print(f"❌ Flask 應用程式建立失敗: {str(e)}")
        sys.exit(1)
    
    # 根據環境設定不同的配置
    if env == 'development':
        # 開發環境配置
        app.config['DEBUG'] = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        host = '127.0.0.1'
        port = 5000
        print("🚀 開發模式啟動...")
        print(f"🌐 服務地址: http://{host}:{port}")
        print("🔧 除錯模式已啟用")
    else:
        # 生產環境配置
        app.config['DEBUG'] = False
        host = os.environ.get('HOST', '0.0.0.0')  # 監聽所有網路介面
        port = int(os.environ.get('PORT', 5000))
        print("🚀 生產模式啟動...")
        print(f"🌐 服務地址: http://{host}:{port}")
        print("🛡️ 安全模式已啟用")
    
    # 設定 Session 安全性
    app.config['SESSION_COOKIE_SECURE'] = (env == 'production')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # 檢查 SECRET_KEY
    secret_key = app.config.get('SECRET_KEY', '')
    if secret_key == 'your-secret-key-change-in-production':
        if env == 'production':
            print("⚠️  警告: 生產環境使用預設 SECRET_KEY，請設定安全的密鑰！")
        else:
            print("ℹ️  提示: 開發環境使用預設 SECRET_KEY")
    
    # 啟動應用程式
    try:
        print(f"🎯 正在啟動 Flask 開發伺服器...")
        app.run(
            host=host,
            port=port,
            debug=app.config['DEBUG'],
            threaded=True,
            use_reloader=(env == 'development')
        )
    except KeyboardInterrupt:
        print("\n👋 應用程式已停止")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ 埠口 {port} 已被佔用，請嘗試其他埠口或停止佔用該埠口的程式")
        else:
            print(f"❌ 網路錯誤: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 啟動失敗: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
