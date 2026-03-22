-- 升級 PORTAL_LINKS 表，支援動態 HTML 內容管理
-- 新增 IS_VISIBLE 和 CONTENT_HTML 欄位

-- 檢查欄位是否存在，如果不存在則新增
DECLARE
    column_exists NUMBER;
BEGIN
    -- 檢查 IS_VISIBLE 欄位是否存在
    SELECT COUNT(*) INTO column_exists 
    FROM USER_TAB_COLUMNS 
    WHERE TABLE_NAME = 'PORTAL_LINKS' 
    AND COLUMN_NAME = 'IS_VISIBLE';
    
    IF column_exists = 0 THEN
        -- 新增 IS_VISIBLE 欄位
        EXECUTE IMMEDIATE 'ALTER TABLE PORTAL_LINKS ADD IS_VISIBLE CHAR(1) DEFAULT ''Y'' NOT NULL';
        DBMS_OUTPUT.PUT_LINE('✅ IS_VISIBLE 欄位新增成功');
    ELSE
        DBMS_OUTPUT.PUT_LINE('ℹ️ IS_VISIBLE 欄位已存在');
    END IF;
    
    -- 檢查 CONTENT_HTML 欄位是否存在
    SELECT COUNT(*) INTO column_exists 
    FROM USER_TAB_COLUMNS 
    WHERE TABLE_NAME = 'PORTAL_LINKS' 
    AND COLUMN_NAME = 'CONTENT_HTML';
    
    IF column_exists = 0 THEN
        -- 新增 CONTENT_HTML 欄位
        EXECUTE IMMEDIATE 'ALTER TABLE PORTAL_LINKS ADD CONTENT_HTML CLOB';
        DBMS_OUTPUT.PUT_LINE('✅ CONTENT_HTML 欄位新增成功');
    ELSE
        DBMS_OUTPUT.PUT_LINE('ℹ️ CONTENT_HTML 欄位已存在');
    END IF;
END;
/

-- 更新現有記錄，設定預設值
UPDATE PORTAL_LINKS 
SET IS_VISIBLE = 'Y' 
WHERE IS_VISIBLE IS NULL;

-- 新增索引以提升查詢效能
CREATE INDEX IDX_PORTAL_LINKS_VISIBLE ON PORTAL_LINKS(IS_VISIBLE);

-- 插入範例資料（如果表為空）
DECLARE
    record_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO record_count FROM PORTAL_LINKS;
    
    IF record_count = 0 THEN
        -- 插入 6 個預設按鈕
        INSERT INTO PORTAL_LINKS (ID, TITLE, ICON, URL, DESCRIPTION, IS_VISIBLE, CONTENT_HTML) VALUES (1, '系統查詢', '🔍', '#', '進行各種資料庫查詢操作', 'Y', '<h2>系統查詢</h2><p>歡迎使用系統查詢功能，您可以進行各種資料庫查詢操作。</p>');
        INSERT INTO PORTAL_LINKS (ID, TITLE, ICON, URL, DESCRIPTION, IS_VISIBLE, CONTENT_HTML) VALUES (2, '報表中心', '📊', '#', '查看各種統計報表和圖表', 'Y', '<h2>報表中心</h2><p>在這裡您可以查看各種統計報表和圖表。</p>');
        INSERT INTO PORTAL_LINKS (ID, TITLE, ICON, URL, DESCRIPTION, IS_VISIBLE, CONTENT_HTML) VALUES (3, '文件管理', '📁', '#', '管理系統文件和附件', 'Y', '<h2>文件管理</h2><p>管理系統文件和附件的地方。</p>');
        INSERT INTO PORTAL_LINKS (ID, TITLE, ICON, URL, DESCRIPTION, IS_VISIBLE, CONTENT_HTML) VALUES (4, '使用者設定', '⚙️', '#', '個人設定和偏好設定', 'Y', '<h2>使用者設定</h2><p>調整個人設定和偏好設定。</p>');
        INSERT INTO PORTAL_LINKS (ID, TITLE, ICON, URL, DESCRIPTION, IS_VISIBLE, CONTENT_HTML) VALUES (5, '系統管理', '🛠️', '#', '系統管理和維護功能', 'Y', '<h2>系統管理</h2><p>系統管理和維護功能。</p>');
        INSERT INTO PORTAL_LINKS (ID, TITLE, ICON, URL, DESCRIPTION, IS_VISIBLE, CONTENT_HTML) VALUES (6, '幫助中心', '❓', '#', '使用說明和技術支援', 'Y', '<h2>幫助中心</h2><p>查看使用說明和獲得技術支援。</p>');
        
        DBMS_OUTPUT.PUT_LINE('✅ 插入 6 個預設按鈕成功');
    ELSE
        DBMS_OUTPUT.PUT_LINE('ℹ️ PORTAL_LINKS 表已有資料，跳過插入');
    END IF;
END;
/

-- 提交變更
COMMIT;

-- 顯示升級結果
SELECT 
    ID, 
    TITLE, 
    ICON, 
    URL, 
    DESCRIPTION,
    IS_VISIBLE,
    DBMS_LOB.SUBSTR(CONTENT_HTML, 50, 1) as CONTENT_PREVIEW
FROM PORTAL_LINKS 
ORDER BY ID;

DBMS_OUTPUT.PUT_LINE('🎉 PORTAL_LINKS 表升級完成！');
