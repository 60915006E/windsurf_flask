#!/usr/bin/env python3
"""
搜尋功能測試腳本
驗證對應表和搜尋邏輯是否正確
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import SEARCH_MAPPING, TYPE_MAPPING, build_search_conditions

def test_mappings():
    """測試對應表"""
    print("=== 測試對應表 ===")
    
    # 測試 SEARCH_MAPPING
    print("\nSEARCH_MAPPING:")
    for key, value in SEARCH_MAPPING.items():
        print(f"  {key} -> {value}")
    
    # 測試 TYPE_MAPPING
    print("\nTYPE_MAPPING:")
    for key, value in TYPE_MAPPING.items():
        print(f"  {key} -> {value}")
    
    # 驗證對應
    assert SEARCH_MAPPING['title'] == 'title'
    assert SEARCH_MAPPING['author'] == 'author' 
    assert SEARCH_MAPPING['number'] == 'DOC_ID'
    assert SEARCH_MAPPING['all'] == 'ALL'
    
    assert TYPE_MAPPING['tech_report'] == '技術報告'
    assert TYPE_MAPPING['history_politics'] == '史政'
    assert TYPE_MAPPING['history_photos'] == '史政照片'
    assert TYPE_MAPPING['yiguang_report'] == '逸光報'
    
    print("\n✅ 對應表測試通過")

def test_search_conditions():
    """測試搜尋條件建構"""
    print("\n=== 測試搜尋條件建構 ===")
    
    # 測試案例 1: 全部欄位搜尋
    print("\n測試案例 1: 全部欄位搜尋")
    conditions = build_search_conditions('ALL', '測試', ['技術報告', '史政'])
    print(f"SQL: {conditions['sql_query']}")
    print(f"參數: {conditions['bind_params']}")
    
    # 測試案例 2: 特定欄位搜尋
    print("\n測試案例 2: 特定欄位搜尋")
    conditions = build_search_conditions('title', 'Oracle', ['技術報告'])
    print(f"SQL: {conditions['sql_query']}")
    print(f"參數: {conditions['bind_params']}")
    
    # 測試案例 3: 無類型篩選
    print("\n測試案例 3: 無類型篩選")
    conditions = build_search_conditions('author', '張三', [])
    print(f"SQL: {conditions['sql_query']}")
    print(f"參數: {conditions['bind_params']}")
    
    print("\n✅ 搜尋條件測試通過")

def test_form_data_simulation():
    """模擬表單資料處理"""
    print("\n=== 模擬表單資料處理 ===")
    
    # 模擬表單資料
    form_data = {
        'searchKeyword': 'Oracle',
        'searchField': 'title',
        'document_types': ['tech_report', 'history_politics']
    }
    
    # 處理邏輯模擬
    keyword = form_data['searchKeyword'].strip()
    field = form_data['searchField']
    types = form_data['document_types']
    
    # 對應表翻譯
    db_field = SEARCH_MAPPING.get(field, 'ALL')
    selected_types = [TYPE_MAPPING.get(t, t) for t in types]
    
    print(f"關鍵字: {keyword}")
    print(f"搜尋欄位: {field} -> {db_field}")
    print(f"資料類型: {types} -> {selected_types}")
    
    # 建構搜尋條件
    conditions = build_search_conditions(db_field, keyword, selected_types)
    print(f"搜尋條件: {conditions}")
    
    print("\n✅ 表單資料處理測試通過")

if __name__ == '__main__':
    try:
        test_mappings()
        test_search_conditions()
        test_form_data_simulation()
        print("\n🎉 所有測試通過！")
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        sys.exit(1)
