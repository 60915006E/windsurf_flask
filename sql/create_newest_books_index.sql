-- 新進書目查詢索引建立腳本
-- 用於提升最新書目查詢效能

-- 請根據 config.py 中的實際配置調整表名和欄位名

-- ===========================================
-- 基本索引建立
-- ===========================================

-- 日期欄位索引（最重要）
-- 用於 ORDER BY 日期 DESC 查詢
CREATE INDEX IDX_NEWEST_BOOKS_DATE ON DOCUMENTS(CREATED_DATE DESC);

-- 複合索引（推薦）
-- 同時支援日期排序和 ID 查詢
CREATE INDEX IDX_NEWEST_BOOKS_DATE_ID ON DOCUMENTS(CREATED_DATE DESC, DOC_ID);

-- 標題欄位索引（可選）
-- 如果有標題搜尋需求
CREATE INDEX IDX_NEWEST_BOOKS_TITLE ON DOCUMENTS(TITLE);

-- ===========================================
-- 效能檢查查詢
-- ===========================================

-- 檢查索引是否建立成功
SELECT 
    INDEX_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    COLUMN_POSITION
FROM USER_IND_COLUMNS 
WHERE TABLE_NAME = 'DOCUMENTS'
    AND INDEX_NAME LIKE 'IDX_NEWEST_BOOKS%'
ORDER BY INDEX_NAME, COLUMN_POSITION;

-- 檢查執行計畫（測試用）
EXPLAIN PLAN FOR
SELECT 
    DOC_ID,
    TITLE,
    TO_CHAR(CREATED_DATE, 'YYYY-MM-DD HH24:MI:SS') as CREATED_DATE
FROM DOCUMENTS
WHERE CREATED_DATE IS NOT NULL
ORDER BY CREATED_DATE DESC
FETCH NEXT 10 ROWS ONLY;

-- 查看執行計畫
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);

-- ===========================================
-- 統計資訊更新
-- ===========================================

-- 更新表格統計資訊（重要！）
-- 讓 Oracle 優化器了解資料分佈
BEGIN
    DBMS_STATS.GATHER_TABLE_STATS(
        OWNNAME => USER,
        TABNAME => 'DOCUMENTS',
        CASCADE => TRUE,
        ESTIMATE_PERCENT => DBMS_STATS.AUTO_SAMPLE_SIZE
    );
END;
/

-- ===========================================
-- 效能測試查詢
-- ===========================================

-- 測試查詢效能
SET TIMING ON;
SET AUTOTRACE ON EXPLAIN;

SELECT 
    DOC_ID,
    TITLE,
    TO_CHAR(CREATED_DATE, 'YYYY-MM-DD HH24:MI:SS') as CREATED_DATE
FROM DOCUMENTS
WHERE CREATED_DATE IS NOT NULL
ORDER BY CREATED_DATE DESC
FETCH NEXT 10 ROWS ONLY;

SET AUTOTRACE OFF;
SET TIMING OFF;

-- ===========================================
-- 索引維護建議
-- ===========================================

-- 查看索引使用狀況
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    USED,
    START_MONITORING,
    END_MONITORING
FROM V$OBJECT_USAGE
WHERE TABLE_NAME = 'DOCUMENTS';

-- 如果需要重建索引
-- ALTER INDEX IDX_NEWEST_BOOKS_DATE REBUILD;

-- 如果需要刪除索引
-- DROP INDEX IDX_NEWEST_BOOKS_DATE;

-- ===========================================
-- 完成訊息
-- ===========================================

BEGIN
    DBMS_OUTPUT.PUT_LINE('🎉 新進書目索引建立完成！');
    DBMS_OUTPUT.PUT_LINE('📊 已建立以下索引：');
    DBMS_OUTPUT.PUT_LINE('  - IDX_NEWEST_BOOKS_DATE (日期降序)');
    DBMS_OUTPUT.PUT_LINE('  - IDX_NEWEST_BOOKS_DATE_ID (日期+ID複合)');
    DBMS_OUTPUT.PUT_LINE('  - IDX_NEWEST_BOOKS_TITLE (標題)');
    DBMS_OUTPUT.PUT_LINE('⚡ 查詢效能已優化');
    DBMS_OUTPUT.PUT_LINE('🔧 請根據實際資料量調整索引策略');
END;
/

COMMIT;
