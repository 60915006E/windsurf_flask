"""
模擬 Oracle 資料庫模組
用於測試環境，模擬 python-oracledb 的基本功能
"""

class MockError(Exception):
    """模擬 Oracle 錯誤"""
    def __init__(self, message, code="MOCK_ERROR"):
        self.code = code
        self.message = message
        super().__init__(message)

class DatabaseError(MockError):
    """模擬資料庫錯誤"""
    pass

class InterfaceError(MockError):
    """模擬介面錯誤"""
    pass

class MockConnection:
    """模擬資料庫連線"""
    def __init__(self):
        self.is_connected = True
    
    def cursor(self):
        return MockCursor()
    
    def close(self):
        self.is_connected = False

class MockCursor:
    """模擬資料庫游標"""
    def __init__(self):
        self.description = None
        self._results = []
        self._executed = False
    
    def execute(self, sql, params=None):
        """模擬 SQL 執行"""
        self._executed = True
        
        # 模擬查詢結果
        if "SELECT" in sql.upper():
            self.description = [
                ('title', str),
                ('author', str), 
                ('DOC_ID', str),
                ('document_type', str),
                ('create_date', str),
                ('description', str),
                ('file_path', str)
            ]
            
            # 模擬一些測試資料
            self._results = [
                {
                    'title': '測試文件 - Oracle 資料庫',
                    'author': '測試工程師',
                    'DOC_ID': 'TEST-001',
                    'document_type': '技術報告',
                    'create_date': '2024-01-01 10:00:00',
                    'description': '這是一份測試文件',
                    'file_path': '/files/test.pdf'
                }
            ]
    
    def fetchall(self):
        """取得所有結果"""
        return [tuple(row.values()) for row in self._results]
    
    def fetchmany(self, size=None):
        """取得部分結果"""
        return self.fetchall()[:size] if size else self.fetchall()
    
    def fetchone(self):
        """取得單筆結果"""
        results = self.fetchall()
        return results[0] if results else None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class MockPool:
    """模擬連線池"""
    def __init__(self, **kwargs):
        self.config = kwargs
        self._connections = []
        self.min_size = kwargs.get('min', 2)
        self.max_size = kwargs.get('max', 10)
    
    def acquire(self):
        """取得連線"""
        if len(self._connections) < self.max_size:
            conn = MockConnection()
            self._connections.append(conn)
            return conn
        else:
            raise InterfaceError("連線池已滿", "POOL_FULL")
    
    def release(self, connection):
        """釋放連線"""
        if connection in self._connections:
            self._connections.remove(connection)
    
    def close(self):
        """關閉連線池"""
        self._connections.clear()

# 模擬常數
SPOOL_ATTRVAL_NOWAIT = 1

def init_oracle_client():
    """模擬初始化 Oracle 客戶端"""
    pass

def create_pool(**kwargs):
    """模擬建立連線池"""
    return MockPool(**kwargs)

# 設定模擬模組
class MockOracleModule:
    Error = MockError
    DatabaseError = DatabaseError
    InterfaceError = InterfaceError
    Connection = MockConnection  # 別名
    Cursor = MockCursor
    SPOOL_ATTRVAL_NOWAIT = SPOOL_ATTRVAL_NOWAIT
    init_oracle_client = init_oracle_client
    create_pool = create_pool

# 如果真實的 oracledb 不存在，使用模擬版本
try:
    import oracledb
except ImportError:
    import sys
    
    # 直接設定模擬類別到 sys.modules
    sys.modules['oracledb'] = MockOracleModule()
    
    # 重新導入以取得正確的屬性
    import oracledb
