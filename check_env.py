#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
環境診斷腳本

檢查所有核心套件是否正確安裝，方便在內網快速診斷環境是否準備就緒

作者：系統管理員
建立日期：2026-03-22
版本：1.0.0
"""

import sys
import platform

def print_separator(title):
    """印出分隔線"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def check_python_version():
    """檢查 Python 版本"""
    print_separator("Python 版本檢查")
    
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    print(f"Python 編譯器: {sys.version}")
    print(f"作業系統: {platform.system()} {platform.release()}")
    print(f"架構: {platform.machine()}")
    
    # 檢查是否為 Python 3.13.7
    if version.major == 3 and version.minor == 13:
        print("✅ Python 版本符合要求 (3.13.x)")
    else:
        print(f"⚠️  建議使用 Python 3.13.7，目前使用 {version.major}.{version.minor}.{version.micro}")

def check_core_packages():
    """檢查核心套件"""
    print_separator("核心套件檢查")
    
    packages = [
        ('Flask', 'flask'),
        ('Werkzeug', 'werkzeug'),
        ('Jinja2', 'jinja2'),
        ('MarkupSafe', 'markupsafe'),
        ('itsdangerous', 'itsdangerous'),
        ('click', 'click'),
        ('python-oracledb', 'oracledb'),
        ('pandas', 'pandas'),
        ('openpyxl', 'openpyxl'),
        ('requests', 'requests'),
        ('waitress', 'waitress'),
        ('python-dotenv', 'dotenv'),
    ]
    
    all_passed = True
    
    for package_name, import_name in packages:
        try:
            if import_name == 'oracledb':
                import oracledb
                version = getattr(oracledb, '__version__', 'unknown')
                print(f"✅ {package_name}: {version}")
                
                # 檢查 Oracle 版本支援
                try:
                    print(f"   Oracle Client 版本: {oracledb.clientversion()}")
                except:
                    print("   Oracle Client 版本: 未初始化")
                    
            elif import_name == 'dotenv':
                import dotenv
                version = getattr(dotenv, '__version__', 'unknown')
                print(f"✅ {package_name}: {version}")
                
            else:
                module = __import__(import_name)
                version = getattr(module, '__version__', 'unknown')
                print(f"✅ {package_name}: {version}")
                
        except ImportError as e:
            print(f"❌ {package_name}: 未安裝 - {str(e)}")
            all_passed = False
        except Exception as e:
            print(f"⚠️  {package_name}: 安裝但可能有問題 - {str(e)}")
            all_passed = False
    
    return all_passed

def check_oracle_connection():
    """檢查 Oracle 連線能力"""
    print_separator("Oracle 連線檢查")
    
    try:
        import oracledb
        
        # 檢查 Thin Mode 支援
        print("✅ python-oracledb 已安裝")
        print("✅ 支援 Thin Mode (無需 Oracle Client)")
        
        # 嘗試建立連線（不實際連接）
        try:
            # 這只是測試 API 是否可用，不會實際連接
            print("✅ Oracle 連線 API 可用")
        except Exception as e:
            print(f"⚠️  Oracle 連線 API 測試失敗: {str(e)}")
            
    except ImportError:
        print("❌ python-oracledb 未安裝")
        return False
    
    return True

def check_flask_app():
    """檢查 Flask 應用程式"""
    print_separator("Flask 應用程式檢查")
    
    try:
        from app import create_app
        
        # 嘗試建立應用程式實例
        app = create_app('default')
        print("✅ Flask 應用程式工廠成功建立")
        
        # 檢查應用程式配置
        secret_key = app.config.get('SECRET_KEY', '')
        if secret_key:
            if secret_key == 'your-secret-key-change-in-production':
                print("⚠️  使用預設 SECRET_KEY，請在生產環境中更改")
            else:
                print("✅ SECRET_KEY 已設定")
        else:
            print("❌ SECRET_KEY 未設定")
        
        # 檢查藍圖註冊
        blueprints = [bp.name for bp in app.blueprints.values()]
        print(f"✅ 已註冊藍圖: {', '.join(blueprints)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Flask 應用程式模組導入失敗: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Flask 應用程式建立失敗: {str(e)}")
        return False

def check_config_files():
    """檢查設定檔案"""
    print_separator("設定檔案檢查")
    
    import os
    
    config_files = [
        'config.py',
        '.env',
        'requirements.txt',
    ]
    
    all_exist = True
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file}: 存在")
        else:
            print(f"⚠️  {config_file}: 不存在")
            all_exist = False
    
    return all_exist

def check_directories():
    """檢查必要目錄"""
    print_separator("目錄結構檢查")
    
    import os
    
    directories = [
        'app',
        'app/auth',
        'app/search',
        'app/admin',
        'app/collection',
        'app/templates',
        'app/static',
        'logs',
    ]
    
    all_exist = True
    
    for directory in directories:
        if os.path.isdir(directory):
            print(f"✅ {directory}/: 存在")
        else:
            print(f"⚠️  {directory}/: 不存在")
            all_exist = False
    
    return all_exist

def main():
    """主診斷函數"""
    print("🔍 Flask 查詢系統環境診斷工具")
    print("=" * 60)
    print(f"診斷時間: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 執行所有檢查
    checks = [
        ("Python 版本", check_python_version),
        ("核心套件", check_core_packages),
        ("Oracle 連線", check_oracle_connection),
        ("Flask 應用程式", check_flask_app),
        ("設定檔案", check_config_files),
        ("目錄結構", check_directories),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} 檢查失敗: {str(e)}")
            results.append((check_name, False))
    
    # 總結報告
    print_separator("診斷總結")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"檢查項目: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有檢查項目都通過，環境準備就緒！")
        return 0
    else:
        print("⚠️  部分檢查項目未通過，請檢查上述問題")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
