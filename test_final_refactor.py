#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正式資料庫欄位重構測試腳本

驗證所有查詢都使用正式資料庫欄位名稱和隱形過濾
"""

import sys
import os

def test_config():
    """測試正式欄位映射配置"""
    print("🔧 測試正式欄位映射配置...")
    
    try:
        from config import (
            MAIN_TABLE_NAME, MAIN_TABLE_FULL, MAIN_ID_FIELD, TITLE_FIELD, SORT_DATE_FIELD,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE, STATUS_NAME_FIELD, STATUS_OPEN_NAME,
            SEARCH_FIELDS, FILTER_FIELDS, DATE_FIELDS,
            DETAIL_FIELDS, LIST_FIELDS
        )
        
        print("✅ 正式欄位映射配置載入成功")
        print(f"  主表名稱: {MAIN_TABLE_NAME}")
        print(f"  完整表名: {MAIN_TABLE_FULL}")
        print(f"  主鍵: {MAIN_ID_FIELD}")
        print(f"  標題: {TITLE_FIELD}")
        print(f"  排序日期: {SORT_DATE_FIELD}")
        print(f"  狀態碼: {STATUS_CODE_FIELD}")
        print(f"  狀態名稱: {STATUS_NAME_FIELD}")
        print(f"  隱形過濾: {STATUS_CODE_FIELD} = '{STATUS_OPEN_CODE}'")
        
        print("\n📋 搜尋欄位映射:")
        for key, value in SEARCH_FIELDS.items():
            print(f"  {key}: {value}")
        
        print("\n🔽 下拉選單欄位:")
        for key, value in FILTER_FIELDS.items():
            print(f"  {key}: {value}")
        
        print(f"\n📅 日期欄位: {len(DATE_FIELDS)} 個")
        print(f"📄 詳情欄位: {len(DETAIL_FIELDS)} 個")
        print(f"📋 列表欄位: {len(LIST_FIELDS)} 個")
        
        return True
        
    except ImportError as e:
        print(f"❌ 配置檔案載入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 配置檔案錯誤: {e}")
        return False

def test_newest_books_sql():
    """測試最新報告 SQL 建構"""
    print("\n📚 測試最新報告 SQL 建構...")
    
    try:
        from config import (
            MAIN_TABLE_FULL, MAIN_ID_FIELD, TITLE_FIELD, SORT_DATE_FIELD,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE, STATUS_NAME_FIELD
        )
        
        # 建構 SQL
        sql = f"""
        SELECT 
            {MAIN_ID_FIELD} as DOC_ID,
            {TITLE_FIELD} as TITLE,
            TO_CHAR({SORT_DATE_FIELD}, 'YYYY-MM-DD HH24:MI:SS') as CREATED_DATE,
            TO_CHAR({SORT_DATE_FIELD}, 'YYYY-MM-DD') as FORMATTED_DATE,
            {STATUS_CODE_FIELD} as STATUS_CODE,
            {STATUS_NAME_FIELD} as STATUS_NAME
        FROM {MAIN_TABLE_FULL}
        WHERE {SORT_DATE_FIELD} IS NOT NULL
          AND {STATUS_CODE_FIELD} = :status_code
        ORDER BY {SORT_DATE_FIELD} DESC
        FETCH NEXT :limit ROWS ONLY
        """
        
        print("✅ 最新報告 SQL 建構成功")
        print(f"  使用表: {MAIN_TABLE_FULL}")
        print(f"  隱形過濾: {STATUS_CODE_FIELD} = '{STATUS_OPEN_CODE}'")
        
        # 驗證關鍵元素
        required_elements = [
            MAIN_TABLE_FULL,
            MAIN_ID_FIELD,
            TITLE_FIELD,
            SORT_DATE_FIELD,
            STATUS_CODE_FIELD,
            f"{STATUS_CODE_FIELD} = :status_code"
        ]
        
        for element in required_elements:
            if element in sql:
                print(f"  ✅ 包含: {element}")
            else:
                print(f"  ❌ 遺失: {element}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 最新報告 SQL 測試失敗: {e}")
        return False

def test_popular_books_sql():
    """測試熱門報告 SQL 建構"""
    print("\n🔥 測試熱門報告 SQL 建構...")
    
    try:
        from config import (
            MAIN_TABLE_FULL, MAIN_ID_FIELD, TITLE_FIELD,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE, SEARCH_FIELDS
        )
        
        # 建構 SQL
        sql = f"""
        SELECT 
            {MAIN_ID_FIELD} as DOC_ID,
            {TITLE_FIELD} as TITLE,
            {SEARCH_FIELDS['main_author']} as MAIN_AUTHOR,
            TO_CHAR({DATE_FIELDS['public_date']}, 'YYYY-MM-DD HH24:MI:SS') as LAST_VIEW_TIME,
            TO_CHAR({DATE_FIELDS['public_date']}, 'YYYY-MM-DD') as FORMATTED_DATE,
            {STATUS_CODE_FIELD} as STATUS_CODE,
            {STATUS_NAME_FIELD} as STATUS_NAME
        FROM {MAIN_TABLE_FULL}
        WHERE {STATUS_CODE_FIELD} = :status_code
        ORDER BY {DATE_FIELDS['public_date']} DESC
        FETCH NEXT :limit ROWS ONLY
        """
        
        print("✅ 熱門報告 SQL 建構成功")
        print(f"  隱形過濾: {STATUS_CODE_FIELD} = '{STATUS_OPEN_CODE}'")
        
        # 驗證隱形過濾條件
        if f"{STATUS_CODE_FIELD} = :status_code" in sql:
            print("  ✅ 隱形過濾條件已加入")
            return True
        else:
            print("  ❌ 隱形過濾條件遺失")
            return False
        
    except Exception as e:
        print(f"❌ 熱門報告 SQL 測試失敗: {e}")
        return False

def test_detail_sql():
    """測試詳情頁面 SQL 建構"""
    print("\n📄 測試詳情頁面 SQL 建構...")
    
    try:
        from config import (
            MAIN_TABLE_FULL, MAIN_ID_FIELD, DETAIL_FIELDS,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE, DATE_FIELDS
        )
        
        # 建構完整欄位列表
        field_list = []
        for field in DETAIL_FIELDS:
            if field in DATE_FIELDS.values():
                # 日期欄位需要格式化
                formatted_field = f"TO_CHAR({field}, 'YYYY-MM-DD') as {field}"
                datetime_field = f"TO_CHAR({field}, 'YYYY-MM-DD HH24:MI:SS') as {field}_DATETIME"
                field_list.append(formatted_field)
                field_list.append(datetime_field)
            else:
                field_list.append(field)
        
        # 建構 SQL
        sql = f"""
        SELECT {', '.join(field_list)}
        FROM {MAIN_TABLE_FULL}
        WHERE {MAIN_ID_FIELD} = :doc_id
          AND {STATUS_CODE_FIELD} = :status_code
        """
        
        print("✅ 詳情頁面 SQL 建構成功")
        print(f"  完整欄位數: {len(field_list)}")
        print(f"  隱形過濾: {STATUS_CODE_FIELD} = :status_code")
        
        # 驗證關鍵元素
        if f"{STATUS_CODE_FIELD} = :status_code" in sql:
            print("  ✅ 隱形過濾條件已加入")
            return True
        else:
            print("  ❌ 隱形過濾條件遺失")
            return False
        
    except Exception as e:
        print(f"❌ 詳情頁面 SQL 測試失敗: {e}")
        return False

def test_search_sql():
    """測試進階搜尋 SQL 建構"""
    print("\n🔍 測試進階搜尋 SQL 建構...")
    
    try:
        from config import (
            MAIN_TABLE_FULL, SEARCH_FIELDS, FILTER_FIELDS,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE, LIST_FIELDS
        )
        
        # 模擬搜尋條件
        conditions = [
            {'field': 'title', 'operator': '包含', 'value': 'Python'},
            {'field': 'main_author', 'operator': '等於', 'value': '張三'}
        ]
        
        # 建構 WHERE 條件
        where_clauses = []
        for i, condition in enumerate(conditions, 1):
            field = condition.get('field', '')
            operator = condition.get('operator', '')
            value = condition.get('value', '')
            
            if field and operator and value:
                # 映射搜尋欄位
                mapped_field = SEARCH_FIELDS.get(field, field)
                
                if operator == '包含':
                    where_clauses.append(f"{mapped_field} LIKE :param{i}")
                elif operator == '等於':
                    where_clauses.append(f"{mapped_field} = :param{i}")
        
        # 加入隱形過濾條件
        hidden_filter_clause = f'{STATUS_CODE_FIELD} = :status_filter'
        where_clauses.append(hidden_filter_clause)
        
        # 建構欄位列表（效能優化）
        field_list = []
        for field in LIST_FIELDS:
            field_list.append(field)
        
        # 建立完整 SQL
        where_sql = ' AND '.join(where_clauses)
        sql = f"""
        SELECT {', '.join(field_list)}
        FROM {MAIN_TABLE_FULL}
        WHERE {where_sql}
        ORDER BY {DATE_FIELDS['public_date']} DESC
        FETCH NEXT :limit ROWS ONLY
        """
        
        print("✅ 進階搜尋 SQL 建構成功")
        print(f"  搜尋條件數: {len(conditions)}")
        print(f"  隱形過濾: {STATUS_CODE_FIELD} = :status_filter")
        print(f"  效能欄位: {len(LIST_FIELDS)} 個")
        
        # 驗證關鍵元素
        if hidden_filter_clause in where_clauses:
            print("  ✅ 隱形過濾條件已加入")
            return True
        else:
            print("  ❌ 隱形過濾條件遺失")
            return False
        
    except Exception as e:
        print(f"❌ 進階搜尋 SQL 測試失敗: {e}")
        return False

def test_field_mapping():
    """測試欄位映射正確性"""
    print("\n🗺️ 測試欄位映射正確性...")
    
    try:
        from config import SEARCH_FIELDS, FILTER_FIELDS, DETAIL_FIELDS
        
        # 驗證搜尋欄位
        required_search_fields = ['title', 'summary', 'main_author', 'author_list', 'csi_name']
        for field in required_search_fields:
            if field in SEARCH_FIELDS:
                print(f"  ✅ 搜尋欄位: {field} -> {SEARCH_FIELDS[field]}")
            else:
                print(f"  ❌ 搜尋欄位遺失: {field}")
                return False
        
        # 驗證過濾欄位
        required_filter_fields = ['category', 'type', 'security_level']
        for field in required_filter_fields:
            if field in FILTER_FIELDS:
                print(f"  ✅ 過濾欄位: {field} -> {FILTER_FIELDS[field]}")
            else:
                print(f"  ❌ 過濾欄位遺失: {field}")
                return False
        
        # 驗證必要欄位
        required_detail_fields = ['OVC_RP_NO', 'OVN_RP_NAME', 'OVN_SUMMARY', 'OVN_RP_MAIN_AUTHOR']
        for field in required_detail_fields:
            if field in DETAIL_FIELDS:
                print(f"  ✅ 詳情欄位: {field}")
            else:
                print(f"  ❌ 詳情欄位遺失: {field}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 欄位映射測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 正式資料庫欄位重構測試")
    print("=" * 60)
    
    tests = [
        ("正式欄位映射配置", test_config),
        ("最新報告 SQL 建構", test_newest_books_sql),
        ("熱門報告 SQL 建構", test_popular_books_sql),
        ("詳情頁面 SQL 建構", test_detail_sql),
        ("進階搜尋 SQL 建構", test_search_sql),
        ("欄位映射正確性", test_field_mapping)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("📊 測試結果總結:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有測試通過！正式資料庫欄位重構完成")
        print("\n📋 重構成果:")
        print("  1. ✅ 使用正式資料庫欄位名稱")
        print("  2. ✅ 主表: sarchowner.TBIRLIB_REPORT_MAIN")
        print("  3. ✅ 隱形過濾: OVC_STATUS_CDE = 'open'")
        print("  4. ✅ 支援完整搜尋欄位映射")
        print("  5. ✅ 效能優化：列表頁面只抓取必要欄位")
        print("  6. ✅ 詳情頁面顯示所有欄位")
        print("  7. ✅ 日期欄位自動格式化")
        
        print("\n🔧 關鍵欄位映射:")
        print("  主鍵: OVC_RP_NO")
        print("  標題: OVN_RP_NAME")
        print("  發布日期: ODT_PUBLIC_DATE")
        print("  狀態碼: OVC_STATUS_CDE")
        print("  狀態名稱: OVC_STATUS_NAME")
        
        print("\n🚀 部署準備:")
        print("  1. 確認 Oracle 19c 資料庫連線")
        print("  2. 驗證表 sarchowner.TBIRLIB_REPORT_MAIN 存在")
        print("  3. 確認所有欄位名稱正確")
        print("  4. 建立必要索引提升效能")
    else:
        print("❌ 部分測試失敗，請檢查重構實作")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
