-- ===========================================
-- 跨資料表聯合搜尋欄位設定更新
-- ===========================================
-- 
-- 功能：為四種資料類型的聯合檢索設定欄位顯示配置
-- 1. 技術報告 (TBIRLIB_REPORT_MAIN) - 背景色：淡藍色
-- 2. 史政 (TRIRLIB_HISTORY_MAIN) - 背景色：淡綠色  
-- 3. 逸光報 (TRIRLIB_PAPER_MAIN) - 背景色：淡灰色
-- 4. 史政照片 (TRIRLIB_PHOTO_MAIN) - 背景色：淡黃色

-- ===========================================
-- 跨表聯合搜尋簡目欄位設定
-- ===========================================

-- 清除現有的跨表設定
DELETE FROM FIELD_SETTINGS WHERE SHOW_TYPE = 'unified_list';

-- 插入跨表聯合搜尋簡目欄位
INSERT INTO FIELD_SETTINGS (
    FIELD_ID, 
    DISPLAY_NAME, 
    FIELD_TYPE, 
    SHOW_ORDER, 
    IS_VISIBLE, 
    SHOW_TYPE,
    DATA_TYPE,
    DESCRIPTION
) VALUES 
-- 通用欄位
('DATA_TYPE_NAME', '資料類型', 'STRING', 1, 'Y', 'unified_list', 'ALL', '顯示資料類型名稱'),
('UNIQUE_ID', '唯一識別碼', 'STRING', 2, 'Y', 'unified_list', 'ALL', '資料的唯一識別碼'),

-- 技術報告專用欄位
('TITLE', '標題', 'STRING', 3, 'Y', 'unified_list', '1', '技術報告標題'),
('RP_CSI_NAME', '報告主號', 'STRING', 4, 'Y', 'unified_list', '1', '技術報告主編號'),
('HOST_NAME', '報告單位', 'STRING', 5, 'Y', 'unified_list', '1', '技術報告單位'),
('YEAR', '報告年度', 'STRING', 6, 'Y', 'unified_list', '1', '技術報告年度'),

-- 史政專用欄位
('HS_NAME', '名稱', 'STRING', 3, 'Y', 'unified_list', '2', '史政資料名稱'),
('HS_CAT_NAME', '史政類型', 'STRING', 4, 'Y', 'unified_list', '2', '史政資料類型'),
('PUBLISH_YEAR', '出版年', 'STRING', 5, 'Y', 'unified_list', '2', '史政出版年份'),
('HA_TYPE', '文物類型', 'STRING', 6, 'Y', 'unified_list', '2', '史政文物類型'),

-- 史政照片專用欄位
('TO_NAME', '照片名稱', 'STRING', 3, 'Y', 'unified_list', '4', '史政照片名稱'),
('TO_PLACE', '照片地點', 'STRING', 4, 'Y', 'unified_list', '4', '史政照片拍攝地點'),
('TO_DATE', '照片日期', 'DATE', 5, 'Y', 'unified_list', '4', '史政照片拍攝日期'),
('TO_DEPT_NAME', '照片單位', 'STRING', 6, 'Y', 'unified_list', '4', '史政照片單位'),

-- 逸光報專用欄位
('PAPER_NAME', '報紙名稱', 'STRING', 3, 'Y', 'unified_list', '3', '逸光報名稱'),
('PAPER_AUTHOR', '報紙作者', 'STRING', 4, 'Y', 'unified_list', '3', '逸光報作者'),
('PUBLIC_DATE', '發布日期', 'DATE', 5, 'Y', 'unified_list', '3', '逸光報發布日期');

-- ===========================================
-- 技術報告詳情欄位設定
-- ===========================================

-- 清除現有的技術報告詳情設定
DELETE FROM FIELD_SETTINGS WHERE SHOW_TYPE = 'unified_detail_1';

-- 插入技術報告詳情欄位
INSERT INTO FIELD_SETTINGS (
    FIELD_ID, 
    DISPLAY_NAME, 
    FIELD_TYPE, 
    SHOW_ORDER, 
    IS_VISIBLE, 
    SHOW_TYPE,
    DATA_TYPE,
    DESCRIPTION
) VALUES 
-- 基本資訊
('UNIQUE_ID', '唯一識別碼', 'STRING', 1, 'Y', 'unified_detail_1', '1', '技術報告唯一識別碼'),
('TITLE', '標題', 'STRING', 2, 'Y', 'unified_detail_1', '1', '技術報告標題'),
('RP_CSI_NAME', '報告主號', 'STRING', 3, 'Y', 'unified_detail_1', '1', '技術報告主編號'),
('RP_CAT_NAME', '性質', 'STRING', 4, 'Y', 'unified_detail_1', '1', '技術報告性質'),
('RP_TYPE_NAME', '分類', 'STRING', 5, 'Y', 'unified_detail_1', '1', '技術報告分類'),

-- 機密相關
('SECERT_LV_NAME', '機密等級', 'STRING', 6, 'Y', 'unified_detail_1', '1', '技術報告機密等級'),
('SECERT_ATTRIBUTE', '機密性質', 'STRING', 7, 'Y', 'unified_detail_1', '1', '技術報告機密性質'),
('TRADE_SECERT_NAME', '贏密類型', 'STRING', 8, 'Y', 'unified_detail_1', '1', '技術報告贏密類型'),

-- 單位與作者
('HOST_NAME', '報告單位', 'STRING', 9, 'Y', 'unified_detail_1', '1', '技術報告單位'),
('YEAR', '報告年度', 'STRING', 10, 'Y', 'unified_detail_1', '1', '技術報告年度'),
('MAIN_AUTHOR', '主要作者', 'STRING', 11, 'Y', 'unified_detail_1', '1', '技術報告主要作者'),
('MAIN_AUTHOR_DEPT_NAME', '主作者單位', 'STRING', 12, 'Y', 'unified_detail_1', '1', '技術報告主作者單位'),
('AUTHOR_LIST', '所有作者', 'STRING', 13, 'Y', 'unified_detail_1', '1', '技術報告所有作者'),

-- 內容描述
('SUMMARY', '摘要', 'TEXT', 14, 'Y', 'unified_detail_1', '1', '技術報告摘要'),
('DESCRIPTION', '現況敘述', 'TEXT', 15, 'Y', 'unified_detail_1', '1', '技術報告現況敘述'),
('APPLICATION', '應用敘述', 'TEXT', 16, 'Y', 'unified_detail_1', '1', '技術報告應用敘述'),

-- 副表資料
('RP_LIB_TITLE_LIST', '其他號碼', 'STRING', 17, 'Y', 'unified_detail_1', '1', '技術報告其他號碼'),
('RP_OTHER_TITLE_LIST', '自編號', 'STRING', 18, 'Y', 'unified_detail_1', '1', '技術報告自編號'),
('RP_OTHER_NAME_LIST', '其他名稱', 'STRING', 19, 'Y', 'unified_detail_1', '1', '技術報告其他名稱'),
('RP_KEYWORD_LIST', '關鍵字', 'STRING', 20, 'Y', 'unified_detail_1', '1', '技術報告關鍵字'),
('RP_PLAN_LIST', '計畫名稱', 'STRING', 21, 'Y', 'unified_detail_1', '1', '技術報告計畫名稱'),

-- 其他資訊
('PROMOTE_CSI_NAME', '報告副號', 'STRING', 22, 'Y', 'unified_detail_1', '1', '技術報告副號'),
('TRAIN_NAME', '受訓類型', 'STRING', 23, 'Y', 'unified_detail_1', '1', '技術報告受訓類型'),
('PAGE', '頁數', 'NUMBER', 24, 'Y', 'unified_detail_1', '1', '技術報告頁數'),
('PUBLIC_DATE', '發布日期', 'DATE', 25, 'Y', 'unified_detail_1', '1', '技術報告發布日期'),
('FIN_DATE', '完成日期', 'DATE', 26, 'Y', 'unified_detail_1', '1', '技術報告完成日期');

-- ===========================================
-- 史政詳情欄位設定
-- ===========================================

-- 清除現有的史政詳情設定
DELETE FROM FIELD_SETTINGS WHERE SHOW_TYPE = 'unified_detail_2';

-- 插入史政詳情欄位
INSERT INTO FIELD_SETTINGS (
    FIELD_ID, 
    DISPLAY_NAME, 
    FIELD_TYPE, 
    SHOW_ORDER, 
    IS_VISIBLE, 
    SHOW_TYPE,
    DATA_TYPE,
    DESCRIPTION
) VALUES 
-- 基本資訊
('UNIQUE_ID', '唯一識別碼', 'STRING', 1, 'Y', 'unified_detail_2', '2', '史政資料唯一識別碼'),
('HS_NAME', '名稱', 'STRING', 2, 'Y', 'unified_detail_2', '2', '史政資料名稱'),
('HS_CAT_NAME', '史政類型', 'STRING', 3, 'Y', 'unified_detail_2', '2', '史政資料類型'),
('PUBLISH_YEAR', '出版年', 'STRING', 4, 'Y', 'unified_detail_2', '2', '史政出版年份'),
('HS_SUMMARY', '內容', 'TEXT', 5, 'Y', 'unified_detail_2', '2', '史政資料內容'),

-- 史政文物資訊
('HA_NO', '史政文物編號', 'STRING', 6, 'Y', 'unified_detail_2', '2', '史政文物編號'),
('HA_TYPE', '史政文物類型', 'STRING', 7, 'Y', 'unified_detail_2', '2', '史政文物類型'),
('HA_UNIT_NUM', '史政文物數量', 'NUMBER', 8, 'Y', 'unified_detail_2', '2', '史政文物數量'),
('HA_UNIT_NAME', '史政文物名稱', 'STRING', 9, 'Y', 'unified_detail_2', '2', '史政文物名稱'),
('HA_LIB_MANAGE', '史政文物狀況', 'STRING', 10, 'Y', 'unified_detail_2', '2', '史政文物狀況'),

-- 取得與歸屬資訊
('HA_GET_INFO', '史政文物取得資訊', 'TEXT', 11, 'Y', 'unified_detail_2', '2', '史政文物取得資訊'),
('GET_YEAR', '史政文物取得年度', 'STRING', 12, 'Y', 'unified_detail_2', '2', '史政文物取得年度'),
('HA_BELONG', '史政文物所屬單位', 'STRING', 13, 'Y', 'unified_detail_2', '2', '史政文物所屬單位'),

-- 尺寸資訊
('HA_SIZE', '史政文物大小', 'STRING', 14, 'Y', 'unified_detail_2', '2', '史政文物大小'),
('HA_ROUND', '史政文物直徑', 'STRING', 15, 'Y', 'unified_detail_2', '2', '史政文物直徑'),
('HA_SPECIAL_SIZE', '史政文物特殊尺寸', 'STRING', 16, 'Y', 'unified_detail_2', '2', '史政文物特殊尺寸'),

-- 事件資訊
('EVENT_DATE', '史政事件日期', 'DATE', 17, 'Y', 'unified_detail_2', '2', '史政事件日期');

-- ===========================================
-- 逸光報詳情欄位設定
-- ===========================================

-- 清除現有的逸光報詳情設定
DELETE FROM FIELD_SETTINGS WHERE SHOW_TYPE = 'unified_detail_3';

-- 插入逸光報詳情欄位
INSERT INTO FIELD_SETTINGS (
    FIELD_ID, 
    DISPLAY_NAME, 
    FIELD_TYPE, 
    SHOW_ORDER, 
    IS_VISIBLE, 
    SHOW_TYPE,
    DATA_TYPE,
    DESCRIPTION
) VALUES 
-- 基本資訊
('UNIQUE_ID', '唯一識別碼', 'STRING', 1, 'Y', 'unified_detail_3', '3', '逸光報唯一識別碼'),
('PAPER_NAME', '報紙名稱', 'STRING', 2, 'Y', 'unified_detail_3', '3', '逸光報名稱'),
('PAPER_AUTHOR', '報紙作者', 'STRING', 3, 'Y', 'unified_detail_3', '3', '逸光報作者');

-- ===========================================
-- 史政照片詳情欄位設定
-- ===========================================

-- 清除現有的史政照片詳情設定
DELETE FROM FIELD_SETTINGS WHERE SHOW_TYPE = 'unified_detail_4';

-- 插入史政照片詳情欄位
INSERT INTO FIELD_SETTINGS (
    FIELD_ID, 
    DISPLAY_NAME, 
    FIELD_TYPE, 
    SHOW_ORDER, 
    IS_VISIBLE, 
    SHOW_TYPE,
    DATA_TYPE,
    DESCRIPTION
) VALUES 
-- 基本資訊
('UNIQUE_ID', '唯一識別碼', 'STRING', 1, 'Y', 'unified_detail_4', '4', '史政照片唯一識別碼'),
('TO_NAME', '照片名稱', 'STRING', 2, 'Y', 'unified_detail_4', '4', '史政照片名稱'),

-- 拍攝資訊
('TO_DATE', '照片日期', 'DATE', 3, 'Y', 'unified_detail_4', '4', '史政照片拍攝日期'),
('TO_PLACE', '照片地點', 'STRING', 4, 'Y', 'unified_detail_4', '4', '史政照片拍攝地點'),
('TO_PEOPLE', '照片人員', 'STRING', 5, 'Y', 'unified_detail_4', '4', '史政照片拍攝人員'),
('TO_SUMMARY', '照片說明', 'TEXT', 6, 'Y', 'unified_detail_4', '4', '史政照片說明'),

-- 單位資訊
('TO_DEPT_NAME', '照片單位名稱', 'STRING', 7, 'Y', 'unified_detail_4', '4', '史政照片單位名稱'),
('TO_APPLY_DEPT_NAME', '照片提供單位名稱', 'STRING', 8, 'Y', 'unified_detail_4', '4', '史政照片提供單位名稱');

-- ===========================================
-- 驗證設定
-- ===========================================

-- 檢查跨表聯合搜尋簡目欄位設定
SELECT 
    SHOW_TYPE,
    COUNT(*) AS FIELD_COUNT,
    LISTAGG(DISPLAY_NAME, ', ') WITHIN GROUP (ORDER BY SHOW_ORDER) AS FIELDS
FROM FIELD_SETTINGS 
WHERE SHOW_TYPE = 'unified_list'
GROUP BY SHOW_TYPE;

-- 檢查各資料類型詳情欄位設定
SELECT 
    SHOW_TYPE,
    COUNT(*) AS FIELD_COUNT,
    LISTAGG(DISPLAY_NAME, ', ') WITHIN GROUP (ORDER BY SHOW_ORDER) AS FIELDS
FROM FIELD_SETTINGS 
WHERE SHOW_TYPE LIKE 'unified_detail_%'
GROUP BY SHOW_TYPE
ORDER BY SHOW_TYPE;

-- 顯示設定摘要
SELECT 
    '設定完成' AS STATUS,
    '跨表聯合搜尋欄位設定已更新' AS MESSAGE,
    SYSDATE AS UPDATE_TIME
FROM DUAL;
