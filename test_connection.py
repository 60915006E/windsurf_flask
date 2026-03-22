#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oracle 19c 連線測試腳本

遵循 .windsurfrules 規範：
- 從 config.py 讀取連線配置
- 使用 python-oracledb Thin Mode 連線
- 執行 SELECT SYSDATE FROM DUAL 測試
- 詳細的錯誤處理和檢查建議
- 測試過程記錄到 logs/test_db.log

作者：系統管理員
建立日期：2026-03-02
版本：1.0.0
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional

# 嘗試導入 python-oracledb
try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False
    print("❌ python-oracledb 未安裝，無法進行 Oracle 連線測試")
    print("💡 請先安裝 python-oracledb: pip install python-oracledb")
    sys.exit(1)

def setup_test_logging():
    """設定測試專用的日誌記錄器
    
    建立專門的測試日誌檔案 logs/test_db.log，
    包含詳細的時間戳記和測試過程記錄。
    """
    # 確保 logs 目錄存在
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"📁 建立日誌目錄: {log_dir}")
    
    # 設定測試日誌檔案路徑
    log_file = os.path.join(log_dir, 'test_db.log')
    
    # 配置測試專用日誌記錄器
    test_logger = logging.getLogger('test_connection')
    test_logger.setLevel(logging.INFO)
    
    # 清除現有的處理器
    test_logger.handlers.clear()
    
    # 設定檔案處理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 設定控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 設定日誌格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加處理器
    test_logger.addHandler(file_handler)
    test_logger.addHandler(console_handler)
    
    return test_logger

def load_config():
    """從 config.py 載入資料庫配置
    
    讀取必要的連線參數：
    - DB_USER: 資料庫使用者名稱
    - DB_PASSWORD: 資料庫密碼
    - DB_HOST: 資料庫主機
    - DB_PORT: 資料庫端口
    - DB_SERVICE_NAME: 資料庫服務名稱
    
    Returns:
        dict: 配置參數字典
        
    Raises:
        ImportError: config.py 不存在時拋出
        ValueError: 必要參數缺失時拋出
    """
    try:
        import config
    except ImportError as e:
        print("❌ 無法載入 config.py 檔案")
        print("💡 請確保 config.py 檔案存在於專案根目錄")
        print(f"📄 錯誤詳情: {str(e)}")
        raise ImportError("config.py 檔案不存在")
    
    # 檢查必要的配置參數
    required_params = {
        'DB_USER': getattr(config, 'DB_USER', None),
        'DB_PASSWORD': getattr(config, 'DB_PASSWORD', None),
        'DB_HOST': getattr(config, 'DB_HOST', None),
        'DB_PORT': getattr(config, 'DB_PORT', None),
        'DB_SERVICE_NAME': getattr(config, 'DB_SERVICE_NAME', None)
    }
    
    # 驗證參數完整性
    missing_params = []
    for param_name, param_value in required_params.items():
        if not param_value:
            missing_params.append(param_name)
    
    if missing_params:
        print("❌ config.py 中缺少必要的配置參數")
        print("💡 請檢查以下參數是否已正確設定:")
        for param in missing_params:
            print(f"   - {param}")
        raise ValueError(f"缺少配置參數: {', '.join(missing_params)}")
    
    print("✅ 配置檔案載入成功")
    return required_params

def get_error_suggestions(error_code: int) -> str:
    """
    根據 Oracle 錯誤代碼提供具體的檢查建議
    
    針對常見的連線錯誤提供實用的解決方案，
    特別是內網環境中常見的問題。
    
    Args:
        error_code: Oracle 錯誤代碼
        
    Returns:
        str: 檢查建議訊息
    """
    suggestions = {
        # 連線超時相關
        12170: "🔍 連線超時建議:\n"
               "   1. 檢查網路連線是否正常\n"
               "   2. 確認防火牆是否開放 1521 端口\n"
               "   3. 檢查資料庫伺服器是否正在運行\n"
               "   4. 考慮增加 DB_CONNECT_TIMEOUT 設定",
        
        # TNS 無法解析
        12154: "🔍 TNS 解析錯誤建議:\n"
               "   1. 檢查 DB_SERVICE_NAME 是否正確\n"
               "   2. 確認 DB_HOST 和 DB_PORT 設定\n"
               "   3. 檢查 tnsnames.ora 檔案（如果使用）\n"
               "   4. 嘗試使用 SID 而非 Service Name",
        
        # 監聽器錯誤
        12541: "🔍 監聽器錯誤建議:\n"
               "   1. 確認 Oracle 監聽器是否啟動\n"
               "   2. 檢查 lsnrctl status 輸出\n"
               "   3. 確認防火牆設定\n"
               "   4. 檢查資料庫服務狀態",
        
        # 協議適配器錯誤
        12560: "🔍 協議適配器錯誤建議:\n"
               "   1. 檢查 Oracle 版本相容性\n"
               "   2. 確認客戶端和伺服器版本匹配\n"
               "   3. 檢查網路協定設定\n"
               "   4. 嘗試重新安裝 python-oracledb",
        
        # 存取被拒絕
        12514: "🔍 存取被拒絕錯誤建議:\n"
               "   1. 檢查使用者名稱和密碼是否正確\n"
               "   2. 確認使用者帳戶是否被鎖定\n"
               "   3. 檢查使用者是否有連線權限\n"
               "   4. 聯繫資料庫管理員重設密碼",
        
        # 服務未註冊
        12537: "🔍 服務未註冊錯誤建議:\n"
               "   1. 檢查 DB_SERVICE_NAME 在資料庫中是否存在\n"
               "   2. 確認資料庫服務是否啟動\n"
               "   3. 檢查服務名稱拼寫是否正確\n"
               "   4. 嘗試使用完整的服務名稱格式",
        
        # 網路相關錯誤
        12541: "🔍 網路連線錯誤建議:\n"
               "   1. 使用 ping 或 telnet 測試連線\n"
               "   2. 檢查 DNS 解析是否正常\n"
               "   3. 確認網路路徑是否通暢\n"
               "   4. 檢查負載平衡器或防火牆設定",
        
        # 認證失敗
        28000: "🔍 認證失敗錯誤建議:\n"
               "   1. 檢查使用者名稱和密碼\n"
               "   2. 確認密碼是否過期\n"
               "   3. 檢查帳戶是否被鎖定\n"
               "   4. 聯繫 DBA 解鎖定問題",
        
        # 內網環境特殊錯誤
        12505: "🔍 內網連線問題建議:\n"
               "   1. 檢查內網 DNS 設定\n"
               "   2. 確認 IP 位址是否正確\n"
               "   3. 檢查子網路遮罩設定\n"
               "   4. 測試其他內網主機連線",
    }
    
    return suggestions.get(error_code, f"🔍 ORA-{error_code} 錯誤發生\n"
                                   "💡 建議:\n"
                                   "   1. 檢查 Oracle 服務狀態\n"
                                   "   2. 確認網路連線正常\n"
                                   "   3. 聯繫資料庫管理員\n"
                                   "   4. 查看完整的錯誤日誌")

def test_oracle_connection(config: dict, logger) -> bool:
    """
    執行 Oracle 連線測試
    
    使用 python-oracledb Thin Mode 建立連線，
    執行 SELECT SYSDATE FROM DUAL 測試查詢，
    並處理各種可能的錯誤情況。
    
    Args:
        config: 資料庫配置字典
        logger: 日誌記錄器
        
    Returns:
        bool: 連線測試是否成功
    """
    try:
        # 初始化 Oracle Thin Mode 客戶端
        logger.info("🔄 初始化 Oracle Thin Mode 客戶端...")
        oracledb.init_oracle_client()
        logger.info("✅ Oracle Thin Mode 客戶端初始化成功")
        
        # 建立連線字串
        dsn = f"{config['DB_HOST']}:{config['DB_PORT']}/{config['DB_SERVICE_NAME']}"
        logger.info(f"🔗 嘗試連線到: {config['DB_USER']}@{dsn}")
        
        # 建立連線
        logger.info("🔄 建立資料庫連線...")
        connection = oracledb.connect(
            user=config['DB_USER'],
            password=config['DB_PASSWORD'],
            dsn=dsn
        )
        
        logger.info("✅ 資料庫連線建立成功")
        
        # 執行測試查詢
        logger.info("🔄 執行測試查詢: SELECT SYSDATE FROM DUAL")
        cursor = connection.cursor()
        cursor.execute("SELECT SYSDATE FROM DUAL")
        result = cursor.fetchone()
        
        if result:
            db_time = result[0]
            logger.info(f"✅ 查詢執行成功，資料庫時間: {db_time}")
            
            # 顯示成功訊息
            print("✅ 連線成功")
            print(f"🕒 資料庫目前時間: {db_time}")
            print(f"🌐 連線資訊: {config['DB_USER']}@{dsn}")
            
            # 關閉連線
            cursor.close()
            connection.close()
            logger.info("🔒 連線已正常關閉")
            return True
        else:
            logger.error("❌ 查詢執行失敗：無法取得資料庫時間")
            print("❌ 連線測試失敗：查詢無返回結果")
            return False
            
    except oracledb.Error as e:
        # 解析 Oracle 錯誤
        error_code = getattr(e, 'code', 0)
        error_message = str(e)
        
        logger.error(f"❌ Oracle 連線錯誤: ORA-{error_code} - {error_message}")
        
        # 顯示錯誤訊息
        print(f"❌ 連線失敗: ORA-{error_code}")
        
        # 根據錯誤代碼提供建議
        suggestions = get_error_suggestions(error_code)
        print(suggestions)
        
        return False
        
    except Exception as e:
        # 處理其他未預期的錯誤
        error_message = str(e)
        logger.error(f"❌ 未預期錯誤: {error_message}")
        
        print(f"❌ 連線測試失敗: {error_message}")
        print("💡 建議檢查系統環境和 python-oracledb 安裝")
        
        return False

def print_internal_network_troubleshooting():
    """
    印出內網環境連線問題的檢查清單
    
    提供系統化的故障排除指引，
    特別針對內網環境中常見的連線問題。
    """
    print("\n" + "="*60)
    print("🔧 內網環境連線問題檢查清單")
    print("="*60)
    
    print("\n📋 網路層級檢查:")
    print("   1. 🌐 網路連線測試:")
    print("      ping {DB_HOST}")
    print("      telnet {DB_HOST} {DB_PORT}")
    print("   2. 🔥 防火牆狀態:")
    print("      確認 1521 端口是否開放")
    print("      檢查內網防火牆規則")
    print("   3. 🌍 DNS 解析:")
    print("      nslookup {DB_SERVICE_NAME}")
    print("      檢查 hosts 檔案設定")
    
    print("\n📋 資料庫服務檢查:")
    print("   1. 🏃 Oracle 服務狀態:")
    print("      lsnrctl status")
    print("      檢查監聽器是否運行")
    print("   2. 📊 服務可用性:")
    print("      檢查資料庫是否啟動")
    print("      確認服務名稱正確性")
    print("   3. 👤 使用者權限:")
    print("      確認使用者帳戶狀態")
    print("      檢查密碼是否正確")
    print("      驗證連線權限設定")
    
    print("\n📋 配置檔案檢查:")
    print("   1. 📄 config.py 內容:")
    print("      確認所有參數正確設定")
    print("      檢查是否有語法錯誤")
    print("   2. 🔧 環境變數:")
    print("      檢查 ORACLE_HOME 設定")
    print("      確認 TNS_ADMIN 路徑")
    print("   3. 📦 python-oracledb 版本:")
    print("      確認版本相容性")
    print("      檢查是否需要更新")
    
    print("\n📋 系統層級檢查:")
    print("   1. 💾 系統資源:")
    print("      檢查磁碟空間是否足夠")
    print("      確認記憶體使用情況")
    print("   2. 🔒 安全設定:")
    print("      檢查 SSL/TLS 設定")
    print("      確認認證配置")
    print("   3. 📝 日誌檔案:")
    print("      查看 Oracle alert log")
    print("      檢查系統事件日誌")
    
    print("\n📋 常見解決方案:")
    print("   1. 🔄 重新啟動服務:")
    print("      重啟 Oracle 監聽器")
    print("      重新啟動資料庫服務")
    print("   2. 🔄 重新安裝客戶端:")
    print("      pip uninstall python-oracledb")
    print("      pip install python-oracledb")
    print("   3. 📞 聯繫支援:")
    print("      聯繫資料庫管理員")
    print("      聯繫網路管理員")
    print("      聯繫系統管理員")
    
    print("\n" + "="*60)
    print("💡 如果以上檢查都無法解決問題，請收集以下資訊:")
    print("   - 完整的錯誤訊息")
    print("   - config.py 內容")
    print("   - 系統環境資訊")
    print("   - 網路連線測試結果")
    print("="*60 + "\n")

def main():
    """
    主函數 - 執行 Oracle 連線測試
    
    按照以下步驟執行測試：
    1. 設定測試日誌
    2. 載入配置檔案
    3. 執行連線測試
    4. 顯示結果或建議
    """
    print("🚀 開始 Oracle 19c 連線測試")
    print("="*50)
    
    # 設定測試日誌
    logger = setup_test_logging()
    logger.info("🚀 Oracle 19c 連線測試啟動")
    
    try:
        # 載入配置
        config = load_config()
        
        # 執行連線測試
        success = test_oracle_connection(config, logger)
        
        if success:
            print("\n🎉 連線測試完成 - 所有檢查通過")
            logger.info("🎉 Oracle 連線測試成功完成")
        else:
            print("\n⚠️  連線測試失敗")
            print_internal_network_troubleshooting()
            logger.warning("⚠️ Oracle 連線測試失敗")
            
    except ImportError as e:
        print(f"\n❌ 配置載入失敗: {str(e)}")
        logger.error(f"❌ 配置載入失敗: {str(e)}")
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {str(e)}")
        logger.error(f"❌ 測試執行失敗: {str(e)}")
    
    print("="*50)
    print(f"📝 詳細日誌請查看: logs/test_db.log")
    print("="*50)

if __name__ == "__main__":
    """
    程式進入點
    
    當直接執行此腳本時，自動執行連線測試。
    提供命令列使用方式。
    """
    main()
