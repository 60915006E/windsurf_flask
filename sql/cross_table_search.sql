-- ===========================================
-- 跨資料表聯合搜尋 SQL 架構
-- ===========================================
-- 
-- 功能：四種資料類型的聯合檢索系統
-- 1. 技術報告 (TBIRLIB_REPORT_MAIN) - 背景色：淡藍色
-- 2. 史政 (TRIRLIB_HISTORY_MAIN) - 背景色：淡綠色  
-- 3. 史政照片 (TRIRLIB_PHOTO_MAIN) - 背景色：淡黃色
-- 4. 逸光報 (TRIRLIB_PAPER_MAIN) - 背景色：淡灰色
--
-- 第一守則：絕對過濾與權限
-- 所有查詢必須強制包含條件：OVC_PUBLIC_TYPE_CDE = 'Y'

-- ===========================================
-- 1. 技術報告查詢 (TBIRLIB_REPORT_MAIN)
-- ===========================================
WITH REPORT_DATA AS (
    SELECT 
        -- 基本資訊
        '1' AS DATA_TYPE,
        '技術報告' AS DATA_TYPE_NAME,
        '#E6F3FF' AS BACKGROUND_COLOR,
        OVC_RP_NO AS UNIQUE_ID,
        
        -- 查詢與顯示欄位
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
        
        -- 副表 LISTAGG 處理
        (
            SELECT LISTAGG(OVC_RP_LIB_TITLE, ',') WITHIN GROUP (ORDER BY OVC_RP_LIB_TITLE)
            FROM TBIRLIB_RP_LIB_TITLE 
            WHERE OVC_RP_NO = R.OVC_RP_NO
        ) AS RP_LIB_TITLE_LIST,
        
        (
            SELECT LISTAGG(OVC_RP_OTHER_TITLE, ',') WITHIN GROUP (ORDER BY OVC_RP_OTHER_TITLE)
            FROM TBIRLIB_RP_OTHER_TITLE 
            WHERE OVC_RP_NO = R.OVC_RP_NO
        ) AS RP_OTHER_TITLE_LIST,
        
        (
            SELECT LISTAGG(OVN_RP_OTHER_NAME, ',') WITHIN GROUP (ORDER BY OVN_RP_OTHER_NAME)
            FROM TBIRLIB_RP_OTHER_NAME 
            WHERE OVC_RP_NO = R.OVC_RP_NO
        ) AS RP_OTHER_NAME_LIST,
        
        (
            SELECT LISTAGG(OVN_RP_KEYWORD, ',') WITHIN GROUP (ORDER BY OVN_RP_KEYWORD)
            FROM TBIRLIB_RP_KEYWORD 
            WHERE OVC_RP_NO = R.OVC_RP_NO
        ) AS RP_KEYWORD_LIST,
        
        (
            SELECT LISTAGG(OVN_RP_PLAN_NAME || '(' || OVC_RP_PLAN_CDE || ')', ',') WITHIN GROUP (ORDER BY OVN_RP_PLAN_NAME)
            FROM TBIRLIB_RP_PLAN 
            WHERE OVC_RP_NO = R.OVC_RP_NO
        ) AS RP_PLAN_LIST
        
    FROM TBIRLIB_REPORT_MAIN R
    WHERE OVC_PUBLIC_TYPE_CDE = 'Y'
),

-- ===========================================
-- 2. 史政查詢 (TRIRLIB_HISTORY_MAIN)
-- ===========================================
HISTORY_DATA AS (
    SELECT 
        -- 基本資訊
        '2' AS DATA_TYPE,
        '史政' AS DATA_TYPE_NAME,
        '#E6FFE6' AS BACKGROUND_COLOR,
        OVC_HS_NO AS UNIQUE_ID,
        
        -- 查詢與顯示欄位
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
        ODT_HS_EVENT_DATE AS EVENT_DATE,
        
        -- 史政沒有副表，設為 NULL
        NULL AS RP_LIB_TITLE_LIST,
        NULL AS RP_OTHER_TITLE_LIST,
        NULL AS RP_OTHER_NAME_LIST,
        NULL AS RP_KEYWORD_LIST,
        NULL AS RP_PLAN_LIST
        
    FROM TRIRLIB_HISTORY_MAIN H
    WHERE OVC_PUBLIC_TYPE_CDE = 'Y'
),

-- ===========================================
-- 3. 史政照片查詢 (TRIRLIB_PHOTO_MAIN)
-- ===========================================
PHOTO_DATA AS (
    SELECT 
        -- 基本資訊
        '4' AS DATA_TYPE,
        '史政照片' AS DATA_TYPE_NAME,
        '#FFFFE6' AS BACKGROUND_COLOR,
        OVC_TO_NO AS UNIQUE_ID,
        
        -- 查詢與顯示欄位
        OVC_TO_NAME AS TO_NAME,
        ODT_TO_DATE AS TO_DATE,
        OVN_TO_PLACE AS TO_PLACE,
        OVN_TO_PEOPLE AS TO_PEOPLE,
        OVN_TO_SUMMARY AS TO_SUMMARY,
        
        -- 合併顯示欄位
        (OVC_TO_DEPT1_NAME || ' ' || OVC_TO_DEPT2_NAME) AS TO_DEPT_NAME,
        (OVC_TO_APPLY_DEPT1_NAME || ' ' || OVC_TO_APPLY_DEPT2_NAME) AS TO_APPLY_DEPT_NAME,
        
        -- 史政照片沒有其他欄位，設為 NULL
        NULL AS HS_CAT_CDE,
        NULL AS HS_CAT_NAME,
        NULL AS HS_NAME,
        NULL AS PUBLISH_YEAR,
        NULL AS HS_SUMMARY,
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
        
        -- 史政照片沒有副表，設為 NULL
        NULL AS RP_LIB_TITLE_LIST,
        NULL AS RP_OTHER_TITLE_LIST,
        NULL AS RP_OTHER_NAME_LIST,
        NULL AS RP_KEYWORD_LIST,
        NULL AS RP_PLAN_LIST
        
    FROM TRIRLIB_PHOTO_MAIN P
    WHERE OVC_PUBLIC_TYPE_CDE = 'Y'
),

-- ===========================================
-- 4. 逸光報查詢 (TRIRLIB_PAPER_MAIN)
-- ===========================================
PAPER_DATA AS (
    SELECT 
        -- 基本資訊
        '3' AS DATA_TYPE,
        '逸光報' AS DATA_TYPE_NAME,
        '#F0F0F0' AS BACKGROUND_COLOR,
        OVC_PAPER_ID AS UNIQUE_ID,
        
        -- 查詢與顯示欄位
        OVN_PAPER_NAME AS PAPER_NAME,
        OVN_PAPER_AUTHOR AS PAPER_AUTHOR,
        
        -- 逸光報沒有其他欄位，設為 NULL
        NULL AS TO_NAME,
        NULL AS TO_DATE,
        NULL AS TO_PLACE,
        NULL AS TO_PEOPLE,
        NULL AS TO_SUMMARY,
        NULL AS TO_DEPT_NAME,
        NULL AS TO_APPLY_DEPT_NAME,
        NULL AS HS_CAT_CDE,
        NULL AS HS_CAT_NAME,
        NULL AS HS_NAME,
        NULL AS PUBLISH_YEAR,
        NULL AS HS_SUMMARY,
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
        
        -- 逸光報沒有副表，設為 NULL
        NULL AS RP_LIB_TITLE_LIST,
        NULL AS RP_OTHER_TITLE_LIST,
        NULL AS RP_OTHER_NAME_LIST,
        NULL AS RP_KEYWORD_LIST,
        NULL AS RP_PLAN_LIST
        
    FROM TRIRLIB_PAPER_MAIN P
    WHERE OVC_PUBLIC_TYPE_CDE = 'Y'
)

-- ===========================================
-- 聯合查詢結果
-- ===========================================
SELECT * FROM (
    SELECT * FROM REPORT_DATA
    UNION ALL
    SELECT * FROM HISTORY_DATA  
    UNION ALL
    SELECT * FROM PAPER_DATA
    UNION ALL
    SELECT * FROM PHOTO_DATA
) ORDER BY 
    DATA_TYPE ASC,           -- 第一優先：資料類型排序
    UNIQUE_ID DESC          -- 第二優先：唯一識別碼降冪排序
