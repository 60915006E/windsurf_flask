"""
動態主題館排程管理模組

整合 Flask-APScheduler 實作自動排程功能
"""

from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging

# 全域排程器實例
scheduler = None

def init_scheduler(app):
    """
    初始化排程器
    
    Args:
        app: Flask 應用實例
    """
    global scheduler
    
    if scheduler is None:
        scheduler = BackgroundScheduler()
        scheduler.start()
        app.logger.info("排程器啟動成功")
    
    # 註冊關閉處理
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        global scheduler
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)
            app.logger.info("排程器已關閉")

def add_collection_job(collection_id, schedule_type, interval=1):
    """
    新增專題館排程任務
    
    Args:
        collection_id: 專題館 ID
        schedule_type: 排程類型 (HOURLY, DAILY, WEEKLY, MONTHLY)
        interval: 間隔數字
    """
    global scheduler
    
    if not scheduler:
        raise RuntimeError("排程器尚未初始化")
    
    # 移除現有任務
    remove_collection_job(collection_id)
    
    # 建立新的觸發器
    trigger = None
    job_id = f"collection_{collection_id}"
    
    if schedule_type == 'HOURLY':
        trigger = IntervalTrigger(hours=interval)
    elif schedule_type == 'DAILY':
        trigger = IntervalTrigger(days=interval)
    elif schedule_type == 'WEEKLY':
        trigger = IntervalTrigger(weeks=interval)
    elif schedule_type == 'MONTHLY':
        trigger = IntervalTrigger(days=30 * interval)  # 簡化處理
    else:
        raise ValueError(f"不支援的排程類型: {schedule_type}")
    
    # 新增任務
    scheduler.add_job(
        func=run_collection_update,
        trigger=trigger,
        id=job_id,
        args=[collection_id],
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300  # 5分鐘寬限期
    )
    
    current_app.logger.info(f"已新增專題館排程任務: {job_id} ({schedule_type}, interval={interval})")

def remove_collection_job(collection_id):
    """
    移除專題館排程任務
    
    Args:
        collection_id: 專題館 ID
    """
    global scheduler
    
    if scheduler:
        job_id = f"collection_{collection_id}"
        try:
            scheduler.remove_job(job_id)
            current_app.logger.info(f"已移除專題館排程任務: {job_id}")
        except:
            pass  # 任務不存在時忽略

def run_collection_update(collection_id):
    """
    執行專題館更新任務
    
    Args:
        collection_id: 專題館 ID
    """
    try:
        current_app.logger.info(f"開始執行專題館更新任務: {collection_id}")
        
        # 導入必要的模組
        from app.collection.services import update_collection_items
        
        # 執行更新
        result = update_collection_items(collection_id, auto_mode=True)
        
        if result['success']:
            current_app.logger.info(f"專題館更新成功: {collection_id}, 新增 {result['added_count']} 筆, 移除 {result['removed_count']} 筆")
        else:
            current_app.logger.error(f"專題館更新失敗: {collection_id}, 錯誤: {result['error']}")
            
    except Exception as e:
        current_app.logger.error(f"專題館更新任務執行失敗: {collection_id}, 錯誤: {str(e)}")

def get_scheduler_status():
    """
    取得排程器狀態
    
    Returns:
        dict: 排程器狀態資訊
    """
    global scheduler
    
    if not scheduler:
        return {
            'running': False,
            'jobs': [],
            'message': '排程器尚未初始化'
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })
    
    return {
        'running': scheduler.running,
        'jobs': jobs,
        'job_count': len(jobs)
    }

def restart_scheduler():
    """
    重新啟動排程器
    
    Returns:
        bool: 是否成功
    """
    global scheduler
    
    try:
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)
        
        scheduler = BackgroundScheduler()
        scheduler.start()
        
        current_app.logger.info("排程器重新啟動成功")
        return True
        
    except Exception as e:
        current_app.logger.error(f"排程器重新啟動失敗: {str(e)}")
        return False
