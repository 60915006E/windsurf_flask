# 實體資料庫連線部署指南

## 📋 概述

本文檔說明如何將 Flask 查詢系統從 Mock 模式切換到實體 Oracle 19c 資料庫連線。

## 🔧 環境準備

### 1. Python 環境
```bash
# 確保 Python 3.13.7
python --version

# 安裝 python-oracledb (Thin Mode)
pip install python-oracledb

# 驗證安裝
python -c "import oracledb; print('python-oracledb 安裝成功')"
```

### 2. Oracle 19c 資料庫
- **主機**: 10.52.141.25
- **端口**: 1610
- **服務名**: ORATESTWORLD
- **使用者**: admin
- **密碼**: adminpassword

## 🏗️ 系統架構

### 雙資料庫架構
```
┌─────────────────┐    ┌─────────────────┐
│   SYSTEM_DB    │    │    DATA_DB     │
│   (讀寫)       │    │    (唯讀)       │
│                │    │                │
│ 使用者認證      │    │ 書目查詢       │
│ 系統日誌      │    │ 報表生成       │
│ 管理員驗證    │    │ 資料分析       │
└─────────────────┘    └─────────────────┘
        │                       │
        └───────────┬───────────┘
                    │
            ┌─────────────┐
            │ Flask App  │
            │ 連線池管理  │
            │ 錯誤處理   │
            └─────────────┘
```

## 📋 配置檔案

### config.py 關鍵配置
```python
# ===========================================
# Oracle 19c 雙資料庫連線參數
# ===========================================

SYSTEM_DB_USER = "admin"
SYSTEM_DB_PASSWORD = "adminpassword"
SYSTEM_DB_HOST = "10.52.141.25"
SYSTEM_DB_PORT = "1610"
SYSTEM_DB_SERVICE_NAME = "ORATESTWORLD"

DATA_DB_USER = "admin"
DATA_DB_PASSWORD = "adminpassword"
DATA_DB_HOST = "10.52.141.25"
DATA_DB_PORT = "1610"
DATA_DB_SERVICE_NAME = "ORATESTWORLD"

# ===========================================
# Schema 配置
# ===========================================

DATA_DB_SCHEMA = "sarchowner"
NEWEST_BOOKS_TABLE = "DOCUMENTS"
NEWEST_BOOKS_ID_FIELD = "DOC_ID"
NEWEST_BOOKS_TITLE_FIELD = "TITLE"
NEWEST_BOOKS_DATE_FIELD = "CREATED_DATE"
```

## 🏗️ 連線池管理

### 連線池配置
```python
# SYSTEM_DB 連線池
min_sessions = 2
max_sessions = 10
increment = 2

# DATA_DB 連線池
min_sessions = 3
max_sessions = 20
increment = 3
```

### 連線池特性
- **高併發支援**: 最多 30 個並發連線
- **自動擴展**: 根據負載動態調整
- **超時控制**: 30 秒連線超時
- **錯誤恢復**: 自動重連和錯誤記錄

## 📋 Schema 設計

### 表名格式
所有 SQL 查詢使用完整 Schema 名稱：
```sql
-- 格式: SCHEMA.TABLE_NAME
SELECT * FROM sarchowner.DOCUMENTS
```

### 新進書目查詢
```sql
SELECT 
    DOC_ID as DOC_ID,
    TITLE as TITLE,
    TO_CHAR(CREATED_DATE, 'YYYY-MM-DD HH24:MI:SS') as CREATED_DATE
FROM sarchowner.DOCUMENTS
WHERE CREATED_DATE IS NOT NULL
ORDER BY CREATED_DATE DESC
FETCH NEXT :limit ROWS ONLY
```

## 🛡️ 錯誤處理

### 錯誤處理策略
1. **資料庫錯誤**: 詳細解析 Oracle 錯誤代碼
2. **連線失敗**: 拋出 RuntimeError 由 Flask 捕捉
3. **友善提示**: 顯示用戶友好的錯誤頁面
4. **詳細日誌**: 記錄完整錯誤資訊

### 常見錯誤處理
```python
# 表不存在
if "ORA-00942" in str(error_code):
    logger.error(f"表 {full_table_name} 不存在")
    # 提供具體的配置建議

# 連線失敗
if "ORA-12541" in error_str:
    return "12541", "TNS:無法連線到監聽器"

# 認證失敗
if "ORA-01017" in error_str:
    return "01017", "無效的使用者名稱/密碼"
```

## 🚀 部署步驟

### 1. 環境檢查
```bash
# 執行配置測試
python test_db_config.py

# 預期輸出
# ✅ 配置檔案: 通過
# ✅ 資料庫管理模組: 通過
# ✅ 路由模組: 通過
# ✅ Schema SQL 建構: 通過
```

### 2. 連線測試
```python
from db_manager import test_connection

# 測試連線
if test_connection():
    print("✅ 資料庫連線成功")
else:
    print("❌ 資料庫連線失敗")
```

### 3. 應用程式啟動
```bash
# 啟動 Flask 應用程式
source venv/bin/activate
python app.py
```

### 4. 功能驗證
- [ ] 首頁正常載入
- [ ] 熱門書目顯示
- [ ] 新進書目顯示
- [ ] 詳情頁面正常
- [ ] SQL 查詢功能
- [ ] 錯誤處理正常

## 📊 效能優化

### 索引建議
```sql
-- 新進書目查詢索引
CREATE INDEX IDX_NEWEST_BOOKS_DATE ON sarchowner.DOCUMENTS(CREATED_DATE DESC);

-- 複合索引
CREATE INDEX IDX_NEWEST_BOOKS_DATE_ID ON sarchowner.DOCUMENTS(CREATED_DATE DESC, DOC_ID);

-- 熱門書目查詢索引
CREATE INDEX IDX_POPULAR_BOOKS_VIEW ON sarchowner.DOCUMENTS(VIEW_COUNT DESC, LAST_VIEW_TIME DESC);
```

### 連線池監控
```python
from db_manager import get_connection_pool_status

# 檢查連線池狀態
status = get_connection_pool_status()
print(f"SYSTEM_DB: {status['system']}")
print(f"DATA_DB: {status['data']}")
```

## 🔧 故障排除

### 常見問題

#### 1. python-oracledb 安裝失敗
```bash
# 解決方案
pip install --upgrade pip
pip install python-oracledb
```

#### 2. 連線超時
```python
# 檢查網路連線
ping 10.52.141.25
telnet 10.52.141.25 1610
```

#### 3. Schema 不存在
```sql
-- 檢查 Schema
SELECT username FROM all_users WHERE username = 'SARCHOWNER';

-- 檢查表
SELECT table_name FROM all_tables WHERE owner = 'SARCHOWNER';
```

#### 4. 權限問題
```sql
-- 檢查使用者權限
SELECT * FROM user_tab_privs WHERE table_name = 'DOCUMENTS';
```

### 日誌檢查
```bash
# 檢查應用程式日誌
tail -f logs/app.log

# 檢查錯誤日誌
grep ERROR logs/app.log
```

## 📋 維護清單

### 日常維護
- [ ] 檢查連線池狀態
- [ ] 監控查詢效能
- [ ] 檢查錯誤日誌
- [ ] 備份重要資料

### 定期維護
- [ ] 更新統計資訊
- [ ] 重建索引
- [ ] 清理舊日誌
- [ ] 效能調優

## 🎯 最佳實踐

### 1. 連線管理
- 使用連線池避免頻繁連線
- 設定適當的超時時間
- 監控連線池使用率

### 2. 錯誤處理
- 記錄詳細錯誤資訊
- 提供用戶友善錯誤提示
- 實作自動重連機制

### 3. 效能優化
- 建立適當的索引
- 使用綁定變數防止 SQL 注入
- 實作查詢結果快取

### 4. 安全性
- 使用參數化查詢
- 限制資料庫權限
- 定期更新密碼

## 📞 技術支援

如遇到問題，請提供以下資訊：
1. 錯誤訊息完整內容
2. 相關日誌檔案
3. 配置檔案內容
4. 資料庫版本資訊
5. 網路連線狀態

---

**版本**: 2.0.0  
**更新日期**: 2026-03-17  
**適用環境**: Windows Server 2022 + Oracle 19c
