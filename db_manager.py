#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oracle 19c 資料庫管理模組

遵循 .windsurfrules 規範：
- 雙資料庫架構：SYSTEM_DB (讀寫) + DATA_DB (唯讀)
- 連線池管理：高併發下的穩定運作
- 安全性：使用綁定變數防止 SQL 注入
- 錯誤處理：詳細的錯誤記錄和用戶友好提示

作者：系統管理員
建立日期：2026-03-02
版本：2.0.0 - 正式連線版本
"""

import logging
import oracledb
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import threading
import time

# 設定日誌
logger = logging.getLogger(__name__)

# ===========================================
# Oracle 19c 連線配置
# ===========================================

# 檢查 python-oracledb 是否可用
try:
    import oracledb
    ORACLE_AVAILABLE = True
    logger.info("python-oracledb 已載入")
except ImportError:
    ORACLE_AVAILABLE = False
    logger.error("python-oracledb 未安裝，無法建立資料庫連線")
    raise ImportError("python-oracledb 是必需的套件，請安裝：pip install python-oracledb")

# 全域連線池
_connection_pools = {}
_pool_lock = threading.Lock()

# ===========================================
# 連線池管理
# ===========================================

def _get_connection_pool(db_type: str):
    """
    取得連線池
    
    Args:
        db_type: 資料庫類型 ('system' 或 'data')
        
    Returns:
        oracledb.ConnectionPool: 連線池物件
    """
    global _connection_pools
    
    with _pool_lock:
        if db_type not in _connection_pools:
            try:
                from config import (
                    SYSTEM_DB_URI, DATA_DB_URI,
                    SYSTEM_DB_USER, DATA_DB_USER,
                    SYSTEM_DB_PASSWORD, DATA_DB_PASSWORD,
                    SYSTEM_DB_HOST, DATA_DB_HOST,
                    SYSTEM_DB_PORT, DATA_DB_PORT,
                    SYSTEM_DB_SERVICE_NAME, DATA_DB_SERVICE_NAME
                )
                
                # 選擇連線參數
                if db_type == 'system':
                    dsn = SYSTEM_DB_URI
                    user = SYSTEM_DB_USER
                    password = SYSTEM_DB_PASSWORD
                    min_sessions = 2
                    max_sessions = 10
                    increment = 2
                else:  # data
                    dsn = DATA_DB_URI
                    user = DATA_DB_USER
                    password = DATA_DB_PASSWORD
                    min_sessions = 3
                    max_sessions = 20
                    increment = 3
                
                # 建立連線池
                logger.info(f"建立 {db_type} 資料庫連線池...")
                
                _connection_pools[db_type] = oracledb.create_pool(
                    user=user,
                    password=password,
                    dsn=dsn,
                    min=min_sessions,
                    max=max_sessions,
                    increment=increment,
                    getmode=oracledb.POOL_GETMODE_WAIT,
                    timeout=30,
                    session_callback=lambda conn: logger.debug(f"新的 {db_type} 連線已建立")
                )
                
                logger.info(f"{db_type} 資料庫連線池建立成功")
                logger.info(f"連線池配置: min={min_sessions}, max={max_sessions}, increment={increment}")
                
            except Exception as e:
                logger.error(f"建立 {db_type} 資料庫連線池失敗: {str(e)}")
                raise
        
        return _connection_pools[db_type]

@contextmanager
def _get_connection(db_type: str):
    """
    取得資料庫連線的上下文管理器
    
    Args:
        db_type: 資料庫類型 ('system' 或 'data')
        
    Yields:
        oracledb.Connection: 資料庫連線物件
    """
    pool = _get_connection_pool(db_type)
    connection = None
    
    try:
        connection = pool.acquire()
        logger.debug(f"取得 {db_type} 資料庫連線")
        yield connection
    except Exception as e:
        logger.error(f"{db_type} 資料庫連線錯誤: {str(e)}")
        raise
    finally:
        if connection:
            try:
                pool.release(connection)
                logger.debug(f"釋放 {db_type} 資料庫連線")
            except Exception as e:
                logger.error(f"釋放 {db_type} 資料庫連線失敗: {str(e)}")

# ===========================================
# 錯誤處理工具
# ===========================================

def _parse_ora_error(error: Exception) -> Tuple[str, str]:
    """
    解析 Oracle 錯誤訊息
    
    Args:
        error: Oracle 錯誤物件
        
    Returns:
        Tuple[str, str]: (錯誤代碼, 錯誤訊息)
    """
    error_str = str(error)
    
    # 常見 Oracle 錯誤代碼解析
    if "ORA-12541" in error_str:
        return "12541", "TNS:無法連線到監聽器"
    elif "ORA-12154" in error_str:
        return "12154", "TNS:無法解析指定的連線識別元"
    elif "ORA-01017" in error_str:
        return "01017", "無效的使用者名稱/密碼；登入被拒絕"
    elif "ORA-28000" in error_str:
        return "28000", "帳戶已被鎖定"
    elif "ORA-28001" in error_str:
        return "28001", "密碼已過期"
    elif "ORA-00942" in error_str:
        return "00942", "表或視圖不存在"
    elif "ORA-00904" in error_str:
        return "00904", "無效的識別元"
    elif "ORA-01403" in error_str:
        return "01403", "未找到資料"
    elif "ORA-01722" in error_str:
        return "01722", "無效的數字"
    elif "ORA-12899" in error_str:
        return "12899", "數值過大，超出欄位實際長度"
    elif "ORA-00001" in error_str:
        return "00001", "違反唯一約束條件"
    elif "ORA-02291" in error_str:
        return "02291", "違反完整性約束條件 - 找不到父項鍵"
    elif "ORA-02292" in error_str:
        return "02292", "違反完整性約束條件 - 找到子項記錄"
    elif "DPY-" in error_str:
        return "DPY", "python-oracledb 驅動程式錯誤"
    else:
        # 提取 ORA 錯誤代碼
        import re
        ora_match = re.search(r'ORA-(\d+)', error_str)
        if ora_match:
            return ora_match.group(1), error_str
        else:
            return "UNKNOWN", error_str

# ===========================================
# 基礎查詢函式
# ===========================================

def execute_query(sql: str, params: Dict[str, Any] = None, db_type: str = 'data') -> List[Dict[str, Any]]:
    """
    執行 SQL 查詢
    
    Args:
        sql: SQL 查詢語句
        params: 查詢參數字典
        db_type: 資料庫類型 ('system' 或 'data')
        
    Returns:
        List[Dict[str, Any]]: 查詢結果列表
    """
    if not ORACLE_AVAILABLE:
        raise RuntimeError("python-oracledb 未安裝，無法執行資料庫查詢")
    
    if params is None:
        params = {}
    
    start_time = time.time()
    
    try:
        with _get_connection(db_type) as connection:
            # 設定 rowfactory 以返回字典格式
            connection.rowfactory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            
            with connection.cursor() as cursor:
                logger.debug(f"執行 {db_type} 資料庫查詢: {sql[:100]}...")
                logger.debug(f"查詢參數: {params}")
                
                cursor.execute(sql, params)
                results = cursor.fetchall()
                
                execution_time = time.time() - start_time
                logger.info(f"{db_type} 資料庫查詢成功，返回 {len(results)} 筆資料，耗時 {execution_time:.3f} 秒")
                
                return results
                
    except oracledb.Error as e:
        error_code, error_message = _parse_ora_error(e)
        execution_time = time.time() - start_time
        logger.error(f"{db_type} 資料庫查詢失敗: ORA-{error_code} - {error_message}")
        logger.error(f"失敗的 SQL: {sql}")
        logger.error(f"查詢參數: {params}")
        logger.error(f"執行時間: {execution_time:.3f} 秒")
        raise RuntimeError(f"資料庫查詢失敗: {error_message}")
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"{db_type} 資料庫查詢發生未預期錯誤: {str(e)}")
        logger.error(f"失敗的 SQL: {sql}")
        logger.error(f"查詢參數: {params}")
        logger.error(f"執行時間: {execution_time:.3f} 秒")
        raise RuntimeError(f"查詢執行失敗: {str(e)}")

def execute_paginated_query(sql: str, params: Dict[str, Any] = None, page: int = 1, 
                        per_page: int = 20, db_type: str = 'data') -> Dict[str, Any]:
    """
    執行分頁查詢
    
    Args:
        sql: SQL 查詢語句
        params: 查詢參數字典
        page: 頁碼 (從 1 開始)
        per_page: 每頁筆數
        db_type: 資料庫類型 ('system' 或 'data')
        
    Returns:
        Dict[str, Any]: 包含查詢結果和分頁資訊的字典
    """
    if not ORACLE_AVAILABLE:
        raise RuntimeError("python-oracledb 未安裝，無法執行資料庫查詢")
    
    if params is None:
        params = {}
    
    offset = (page - 1) * per_page
    
    try:
        # 建立分頁 SQL
        paginated_sql = f"""
        SELECT * FROM (
            SELECT a.*, ROWNUM as rn FROM (
                {sql}
            ) a WHERE ROWNUM <= :offset + :per_page
        ) WHERE rn > :offset
        """
        
        # 設定分頁參數
        paginated_params = params.copy()
        paginated_params.update({
            'offset': offset,
            'per_page': per_page
        })
        
        # 執行分頁查詢
        results = execute_query(paginated_sql, paginated_params, db_type)
        
        # 執行總數查詢
        count_sql = f"SELECT COUNT(*) as total FROM ({sql})"
        count_result = execute_query(count_sql, params, db_type)
        total = count_result[0]['total'] if count_result else 0
        
        # 計算分頁資訊
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return {
            'results': results,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_num': page - 1 if has_prev else None,
            'next_num': page + 1 if has_next else None
        }
        
    except Exception as e:
        logger.error(f"分頁查詢失敗: {str(e)}")
        raise RuntimeError(f"分頁查詢失敗: {str(e)}")

# ===========================================
# 系統管理功能
# ===========================================

def test_connection() -> bool:
    """
    測試資料庫連線
    
    執行 SELECT SYSDATE FROM DUAL 以便在伺服器上快速驗證連線狀態。
    
    Returns:
        bool: 連線測試是否成功
    """
    if not ORACLE_AVAILABLE:
        logger.error("python-oracledb 未安裝，無法測試連線")
        return False
    
    try:
        with _get_connection('system') as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT SYSDATE FROM DUAL")
                result = cursor.fetchone()
                logger.info(f"資料庫連線測試成功，伺服器時間: {result[0]}")
                return True
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"資料庫連線測試失敗: ORA-{error_code} - {error_message}")
        return False

def get_connection_pool_status() -> Dict[str, Any]:
    """
    取得連線池狀態
    
    Returns:
        Dict[str, Any]: 連線池狀態資訊
    """
    status = {}
    
    for db_type in ['system', 'data']:
        try:
            pool = _get_connection_pool(db_type)
            status[db_type] = {
                'busy': pool.busy,
                'opened': pool.opened,
                'max': pool.max,
                'min': pool.min,
                'increment': pool.increment,
                'timeout': pool.timeout,
                'getmode': pool.getmode
            }
        except Exception as e:
            status[db_type] = {'error': str(e)}
    
    return status

def close_all_pools():
    """
    關閉所有連線池
    
    通常在應用程式關閉時呼叫
    """
    global _connection_pools
    
    with _pool_lock:
        for db_type, pool in _connection_pools.items():
            try:
                pool.close()
                logger.info(f"{db_type} 資料庫連線池已關閉")
            except Exception as e:
                logger.error(f"關閉 {db_type} 資料庫連線池失敗: {str(e)}")
        
        _connection_pools.clear()

# ===========================================
# 初始化連線池
# ===========================================

def initialize_connection_pools():
    """
    初始化所有連線池
    
    在應用程式啟動時呼叫
    """
    try:
        # 預先建立連線池
        _get_connection_pool('system')
        _get_connection_pool('data')
        logger.info("所有資料庫連線池初始化完成")
    except Exception as e:
        logger.error(f"連線池初始化失敗: {str(e)}")
        raise

# 應用程式關閉時清理連線池
import atexit
atexit.register(close_all_pools)

# ===========================================
# 書目查詢功能
# ===========================================

def get_newest_books(limit: int = 10) -> List[Dict[str, Any]]:
    """
    取得最新報告
    
    根據發布日期排序，返回最新的報告
    包含隱形過濾：只顯示狀態為 'open' 的報告
    
    Args:
        limit: 返回筆數限制
        
    Returns:
        List[Dict[str, Any]]: 最新報告列表
    """
    try:
        # 從配置檔案取得正式欄位映射
        from config import (
            MAIN_TABLE_FULL, MAIN_ID_FIELD, TITLE_FIELD, SORT_DATE_FIELD,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE, STATUS_NAME_FIELD, STATUS_OPEN_NAME,
            DATE_FIELDS
        )
        
        with _get_connection('data') as connection:
            # 設定 rowfactory 以返回字典格式
            connection.rowfactory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            
            with connection.cursor() as cursor:
                # 使用正式欄位名稱建構 SQL
                # 包含隱形過濾條件：只顯示狀態為 'open' 的報告
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
                
                cursor.execute(sql, {
                    'status_code': STATUS_OPEN_CODE,
                    'limit': limit
                })
                results = cursor.fetchall()
                
                logger.info(f"最新報告查詢成功，返回 {len(results)} 筆資料")
                logger.info(f"使用表名: {MAIN_TABLE_FULL}, 排序欄位: {SORT_DATE_FIELD}")
                logger.info(f"隱形過濾: {STATUS_CODE_FIELD} = '{STATUS_OPEN_CODE}'")
                
                return results
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"查詢最新報告失敗: ORA-{error_code} - {error_message}")
        
        # 如果是表不存在的錯誤，提供具體的建議
        if "ORA-00942" in str(error_code):  # 表或視圖不存在
            from config import (
                DATA_DB_SCHEMA, MAIN_TABLE_NAME, MAIN_ID_FIELD, 
                TITLE_FIELD, SORT_DATE_FIELD, STATUS_CODE_FIELD
            )
            logger.error(f"表 {MAIN_TABLE_FULL} 不存在，請確認 DATA_DB 中的資料表結構")
            logger.error("請檢查 config.py 中的以下參數：")
            logger.error(f"DATA_DB_SCHEMA = '{DATA_DB_SCHEMA}'")
            logger.error(f"MAIN_TABLE_NAME = '{MAIN_TABLE_NAME}'")
            logger.error(f"MAIN_ID_FIELD = '{MAIN_ID_FIELD}'")
            logger.error(f"TITLE_FIELD = '{TITLE_FIELD}'")
            logger.error(f"SORT_DATE_FIELD = '{SORT_DATE_FIELD}'")
            logger.error(f"STATUS_CODE_FIELD = '{STATUS_CODE_FIELD}'")
            logger.error("確保日期欄位和狀態欄位有索引以提升查詢效能")
        
        # 拋出錯誤，由 Flask 捕捉並顯示友善錯誤頁面
        raise RuntimeError(f"查詢最新報告失敗: {error_message}")

def get_popular_books(limit: int = 10) -> List[Dict[str, Any]]:
    """
    取得熱門報告
    
    根據瀏覽次數排序，返回最受歡迎的報告
    包含隱形過濾：只顯示狀態為 'open' 的報告
    
    Args:
        limit: 返回筆數限制
        
    Returns:
        List[Dict[str, Any]]: 熱門報告列表
    """
    try:
        # 從配置檔案取得正式欄位映射
        from config import (
            MAIN_TABLE_FULL, MAIN_ID_FIELD, TITLE_FIELD,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE, STATUS_NAME_FIELD, STATUS_OPEN_NAME,
            SEARCH_FIELDS
        )
        
        with _get_connection('data') as connection:
            # 設定 rowfactory 以返回字典格式
            connection.rowfactory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            
            with connection.cursor() as cursor:
                # 使用正式欄位名稱建構 SQL
                # 包含隱形過濾條件：只顯示狀態為 'open' 的報告
                # 注意：假設有 VIEW_COUNT 欄位，如果沒有需要調整邏輯
                sql = f"""
                SELECT 
                    {MAIN_ID_FIELD} as DOC_ID,
                    {TITLE_FIELD} as TITLE,
                    {SEARCH_FIELDS['main_author']} as MAIN_AUTHOR,
                    TO_CHAR({SEARCH_FIELDS.get('public_date', 'ODT_PUBLIC_DATE')}, 'YYYY-MM-DD HH24:MI:SS') as LAST_VIEW_TIME,
                    TO_CHAR({SEARCH_FIELDS.get('public_date', 'ODT_PUBLIC_DATE')}, 'YYYY-MM-DD') as FORMATTED_DATE,
                    {STATUS_CODE_FIELD} as STATUS_CODE,
                    {STATUS_NAME_FIELD} as STATUS_NAME
                FROM {MAIN_TABLE_FULL}
                WHERE {STATUS_CODE_FIELD} = :status_code
                ORDER BY {SEARCH_FIELDS.get('public_date', 'ODT_PUBLIC_DATE')} DESC
                FETCH NEXT :limit ROWS ONLY
                """
                
                cursor.execute(sql, {
                    'status_code': STATUS_OPEN_CODE,
                    'limit': limit
                })
                results = cursor.fetchall()
                
                logger.info(f"熱門報告查詢成功，返回 {len(results)} 筆資料")
                logger.info(f"隱形過濾: {STATUS_CODE_FIELD} = '{STATUS_OPEN_CODE}'")
                
                return results
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"查詢熱門報告失敗: ORA-{error_code} - {error_message}")
        
        # 拋出錯誤，由 Flask 捕捉並顯示友善錯誤頁面
        raise RuntimeError(f"查詢熱門報告失敗: {error_message}")

def get_report_detail(doc_id: str) -> Dict[str, Any]:
    """
    取得報告詳情
    
    根據報告 ID 取得完整詳細資訊
    包含隱形過濾：只顯示狀態為 'open' 的報告
    
    Args:
        doc_id: 報告 ID
        
    Returns:
        Dict[str, Any]: 報告詳情資料
    """
    try:
        # 從配置檔案取得正式欄位映射
        from config import (
            MAIN_TABLE_FULL, MAIN_ID_FIELD, TITLE_FIELD,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE, STATUS_NAME_FIELD, STATUS_OPEN_NAME,
            DETAIL_FIELDS, DATE_FIELDS
        )
        
        with _get_connection('data') as connection:
            # 設定 rowfactory 以返回字典格式
            connection.rowfactory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            
            with connection.cursor() as cursor:
                # 建構完整欄位列表
                field_list = []
                date_field_list = []
                
                for field in DETAIL_FIELDS:
                    if field in DATE_FIELDS.values():
                        # 日期欄位需要格式化
                        formatted_field = f"TO_CHAR({field}, 'YYYY-MM-DD') as {field}"
                        datetime_field = f"TO_CHAR({field}, 'YYYY-MM-DD HH24:MI:SS') as {field}_DATETIME"
                        field_list.append(formatted_field)
                        field_list.append(datetime_field)
                    else:
                        field_list.append(field)
                
                # 使用正式欄位名稱建構 SQL
                # 包含隱形過濾條件：只顯示狀態為 'open' 的報告
                sql = f"""
                SELECT {', '.join(field_list)}
                FROM {MAIN_TABLE_FULL}
                WHERE {MAIN_ID_FIELD} = :doc_id
                  AND {STATUS_CODE_FIELD} = :status_code
                """
                
                cursor.execute(sql, {
                    'doc_id': doc_id,
                    'status_code': STATUS_OPEN_CODE
                })
                results = cursor.fetchall()
                
                if not results:
                    return None
                
                logger.info(f"報告詳情查詢成功: {doc_id}")
                logger.info(f"隱形過濾: {STATUS_CODE_FIELD} = '{STATUS_OPEN_CODE}'")
                
                return results[0]
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"查詢報告詳情失敗: ORA-{error_code} - {error_message}")
        
        # 拋出錯誤，由 Flask 捕捉並顯示友善錯誤頁面
        raise RuntimeError(f"查詢報告詳情失敗: {error_message}")

def search_reports(conditions: List[Dict], limit: int = 50) -> List[Dict[str, Any]]:
    """
    搜尋報告
    
    根據搜尋條件查詢報告
    包含隱形過濾：只顯示狀態為 'open' 的報告
    
    Args:
        conditions: 搜尋條件列表
        limit: 返回筆數限制
        
    Returns:
        List[Dict[str, Any]]: 搜尋結果列表
    """
    try:
        # 從配置檔案取得正式欄位映射
        from config import (
            MAIN_TABLE_FULL, MAIN_ID_FIELD, TITLE_FIELD,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE, STATUS_NAME_FIELD, STATUS_OPEN_NAME,
            SEARCH_FIELDS, LIST_FIELDS, DATE_FIELDS
        )
        
        with _get_connection('data') as connection:
            # 設定 rowfactory 以返回字典格式
            connection.rowfactory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            
            with connection.cursor() as cursor:
                # 建構 WHERE 條件
                where_clauses = []
                params = {}
                
                # 處理搜尋條件
                for i, condition in enumerate(conditions, 1):
                    field = condition.get('field', '')
                    operator = condition.get('operator', '')
                    value = condition.get('value', '')
                    
                    if not field or not operator or not value:
                        continue
                    
                    # 映射搜尋欄位
                    mapped_field = SEARCH_FIELDS.get(field, field)
                    
                    # 處理不同的操作符
                    if operator == '包含':
                        where_clauses.append(f"{mapped_field} LIKE :param{i}")
                        params[f'param{i}'] = f'%{value}%'
                    elif operator == '等於':
                        where_clauses.append(f"{mapped_field} = :param{i}")
                        params[f'param{i}'] = value
                    elif operator == '開頭為':
                        where_clauses.append(f"{mapped_field} LIKE :param{i}")
                        params[f'param{i}'] = f'{value}%'
                    else:
                        where_clauses.append(f"{mapped_field} {operator} :param{i}")
                        params[f'param{i}'] = value
                
                # 加入隱形過濾條件
                where_clauses.append(f"{STATUS_CODE_FIELD} = :status_filter")
                params['status_filter'] = STATUS_OPEN_CODE
                
                # 建構欄位列表（效能優化）
                field_list = []
                for field in LIST_FIELDS:
                    if field in DATE_FIELDS.values():
                        formatted_field = f"TO_CHAR({field}, 'YYYY-MM-DD') as {field}"
                        field_list.append(formatted_field)
                    else:
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
                
                params['limit'] = limit
                
                cursor.execute(sql, params)
                results = cursor.fetchall()
                
                logger.info(f"報告搜尋成功，返回 {len(results)} 筆資料")
                logger.info(f"隱形過濾: {STATUS_CODE_FIELD} = '{STATUS_OPEN_CODE}'")
                
                return results
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"報告搜尋失敗: ORA-{error_code} - {error_message}")
        
        # 拋出錯誤，由 Flask 捕捉並顯示友善錯誤頁面
        raise RuntimeError(f"報告搜尋失敗: {error_message}")

# ===========================================
# 動態欄位管理系統
# ===========================================

def get_field_settings(show_type: str = None) -> List[Dict[str, Any]]:
    """
    取得欄位設定
    
    Args:
        show_type: 顯示類型 ('list', 'detail', None=全部)
        
    Returns:
        List[Dict[str, Any]]: 欄位設定列表
    """
    try:
        with _get_connection('system') as connection:
            # 設定 rowfactory 以返回字典格式
            connection.rowfactory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            
            with connection.cursor() as cursor:
                # 建構 SQL 查詢
                sql = """
                SELECT FIELD_ID, FIELD_NAME, DISPLAY_NAME, SHOW_IN_LIST, 
                       SHOW_IN_DETAIL, SORT_ORDER, FIELD_TYPE, IS_REQUIRED,
                       DESCRIPTION, CREATED_DATE, UPDATED_DATE, CREATED_BY, UPDATED_BY
                FROM FIELD_SETTINGS
                """
                
                params = {}
                if show_type == 'list':
                    sql += " WHERE SHOW_IN_LIST = 'Y'"
                elif show_type == 'detail':
                    sql += " WHERE SHOW_IN_DETAIL = 'Y'"
                
                sql += " ORDER BY SORT_ORDER, FIELD_ID"
                
                cursor.execute(sql, params)
                results = cursor.fetchall()
                
                logger.info(f"欄位設定查詢成功，返回 {len(results)} 筆資料")
                if show_type:
                    logger.info(f"篩選類型: {show_type}")
                
                return results
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"查詢欄位設定失敗: ORA-{error_code} - {error_message}")
        raise RuntimeError(f"查詢欄位設定失敗: {error_message}")

def update_field_settings(field_updates: List[Dict[str, Any]], updated_by: str = 'SYSTEM') -> bool:
    """
    更新欄位設定
    
    Args:
        field_updates: 欄位更新列表
        updated_by: 更新者
        
    Returns:
        bool: 是否更新成功
    """
    try:
        with _get_connection('system') as connection:
            with connection.cursor() as cursor:
                success_count = 0
                
                for update in field_updates:
                    field_id = update.get('field_id')
                    show_in_list = update.get('show_in_list', 'N')
                    show_in_detail = update.get('show_in_detail', 'N')
                    sort_order = update.get('sort_order', 0)
                    
                    if not field_id:
                        continue
                    
                    # 更新欄位設定
                    sql = """
                    UPDATE FIELD_SETTINGS
                    SET SHOW_IN_LIST = :show_in_list,
                        SHOW_IN_DETAIL = :show_in_detail,
                        SORT_ORDER = :sort_order,
                        UPDATED_DATE = SYSDATE,
                        UPDATED_BY = :updated_by
                    WHERE FIELD_ID = :field_id
                    """
                    
                    cursor.execute(sql, {
                        'field_id': field_id,
                        'show_in_list': show_in_list,
                        'show_in_detail': show_in_detail,
                        'sort_order': sort_order,
                        'updated_by': updated_by
                    })
                    
                    success_count += cursor.rowcount
                
                connection.commit()
                logger.info(f"欄位設定更新成功，更新 {success_count} 筆資料")
                
                return success_count > 0
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"更新欄位設定失敗: ORA-{error_code} - {error_message}")
        raise RuntimeError(f"更新欄位設定失敗: {error_message}")

def get_dynamic_sql_fields(show_type: str = 'list') -> List[str]:
    """
    生成動態 SQL 欄位列表（支援多表關聯和 LISTAGG）
    
    Args:
        show_type: 顯示類型 ('list', 'detail')
        
    Returns:
        List[str]: SQL 欄位列表
    """
    try:
        # 取得欄位設定
        field_settings = get_field_settings(show_type)
        
        # 生成 SQL 欄位列表
        sql_fields = []
        from config import DATE_FIELDS
        
        for field in field_settings:
            field_name = field['FIELD_NAME']
            field_type = field['FIELD_TYPE']
            field_id = field['FIELD_ID']
            
            # 處理多表關聯欄位（使用 LISTAGG）
            if field_id in ['RP_LIB_TITLE', 'RP_OTHER_TITLE', 'RP_OTHER_NAME', 'RP_KEYWORD', 'RP_PLAN_NAME', 'RP_PLAN_CDE']:
                if field_id == 'RP_LIB_TITLE':
                    aliased_field = "LISTAGG(lib.OVC_RP_LIB_TITLE, '<br>') WITHIN GROUP (ORDER BY lib.OVC_RP_LIB_TITLE) as RP_LIB_TITLE"
                elif field_id == 'RP_OTHER_TITLE':
                    aliased_field = "LISTAGG(other_title.OVC_RP_OTHER_TITLE, '<br>') WITHIN GROUP (ORDER BY other_title.OVC_RP_OTHER_TITLE) as RP_OTHER_TITLE"
                elif field_id == 'RP_OTHER_NAME':
                    aliased_field = "LISTAGG(other_name.OVN_RP_OTHER_NAME, '<br>') WITHIN GROUP (ORDER BY other_name.OVN_RP_OTHER_NAME) as RP_OTHER_NAME"
                elif field_id == 'RP_KEYWORD':
                    aliased_field = "LISTAGG(keyword.OVN_RP_KEYWORD, '<br>') WITHIN GROUP (ORDER BY keyword.OVN_RP_KEYWORD) as RP_KEYWORD"
                elif field_id == 'RP_PLAN_NAME':
                    aliased_field = "LISTAGG(plan.OVN_RP_PLAN_NAME, '<br>') WITHIN GROUP (ORDER BY plan.OVN_RP_PLAN_NAME) as RP_PLAN_NAME"
                elif field_id == 'RP_PLAN_CDE':
                    aliased_field = "LISTAGG(plan.OVC_RP_PLAN_CDE, '<br>') WITHIN GROUP (ORDER BY plan.OVC_RP_PLAN_CDE) as RP_PLAN_CDE"
                else:
                    aliased_field = f"{field_name} as {field_id}"
                sql_fields.append(aliased_field)
            # 處理日期欄位格式化
            elif field_type == 'DATE' and field_name in DATE_FIELDS.values():
                formatted_field = f"TO_CHAR({field_name}, 'YYYY-MM-DD') as {field_id}"
                datetime_field = f"TO_CHAR({field_name}, 'YYYY-MM-DD HH24:MI:SS') as {field_id}_DATETIME"
                sql_fields.append(formatted_field)
                sql_fields.append(datetime_field)
            else:
                # 一般欄位直接使用別名
                aliased_field = f"{field_name} as {field_id}"
                sql_fields.append(aliased_field)
        
        logger.info(f"動態 SQL 欄位列表生成成功，{show_type} 類型 {len(sql_fields)} 個欄位")
        
        return sql_fields
        
    except Exception as e:
        logger.error(f"生成動態 SQL 欄位列表失敗: {str(e)}")
        raise RuntimeError(f"生成動態 SQL 欄位列表失敗: {str(e)}")

def search_reports_dynamic(conditions: List[Dict], limit: int = 50, show_type: str = 'list') -> List[Dict[str, Any]]:
    """
    動態搜尋報告
    
    根據欄位設定動態生成查詢
    
    Args:
        conditions: 搜尋條件列表
        limit: 返回筆數限制
        show_type: 顯示類型 ('list', 'detail')
        
    Returns:
        List[Dict[str, Any]]: 搜尋結果列表
    """
    try:
        # 從配置檔案取得正式欄位映射
        from config import (
            MAIN_TABLE_FULL, MAIN_ID_FIELD, TITLE_FIELD,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE, SEARCH_FIELDS, DATE_FIELDS
        )
        
        # 取得動態 SQL 欄位
        dynamic_fields = get_dynamic_sql_fields(show_type)
        
        # 確保包含主鍵欄位
        if MAIN_ID_FIELD not in [field.split(' as ')[0] for field in dynamic_fields]:
            dynamic_fields.insert(0, f"{MAIN_ID_FIELD} as DOC_ID")
        
        with _get_connection('data') as connection:
            # 設定 rowfactory 以返回字典格式
            connection.rowfactory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            
            with connection.cursor() as cursor:
                # 建構 WHERE 條件
                where_clauses = []
                params = {}
                
                # 處理搜尋條件
                for i, condition in enumerate(conditions, 1):
                    field = condition.get('field', '')
                    operator = condition.get('operator', '')
                    value = condition.get('value', '')
                    
                    if not field or not operator or not value:
                        continue
                    
                    # 映射搜尋欄位到正式資料庫欄位
                    mapped_field = SEARCH_FIELDS.get(field, field)
                    
                    # 處理不同的操作符
                    if operator == '包含':
                        where_clauses.append(f"{mapped_field} LIKE :param{i}")
                        params[f'param{i}'] = f'%{value}%'
                    elif operator == '等於':
                        where_clauses.append(f"{mapped_field} = :param{i}")
                        params[f'param{i}'] = value
                    elif operator == '開頭為':
                        where_clauses.append(f"{mapped_field} LIKE :param{i}")
                        params[f'param{i}'] = f'{value}%'
                    else:
                        where_clauses.append(f"{mapped_field} {operator} :param{i}")
                        params[f'param{i}'] = value
                
                # 加入隱形過濾條件
                where_clauses.append(f"{STATUS_CODE_FIELD} = :status_filter")
                params['status_filter'] = STATUS_OPEN_CODE
                
                # 建立完整 SQL（支援多表關聯）
                where_sql = ' AND '.join(where_clauses)
                
                # 檢查是否需要多表關聯
                needs_joins = any(field_id in ['RP_LIB_TITLE', 'RP_OTHER_TITLE', 'RP_OTHER_NAME', 'RP_KEYWORD', 'RP_PLAN_NAME', 'RP_PLAN_CDE'] 
                                for field_id in [field.get('FIELD_ID', '') for field in field_settings])
                
                if needs_joins:
                    sql = f"""
                    SELECT {', '.join(dynamic_fields)}
                    FROM {MAIN_TABLE_FULL} main
                    LEFT JOIN TBIRLIB_RP_LIB_TITLE lib ON main.OVC_RP_NO = lib.OVC_RP_NO
                    LEFT JOIN TBIRLIB_RP_OTHER_TITLE other_title ON main.OVC_RP_NO = other_title.OVC_RP_NO
                    LEFT JOIN TBIRLIB_RP_OTHER_NAME other_name ON main.OVC_RP_NO = other_name.OVC_RP_NO
                    LEFT JOIN TBIRLIB_RP_KEYWORD keyword ON main.OVC_RP_NO = keyword.OVC_RP_NO
                    LEFT JOIN TBIRLIB_RP_PLAN plan ON main.OVC_RP_NO = plan.OVC_RP_NO
                    WHERE {where_sql}
                    GROUP BY main.OVC_RP_NO, {', '.join([f"main.{field}" for field in ['OVC_RP_NO', 'OVN_RP_NAME', 'OVC_STATUS_CDE', 'ODT_PUBLIC_DATE']])}
                    ORDER BY main.{DATE_FIELDS['public_date']} DESC
                    FETCH NEXT :limit ROWS ONLY
                    """
                else:
                    sql = f"""
                    SELECT {', '.join(dynamic_fields)}
                    FROM {MAIN_TABLE_FULL}
                    WHERE {where_sql}
                    ORDER BY {DATE_FIELDS['public_date']} DESC
                    FETCH NEXT :limit ROWS ONLY
                    """
                
                params['limit'] = limit
                
                cursor.execute(sql, params)
                results = cursor.fetchall()
                
                logger.info(f"動態報告搜尋成功，返回 {len(results)} 筆資料")
                logger.info(f"顯示類型: {show_type}, 動態欄位數: {len(dynamic_fields)}")
                logger.info(f"隱形過濾: {STATUS_CODE_FIELD} = '{STATUS_OPEN_CODE}'")
                
                return results
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"動態報告搜尋失敗: ORA-{error_code} - {error_message}")
        raise RuntimeError(f"動態報告搜尋失敗: {error_message}")

def get_report_detail_dynamic(doc_id: str) -> Dict[str, Any]:
    """
    動態取得報告詳情
    
    根據欄位設定動態生成詳情查詢
    
    Args:
        doc_id: 文件 ID
        
    Returns:
        Dict[str, Any]: 報告詳情資料
    """
    try:
        # 從配置檔案取得正式欄位映射
        from config import (
            MAIN_TABLE_FULL, MAIN_ID_FIELD, TITLE_FIELD,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE, SEARCH_FIELDS, DATE_FIELDS
        )
        
        # 取得動態 SQL 欄位
        dynamic_fields = get_dynamic_sql_fields('detail')
        
        # 確保包含主鍵欄位
        if MAIN_ID_FIELD not in [field.split(' as ')[0] for field in dynamic_fields]:
            dynamic_fields.insert(0, f"{MAIN_ID_FIELD} as DOC_ID")
        
        with _get_connection('data') as connection:
            # 設定 rowfactory 以返回字典格式
            connection.rowfactory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            
            with connection.cursor() as cursor:
                # 檢查是否需要多表關聯
                needs_joins = any(field_id in ['RP_LIB_TITLE', 'RP_OTHER_TITLE', 'RP_OTHER_NAME', 'RP_KEYWORD', 'RP_PLAN_NAME', 'RP_PLAN_CDE'] 
                                for field_id in [field.split(' as ')[-1] for field in dynamic_fields])
                
                if needs_joins:
                    sql = f"""
                    SELECT {', '.join(dynamic_fields)}
                    FROM {MAIN_TABLE_FULL} main
                    LEFT JOIN TBIRLIB_RP_LIB_TITLE lib ON main.OVC_RP_NO = lib.OVC_RP_NO
                    LEFT JOIN TBIRLIB_RP_OTHER_TITLE other_title ON main.OVC_RP_NO = other_title.OVC_RP_NO
                    LEFT JOIN TBIRLIB_RP_OTHER_NAME other_name ON main.OVC_RP_NO = other_name.OVC_RP_NO
                    LEFT JOIN TBIRLIB_RP_KEYWORD keyword ON main.OVC_RP_NO = keyword.OVC_RP_NO
                    LEFT JOIN TBIRLIB_RP_PLAN plan ON main.OVC_RP_NO = plan.OVC_RP_NO
                    WHERE main.{MAIN_ID_FIELD} = :doc_id 
                      AND main.{STATUS_CODE_FIELD} = :status_filter
                    GROUP BY main.OVC_RP_NO, {', '.join([f"main.{field}" for field in ['OVC_RP_NO', 'OVN_RP_NAME', 'OVC_STATUS_CDE', 'ODT_PUBLIC_DATE']])}
                    """
                else:
                    sql = f"""
                    SELECT {', '.join(dynamic_fields)}
                    FROM {MAIN_TABLE_FULL}
                    WHERE {MAIN_ID_FIELD} = :doc_id 
                      AND {STATUS_CODE_FIELD} = :status_filter
                    """
                
                cursor.execute(sql, {
                    'doc_id': doc_id,
                    'status_filter': STATUS_OPEN_CODE
                })
                
                result = cursor.fetchone()
                
                if not result:
                    logger.warning(f"找不到報告詳情: {doc_id}")
                    return {}
                
                logger.info(f"動態報告詳情查詢成功: {doc_id}")
                return result
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"動態報告詳情查詢失敗: ORA-{error_code} - {error_message}")
        raise RuntimeError(f"動態報告詳情查詢失敗: {error_message}")

def get_attachment_files(doc_id: str, security_level: str) -> List[Dict[str, Any]]:
    """
    取得附件檔案（根據安全等級判斷）
    
    Args:
        doc_id: 文件 ID
        security_level: 安全等級
        
    Returns:
        List[Dict[str, Any]]: 附件檔案列表
    """
    try:
        # 只有「一般」安全等級才能查詢附件
        if security_level != '一般':
            logger.info(f"安全等級為 {security_level}，不提供附件下載: {doc_id}")
            return []
        
        with _get_connection('data') as connection:
            # 設定 rowfactory 以返回字典格式
            connection.rowfactory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            
            with connection.cursor() as cursor:
                sql = """
                SELECT 
                    OVC_GUID,
                    OVC_FILE_NAME,
                    OVC_FILE_SIZE,
                    OVC_FILE_TYPE,
                    OVC_UPLOAD_DATE,
                    OVC_UPLOAD_USER,
                    OVC_SYS_NO
                FROM TBIRLIB_FILE
                WHERE OVC_SYS_NO = :doc_id
                ORDER BY OVC_UPLOAD_DATE DESC
                """
                
                cursor.execute(sql, {'doc_id': doc_id})
                results = cursor.fetchall()
                
                # 格式化檔案大小和日期
                for result in results:
                    if result.get('OVC_FILE_SIZE'):
                        result['formatted_file_size'] = f"{result['OVC_FILE_SIZE'] / 1024:.2f} KB"
                    else:
                        result['formatted_file_size'] = "未知"
                    
                    if result.get('OVC_UPLOAD_DATE'):
                        result['formatted_upload_date'] = result['OVC_UPLOAD_DATE'].strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        result['formatted_upload_date'] = "未知"
                
                logger.info(f"附件查詢成功: {doc_id}, 返回 {len(results)} 個檔案")
                return results
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"附件查詢失敗: ORA-{error_code} - {error_message}")
        return []

def download_attachment_from_api(ovc_guid: str) -> bytes:
    """
    從外部 API 下載附件檔案
    
    Args:
        ovc_guid: 檔案 GUID
        
    Returns:
        bytes: 檔案內容
        
    Raises:
        RuntimeError: API 呼叫失敗
    """
    try:
        import requests
        from flask import current_app
        
        # 從配置取得 API 端點
        api_endpoint = current_app.config.get('ATTACHMENT_API_ENDPOINT', 'http://localhost:8080/api/download')
        
        logger.info(f"開始從 API 下載附件: {ovc_guid}")
        
        # 呼叫外部 API
        response = requests.post(
            api_endpoint,
            json={'guid': ovc_guid},
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"附件下載成功: {ovc_guid}, 大小: {len(response.content)} bytes")
            return response.content
        else:
            error_msg = f"API 呼叫失敗: HTTP {response.status_code}"
            logger.error(f"{error_msg}, GUID: {ovc_guid}")
            raise RuntimeError(error_msg)
            
    except requests.RequestException as e:
        error_msg = f"API 呼叫異常: {str(e)}"
        logger.error(f"{error_msg}, GUID: {ovc_guid}")
        raise RuntimeError(f"附件下載失敗: {str(e)}")
    except Exception as e:
        error_msg = f"附件下載失敗: {str(e)}"
        logger.error(f"{error_msg}, GUID: {ovc_guid}")
        raise RuntimeError(error_msg)

def log_search_history(account: str, mode: str, query_details: Dict[str, Any], 
                      result_count: int = 0, error_message: str = None) -> bool:
    """
    記錄搜尋歷史
    
    Args:
        account: 使用者帳號
        mode: 搜尋模式 ('simple' 或 'advanced')
        query_details: 查詢詳細資訊
        result_count: 結果筆數
        error_message: 錯誤訊息（如果有的話）
        
    Returns:
        bool: 是否記錄成功
    """
    try:
        with _get_connection('system') as connection:
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO SEARCH_HISTORY (
                    ACCOUNT, SEARCH_MODE, QUERY_DETAILS, RESULT_COUNT, 
                    ERROR_MESSAGE, SEARCH_TIME
                ) VALUES (
                    :account, :mode, :query_details, :result_count,
                    :error_message, SYSDATE
                )
                """
                
                import json
                cursor.execute(sql, {
                    'account': account,
                    'mode': mode,
                    'query_details': json.dumps(query_details, ensure_ascii=False),
                    'result_count': result_count,
                    'error_message': error_message
                })
                
                connection.commit()
                logger.info(f"搜尋歷史記錄成功: {account}, {mode}, {result_count} 筆結果")
                return True
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"記錄搜尋歷史失敗: ORA-{error_code} - {error_message}")
        return False

def get_dynamic_field_list(show_type: str = 'list') -> List[Dict[str, Any]]:
    """
    取得動態欄位列表（別名函數，與 get_field_settings 功能相同）
    
    Args:
        show_type: 顯示類型 ('list', 'detail')
        
    Returns:
        List[Dict[str, Any]]: 欄位設定列表
    """
    return get_field_settings(show_type)

# ===========================================
# 跨資料表聯合搜尋系統
# ===========================================

def search_cross_table_unified(keyword: str = None, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
    """
    跨資料表聯合搜尋 - 四種資料類型統一檢索
    
    Args:
        keyword: 搜尋關鍵字
        page: 頁碼
        page_size: 每頁筆數
        
    Returns:
        Dict[str, Any]: 搜尋結果包含資料、總筆數、分頁資訊
    """
    try:
        with _get_connection('main') as connection:
            with connection.cursor() as cursor:
                # 建立基礎 SQL
                base_sql = """
                WITH REPORT_DATA AS (
                    SELECT 
                        '1' AS DATA_TYPE,
                        '技術報告' AS DATA_TYPE_NAME,
                        '#E6F3FF' AS BACKGROUND_COLOR,
                        OVC_RP_NO AS UNIQUE_ID,
                        OVC_RP_CAT_CDE AS RP_CAT_CDE,
                        OVC_RP_CAT_NAME AS RP_CAT_NAME,
                        OVC_RP_TYPE_CDE AS RP_TYPE_CDE,
                        OVC_RP_TYPE_NAME AS RP_TYPE_NAME,
                        OVC_RP_CSI_NAME AS RP_CSI_NAME,
                        OVC_SECERT_LV_CDE AS SECERT_LV_CDE,
                        OVC_SECERT_LV_NAME AS SECERT_LV_NAME,
                        OVC_SECERT_ATTRIBUTE AS SECERT_ATTRIBUTE,
                        OVC_TRADE_SECERT_CDE AS TRADE_SECERT_CDE,
                        OVC_TRADE_SECERT_NAME AS TRADE_SECERT_NAME,
                        OVC_PROMOTE_CSI_NAME AS PROMOTE_CSI_NAME,
                        OVC_TRAIN_CDE AS TRAIN_CDE,
                        OVC_TRAIN_NAME AS TRAIN_NAME,
                        OVN_SUMMARY AS SUMMARY,
                        OVN_DESCRIPTION AS DESCRIPTION,
                        OVN_APPLICATION AS APPLICATION,
                        OVN_RP_MAIN_AUTHOR_DEPT_NAME AS MAIN_AUTHOR_DEPT_NAME,
                        OVN_RP_MAIN_AUTHOR AS MAIN_AUTHOR,
                        OVN_RP_AUTHOR_LIST AS AUTHOR_LIST,
                        OVC_HOST_NAME AS HOST_NAME,
                        OVC_YEAR AS YEAR,
                        ODT_RP_FIN_DATE AS FIN_DATE,
                        OVC_RP_PAGE AS PAGE,
                        OVN_RP_NAME AS TITLE,
                        ODT_PUBLIC_DATE AS PUBLIC_DATE,
                        (SELECT LISTAGG(OVC_RP_LIB_TITLE, ',') WITHIN GROUP (ORDER BY OVC_RP_LIB_TITLE)
                         FROM TBIRLIB_RP_LIB_TITLE WHERE OVC_RP_NO = R.OVC_RP_NO) AS RP_LIB_TITLE_LIST,
                        (SELECT LISTAGG(OVC_RP_OTHER_TITLE, ',') WITHIN GROUP (ORDER BY OVC_RP_OTHER_TITLE)
                         FROM TBIRLIB_RP_OTHER_TITLE WHERE OVC_RP_NO = R.OVC_RP_NO) AS RP_OTHER_TITLE_LIST,
                        (SELECT LISTAGG(OVN_RP_OTHER_NAME, ',') WITHIN GROUP (ORDER BY OVN_RP_OTHER_NAME)
                         FROM TBIRLIB_RP_OTHER_NAME WHERE OVC_RP_NO = R.OVC_RP_NO) AS RP_OTHER_NAME_LIST,
                        (SELECT LISTAGG(OVN_RP_KEYWORD, ',') WITHIN GROUP (ORDER BY OVN_RP_KEYWORD)
                         FROM TBIRLIB_RP_KEYWORD WHERE OVC_RP_NO = R.OVC_RP_NO) AS RP_KEYWORD_LIST,
                        (SELECT LISTAGG(OVN_RP_PLAN_NAME || '(' || OVC_RP_PLAN_CDE || ')', ',') WITHIN GROUP (ORDER BY OVN_RP_PLAN_NAME)
                         FROM TBIRLIB_RP_PLAN WHERE OVC_RP_NO = R.OVC_RP_NO) AS RP_PLAN_LIST
                    FROM TBIRLIB_REPORT_MAIN R
                    WHERE OVC_PUBLIC_TYPE_CDE = 'Y'
                ),
                HISTORY_DATA AS (
                    SELECT 
                        '2' AS DATA_TYPE,
                        '史政' AS DATA_TYPE_NAME,
                        '#E6FFE6' AS BACKGROUND_COLOR,
                        OVC_HS_NO AS UNIQUE_ID,
                        OVC_HS_CAT_CDE AS HS_CAT_CDE,
                        OVC_HS_CAT_NAME AS HS_CAT_NAME,
                        NULL AS RP_TYPE_CDE,
                        NULL AS RP_TYPE_NAME,
                        NULL AS RP_CSI_NAME,
                        NULL AS SECERT_LV_CDE,
                        NULL AS SECERT_LV_NAME,
                        NULL AS SECERT_ATTRIBUTE,
                        NULL AS TRADE_SECERT_CDE,
                        NULL AS TRADE_SECERT_NAME,
                        NULL AS PROMOTE_CSI_NAME,
                        NULL AS TRAIN_CDE,
                        NULL AS TRAIN_NAME,
                        OVC_HS_SUMMARY AS SUMMARY,
                        NULL AS DESCRIPTION,
                        NULL AS APPLICATION,
                        NULL AS MAIN_AUTHOR_DEPT_NAME,
                        NULL AS MAIN_AUTHOR,
                        NULL AS AUTHOR_LIST,
                        NULL AS HOST_NAME,
                        NULL AS YEAR,
                        NULL AS FIN_DATE,
                        NULL AS PAGE,
                        OVN_HS_NAME AS TITLE,
                        NULL AS PUBLIC_DATE,
                        OVC_HS_PULISH_YEAE AS PUBLISH_YEAR,
                        OVC_HA_NO AS HA_NO,
                        OVN_HA_TYPE AS HA_TYPE,
                        ONB_HA_UNIT_NUM AS HA_UNIT_NUM,
                        OVN_HA_UNIT_NAME AS HA_UNIT_NAME,
                        OVC_HA_LIB_MANAGE AS HA_LIB_MANAGE,
                        OVN_HA_GET_INFO AS HA_GET_INFO,
                        OVC_GET_YEAR AS GET_YEAR,
                        OVN_HA_BELONG AS HA_BELONG,
                        OVC_HA_SIZE AS HA_SIZE,
                        OVC_HA_ROUND AS HA_ROUND,
                        OVC_HA_SPECIAL_SIZE AS HA_SPECIAL_SIZE,
                        ODT_HS_EVENT_DATE AS EVENT_DATE,
                        NULL AS RP_LIB_TITLE_LIST,
                        NULL AS RP_OTHER_TITLE_LIST,
                        NULL AS RP_OTHER_NAME_LIST,
                        NULL AS RP_KEYWORD_LIST,
                        NULL AS RP_PLAN_LIST
                    FROM TRIRLIB_HISTORY_MAIN H
                    WHERE OVC_PUBLIC_TYPE_CDE = 'Y'
                ),
                PHOTO_DATA AS (
                    SELECT 
                        '4' AS DATA_TYPE,
                        '史政照片' AS DATA_TYPE_NAME,
                        '#FFFFE6' AS BACKGROUND_COLOR,
                        OVC_TO_NO AS UNIQUE_ID,
                        NULL AS RP_CAT_CDE,
                        NULL AS RP_CAT_NAME,
                        NULL AS RP_TYPE_CDE,
                        NULL AS RP_TYPE_NAME,
                        NULL AS RP_CSI_NAME,
                        NULL AS SECERT_LV_CDE,
                        NULL AS SECERT_LV_NAME,
                        NULL AS SECERT_ATTRIBUTE,
                        NULL AS TRADE_SECERT_CDE,
                        NULL AS TRADE_SECERT_NAME,
                        NULL AS PROMOTE_CSI_NAME,
                        NULL AS TRAIN_CDE,
                        NULL AS TRAIN_NAME,
                        OVN_TO_SUMMARY AS SUMMARY,
                        NULL AS DESCRIPTION,
                        NULL AS APPLICATION,
                        NULL AS MAIN_AUTHOR_DEPT_NAME,
                        NULL AS MAIN_AUTHOR,
                        NULL AS AUTHOR_LIST,
                        NULL AS HOST_NAME,
                        NULL AS YEAR,
                        NULL AS FIN_DATE,
                        NULL AS PAGE,
                        OVC_TO_NAME AS TITLE,
                        ODT_TO_DATE AS PUBLIC_DATE,
                        NULL AS PUBLISH_YEAR,
                        NULL AS HA_NO,
                        NULL AS HA_TYPE,
                        NULL AS HA_UNIT_NUM,
                        NULL AS HA_UNIT_NAME,
                        NULL AS HA_LIB_MANAGE,
                        NULL AS HA_GET_INFO,
                        NULL AS GET_YEAR,
                        NULL AS HA_BELONG,
                        NULL AS HA_SIZE,
                        NULL AS HA_ROUND,
                        NULL AS HA_SPECIAL_SIZE,
                        NULL AS EVENT_DATE,
                        OVN_TO_PLACE AS TO_PLACE,
                        OVN_TO_PEOPLE AS TO_PEOPLE,
                        (OVC_TO_DEPT1_NAME || ' ' || OVC_TO_DEPT2_NAME) AS TO_DEPT_NAME,
                        (OVC_TO_APPLY_DEPT1_NAME || ' ' || OVC_TO_APPLY_DEPT2_NAME) AS TO_APPLY_DEPT_NAME,
                        NULL AS RP_LIB_TITLE_LIST,
                        NULL AS RP_OTHER_TITLE_LIST,
                        NULL AS RP_OTHER_NAME_LIST,
                        NULL AS RP_KEYWORD_LIST,
                        NULL AS RP_PLAN_LIST
                    FROM TRIRLIB_PHOTO_MAIN P
                    WHERE OVC_PUBLIC_TYPE_CDE = 'Y'
                ),
                PAPER_DATA AS (
                    SELECT 
                        '3' AS DATA_TYPE,
                        '逸光報' AS DATA_TYPE_NAME,
                        '#F0F0F0' AS BACKGROUND_COLOR,
                        OVC_PAPER_ID AS UNIQUE_ID,
                        NULL AS RP_CAT_CDE,
                        NULL AS RP_CAT_NAME,
                        NULL AS RP_TYPE_CDE,
                        NULL AS RP_TYPE_NAME,
                        NULL AS RP_CSI_NAME,
                        NULL AS SECERT_LV_CDE,
                        NULL AS SECERT_LV_NAME,
                        NULL AS SECERT_ATTRIBUTE,
                        NULL AS TRADE_SECERT_CDE,
                        NULL AS TRADE_SECERT_NAME,
                        NULL AS PROMOTE_CSI_NAME,
                        NULL AS TRAIN_CDE,
                        NULL AS TRAIN_NAME,
                        NULL AS SUMMARY,
                        NULL AS DESCRIPTION,
                        NULL AS APPLICATION,
                        NULL AS MAIN_AUTHOR_DEPT_NAME,
                        NULL AS MAIN_AUTHOR,
                        NULL AS AUTHOR_LIST,
                        NULL AS HOST_NAME,
                        NULL AS YEAR,
                        NULL AS FIN_DATE,
                        NULL AS PAGE,
                        OVN_PAPER_NAME AS TITLE,
                        NULL AS PUBLIC_DATE,
                        NULL AS PUBLISH_YEAR,
                        NULL AS HA_NO,
                        NULL AS HA_TYPE,
                        NULL AS HA_UNIT_NUM,
                        NULL AS HA_UNIT_NAME,
                        NULL AS HA_LIB_MANAGE,
                        NULL AS HA_GET_INFO,
                        NULL AS GET_YEAR,
                        NULL AS HA_BELONG,
                        NULL AS HA_SIZE,
                        NULL AS HA_ROUND,
                        NULL AS HA_SPECIAL_SIZE,
                        NULL AS EVENT_DATE,
                        NULL AS TO_PLACE,
                        NULL AS TO_PEOPLE,
                        NULL AS TO_DEPT_NAME,
                        NULL AS TO_APPLY_DEPT_NAME,
                        NULL AS RP_LIB_TITLE_LIST,
                        NULL AS RP_OTHER_TITLE_LIST,
                        NULL AS RP_OTHER_NAME_LIST,
                        NULL AS RP_KEYWORD_LIST,
                        NULL AS RP_PLAN_LIST,
                        OVN_PAPER_AUTHOR AS PAPER_AUTHOR
                    FROM TRIRLIB_PAPER_MAIN P
                    WHERE OVC_PUBLIC_TYPE_CDE = 'Y'
                )
                """
                
                # 添加關鍵字搜尋條件
                where_clause = ""
                if keyword and keyword.strip():
                    where_clause = """
                    WHERE (
                        -- 技術報告欄位
                        UPPER(RP_CSI_NAME) LIKE UPPER(:keyword) OR
                        UPPER(RP_CAT_NAME) LIKE UPPER(:keyword) OR
                        UPPER(RP_TYPE_NAME) LIKE UPPER(:keyword) OR
                        UPPER(SECERT_LV_NAME) LIKE UPPER(:keyword) OR
                        UPPER(TRADE_SECERT_NAME) LIKE UPPER(:keyword) OR
                        UPPER(PROMOTE_CSI_NAME) LIKE UPPER(:keyword) OR
                        UPPER(TRAIN_NAME) LIKE UPPER(:keyword) OR
                        UPPER(SUMMARY) LIKE UPPER(:keyword) OR
                        UPPER(DESCRIPTION) LIKE UPPER(:keyword) OR
                        UPPER(APPLICATION) LIKE UPPER(:keyword) OR
                        UPPER(MAIN_AUTHOR_DEPT_NAME) LIKE UPPER(:keyword) OR
                        UPPER(MAIN_AUTHOR) LIKE UPPER(:keyword) OR
                        UPPER(AUTHOR_LIST) LIKE UPPER(:keyword) OR
                        UPPER(HOST_NAME) LIKE UPPER(:keyword) OR
                        UPPER(TITLE) LIKE UPPER(:keyword) OR
                        UPPER(RP_LIB_TITLE_LIST) LIKE UPPER(:keyword) OR
                        UPPER(RP_OTHER_TITLE_LIST) LIKE UPPER(:keyword) OR
                        UPPER(RP_OTHER_NAME_LIST) LIKE UPPER(:keyword) OR
                        UPPER(RP_KEYWORD_LIST) LIKE UPPER(:keyword) OR
                        UPPER(RP_PLAN_LIST) LIKE UPPER(:keyword) OR
                        
                        -- 史政欄位
                        UPPER(HS_CAT_NAME) LIKE UPPER(:keyword) OR
                        UPPER(HS_NAME) LIKE UPPER(:keyword) OR
                        UPPER(HS_SUMMARY) LIKE UPPER(:keyword) OR
                        UPPER(HA_TYPE) LIKE UPPER(:keyword) OR
                        UPPER(HA_UNIT_NAME) LIKE UPPER(:keyword) OR
                        UPPER(HA_LIB_MANAGE) LIKE UPPER(:keyword) OR
                        UPPER(HA_GET_INFO) LIKE UPPER(:keyword) OR
                        UPPER(HA_BELONG) LIKE UPPER(:keyword) OR
                        
                        -- 史政照片欄位
                        UPPER(TO_NAME) LIKE UPPER(:keyword) OR
                        UPPER(TO_PLACE) LIKE UPPER(:keyword) OR
                        UPPER(TO_PEOPLE) LIKE UPPER(:keyword) OR
                        UPPER(TO_SUMMARY) LIKE UPPER(:keyword) OR
                        UPPER(TO_DEPT_NAME) LIKE UPPER(:keyword) OR
                        UPPER(TO_APPLY_DEPT_NAME) LIKE UPPER(:keyword) OR
                        
                        -- 逸光報欄位
                        UPPER(PAPER_NAME) LIKE UPPER(:keyword) OR
                        UPPER(PAPER_AUTHOR) LIKE UPPER(:keyword)
                    )
                    """
                
                # 完整 SQL
                full_sql = f"""
                {base_sql}
                SELECT * FROM (
                    SELECT * FROM REPORT_DATA
                    UNION ALL
                    SELECT * FROM HISTORY_DATA
                    UNION ALL
                    SELECT * FROM PAPER_DATA  
                    UNION ALL
                    SELECT * FROM PHOTO_DATA
                ) {where_clause}
                ORDER BY DATA_TYPE ASC, UNIQUE_ID DESC
                """
                
                # 計算總筆數
                count_sql = f"""
                {base_sql}
                SELECT COUNT(*) AS TOTAL_COUNT FROM (
                    SELECT * FROM REPORT_DATA
                    UNION ALL
                    SELECT * FROM HISTORY_DATA
                    UNION ALL
                    SELECT * FROM PAPER_DATA
                    UNION ALL
                    SELECT * FROM PHOTO_DATA
                ) {where_clause}
                """
                
                # 執行總筆數查詢
                params = {'keyword': f'%{keyword}%'} if keyword and keyword.strip() else {}
                cursor.execute(count_sql, params)
                total_count = cursor.fetchone()[0]
                
                # 計算分頁
                offset = (page - 1) * page_size
                total_pages = (total_count + page_size - 1) // page_size
                
                # 執行分頁查詢
                paginated_sql = f"""
                SELECT * FROM (
                    SELECT A.*, ROWNUM AS RN FROM (
                        {full_sql}
                    ) A WHERE ROWNUM <= {offset + page_size}
                ) WHERE RN > {offset}
                """
                
                cursor.execute(paginated_sql, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                logger.info(f"跨表搜尋完成: 關鍵字='{keyword}', 總筆數={total_count}, 頁碼={page}")
                
                return {
                    'results': results,
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"跨表搜尋失敗: ORA-{error_code} - {error_message}")
        raise RuntimeError(f"跨表搜尋失敗: {error_message}")

def get_cross_table_detail(data_type: str, unique_id: str) -> Dict[str, Any]:
    """
    取得跨表資料詳情
    
    Args:
        data_type: 資料類型 ('1'=技術報告, '2'=史政, '3'=逸光報, '4'=史政照片)
        unique_id: 唯一識別碼
        
    Returns:
        Dict[str, Any]: 詳情資料
    """
    try:
        with _get_connection('main') as connection:
            with connection.cursor() as cursor:
                if data_type == '1':  # 技術報告
                    sql = """
                    SELECT 
                        OVC_RP_NO AS UNIQUE_ID,
                        OVC_RP_CAT_CDE AS RP_CAT_CDE,
                        OVC_RP_CAT_NAME AS RP_CAT_NAME,
                        OVC_RP_TYPE_CDE AS RP_TYPE_CDE,
                        OVC_RP_TYPE_NAME AS RP_TYPE_NAME,
                        OVC_RP_CSI_NAME AS RP_CSI_NAME,
                        OVC_SECERT_LV_CDE AS SECERT_LV_CDE,
                        OVC_SECERT_LV_NAME AS SECERT_LV_NAME,
                        OVC_SECERT_ATTRIBUTE AS SECERT_ATTRIBUTE,
                        OVC_TRADE_SECERT_CDE AS TRADE_SECERT_CDE,
                        OVC_TRADE_SECERT_NAME AS TRADE_SECERT_NAME,
                        OVC_PROMOTE_CSI_NAME AS PROMOTE_CSI_NAME,
                        OVC_TRAIN_CDE AS TRAIN_CDE,
                        OVC_TRAIN_NAME AS TRAIN_NAME,
                        OVN_SUMMARY AS SUMMARY,
                        OVN_DESCRIPTION AS DESCRIPTION,
                        OVN_APPLICATION AS APPLICATION,
                        OVN_RP_MAIN_AUTHOR_DEPT_NAME AS MAIN_AUTHOR_DEPT_NAME,
                        OVN_RP_MAIN_AUTHOR AS MAIN_AUTHOR,
                        OVN_RP_AUTHOR_LIST AS AUTHOR_LIST,
                        OVC_HOST_NAME AS HOST_NAME,
                        OVC_YEAR AS YEAR,
                        ODT_RP_FIN_DATE AS FIN_DATE,
                        OVC_RP_PAGE AS PAGE,
                        OVN_RP_NAME AS TITLE,
                        ODT_PUBLIC_DATE AS PUBLIC_DATE,
                        (SELECT LISTAGG(OVC_RP_LIB_TITLE, ',') WITHIN GROUP (ORDER BY OVC_RP_LIB_TITLE)
                         FROM TBIRLIB_RP_LIB_TITLE WHERE OVC_RP_NO = :unique_id) AS RP_LIB_TITLE_LIST,
                        (SELECT LISTAGG(OVC_RP_OTHER_TITLE, ',') WITHIN GROUP (ORDER BY OVC_RP_OTHER_TITLE)
                         FROM TBIRLIB_RP_OTHER_TITLE WHERE OVC_RP_NO = :unique_id) AS RP_OTHER_TITLE_LIST,
                        (SELECT LISTAGG(OVN_RP_OTHER_NAME, ',') WITHIN GROUP (ORDER BY OVN_RP_OTHER_NAME)
                         FROM TBIRLIB_RP_OTHER_NAME WHERE OVC_RP_NO = :unique_id) AS RP_OTHER_NAME_LIST,
                        (SELECT LISTAGG(OVN_RP_KEYWORD, ',') WITHIN GROUP (ORDER BY OVN_RP_KEYWORD)
                         FROM TBIRLIB_RP_KEYWORD WHERE OVC_RP_NO = :unique_id) AS RP_KEYWORD_LIST,
                        (SELECT LISTAGG(OVN_RP_PLAN_NAME || '(' || OVC_RP_PLAN_CDE || ')', ',') WITHIN GROUP (ORDER BY OVN_RP_PLAN_NAME)
                         FROM TBIRLIB_RP_PLAN WHERE OVC_RP_NO = :unique_id) AS RP_PLAN_LIST
                    FROM TBIRLIB_REPORT_MAIN
                    WHERE OVC_RP_NO = :unique_id AND OVC_PUBLIC_TYPE_CDE = 'Y'
                    """
                    
                elif data_type == '2':  # 史政
                    sql = """
                    SELECT 
                        OVC_HS_NO AS UNIQUE_ID,
                        OVC_HS_CAT_CDE AS HS_CAT_CDE,
                        OVC_HS_CAT_NAME AS HS_CAT_NAME,
                        OVN_HS_NAME AS HS_NAME,
                        OVC_HS_PULISH_YEAE AS PUBLISH_YEAR,
                        OVC_HS_SUMMARY AS HS_SUMMARY,
                        OVC_HA_NO AS HA_NO,
                        OVN_HA_TYPE AS HA_TYPE,
                        ONB_HA_UNIT_NUM AS HA_UNIT_NUM,
                        OVN_HA_UNIT_NAME AS HA_UNIT_NAME,
                        OVC_HA_LIB_MANAGE AS HA_LIB_MANAGE,
                        OVN_HA_GET_INFO AS HA_GET_INFO,
                        OVC_GET_YEAR AS GET_YEAR,
                        OVN_HA_BELONG AS HA_BELONG,
                        OVC_HA_SIZE AS HA_SIZE,
                        OVC_HA_ROUND AS HA_ROUND,
                        OVC_HA_SPECIAL_SIZE AS HA_SPECIAL_SIZE,
                        ODT_HS_EVENT_DATE AS EVENT_DATE
                    FROM TRIRLIB_HISTORY_MAIN
                    WHERE OVC_HS_NO = :unique_id AND OVC_PUBLIC_TYPE_CDE = 'Y'
                    """
                    
                elif data_type == '3':  # 逸光報
                    sql = """
                    SELECT 
                        OVC_PAPER_ID AS UNIQUE_ID,
                        OVN_PAPER_NAME AS PAPER_NAME,
                        OVN_PAPER_AUTHOR AS PAPER_AUTHOR
                    FROM TRIRLIB_PAPER_MAIN
                    WHERE OVC_PAPER_ID = :unique_id AND OVC_PUBLIC_TYPE_CDE = 'Y'
                    """
                    
                elif data_type == '4':  # 史政照片
                    sql = """
                    SELECT 
                        OVC_TO_NO AS UNIQUE_ID,
                        OVC_TO_NAME AS TO_NAME,
                        ODT_TO_DATE AS TO_DATE,
                        OVN_TO_PLACE AS TO_PLACE,
                        OVN_TO_PEOPLE AS TO_PEOPLE,
                        OVN_TO_SUMMARY AS TO_SUMMARY,
                        (OVC_TO_DEPT1_NAME || ' ' || OVC_TO_DEPT2_NAME) AS TO_DEPT_NAME,
                        (OVC_TO_APPLY_DEPT1_NAME || ' ' || OVC_TO_APPLY_DEPT2_NAME) AS TO_APPLY_DEPT_NAME
                    FROM TRIRLIB_PHOTO_MAIN
                    WHERE OVC_TO_NO = :unique_id AND OVC_PUBLIC_TYPE_CDE = 'Y'
                    """
                    
                else:
                    raise ValueError(f"不支援的資料類型: {data_type}")
                
                cursor.execute(sql, {'unique_id': unique_id})
                row = cursor.fetchone()
                
                if not row:
                    raise ValueError(f"找不到資料: data_type={data_type}, unique_id={unique_id}")
                
                columns = [col[0] for col in cursor.description]
                result = dict(zip(columns, row))
                
                # 添加資料類型資訊
                type_mapping = {
                    '1': {'name': '技術報告', 'color': '#E6F3FF'},
                    '2': {'name': '史政', 'color': '#E6FFE6'},
                    '3': {'name': '逸光報', 'color': '#F0F0F0'},
                    '4': {'name': '史政照片', 'color': '#FFFFE6'}
                }
                
                result['DATA_TYPE'] = data_type
                result['DATA_TYPE_NAME'] = type_mapping[data_type]['name']
                result['BACKGROUND_COLOR'] = type_mapping[data_type]['color']
                
                logger.info(f"取得跨表詳情成功: {type_mapping[data_type]['name']} - {unique_id}")
                return result
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"取得跨表詳情失敗: ORA-{error_code} - {error_message}")
        raise RuntimeError(f"取得詳情失敗: {error_message}")

def get_cross_table_attachments(data_type: str, unique_id: str) -> List[Dict[str, Any]]:
    """
    取得跨表資料附件
    
    Args:
        data_type: 資料類型
        unique_id: 唯一識別碼
        
    Returns:
        List[Dict[str, Any]]: 附件列表
    """
    try:
        with _get_connection('main') as connection:
            with connection.cursor() as cursor:
                if data_type == '1':  # 技術報告 - 需要檢查機密等級
                    # 先取得機密等級
                    cursor.execute("""
                        SELECT OVC_SECERT_LV_CDE FROM TBIRLIB_REPORT_MAIN 
                        WHERE OVC_RP_NO = :unique_id AND OVC_PUBLIC_TYPE_CDE = 'Y'
                    """, {'unique_id': unique_id})
                    
                    row = cursor.fetchone()
                    if not row:
                        return []
                    
                    secret_level = row[0]
                    
                    # 只有機密等級為'一般'才能取得附件
                    if secret_level != '一般':
                        logger.info(f"技術報告機密等級非一般，無法取得附件: {unique_id}")
                        return []
                    
                    # 取得附件
                    cursor.execute("""
                        SELECT OVC_SYS_NO, OVC_GUID, OVC_FILE_NAME, OVC_FILE_SIZE
                        FROM TBIRLIB_FILE 
                        WHERE OVC_RP_NO = :unique_id
                        ORDER BY OVC_FILE_NAME
                    """, {'unique_id': unique_id})
                    
                else:  # 其他三種資料類型直接取得附件
                    if data_type == '2':  # 史政
                        cursor.execute("""
                            SELECT OVC_SYS_NO, OVC_GUID, OVC_FILE_NAME, OVC_FILE_SIZE
                            FROM TBIRLIB_FILE 
                            WHERE OVC_HS_NO = :unique_id
                            ORDER BY OVC_FILE_NAME
                        """, {'unique_id': unique_id})
                    elif data_type == '3':  # 逸光報
                        cursor.execute("""
                            SELECT OVC_SYS_NO, OVC_GUID, OVC_FILE_NAME, OVC_FILE_SIZE
                            FROM TBIRLIB_FILE 
                            WHERE OVC_PAPER_ID = :unique_id
                            ORDER BY OVC_FILE_NAME
                        """, {'unique_id': unique_id})
                    elif data_type == '4':  # 史政照片
                        cursor.execute("""
                            SELECT OVC_SYS_NO, OVC_GUID, OVC_FILE_NAME, OVC_FILE_SIZE
                            FROM TBIRLIB_FILE 
                            WHERE OVC_TO_NO = :unique_id
                            ORDER BY OVC_FILE_NAME
                        """, {'unique_id': unique_id})
                
                columns = [col[0] for col in cursor.description]
                attachments = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                logger.info(f"取得跨表附件成功: {data_type} - {unique_id}, 附件數: {len(attachments)}")
                return attachments
                
    except Exception as e:
        error_code, error_message = _parse_ora_error(e)
        logger.error(f"取得跨表附件失敗: ORA-{error_code} - {error_message}")
        return []
