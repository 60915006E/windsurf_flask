#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oracle 19c 資料庫配置檔案

遵循 .windsurfrules 規範：
- 設定檔分離，支援內網環境手動修改
- 詳細註解說明，方便 Windows Server 維護
- 預留所有必要的連線參數

作者：系統管理員
建立日期：2026-03-02
版本：1.0.0
"""

# ===========================================
# Oracle 19c 雙資料庫連線參數
# ===========================================

# ===========================================
# SYSTEM_DB - 讀寫資料庫 (系統管理用)
# ===========================================
SYSTEM_DB_USER = "admin"
SYSTEM_DB_PASSWORD = "adminpassword"
SYSTEM_DB_HOST = "10.52.141.25"
SYSTEM_DB_PORT = "1610"
SYSTEM_DB_SERVICE_NAME = "ORATESTWORLD"

# SYSTEM_DB 完整 DSN 字串 (讀寫)
# 用於：使用者認證、系統日誌、管理員驗證、按鈕配置
SYSTEM_DB_URI = f"{SYSTEM_DB_USER}:{SYSTEM_DB_PASSWORD}@{SYSTEM_DB_HOST}:{SYSTEM_DB_PORT}/{SYSTEM_DB_SERVICE_NAME}"

# ===========================================
# DATA_DB - 唯讀資料庫 (資料查詢用)
# ===========================================
DATA_DB_USER = "admin"
DATA_DB_PASSWORD = "adminpassword"
DATA_DB_HOST = "10.52.141.25"
DATA_DB_PORT = "1610"
DATA_DB_SERVICE_NAME = "ORATESTWORLD"

# DATA_DB 完整 DSN 字串 (唯讀)
# 用於：一般使用者資料查詢、報表生成、資料分析
DATA_DB_URI = f"{DATA_DB_USER}:{DATA_DB_PASSWORD}@{DATA_DB_HOST}:{DATA_DB_PORT}/{DATA_DB_SERVICE_NAME}"

# ===========================================
# 新進書目查詢配置
# ===========================================

# Schema 配置 - 考量到表擁有者為 sarchowner
DATA_DB_SCHEMA = "sarchowner"

# ===========================================
# 狀態碼配置 - 隱形過濾設定
# ===========================================

# 狀態欄位名稱配置（正式資料庫欄位）
STATUS_CODE_FIELD = "OVC_STATUS_CDE"        # 狀態碼欄位名稱
STATUS_NAME_FIELD = "OVC_STATUS_NAME"       # 狀態中文名稱欄位名稱

# 狀態碼值配置
STATUS_OPEN_CODE = "open"                   # 已登錄狀態碼
STATUS_OPEN_NAME = "已登錄"                 # 已登錄狀態中文名稱

# 其他常見狀態碼（供參考）
STATUS_DRAFT_CODE = "draft"                 # 草稿狀態碼
STATUS_DRAFT_NAME = "草稿"                   # 草稿狀態中文名稱
STATUS_DELETED_CODE = "deleted"             # 刪除狀態碼
STATUS_DELETED_NAME = "已刪除"               # 刪除狀態中文名稱

# 隱形過濾條件 - 所有 DATA_DB 查詢都必須包含此條件
# 確保只顯示狀態為『已登錄』的文章
STATUS_FILTER_CONDITION = f"{STATUS_CODE_FIELD} = '{STATUS_OPEN_CODE}'"

# ===========================================
# 正式資料庫欄位映射定義
# ===========================================

# 主表配置
MAIN_TABLE_NAME = "TBIRLIB_REPORT_MAIN"     # 主表名稱
MAIN_TABLE_FULL = f"{DATA_DB_SCHEMA}.{MAIN_TABLE_NAME}"  # 完整表名

# 主要欄位映射
MAIN_ID_FIELD = "OVC_RP_NO"                # 主鍵
TITLE_FIELD = "OVN_RP_NAME"                 # 標題
SORT_DATE_FIELD = "ODT_PUBLIC_DATE"        # 排序日期

# 搜尋支援欄位
SEARCH_FIELDS = {
    'title': 'OVN_RP_NAME',                 # 標題
    'summary': 'OVN_SUMMARY',               # 摘要
    'main_author': 'OVN_RP_MAIN_AUTHOR',    # 主作者
    'author_list': 'OVN_RP_AUTHOR_LIST',    # 所有作者
    'csi_name': 'OVC_RP_CSI_NAME'           # 主號
}

# 下拉選單過濾欄位
FILTER_FIELDS = {
    'category': 'OVC_RP_CAT_NAME',         # 性質
    'type': 'OVC_RP_TYPE_NAME',            # 分類
    'security_level': 'OVC_SECERT_LV_NAME'  # 機密等級
}

# 日期欄位配置
DATE_FIELDS = {
    'public_date': 'ODT_PUBLIC_DATE',      # 發布日期
    'finish_date': 'ODT_RP_FIN_DATE'        # 完成日期
}

# 詳情頁面完整欄位列表
DETAIL_FIELDS = [
    'OVC_RP_NO',                           # 主鍵
    'OVN_RP_NAME',                         # 標題
    'OVN_SUMMARY',                         # 摘要
    'OVN_RP_MAIN_AUTHOR',                  # 主作者
    'OVN_RP_AUTHOR_LIST',                  # 所有作者
    'OVC_RP_CSI_NAME',                     # 主號
    'OVC_RP_CAT_NAME',                     # 性質
    'OVC_RP_TYPE_NAME',                    # 分類
    'OVC_SECERT_LV_NAME',                  # 機密等級
    'ODT_PUBLIC_DATE',                     # 發布日期
    'ODT_RP_FIN_DATE',                     # 完成日期
    'OVC_STATUS_CDE',                      # 狀態碼
    'OVC_STATUS_NAME',                     # 狀態名稱
    'OVN_RP_TRAIN_TYPE',                   # 受訓類型
    'OVN_RP_CURRENT_DESC',                 # 現況敘述
    'OVN_RP_APP_DESC',                     # 應用敘述
    'OVN_RP_AUTHOR_UNIT'                   # 作者單位
]

# 列表頁面必要欄位（效能優化）
LIST_FIELDS = [
    'OVC_RP_NO',                           # 主鍵
    'OVN_RP_NAME',                         # 標題
    'ODT_PUBLIC_DATE',                     # 發布日期
    'OVN_RP_MAIN_AUTHOR',                  # 主作者
    'OVC_RP_CAT_NAME',                     # 性質
    'OVC_STATUS_CDE',                      # 狀態碼
    'OVC_STATUS_NAME'                      # 狀態名稱
]

# 新進書目資料表配置 - 請根據實際資料庫結構調整
# 表名：存放書目資料的資料表
NEWEST_BOOKS_TABLE = "DOCUMENTS"

# 欄位名稱配置 - 請根據實際資料表結構調整
NEWEST_BOOKS_ID_FIELD = "DOC_ID"        # 書目 ID 欄位
NEWEST_BOOKS_TITLE_FIELD = "TITLE"      # 書目標題欄位
NEWEST_BOOKS_DATE_FIELD = "CREATED_DATE" # 日期欄位（用於排序）

# 完整表名（包含 Schema）
NEWEST_BOOKS_FULL_TABLE = f"{DATA_DB_SCHEMA}.{NEWEST_BOOKS_TABLE}"

# 常見日期欄位選項（請根據實際表結構選擇）：
# CREATED_DATE - 建檔日期
# PUBLISH_DATE - 出版日期
# UPDATE_DATE - 更新日期
# ADD_DATE - 新增日期
# CREATE_TIME - 建立時間

# 效能優化建議：
# 1. 確保 NEWEST_BOOKS_DATE_FIELD 欄位有索引
# 2. 建議建立複合索引：(NEWEST_BOOKS_DATE_FIELD DESC, NEWEST_BOOKS_ID_FIELD)
# 3. 如果資料量很大，可考慮分割區表

# ===========================================
# 連線池配置
# ===========================================

# ===========================================
# 連線池設定 (Windows Server 效能優化)
# ===========================================

# 連線池最小連線數
# 內網環境建議設定為 2，確保基本連線可用
# 過高可能造成資源浪費，過低可能影響響應速度
DB_POOL_MIN = 2

# 連線池最大連線數
# 內網環境建議設定為 5，平衡效能與資源使用
# 可根據實際併發需求調整 (建議範圍：3-10)
DB_POOL_MAX = 5

# 連線池增量
# 當連線不足時，每次增加的連線數量
# 建議設定為 1，避免連線數量急劇增長
DB_POOL_INCREMENT = 1

# ===========================================
# 連線超時設定 (內網環境優化)
# ===========================================

# 連線超時時間 (秒)
# 內網環境通常延遲較低，可設定較短時間
# 建議範圍：10-30 秒
DB_CONNECT_TIMEOUT = 30

# 會話超時時間 (秒)
# 資料庫會話閒置超時時間
# 建議範圍：300-1800 秒 (5-30 分鐘)
DB_SESSION_TIMEOUT = 600

# ===========================================
# NLS (National Language Support) 設定
# ===========================================

# 日期格式設定
# 確保日期時間在應用程式中正確顯示
# 常用格式：'YYYY-MM-DD HH24:MI:SS'
NLS_DATE_FORMAT = "YYYY-MM-DD HH24:MI:SS"

# 時間戳格式設定
# 包含毫秒精確度的時間格式
# 常用格式：'YYYY-MM-DD HH24:MI:SS.FF'
NLS_TIMESTAMP_FORMAT = "YYYY-MM-DD HH24:MI:SS.FF"

# 語言設定
# 影響錯誤訊息和日期月份顯示
# 常用值：'TRADITIONAL CHINEAN', 'AMERICAN'
NLS_LANGUAGE = "TRADITIONAL CHINEAN"

# 地區設定
# 影響數字、日期、貨幣格式
# 常用值：'TAIWAN', 'AMERICA'
NLS_TERRITORY = "TAIWAN"

# ===========================================
# 字元集設定
# ===========================================

# 資料庫字元集
# 支援中文字元的字元集
# 建議：'AL32UTF8' (UTF-8) 或 'ZHT16MSWIN950' (繁體中文)
CHARACTER_SET = "AL32UTF8"

# 國家字元集
# 用於 NCHAR 和 NCLOB 欄位
# 建議：'AL16UTF16'
NCHARACTER_SET = "AL16UTF16"

# ===========================================
# 安全性設定
# ===========================================

# SSL 加密連線
# 內網環境通常不需要，但如有特殊安全需求可啟用
# 值：True 或 False
SSL_ENABLED = False

# Oracle Wallet 位置 (SSL 時使用)
# 如果啟用 SSL，需要指定 Wallet 路徑
# 範例：'/path/to/oracle/wallet'
WALLET_LOCATION = ""

# ===========================================
# 效能調整參數
# ===========================================

# 查詢擷取大小
# 每次從資料庫擷取的記錄數量
# 內網環境可設定較大值以提升效能
# 建議範圍：100-1000
FETCH_SIZE = 1000

# 陣列大小
# 批次操作的陣列大小
# 影響批次插入和更新的效能
# 建議範圍：50-500
ARRAY_SIZE = 100

# 預取列數
# 預先擷取的列數，減少網路往返
# 建議範圍：50-200
PREFETCH_ROWS = 100

# ===========================================
# 日誌與監控設定
# ===========================================

# 資料庫操作日誌級別
# 可選值：'DEBUG', 'INFO', 'WARNING', 'ERROR'
# 生產環境建議使用 'INFO' 或 'WARNING'
DB_LOG_LEVEL = "INFO"

# 是否記錄 SQL 語句
# 開發時可設為 True 進行除錯
# 生產環境建議設為 False 以避免日誌過大
DB_LOG_SQL = False

# ===========================================
# 開發與測試設定
# ===========================================

# 開發模式標記
# 影響錯誤處理和日誌詳細程度
# 值：True 或 False
DEVELOPMENT_MODE = False

# 是否使用模擬資料
# 無真實資料庫時使用模擬資料進行開發
# 值：True 或 False
MOCK_DATA = False

# ===========================================
# 內網環境特定設定
# ===========================================

# 內網環境標記
# 設定為 True 以啟用內網環境優化
# 值：True 或 False
INTERNAL_NETWORK = True

# 防火牆環境標記
# 如果有防火牆，可能需要調整連線參數
# 值：True 或 False
FIREWALL_ENABLED = True

# VPN 需求標記
# 如果需要 VPN 才能連線資料庫
# 值：True 或 False
VPN_REQUIRED = False

# ===========================================
# 檔案儲存配置
# ===========================================

# 檔案儲存路徑 (伺服器存放 PDF 的資料夾路徑)
# Windows Server 環境請使用絕對路徑，例如：C:\\file_storage\\documents
# Linux 環境請使用絕對路徑，例如：/var/www/file_storage/documents
import os
FILE_STORAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'file_storage')

# 允許下載的副檔名 (安全性限制)
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx'}

# 檔案上傳大小限制 (單位：MB)
MAX_FILE_SIZE = 50

# ===========================================
# 應用程式識別資訊
# ===========================================

# 應用程式名稱
# 出現在資料庫監控工具中，便於識別連線來源
APPLICATION_NAME = "Oracle_19c_Query_System"

# 應用程式模組名稱
# 識別應用程式的具體模組
APPLICATION_MODULE = "Database_Manager"

# 應用程式操作名稱
# 識別當前執行的操作類型
APPLICATION_ACTION = "Query"

# ===========================================
# 備用資料庫設定 (可選)
# ===========================================

# 備用資料庫主機
# 當主資料庫不可用時的備用選擇
BACKUP_DB_HOST = ""

# 備用資料庫端口
BACKUP_DB_PORT = "1521"

# 備用資料庫服務名稱
BACKUP_DB_SERVICE_NAME = ""

# 備用資料庫使用者名稱
BACKUP_DB_USERNAME = ""

# 備用資料庫密碼
BACKUP_DB_PASSWORD = ""

# ===========================================
# 設定檔驗證函式
# ===========================================

def validate_config():
    """
    驗證配置檔案的完整性和正確性
    
    檢查所有必要的連線參數是否已設定，
    並驗證參數值的合理性。
    
    Returns:
        bool: 配置是否有效
        
    Raises:
        ValueError: 配置無效時拋出異常
    """
    # 檢查必要的連線參數
    required_params = [
        'DB_USER',
        'DB_PASSWORD', 
        'DB_HOST',
        'DB_PORT',
        'DB_SERVICE_NAME'
    ]
    
    missing_params = []
    for param in required_params:
        if not globals().get(param):
            missing_params.append(param)
    
    if missing_params:
        raise ValueError(f"缺少必要的配置參數: {', '.join(missing_params)}")
    
    # 驗證端口號碼
    try:
        port = int(DB_PORT)
        if not (1 <= port <= 65535):
            raise ValueError(f"端口號碼無效: {port} (必須在 1-65535 範圍內)")
    except ValueError:
        raise ValueError(f"端口號碼格式錯誤: {DB_PORT}")
    
    # 驗證連線池參數
    try:
        min_conn = int(DB_POOL_MIN)
        max_conn = int(DB_POOL_MAX)
        increment = int(DB_POOL_INCREMENT)
        
        if min_conn < 1:
            raise ValueError(f"最小連線數必須大於 0: {min_conn}")
        if max_conn < min_conn:
            raise ValueError(f"最大連線數必須大於等於最小連線數: {min_conn} >= {max_conn}")
        if increment < 1:
            raise ValueError(f"連線增量必須大於 0: {increment}")
            
    except ValueError:
        raise ValueError("連線池參數必須為整數")
    
    # 驗證超時參數
    try:
        connect_timeout = int(DB_CONNECT_TIMEOUT)
        session_timeout = int(DB_SESSION_TIMEOUT)
        
        if connect_timeout < 1:
            raise ValueError(f"連線超時必須大於 0: {connect_timeout}")
        if session_timeout < 1:
            raise ValueError(f"會話超時必須大於 0: {session_timeout}")
            
    except ValueError:
        raise ValueError("超時參數必須為整數")
    
    print("✅ Oracle 資料庫配置檔案驗證通過")
    return True

def get_connection_string():
    """
    建立完整的資料庫連線字串
    
    Returns:
        str: 格式化的連線字串
    """
    return f"{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_SERVICE_NAME}"

def print_config_summary():
    """
    列印配置摘要 (隱藏敏感資訊)
    
    用於除錯和確認當前配置狀態，
    敏感資訊如密碼會被遮蔽。
    """
    print("=" * 50)
    print("Oracle 19c 資料庫配置摘要")
    print("=" * 50)
    print(f"使用者名稱: {DB_USER}")
    print(f"資料庫主機: {DB_HOST}")
    print(f"連線端口: {DB_PORT}")
    print(f"服務名稱: {DB_SERVICE_NAME}")
    print(f"連線池: 最小={DB_POOL_MIN}, 最大={DB_POOL_MAX}, 增量={DB_POOL_INCREMENT}")
    print(f"連線超時: {DB_CONNECT_TIMEOUT}秒")
    print(f"會話超時: {DB_SESSION_TIMEOUT}秒")
    print(f"內網環境: {INTERNAL_NETWORK}")
    print(f"開發模式: {DEVELOPMENT_MODE}")
    print("=" * 50)

# 如果直接執行此檔案，則進行驗證和測試
if __name__ == "__main__":
    try:
        # 驗證配置
        validate_config()
        
        # 列印配置摘要
        print_config_summary()
        
        print("🎉 Oracle 資料庫配置檔案準備就緒")
        print("💡 提示：請在內網環境中修改上述參數為實際值")
        
    except ValueError as e:
        print(f"❌ 配置錯誤: {e}")
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
