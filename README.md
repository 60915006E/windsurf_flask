# Oracle 19c 資料查詢系統

遵循 Windows Server 2022 離線環境開發規範的 Flask 查詢系統。

## 🏗️ 系統架構

- **Python 版本**: 3.13.7
- **Web 框架**: Flask 3.1.3
- **資料庫**: Oracle 19c (python-oracledb Thin Mode)
- **設計風格**: 暖色調 UI (淺黃底色、深褐文字、暖橘按鈕)
- **安全規範**: OWASP Top 10 防範、參數化查詢

## 🚀 快速開始

### 1. 建立虛擬環境

```bash
# 在專案根目錄執行
python3 -m venv venv
```

### 2. 啟動虛擬環境

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 4. 啟動應用程式

```bash
# 使用啟動腳本（推薦）
python run.py

# 或直接啟動
python app.py
```

### 5. 訪問系統

開啟瀏覽器訪問: http://localhost:5000

## 📁 專案結構

```
windsurf_flask/
├── venv/                    # 虛擬環境目錄
├── templates/                # HTML 樣板
│   ├── base.html           # 母版頁面
│   ├── index.html          # 搜尋首頁
│   ├── results.html        # 搜尋結果頁
│   └── error.html          # 錯誤頁面
├── static/                   # 靜態檔案
│   └── css/
│       └── style.css      # 暖色調樣式表
├── logs/                    # 日誌檔案目錄
├── backups/                 # 備份檔案目錄
├── app.py                  # Flask 主程式
├── database.py              # Oracle 資料庫連線模組
├── mock_oracledb.py        # 模擬資料庫模組（測試用）
├── run.py                  # 啟動腳本
├── test_search.py           # 搜尋功能測試
├── test_database.py         # 資料庫連線測試
├── requirements.txt         # Python 依賴套件
├── requirements_installed.txt # 實際安裝的套件版本
├── .windsurfrules         # 開發規範文件
└── README.md               # 本檔案
```

## 🔧 配置說明

### 環境變數配置

```bash
# 資料庫連線配置
export DB_USER="your_username"
export DB_PASSWORD="your_password"
export DB_DSN="localhost:1521/XEPDB1"

# 連線池配置
export DB_MIN_CONNECTIONS="2"
export DB_MAX_CONNECTIONS="10"
export DB_INCREMENT="1"
```

### 資料庫對應表

#### 搜尋欄位對應 (SEARCH_MAPPING)
| 前端選項 | 資料庫欄位 |
|-----------|-----------|
| 全部欄位 | ALL |
| 題名 | title |
| 撰寫人 | author |
| 編號 | DOC_ID |

#### 文件類型對應 (TYPE_MAPPING)
| 前端值 | 顯示名稱 |
|---------|---------|
| tech_report | 技術報告 |
| history_politics | 史政 |
| history_photos | 史政照片 |
| yiguang_report | 逸光報 |

## 🎨 UI 設計規範

### 色彩配置
- **背景色**: #FFFFE0 (淺黃色)
- **文字色**: #8B4513 (深褐色)
- **按鈕色**: #FF8C00 (暖橘色)
- **禁止使用**: 任何紫色系 (#800080 等)

### 響應式設計
- 桌面: 1200px 最大寬度
- 平板: 768px 以下
- 手機: 480px 以下

## 🔒 安全規範

### SQL 注入防護
- ✅ 使用參數化查詢 (綁定變數)
- ✅ 禁止字串拼接 SQL
- ✅ 輸入驗證與過濾

### 錯誤處理
- ✅ 遮蔽 ORA 錯誤代碼
- ✅ 詳細日誌記錄
- ✅ 友善錯誤頁面

## 🧪 測試

### 執行測試

```bash
# 搜尋功能測試
python test_search.py

# 資料庫連線測試
python test_database.py
```

### 測試覆蓋範圍
- ✅ 對應表功能
- ✅ 搜尋條件建構
- ✅ SQL 注入防護
- ✅ 錯誤處理機制
- ✅ 連線池管理

## 📦 部署

### Windows Server 2022 離線環境

1. **安裝依賴**:
   ```bash
   pip install -r requirements.txt
   ```

2. **設定環境變數**:
   - 資料庫連線資訊
   - 日誌路徑配置

3. **使用 PyInstaller 打包**:
   ```bash
   pip install pyinstaller
   pyinstaller --onefile app.py
   ```

## 🔄 備份政策

- **備份頻率**: 每 7 天
- **保留期限**: 最近一年
- **自動清理**: FIFO 邏輯，超過 52 份時刪除最舊檔案

## 📝 開發規範

詳細規範請參考 `.windsurfrules` 檔案，包含：
- 核心環境與打包規範
- Oracle 19c 資料庫與安全性
- 錯誤處理與日誌規範
- 備份與保留政策
- UI/UX 視覺規範
- 代碼品質規範

## 🐛 問題排除

### 常見問題

1. **虛擬環境問題**:
   ```bash
   # 重新建立虛擬環境
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **資料庫連線失敗**:
   - 檢查 Oracle 服務是否啟動
   - 驗證連線字串格式
   - 確認防火牆設定

3. **靜態檔案 404**:
   - 檢查 `app.static_folder` 路徑設定
   - 確認 `static/` 目錄存在

## 📞 技術支援

如有問題請檢查：
1. `logs/app.log` 日誌檔案
2. 虛擬環境是否正確啟動
3. 依賴套件是否完整安裝

---

**版本**: 1.0.0  
**最後更新**: 2026-03-01  
**相容性**: Python 3.13.7+, Windows Server 2022
