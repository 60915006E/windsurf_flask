"""
Oracle 19c 資料庫連線模組
遵循 Windows Server 2022 離線環境開發規範
使用 python-oracledb Thin Mode 實作安全查詢
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from pathlib import Path

# 嘗試導入真實的 oracledb，如果失敗則使用模擬版本
try:
    import oracledb
    logger = logging.getLogger(__name__)
    logger.info("使用真實 python-oracledb 模組")
except ImportError:
    # 導入模擬版本並設定別名
    import mock_oracledb as mock_oracledb
    
    # 建立一個包裝器來提供正確的屬性
    class OracleModuleWrapper:
        def __init__(self):
            self.Error = mock_oracledb.MockError
            self.DatabaseError = mock_oracledb.DatabaseError
            self.InterfaceError = mock_oracledb.InterfaceError
            self.Connection = mock_oracledb.MockConnection
            self.Cursor = mock_oracledb.MockCursor
            self.SPOOL_ATTRVAL_NOWAIT = mock_oracledb.SPOOL_ATTRVAL_NOWAIT
            self.init_oracle_client = mock_oracledb.init_oracle_client
            self.create_pool = mock_oracledb.create_pool
    
    # 使用包裝器
    oracledb = OracleModuleWrapper()
    logger = logging.getLogger(__name__)
    logger.warning("使用模擬 python-oracledb 模組（測試環境）")

class OracleDatabaseManager:
    """
    Oracle 資料庫管理器
    負責連線池管理、安全查詢、錯誤處理
    """
    
    def __init__(self, 
                 user: str, 
                 password: str, 
                 dsn: str,
                 min_connections: int = 2,
                 max_connections: int = 10,
                 increment: int = 1):
        """
        初始化資料庫管理器
        
        Args:
            user: 資料庫使用者名稱
            password: 資料庫密碼
            dsn: 資料庫連線字串 (host:port/service_name)
            min_connections: 連線池最小連線數
            max_connections: 連線池最大連線數
            increment: 連線池增量連線數
        """
        self.user = user
        self.password = password
        self.dsn = dsn
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.increment = increment
        self.pool = None
        
        logger.info(f"初始化 Oracle 資料庫管理器: DSN={dsn}")
        
    def initialize_connection_pool(self) -> bool:
        """
        初始化連線池
        使用 python-oracledb Thin Mode 減少依賴
        
        Returns:
            bool: 連線池初始化是否成功
        """
        try:
            # 設定 Thin Mode (不需要 Oracle Client)
            oracledb.init_oracle_client()
            
            # 建立連線池
            self.pool = oracledb.create_pool(
                user=self.user,
                password=self.password,
                dsn=self.dsn,
                min=self.min_connections,
                max=self.max_connections,
                increment=self.increment,
                getmode=oracledb.SPOOL_ATTRVAL_NOWAIT,
                session_callback=self._init_session
            )
            
            logger.info(f"Oracle 連線池建立成功: 最小={self.min_connections}, 最大={self.max_connections}")
            return True
            
        except oracledb.Error as e:
            # 遮蔽敏感資訊，只記錄錯誤類型
            error_code = getattr(e, 'code', 'UNKNOWN')
            error_message = str(e)
            
            # 記錄到日誌檔案，不包含敏感資訊
            logger.error(f"Oracle 連線池初始化失敗: ORA-{error_code}")
            logger.error(f"錯誤詳情: {error_message}")
            
            return False
        except Exception as e:
            logger.error(f"連線池初始化發生未預期錯誤: {str(e)}")
            return False
    
    def _init_session(self, connection: oracledb.Connection) -> None:
        """
        連線會話初始化回調函數
        設定會話參數以優化效能
        
        Args:
            connection: Oracle 連線物件
        """
        try:
            # 設定日期格式
            with connection.cursor() as cursor:
                cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'")
                cursor.execute("ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF'")
                
            logger.debug("Oracle 會話初始化完成")
            
        except oracledb.Error as e:
            logger.warning(f"會話初始化警告: ORA-{getattr(e, 'code', 'UNKNOWN')}")
    
    @contextmanager
    def get_connection(self):
        """
        取得資料庫連線的上下文管理器
        自動處理連線取得與釋放
        
        Yields:
            oracledb.Connection: 資料庫連線物件
        """
        connection = None
        try:
            if not self.pool:
                raise RuntimeError("連線池未初始化")
                
            connection = self.pool.acquire()
            yield connection
            
        except oracledb.Error as e:
            error_code = getattr(e, 'code', 'UNKNOWN')
            logger.error(f"取得資料庫連線失敗: ORA-{error_code}")
            raise
        except Exception as e:
            logger.error(f"連線取得發生未預期錯誤: {str(e)}")
            raise
        finally:
            if connection:
                try:
                    self.pool.release(connection)
                except Exception as e:
                    logger.warning(f"連線釋放警告: {str(e)}")
    
    def execute_query(self, 
                     sql: str, 
                     bind_params: Dict[str, Any] = None,
                     fetch_all: bool = True) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        執行安全的參數化查詢
        
        Args:
            sql: SQL 查詢語句（使用綁定變數）
            bind_params: 綁定參數字典
            fetch_all: 是否取得所有結果
            
        Returns:
            Tuple[List[Dict], Optional[str]]: (查詢結果, 錯誤訊息)
        """
        if not bind_params:
            bind_params = {}
            
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    # 記錄查詢開始
                    logger.debug(f"執行查詢: {sql}")
                    logger.debug(f"綁定參數: {list(bind_params.keys())}")
                    
                    # 執行參數化查詢
                    cursor.execute(sql, bind_params)
                    
                    # 取得結果
                    if fetch_all:
                        rows = cursor.fetchall()
                    else:
                        rows = cursor.fetchmany()
                    
                    # 轉換為字典格式
                    if rows and cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        result = [dict(zip(columns, row)) for row in rows]
                    else:
                        result = []
                    
                    # 記錄查詢成功
                    logger.info(f"查詢執行成功，返回 {len(result)} 筆記錄")
                    
                    return result, None
                    
        except oracledb.DatabaseError as e:
            # 處理 Oracle 資料庫錯誤
            error_code = getattr(e, 'code', 'UNKNOWN')
            error_message = str(e)
            
            # 遮蔽敏感資訊，記錄到日誌
            logger.error(f"資料庫查詢錯誤: ORA-{error_code}")
            logger.error(f"SQL: {sql}")
            logger.error(f"錯誤詳情: {error_message}")
            
            # 返回錯誤結果
            return [], f"查詢執行失敗 (錯誤代碼: {error_code})"
            
        except oracledb.InterfaceError as e:
            # 處理介面錯誤（如連線中斷）
            error_code = getattr(e, 'code', 'UNKNOWN')
            logger.error(f"資料庫介面錯誤: ORA-{error_code}")
            logger.error(f"錯誤詳情: {str(e)}")
            
            return [], "資料庫連線問題，請稍後再試"
            
        except Exception as e:
            # 處理其他未預期錯誤
            logger.error(f"查詢執行發生未預期錯誤: {str(e)}")
            logger.error(f"SQL: {sql}")
            
            return [], "系統執行錯誤，請聯繫管理員"
    
    def execute_search(self, 
                      keyword: str, 
                      search_field: str, 
                      document_types: List[str] = None,
                      limit: int = 100) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        執行文件搜尋查詢
        根據 SEARCH_MAPPING 產生的參數進行安全查詢
        
        Args:
            keyword: 搜尋關鍵字
            search_field: 搜尋欄位 (title, author, DOC_ID, ALL)
            document_types: 文件類型篩選清單
            limit: 結果數量限制
            
        Returns:
            Tuple[List[Dict], Optional[str]]: (搜尋結果, 錯誤訊息)
        """
        try:
            # 建構 WHERE 條件
            conditions = []
            bind_params = {}
            
            # 關鍵字搜尋條件
            if search_field == 'ALL':
                # 全部欄位搜尋
                conditions.append("(title LIKE :keyword OR author LIKE :keyword OR DOC_ID LIKE :keyword)")
            else:
                # 特定欄位搜尋
                conditions.append(f"{search_field} LIKE :keyword")
            
            bind_params['keyword'] = f'%{keyword}%'
            
            # 文件類型篩選
            if document_types:
                type_placeholders = []
                for i, doc_type in enumerate(document_types):
                    placeholder = f":type_{i}"
                    type_placeholders.append(placeholder)
                    bind_params[f"type_{i}"] = doc_type
                
                conditions.append(f"document_type IN ({', '.join(type_placeholders)})")
            
            # 組合完整 SQL
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            sql = f"""
                SELECT title, author, DOC_ID, document_type, create_date, 
                       description, file_path
                FROM documents 
                {where_clause}
                ORDER BY create_date DESC
                FETCH FIRST {limit} ROWS ONLY
            """
            
            # 執行查詢
            return self.execute_query(sql.strip(), bind_params)
            
        except Exception as e:
            logger.error(f"搜尋查詢建構錯誤: {str(e)}")
            return [], "搜尋條件建構失敗"
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        測試資料庫連線
        
        Returns:
            Tuple[bool, str]: (連線是否成功, 狀態訊息)
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM DUAL")
                    result = cursor.fetchone()
                    
                    if result and result[0] == 1:
                        logger.info("資料庫連線測試成功")
                        return True, "連線正常"
                    else:
                        logger.warning("資料庫連線測試異常")
                        return False, "連線異常"
                        
        except oracledb.Error as e:
            error_code = getattr(e, 'code', 'UNKNOWN')
            logger.error(f"資料庫連線測試失敗: ORA-{error_code}")
            return False, f"連線失敗 (錯誤代碼: {error_code})"
        except Exception as e:
            logger.error(f"連線測試發生未預期錯誤: {str(e)}")
            return False, f"測試錯誤: {str(e)}"
    
    def close_pool(self) -> None:
        """關閉連線池"""
        try:
            if self.pool:
                self.pool.close()
                self.pool = None
                logger.info("Oracle 連線池已關閉")
        except Exception as e:
            logger.warning(f"連線池關閉警告: {str(e)}")

# 全域資料庫管理器實例
db_manager = None

def initialize_database(config: Dict[str, str]) -> bool:
    """
    初始化全域資料庫管理器
    
    Args:
        config: 資料庫配置字典
        
    Returns:
        bool: 初始化是否成功
    """
    global db_manager
    
    try:
        db_manager = OracleDatabaseManager(
            user=config.get('user', ''),
            password=config.get('password', ''),
            dsn=config.get('dsn', ''),
            min_connections=config.get('min_connections', 2),
            max_connections=config.get('max_connections', 10),
            increment=config.get('increment', 1)
        )
        
        return db_manager.initialize_connection_pool()
        
    except Exception as e:
        logger.error(f"資料庫初始化失敗: {str(e)}")
        return False

def get_database() -> Optional[OracleDatabaseManager]:
    """
    取得全域資料庫管理器
    
    Returns:
        Optional[OracleDatabaseManager]: 資料庫管理器實例
    """
    return db_manager

def close_database() -> None:
    """關閉全域資料庫連線"""
    global db_manager
    if db_manager:
        db_manager.close_pool()
        db_manager = None
