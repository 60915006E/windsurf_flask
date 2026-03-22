#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫配置測試腳本

驗證配置檔案和模組結構是否正確
"""

import sys
import os

def test_config():
    """測試配置檔案"""
    print("🔧 測試配置檔案...")
    
    try:
        from config import (
            SYSTEM_DB_USER, SYSTEM_DB_PASSWORD, SYSTEM_DB_HOST, SYSTEM_DB_PORT, SYSTEM_DB_SERVICE_NAME,
            DATA_DB_USER, DATA_DB_PASSWORD, DATA_DB_HOST, DATA_DB_PORT, DATA_DB_SERVICE_NAME,
            DATA_DB_SCHEMA, NEWEST_BOOKS_TABLE, NEWEST_BOOKS_ID_FIELD, 
            NEWEST_BOOKS_TITLE_FIELD, NEWEST_BOOKS_DATE_FIELD
        )
        
        print("✅ 配置檔案載入成功")
        print(f"  SYSTEM_DB: {SYSTEM_DB_USER}@{SYSTEM_DB_HOST}:{SYSTEM_DB_PORT}/{SYSTEM_DB_SERVICE_NAME}")
        print(f"  DATA_DB: {DATA_DB_USER}@{DATA_DB_HOST}:{DATA_DB_PORT}/{DATA_DB_SERVICE_NAME}")
        print(f"  Schema: {DATA_DB_SCHEMA}")
        print(f"  新進書目表: {NEWEST_BOOKS_TABLE}")
        print(f"  ID 欄位: {NEWEST_BOOKS_ID_FIELD}")
        print(f"  標題欄位: {NEWEST_BOOKS_TITLE_FIELD}")
        print(f"  日期欄位: {NEWEST_BOOKS_DATE_FIELD}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 配置檔案載入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 配置檔案錯誤: {e}")
        return False

def test_db_manager():
    """測試資料庫管理模組"""
    print("\n🏗️ 測試資料庫管理模組...")
    
    try:
        # 測試模組載入
        import db_manager
        print("✅ db_manager 模組載入成功")
        
        # 測試函數存在
        functions = [
            'execute_query', 'execute_paginated_query', 'test_connection',
            'get_connection_pool_status', 'get_newest_books', 'get_popular_books'
        ]
        
        for func_name in functions:
            if hasattr(db_manager, func_name):
                print(f"  ✅ {func_name} 函數存在")
            else:
                print(f"  ❌ {func_name} 函數不存在")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ db_manager 模組載入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ db_manager 模組錯誤: {e}")
        return False

def test_routes():
    """測試路由模組"""
    print("\n🌐 測試路由模組...")
    
    try:
        from app.search.routes import bp
        print("✅ search 藍圖載入成功")
        
        # 檢查路由
        routes = []
        for rule in bp.deferred_functions:
            if hasattr(rule, '__name__'):
                routes.append(rule.__name__)
        
        print(f"  路由數量: {len(routes)}")
        return True
        
    except ImportError as e:
        print(f"❌ 路由模組載入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 路由模組錯誤: {e}")
        return False

def test_schema_sql():
    """測試 Schema SQL 建構"""
    print("\n📋 測試 Schema SQL 建構...")
    
    try:
        from config import (
            DATA_DB_SCHEMA, NEWEST_BOOKS_TABLE, NEWEST_BOOKS_ID_FIELD,
            NEWEST_BOOKS_TITLE_FIELD, NEWEST_BOOKS_DATE_FIELD
        )
        
        # 建構完整表名
        full_table_name = f"{DATA_DB_SCHEMA}.{NEWEST_BOOKS_TABLE}"
        
        # 建構 SQL
        sql = f"""
        SELECT 
            {NEWEST_BOOKS_ID_FIELD} as DOC_ID,
            {NEWEST_BOOKS_TITLE_FIELD} as TITLE,
            TO_CHAR({NEWEST_BOOKS_DATE_FIELD}, 'YYYY-MM-DD HH24:MI:SS') as CREATED_DATE
        FROM {full_table_name}
        WHERE {NEWEST_BOOKS_DATE_FIELD} IS NOT NULL
        ORDER BY {NEWEST_BOOKS_DATE_FIELD} DESC
        FETCH NEXT :limit ROWS ONLY
        """
        
        print("✅ SQL 建構成功")
        print(f"  完整表名: {full_table_name}")
        print(f"  SQL 範例:")
        print(f"    {sql.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ SQL 建構失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 實體資料庫連線配置測試")
    print("=" * 50)
    
    tests = [
        ("配置檔案", test_config),
        ("資料庫管理模組", test_db_manager),
        ("路由模組", test_routes),
        ("Schema SQL 建構", test_schema_sql)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 測試結果總結:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有測試通過！實體資料庫連線配置完成")
        print("\n📋 部署檢查清單:")
        print("  1. 安裝 python-oracledb: pip install python-oracledb")
        print("  2. 確認 Oracle 19c 資料庫可連線")
        print("  3. 確認 Schema sarchowner 存在")
        print("  4. 確認資料表結構符合配置")
        print("  5. 建立必要的索引以提升效能")
    else:
        print("❌ 部分測試失敗，請檢查配置")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
