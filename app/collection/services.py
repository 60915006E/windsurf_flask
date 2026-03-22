"""
專題館服務模組

提供專題館的資料庫操作和業務邏輯
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def get_collection_config(collection_id: str = None) -> List[Dict[str, Any]]:
    """
    取得專題館設定
    
    Args:
        collection_id: 專題館 ID，None 表示取得全部
        
    Returns:
        List[Dict[str, Any]]: 專題館設定列表
    """
    try:
        from db_manager import execute_query
        
        sql = """
        SELECT COLLECTION_ID, COLLECTION_NAME, DESCRIPTION, SQL_FILTER_CONDITION,
               SCHEDULE_TYPE, SCHEDULE_INTERVAL, LAST_RUN_TIME, NEXT_RUN_TIME,
               IS_ACTIVE, AUTO_UPDATE, CREATED_DATE, UPDATED_DATE, CREATED_BY, UPDATED_BY
        FROM COLLECTION_CONFIG
        """
        
        params = {}
        if collection_id:
            sql += " WHERE COLLECTION_ID = :collection_id"
            params['collection_id'] = collection_id
        
        sql += " ORDER BY COLLECTION_NAME"
        
        results = execute_query(sql, params)
        logger.info(f"取得專題館設定成功，返回 {len(results)} 筆資料")
        
        return results
        
    except Exception as e:
        logger.error(f"取得專題館設定失敗: {str(e)}")
        raise RuntimeError(f"取得專題館設定失敗: {str(e)}")

def create_collection_config(collection_data: Dict[str, Any], created_by: str = 'SYSTEM') -> bool:
    """
    建立專題館設定
    
    Args:
        collection_data: 專題館資料
        created_by: 建立者
        
    Returns:
        bool: 是否成功
    """
    try:
        from db_manager import execute_query
        
        # 計算下次執行時間
        next_run_time = calculate_next_run_time(
            collection_data.get('schedule_type', 'DAILY'),
            collection_data.get('schedule_interval', 1)
        )
        
        sql = """
        INSERT INTO COLLECTION_CONFIG (
            COLLECTION_ID, COLLECTION_NAME, DESCRIPTION, SQL_FILTER_CONDITION,
            SCHEDULE_TYPE, SCHEDULE_INTERVAL, NEXT_RUN_TIME, IS_ACTIVE, AUTO_UPDATE,
            CREATED_DATE, UPDATED_DATE, CREATED_BY, UPDATED_BY
        ) VALUES (
            :collection_id, :collection_name, :description, :sql_filter_condition,
            :schedule_type, :schedule_interval, :next_run_time, :is_active, :auto_update,
            SYSDATE, SYSDATE, :created_by, :updated_by
        )
        """
        
        params = {
            'collection_id': collection_data['collection_id'],
            'collection_name': collection_data['collection_name'],
            'description': collection_data.get('description', ''),
            'sql_filter_condition': collection_data.get('sql_filter_condition', ''),
            'schedule_type': collection_data.get('schedule_type', 'DAILY'),
            'schedule_interval': collection_data.get('schedule_interval', 1),
            'next_run_time': next_run_time,
            'is_active': collection_data.get('is_active', 'Y'),
            'auto_update': collection_data.get('auto_update', 'Y'),
            'created_by': created_by,
            'updated_by': created_by
        }
        
        execute_query(sql, params)
        logger.info(f"專題館設定建立成功: {collection_data['collection_id']}")
        
        return True
        
    except Exception as e:
        logger.error(f"建立專題館設定失敗: {str(e)}")
        raise RuntimeError(f"建立專題館設定失敗: {str(e)}")

def update_collection_config(collection_id: str, collection_data: Dict[str, Any], updated_by: str = 'SYSTEM') -> bool:
    """
    更新專題館設定
    
    Args:
        collection_id: 專題館 ID
        collection_data: 更新資料
        updated_by: 更新者
        
    Returns:
        bool: 是否成功
    """
    try:
        from db_manager import execute_query
        
        # 重新計算下次執行時間（如果排程設定有變）
        next_run_time = None
        if 'schedule_type' in collection_data or 'schedule_interval' in collection_data:
            schedule_type = collection_data.get('schedule_type')
            schedule_interval = collection_data.get('schedule_interval')
            
            # 需要先取得現有設定
            current_config = get_collection_config(collection_id)
            if current_config:
                current_config = current_config[0]
                schedule_type = schedule_type or current_config['SCHEDULE_TYPE']
                schedule_interval = schedule_interval or current_config['SCHEDULE_INTERVAL']
                next_run_time = calculate_next_run_time(schedule_type, schedule_interval)
        
        sql = """
        UPDATE COLLECTION_CONFIG
        SET COLLECTION_NAME = :collection_name,
            DESCRIPTION = :description,
            SQL_FILTER_CONDITION = :sql_filter_condition,
            SCHEDULE_TYPE = :schedule_type,
            SCHEDULE_INTERVAL = :schedule_interval,
            IS_ACTIVE = :is_active,
            AUTO_UPDATE = :auto_update,
            UPDATED_DATE = SYSDATE,
            UPDATED_BY = :updated_by
        """
        
        params = {
            'collection_id': collection_id,
            'collection_name': collection_data.get('collection_name'),
            'description': collection_data.get('description'),
            'sql_filter_condition': collection_data.get('sql_filter_condition'),
            'schedule_type': collection_data.get('schedule_type'),
            'schedule_interval': collection_data.get('schedule_interval'),
            'is_active': collection_data.get('is_active'),
            'auto_update': collection_data.get('auto_update'),
            'updated_by': updated_by
        }
        
        # 加入下次執行時間更新
        if next_run_time:
            sql += ", NEXT_RUN_TIME = :next_run_time"
            params['next_run_time'] = next_run_time
        
        sql += " WHERE COLLECTION_ID = :collection_id"
        
        execute_query(sql, params)
        logger.info(f"專題館設定更新成功: {collection_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"更新專題館設定失敗: {str(e)}")
        raise RuntimeError(f"更新專題館設定失敗: {str(e)}")

def delete_collection_config(collection_id: str) -> bool:
    """
    刪除專題館設定
    
    Args:
        collection_id: 專題館 ID
        
    Returns:
        bool: 是否成功
    """
    try:
        from db_manager import execute_query
        
        # 先刪除所有項目
        execute_query("DELETE FROM COLLECTION_ITEMS WHERE COLLECTION_ID = :collection_id", 
                      {'collection_id': collection_id})
        
        # 再刪除設定
        execute_query("DELETE FROM COLLECTION_CONFIG WHERE COLLECTION_ID = :collection_id", 
                      {'collection_id': collection_id})
        
        logger.info(f"專題館刪除成功: {collection_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"刪除專題館失敗: {str(e)}")
        raise RuntimeError(f"刪除專題館失敗: {str(e)}")

def get_collection_items(collection_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """
    取得專題館項目
    
    Args:
        collection_id: 專題館 ID
        active_only: 是否只取啟用項目
        
    Returns:
        List[Dict[str, Any]]: 專題館項目列表
    """
    try:
        from db_manager import execute_query
        
        sql = """
        SELECT ITEM_ID, COLLECTION_ID, OVC_RP_NO, ADDED_DATE, ADDED_BY,
               ADD_TYPE, IS_ACTIVE, NOTES, CREATED_DATE, UPDATED_DATE, UPDATED_BY
        FROM COLLECTION_ITEMS
        WHERE COLLECTION_ID = :collection_id
        """
        
        params = {'collection_id': collection_id}
        
        if active_only:
            sql += " AND IS_ACTIVE = 'Y'"
        
        sql += " ORDER BY ADDED_DATE DESC"
        
        results = execute_query(sql, params)
        logger.info(f"取得專題館項目成功: {collection_id}, 返回 {len(results)} 筆資料")
        
        return results
        
    except Exception as e:
        logger.error(f"取得專題館項目失敗: {str(e)}")
        raise RuntimeError(f"取得專題館項目失敗: {str(e)}")

def add_collection_item(collection_id: str, ovc_rp_no: str, added_by: str = 'SYSTEM', 
                       add_type: str = 'MANUAL', notes: str = '') -> bool:
    """
    新增專題館項目
    
    Args:
        collection_id: 專題館 ID
        ovc_rp_no: 報告編號
        added_by: 加入者
        add_type: 加入類型 (AUTO, MANUAL)
        notes: 備註
        
    Returns:
        bool: 是否成功
    """
    try:
        from db_manager import execute_query
        
        # 檢查是否已存在
        existing = execute_query(
            "SELECT COUNT(*) as count FROM COLLECTION_ITEMS WHERE COLLECTION_ID = :collection_id AND OVC_RP_NO = :ovc_rp_no AND IS_ACTIVE = 'Y'",
            {'collection_id': collection_id, 'ovc_rp_no': ovc_rp_no}
        )
        
        if existing and existing[0]['COUNT'] > 0:
            logger.warning(f"專題館項目已存在: {collection_id}, {ovc_rp_no}")
            return False
        
        sql = """
        INSERT INTO COLLECTION_ITEMS (
            COLLECTION_ID, OVC_RP_NO, ADDED_BY, ADD_TYPE, NOTES,
            CREATED_DATE, UPDATED_DATE, UPDATED_BY
        ) VALUES (
            :collection_id, :ovc_rp_no, :added_by, :add_type, :notes,
            SYSDATE, SYSDATE, :updated_by
        )
        """
        
        params = {
            'collection_id': collection_id,
            'ovc_rp_no': ovc_rp_no,
            'added_by': added_by,
            'add_type': add_type,
            'notes': notes,
            'updated_by': added_by
        }
        
        execute_query(sql, params)
        logger.info(f"專題館項目新增成功: {collection_id}, {ovc_rp_no}")
        
        return True
        
    except Exception as e:
        logger.error(f"新增專題館項目失敗: {str(e)}")
        raise RuntimeError(f"新增專題館項目失敗: {str(e)}")

def remove_collection_item(collection_id: str, ovc_rp_no: str, updated_by: str = 'SYSTEM') -> bool:
    """
    移除專題館項目
    
    Args:
        collection_id: 專題館 ID
        ovc_rp_no: 報告編號
        updated_by: 更新者
        
    Returns:
        bool: 是否成功
    """
    try:
        from db_manager import execute_query
        
        sql = """
        UPDATE COLLECTION_ITEMS
        SET IS_ACTIVE = 'N',
            UPDATED_DATE = SYSDATE,
            UPDATED_BY = :updated_by
        WHERE COLLECTION_ID = :collection_id AND OVC_RP_NO = :ovc_rp_no
        """
        
        params = {
            'collection_id': collection_id,
            'ovc_rp_no': ovc_rp_no,
            'updated_by': updated_by
        }
        
        result = execute_query(sql, params)
        logger.info(f"專題館項目移除成功: {collection_id}, {ovc_rp_no}")
        
        return True
        
    except Exception as e:
        logger.error(f"移除專題館項目失敗: {str(e)}")
        raise RuntimeError(f"移除專題館項目失敗: {str(e)}")

def update_collection_items(collection_id: str, auto_mode: bool = False) -> Dict[str, Any]:
    """
    更新專題館項目（根據 SQL 條件查詢並增量更新）
    
    Args:
        collection_id: 專題館 ID
        auto_mode: 是否為自動模式
        
    Returns:
        Dict[str, Any]: 更新結果
    """
    try:
        from db_manager import execute_query
        from config import MAIN_TABLE_FULL, STATUS_CODE_FIELD, STATUS_OPEN_CODE
        
        # 取得專題館設定
        configs = get_collection_config(collection_id)
        if not configs:
            return {'success': False, 'error': f'找不到專題館設定: {collection_id}'}
        
        config = configs[0]
        sql_filter = config['SQL_FILTER_CONDITION']
        
        if not sql_filter:
            return {'success': False, 'error': 'SQL 篩選條件為空'}
        
        # 建立完整查詢 SQL
        query_sql = f"""
        SELECT OVC_RP_NO 
        FROM {MAIN_TABLE_FULL}
        WHERE {sql_filter}
          AND {STATUS_CODE_FIELD} = :status_code
        ORDER BY OVC_RP_NO
        """
        
        # 執行查詢取得應該包含的報告編號
        current_reports = execute_query(query_sql, {'status_code': STATUS_OPEN_CODE})
        current_rp_nos = {row['OVC_RP_NO'] for row in current_reports}
        
        # 取得現有項目
        existing_items = get_collection_items(collection_id, active_only=True)
        existing_rp_nos = {item['OVC_RP_NO'] for item in existing_items}
        
        # 計算需要新增和移除的項目
        to_add = current_rp_nos - existing_rp_nos
        to_remove = existing_rp_nos - current_rp_nos
        
        added_count = 0
        removed_count = 0
        
        # 新增項目
        for rp_no in to_add:
            try:
                add_collection_item(
                    collection_id, rp_no, 
                    added_by='SCHEDULER' if auto_mode else 'SYSTEM',
                    add_type='AUTO',
                    notes='自動更新新增'
                )
                added_count += 1
            except Exception as e:
                logger.error(f"新增專題館項目失敗: {collection_id}, {rp_no}, 錯誤: {str(e)}")
        
        # 移除項目
        for rp_no in to_remove:
            try:
                remove_collection_item(collection_id, rp_no, updated_by='SCHEDULER' if auto_mode else 'SYSTEM')
                removed_count += 1
            except Exception as e:
                logger.error(f"移除專題館項目失敗: {collection_id}, {rp_no}, 錯誤: {str(e)}")
        
        # 更新最後執行時間
        update_last_run_time(collection_id)
        
        # 重新計算下次執行時間
        next_run_time = calculate_next_run_time(config['SCHEDULE_TYPE'], config['SCHEDULE_INTERVAL'])
        update_next_run_time(collection_id, next_run_time)
        
        logger.info(f"專題館更新完成: {collection_id}, 新增 {added_count} 筆, 移除 {removed_count} 筆")
        
        return {
            'success': True,
            'added_count': added_count,
            'removed_count': removed_count,
            'total_current': len(current_rp_nos),
            'next_run_time': next_run_time
        }
        
    except Exception as e:
        logger.error(f"更新專題館項目失敗: {collection_id}, 錯誤: {str(e)}")
        return {'success': False, 'error': str(e)}

def update_last_run_time(collection_id: str) -> bool:
    """
    更新最後執行時間
    
    Args:
        collection_id: 專題館 ID
        
    Returns:
        bool: 是否成功
    """
    try:
        from db_manager import execute_query
        
        sql = "UPDATE COLLECTION_CONFIG SET LAST_RUN_TIME = SYSDATE WHERE COLLECTION_ID = :collection_id"
        execute_query(sql, {'collection_id': collection_id})
        
        return True
        
    except Exception as e:
        logger.error(f"更新最後執行時間失敗: {str(e)}")
        return False

def update_next_run_time(collection_id: str, next_run_time: datetime) -> bool:
    """
    更新下次執行時間
    
    Args:
        collection_id: 專題館 ID
        next_run_time: 下次執行時間
        
    Returns:
        bool: 是否成功
    """
    try:
        from db_manager import execute_query
        
        sql = "UPDATE COLLECTION_CONFIG SET NEXT_RUN_TIME = :next_run_time WHERE COLLECTION_ID = :collection_id"
        execute_query(sql, {'collection_id': collection_id, 'next_run_time': next_run_time})
        
        return True
        
    except Exception as e:
        logger.error(f"更新下次執行時間失敗: {str(e)}")
        return False

def calculate_next_run_time(schedule_type: str, interval: int) -> datetime:
    """
    計算下次執行時間
    
    Args:
        schedule_type: 排程類型
        interval: 間隔
        
    Returns:
        datetime: 下次執行時間
    """
    now = datetime.now()
    
    if schedule_type == 'HOURLY':
        return now + timedelta(hours=interval)
    elif schedule_type == 'DAILY':
        return now + timedelta(days=interval)
    elif schedule_type == 'WEEKLY':
        return now + timedelta(weeks=interval)
    elif schedule_type == 'MONTHLY':
        return now + timedelta(days=30 * interval)  # 簡化處理
    else:
        return now + timedelta(days=1)  # 預設一天

def get_pending_collections() -> List[Dict[str, Any]]:
    """
    取得待執行的專題館
    
    Returns:
        List[Dict[str, Any]]: 待執行專題館列表
    """
    try:
        from db_manager import execute_query
        
        sql = """
        SELECT COLLECTION_ID, COLLECTION_NAME, NEXT_RUN_TIME
        FROM COLLECTION_CONFIG
        WHERE IS_ACTIVE = 'Y' 
          AND AUTO_UPDATE = 'Y'
          AND NEXT_RUN_TIME <= SYSDATE
        ORDER BY NEXT_RUN_TIME
        """
        
        results = execute_query(sql, {})
        logger.info(f"取得待執行專題館 {len(results)} 個")
        
        return results
        
    except Exception as e:
        logger.error(f"取得待執行專題館失敗: {str(e)}")
        return []

def get_collection_status() -> List[Dict[str, Any]]:
    """
    取得所有專題館狀態
    
    Returns:
        List[Dict[str, Any]]: 專題館狀態列表
    """
    try:
        from db_manager import execute_query
        
        sql = """
        SELECT 
            cc.COLLECTION_ID,
            cc.COLLECTION_NAME,
            cc.DESCRIPTION,
            cc.SCHEDULE_TYPE,
            cc.SCHEDULE_INTERVAL,
            cc.IS_ACTIVE,
            cc.AUTO_UPDATE,
            cc.LAST_RUN_TIME,
            cc.NEXT_RUN_TIME,
            COUNT(ci.ITEM_ID) as ITEM_COUNT,
            COUNT(CASE WHEN ci.ADD_TYPE = 'AUTO' THEN 1 END) as AUTO_COUNT,
            COUNT(CASE WHEN ci.ADD_TYPE = 'MANUAL' THEN 1 END) as MANUAL_COUNT,
            CASE 
                WHEN cc.NEXT_RUN_TIME <= SYSDATE AND cc.IS_ACTIVE = 'Y' AND cc.AUTO_UPDATE = 'Y' 
                THEN 'PENDING'
                WHEN cc.IS_ACTIVE = 'Y' THEN 'ACTIVE'
                ELSE 'INACTIVE'
            END as STATUS
        FROM COLLECTION_CONFIG cc
        LEFT JOIN COLLECTION_ITEMS ci ON cc.COLLECTION_ID = ci.COLLECTION_ID AND ci.IS_ACTIVE = 'Y'
        GROUP BY 
            cc.COLLECTION_ID,
            cc.COLLECTION_NAME,
            cc.DESCRIPTION,
            cc.SCHEDULE_TYPE,
            cc.SCHEDULE_INTERVAL,
            cc.IS_ACTIVE,
            cc.AUTO_UPDATE,
            cc.LAST_RUN_TIME,
            cc.NEXT_RUN_TIME
        ORDER BY cc.COLLECTION_NAME
        """
        
        results = execute_query(sql, {})
        logger.info(f"取得專題館狀態成功，返回 {len(results)} 筆資料")
        
        return results
        
    except Exception as e:
        logger.error(f"取得專題館狀態失敗: {str(e)}")
        return []
