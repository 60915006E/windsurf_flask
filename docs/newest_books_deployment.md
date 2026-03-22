# 新進書目功能部署說明

## 📋 功能概述

新進書目功能為 Oracle 19c 查詢系統新增了最新書目展示區塊，與熱門書目並排顯示在首頁左側。

## 🔧 部署步驟

### 1. 資料庫配置

#### 1.1 檢查資料表結構
確認 DATA_DB 中的書目資料表，找出最適合的日期欄位：

```sql
-- 查看資料表結構
DESCRIBE YOUR_BOOK_TABLE;

-- 查看日期欄位
SELECT COLUMN_NAME, DATA_TYPE, NULLABLE 
FROM USER_TAB_COLUMNS 
WHERE TABLE_NAME = 'YOUR_BOOK_TABLE' 
    AND DATA_TYPE IN ('DATE', 'TIMESTAMP');
```

#### 1.2 更新 config.py
根據實際資料表結構修改配置：

```python
# 在 config.py 中調整以下參數
NEWEST_BOOKS_TABLE = "YOUR_ACTUAL_TABLE"      # 實際表名
NEWEST_BOOKS_ID_FIELD = "YOUR_ID_FIELD"      # 實際 ID 欄位
NEWEST_BOOKS_TITLE_FIELD = "YOUR_TITLE_FIELD"  # 實際標題欄位
NEWEST_BOOKS_DATE_FIELD = "YOUR_DATE_FIELD"  # 實際日期欄位
```

#### 1.3 建立索引
執行索引建立腳本：

```bash
# 在 Oracle 伺服器上執行
sqlplus data_user/password@//host:port/service @sql/create_newest_books_index.sql
```

### 2. 應用程式部署

#### 2.1 確認程式碼
確認以下檔案已更新：
- `db_manager.py` - 新增 `get_newest_books()` 函式
- `app/search/routes.py` - 首頁路由整合
- `app/templates/search/index.html` - 前端 UI
- `config.py` - 配置參數

#### 2.2 重啟應用程式
```bash
# 重啟 Flask 應用程式
# 或使用 PyInstaller 打包的 .exe 檔案
```

## 🎨 UI 佈局

### 首頁左側佈局
```
┌─────────────────────────┐
│   SQL 查詢區塊      │
├─────────────────────────┤
│   🔥 熱門推薦       │
│   1. 書目一         │
│   2. 書目二         │
│   ...               │
├─────────────────────────┤
│   🆕 最新進展       │
│   1. 書目A         │
│   2. 書目B         │
│   ...               │
└─────────────────────────┘
```

### 視覺設計
- **熱門推薦**：金色邊框 (#FFD700)
- **最新進展**：橙色邊框 (#FFA500)
- **排名徽章**：圓形數字標示
- **懸停效果**：背景色變化和位移

## 📊 效能優化

### 索引策略
1. **主要索引**：日期欄位降序
2. **複合索引**：日期 + ID
3. **可選索引**：標題欄位

### 查詢優化
```sql
-- 使用 FETCH NEXT 語法（Oracle 12c+）
SELECT * FROM TABLE 
ORDER BY DATE_FIELD DESC 
FETCH NEXT 10 ROWS ONLY;

-- 避免 ROWNUM 偽劣化
-- 不推薦：WHERE ROWNUM <= 10
```

## 🛡️ 錯誤處理

### Mock Data 機制
當資料庫連線失敗時，系統會：
1. 記錄錯誤到日誌
2. 返回 10 筆測試資料
3. 確保前端正常顯示
4. 顯示友善提示訊息

### 常見問題解決

#### 問題 1：表不存在
**錯誤**：`ORA-00942: table or view does not exist`
**解決**：檢查 config.py 中的 `NEWEST_BOOKS_TABLE` 設定

#### 問題 2：欄位不存在
**錯誤**：`ORA-00904: invalid identifier`
**解決**：檢查 config.py 中的欄位名稱設定

#### 問題 3：查詢緩慢
**原因**：缺少日期欄位索引
**解決**：執行索引建立腳本

## 🔍 測試驗證

### 功能測試
1. **首頁載入**：確認兩個區塊正常顯示
2. **點擊導航**：點擊書目跳轉詳情頁
3. **資料正確性**：確認日期排序正確
4. **響應式設計**：測試不同螢幕尺寸

### 效能測試
```sql
-- 測試查詢時間
SET TIMING ON;
SELECT * FROM (
    SELECT * FROM DOCUMENTS 
    WHERE CREATED_DATE IS NOT NULL 
    ORDER BY CREATED_DATE DESC
) WHERE ROWNUM <= 10;
```

## 📝 維護建議

### 定期維護
1. **統計更新**：每週更新表格統計
2. **索引重建**：每月檢查索引碎片
3. **效能監控**：監控查詢執行時間

### 監控指標
- 查詢響應時間 < 1 秒
- 首頁載入時間 < 2 秒
- 錯誤率 < 0.1%

## 🎯 預期效果

### 使用者體驗提升
- **發現性**：更容易發現新書目
- **導航性**：清晰的視覺層次
- **響應性**：快速的互動回饋

### 系統效能
- **查詢優化**：索引加速查詢
- **前端穩定**：Mock Data 確保可用性
- **配置彈性**：易於調整和維護

## 📞 技術支援

如遇到問題，請檢查：
1. 應用程式日誌 (`logs/app.log`)
2. Oracle 錯誤日誌
3. config.py 配置參數
4. 資料庫索引狀態

---

**部署完成後，新進書目功能將為使用者提供更好的書目發現體驗！** 🎉
