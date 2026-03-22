#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oracle 19c 資料查詢系統 - 備份服務

遵循 .windsurfrules 規範：
- 每週執行一次全系統備份
- 保留最近一年的備份檔（52 份）
- FIFO 邏輯自動清理舊檔案
- 完整的日誌記錄與錯誤處理
- 離線環境相容性

作者：系統管理員
建立日期：2026-03-02
版本：1.0.0
"""

import os
import sys
import zipfile
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional


class BackupService:
    """備份服務類別
    
    負責執行專案備份、管理備份檔案保留政策、
    磁碟空間檢查以及完整的日誌記錄。
    """
    
    def __init__(self):
        """初始化備份服務
        
        設定基本路徑、日誌記錄器、以及備份相關的配置參數。
        所有路徑都使用絕對路徑以確保在不同環境下的正確性。
        """
        # 取得腳本所在目錄的絕對路徑
        self.script_dir = Path(__file__).parent.absolute()
        self.project_root = self.script_dir
        
        # 設定關鍵目錄路徑
        self.backup_dir = self.project_root / 'backups'
        self.logs_dir = self.project_root / 'logs'
        self.temp_dir = self.project_root / 'temp'
        
        # 備份配置參數
        self.required_space_gb = 1  # 預留 1GB 磁碟空間
        self.max_backup_files = 52   # 最多保留 52 份備份（一年）
        self.max_age_days = 365     # 檔案最大保留天數（一年）
        
        # 需要排除的目錄和檔案
        self.exclude_patterns = [
            'venv/',           # 虛擬環境目錄
            '__pycache__/',    # Python 編譯快取
            '*.pyc',          # Python 編譯檔案
            '*.pyo',          # Python 優化檔案
            '.DS_Store',       # macOS 系統檔案
            'Thumbs.db',       # Windows 縮圖快取
            'temp/',           # 暫存目錄
            'logs/backup.log', # 備份日誌本身（避免循環備份）
        ]
        
        # 初始化日誌記錄器
        self._setup_logging()
        
        self.logger.info("備份服務初始化完成")
        self.logger.info(f"專案根目錄: {self.project_root}")
        self.logger.info(f"備份目錄: {self.backup_dir}")
    
    def _setup_logging(self) -> None:
        """設定日誌記錄器
        
        建立專門的備份日誌檔案，設定日誌格式，
        確保所有備份操作都有詳細的記錄。
        """
        # 確保 logs 目錄存在
        self.logs_dir.mkdir(exist_ok=True)
        
        # 設定日誌檔案路徑
        log_file = self.logs_dir / 'backup.log'
        
        # 配置日誌記錄器
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)  # 同時輸出到控制台
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def check_disk_space(self) -> bool:
        """檢查磁碟空間是否足夠
        
        檢查專案根目錄所在磁碟的可用空間，
        確保至少有 1GB 的可用空間進行備份操作。
        
        Returns:
            bool: True 表示空間足夠，False 表示空間不足
        """
        try:
            # 取得磁碟使用統計資訊
            stat = shutil.disk_usage(self.project_root)
            
            # 計算可用空間（GB）
            free_space_gb = stat.free / (1024 ** 3)
            
            self.logger.info(f"磁碟可用空間: {free_space_gb:.2f} GB")
            self.logger.info(f"所需最小空間: {self.required_space_gb} GB")
            
            if free_space_gb < self.required_space_gb:
                self.logger.error(f"磁碟空間不足！可用: {free_space_gb:.2f} GB，需要: {self.required_space_gb} GB")
                return False
            
            self.logger.info("磁碟空間檢查通過")
            return True
            
        except Exception as e:
            self.logger.error(f"檢查磁碟空間時發生錯誤: {str(e)}")
            return False
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """判斷檔案是否應該被排除
        
        根據預設的排除模式檢查檔案或目錄是否應該排除在備份之外。
        
        Args:
            file_path: 要檢查的檔案路徑
            
        Returns:
            bool: True 表示應該排除，False 表示應該包含
        """
        # 轉換為相對路徑進行模式匹配
        relative_path = file_path.relative_to(self.project_root)
        path_str = str(relative_path)
        
        for pattern in self.exclude_patterns:
            if path_str.startswith(pattern.rstrip('/')) or path_str.endswith(pattern.lstrip('/')):
                return True
        
        return False
    
    def create_backup_zip(self) -> Optional[Path]:
        """建立備份 ZIP 檔案
        
        將專案目錄壓縮成 ZIP 檔案，排除指定的檔案和目錄。
        使用 FIFO 邏輯確保備份檔案的管理。
        
        Returns:
            Optional[Path]: 成功時返回備份檔案路徑，失敗時返回 None
        """
        try:
            # 生成備份檔名（包含日期）
            timestamp = datetime.now().strftime('%Y%m%d')
            backup_filename = f'backup_{timestamp}.zip'
            backup_path = self.backup_dir / backup_filename
            
            self.logger.info(f"開始建立備份檔案: {backup_filename}")
            
            # 確保備份目錄存在
            self.backup_dir.mkdir(exist_ok=True)
            
            # 建立 ZIP 檔案
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                # 遍歷專案目錄中的所有檔案
                for file_path in self.project_root.rglob('*'):
                    # 跳過目錄本身（只處理檔案）
                    if file_path.is_dir():
                        continue
                    
                    # 檢查是否應該排除此檔案
                    if self.should_exclude_file(file_path):
                        self.logger.debug(f"排除檔案: {file_path.relative_to(self.project_root)}")
                        continue
                    
                    # 計算相對路徑（用於 ZIP 內部路徑）
                    relative_path = file_path.relative_to(self.project_root)
                    
                    # 添加檔案到 ZIP
                    zipf.write(file_path, relative_path)
                    self.logger.debug(f"已備份: {relative_path}")
            
            # 檢查備份檔案是否建立成功
            if backup_path.exists():
                file_size_mb = backup_path.stat().st_size / (1024 * 1024)
                self.logger.info(f"備份檔案建立成功: {backup_filename} ({file_size_mb:.2f} MB)")
                return backup_path
            else:
                self.logger.error("備份檔案建立失敗：檔案不存在")
                return None
                
        except Exception as e:
            self.logger.error(f"建立備份檔案時發生錯誤: {str(e)}")
            return None
    
    def get_existing_backups(self) -> List[Path]:
        """取得現有的備份檔案列表
        
        掃描備份目錄，取得所有符合命名規則的備份檔案，
        並按建立時間排序（最新的在前）。
        
        Returns:
            List[Path]: 排序後的備份檔案列表
        """
        try:
            # 確保備份目錄存在
            if not self.backup_dir.exists():
                self.logger.info("備份目錄不存在，將會自動建立")
                return []
            
            # 搜尋所有符合 backup_YYYYMMDD.zip 格式的檔案
            backup_files = []
            for file_path in self.backup_dir.glob('backup_*.zip'):
                if file_path.is_file():
                    backup_files.append(file_path)
            
            # 按修改時間排序（最新的在前）
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            self.logger.info(f"找到 {len(backup_files)} 個現有備份檔案")
            return backup_files
            
        except Exception as e:
            self.logger.error(f"掃描備份目錄時發生錯誤: {str(e)}")
            return []
    
    def cleanup_old_backups(self) -> Tuple[int, int]:
        """清理舊的備份檔案
        
        根據保留政策清理舊的備份檔案：
        1. 檔案數量超過 52 個時，刪除最舊的
        2. 檔案年齡超過 365 天時，刪除最舊的
        
        實作 FIFO（先進先出）邏輯。
        
        Returns:
            Tuple[int, int]: (刪除的檔案數量, 釋放的空間 MB)
        """
        try:
            # 取得現有備份檔案列表
            backup_files = self.get_existing_backups()
            
            if not backup_files:
                self.logger.info("沒有現有備份檔案需要清理")
                return 0, 0
            
            deleted_count = 0
            freed_space_mb = 0
            
            # 取得當前時間
            current_time = datetime.now()
            
            # 檢查檔案數量是否超過限制
            if len(backup_files) > self.max_backup_files:
                # 計算需要刪除的檔案數量
                excess_count = len(backup_files) - self.max_backup_files
                
                # 刪除最舊的檔案（列表最後的）
                for i in range(excess_count):
                    file_to_delete = backup_files[-(i + 1)]
                    
                    if self._delete_backup_file(file_to_delete):
                        deleted_count += 1
                        file_size_mb = file_to_delete.stat().st_size / (1024 * 1024)
                        freed_space_mb += file_size_mb
                
                self.logger.info(f"因檔案數量超限，刪除了 {excess_count} 個舊備份")
            
            # 重新取得更新後的檔案列表
            backup_files = self.get_existing_backups()
            
            # 檢查檔案年齡是否超過限制
            files_to_delete_by_age = []
            for file_path in backup_files:
                # 取得檔案修改時間
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                age_days = (current_time - file_time).days
                
                if age_days > self.max_age_days:
                    files_to_delete_by_age.append(file_path)
            
            # 刪除過期的檔案
            for file_path in files_to_delete_by_age:
                if self._delete_backup_file(file_path):
                    deleted_count += 1
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    freed_space_mb += file_size_mb
            
            if files_to_delete_by_age:
                self.logger.info(f"因檔案過期，刪除了 {len(files_to_delete_by_age)} 個備份")
            
            self.logger.info(f"清理完成：刪除 {deleted_count} 個檔案，釋放 {freed_space_mb:.2f} MB 空間")
            return deleted_count, freed_space_mb
            
        except Exception as e:
            self.logger.error(f"清理舊備份時發生錯誤: {str(e)}")
            return 0, 0
    
    def _delete_backup_file(self, file_path: Path) -> bool:
        """刪除單個備份檔案
        
        安全地刪除指定的備份檔案，並記錄相關資訊。
        
        Args:
            file_path: 要刪除的檔案路徑
            
        Returns:
            bool: True 表示刪除成功，False 表示刪除失敗
        """
        try:
            if file_path.exists():
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                file_path.unlink()
                self.logger.info(f"已刪除舊備份: {file_path.name} ({file_size_mb:.2f} MB)")
                return True
            else:
                self.logger.warning(f"要刪除的檔案不存在: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"刪除檔案 {file_path} 時發生錯誤: {str(e)}")
            return False
    
    def execute_backup(self) -> bool:
        """執行完整的備份流程
        
        按照以下順序執行備份操作：
        1. 檢查磁碟空間
        2. 清理舊備份
        3. 建立新備份
        4. 記錄結果統計
        
        Returns:
            bool: True 表示備份成功，False 表示備份失敗
        """
        try:
            self.logger.info("=" * 50)
            self.logger.info("開始執行備份服務")
            self.logger.info(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("=" * 50)
            
            # 步驟 1: 檢查磁碟空間
            self.logger.info("步驟 1: 檢查磁碟空間...")
            if not self.check_disk_space():
                self.logger.error("磁碟空間不足，備份終止")
                return False
            
            # 步驟 2: 清理舊備份
            self.logger.info("步驟 2: 清理舊備份檔案...")
            deleted_count, freed_space_mb = self.cleanup_old_backups()
            
            # 步驟 3: 建立新備份
            self.logger.info("步驟 3: 建立新的備份檔案...")
            backup_path = self.create_backup_zip()
            
            if backup_path is None:
                self.logger.error("建立備份檔案失敗")
                return False
            
            # 步驟 4: 記錄結果統計
            backup_size_mb = backup_path.stat().st_size / (1024 * 1024)
            self.logger.info("=" * 50)
            self.logger.info("備份執行完成")
            self.logger.info(f"備份檔案: {backup_path.name}")
            self.logger.info(f"備份大小: {backup_size_mb:.2f} MB")
            self.logger.info(f"清理檔案: {deleted_count} 個")
            self.logger.info(f"釋放空間: {freed_space_mb:.2f} MB")
            self.logger.info("=" * 50)
            
            return True
            
        except Exception as e:
            self.logger.error(f"執行備份流程時發生未預期的錯誤: {str(e)}")
            return False


def main():
    """主函數 - 程式進入點
    
    處理命令列參數，建立備份服務實例，
    並執行備份操作。提供適當的退出碼。
    """
    try:
        # 建立備份服務實例
        backup_service = BackupService()
        
        # 執行備份
        success = backup_service.execute_backup()
        
        # 根據結果返回適當的退出碼
        if success:
            print("✅ 備份執行成功")
            sys.exit(0)
        else:
            print("❌ 備份執行失敗")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  備份被使用者中斷")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 程式執行發生錯誤: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    """程式進入點檢查
    
    確保腳本被直接執行時才運行主要邏輯，
    避免被匯入時自動執行。
    """
    main()
