#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理路由模組

遵循 .windsurfrules 規範：
- 後台儀表板
- 使用者存取記錄
- 系統狀態監控
- 設定管理功能

作者：系統管理員
建立日期：2026-03-03
版本：1.0.0
"""

import os
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, session, flash, current_app, jsonify
from app.admin import bp
from app.auth.routes import require_admin_verified
from db_manager import get_connection_info, test_connection, execute_query, get_search_history, get_today_hot_searches, get_portal_links, update_portal_link

@bp.route('/dashboard')
@require_admin_verified
def dashboard():
    """
    後台儀表板
    
    顯示系統概況和統計資訊
    
    Returns:
        str: 儀表板頁面 HTML
    """
    try:
        # 取得連線資訊
        conn_info = get_connection_info()
        
        # 取得系統統計
        stats = get_system_stats()
        
        # 取得今日熱門搜尋
        try:
            hot_searches = get_today_hot_searches(limit=5)
        except Exception as e:
            current_app.logger.error(f'取得今日熱門搜尋失敗: {str(e)}')
            hot_searches = []
        
        current_app.logger.info(f'管理員 {session["username"]} 存取後台儀表板')
        
        return render_template('admin/dashboard.html', 
                             conn_info=conn_info, 
                             stats=stats,
                             hot_searches=hot_searches)
        
    except Exception as e:
        current_app.logger.error(f'載入儀表板失敗: {str(e)}')
        flash('載入儀表板失敗', 'error')
        return redirect(url_for('auth.admin_choice'))

@bp.route('/users')
@require_admin_verified
def users():
    """
    使用者管理頁面
    
    顯示使用者列表和存取記錄
    
    Returns:
        str: 使用者管理頁面 HTML
    """
    try:
        # 讀取使用者存取記錄
        access_logs = get_access_logs()
        
        current_app.logger.info(f'管理員 {session["username"]} 存取使用者管理頁面')
        
        return render_template('admin/users.html', access_logs=access_logs)
        
    except Exception as e:
        current_app.logger.error(f'載入使用者管理失敗: {str(e)}')
        flash('載入使用者管理失敗', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/logs')
@require_admin_verified
def logs():
    """
    日誌管理頁面
    
    顯示系統日誌和使用者存取記錄
    
    Returns:
        str: 日誌管理頁面 HTML
    """
    try:
        # 取得日誌檔案列表
        log_files = get_log_files()
        
        current_app.logger.info(f'管理員 {session["username"]} 存取日誌管理頁面')
        
        return render_template('admin/logs.html', log_files=log_files)
        
    except Exception as e:
        current_app.logger.error(f'載入日誌管理失敗: {str(e)}')
        flash('載入日誌管理失敗', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/view_log/<filename>')
@require_admin_verified
def view_log(filename):
    """
    查看日誌檔案內容
    
    Args:
        filename: 日誌檔案名稱
        
    Returns:
        str: 日誌內容頁面 HTML
    """
    try:
        # 安全檢查檔案名稱
        if not filename.endswith('.log') or '..' in filename:
            flash('不安全的檔案名稱', 'error')
            return redirect(url_for('admin.logs'))
        
        log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', filename)
        
        if not os.path.exists(log_path):
            flash('日誌檔案不存在', 'error')
            return redirect(url_for('admin.logs'))
        
        # 讀取日誌內容
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        current_app.logger.info(f'管理員 {session["username"]} 查看日誌檔案: {filename}')
        
        return render_template('admin/view_log.html', 
                             filename=filename, 
                             content=content)
        
    except Exception as e:
        current_app.logger.error(f'查看日誌檔案失敗: {str(e)}')
        flash('查看日誌檔案失敗', 'error')
        return redirect(url_for('admin.logs'))

@bp.route('/system')
@require_admin_verified
def system():
    """
    系統狀態頁面
    
    顯示系統資源和連線狀態
    
    Returns:
        str: 系統狀態頁面 HTML
    """
    try:
        # 取得系統資訊
        system_info = get_system_info()
        
        current_app.logger.info(f'管理員 {session["username"]} 存取系統狀態頁面')
        
        return render_template('admin/system.html', system_info=system_info)
        
    except Exception as e:
        current_app.logger.error(f'載入系統狀態失敗: {str(e)}')
        flash('載入系統狀態失敗', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/test_db')
@require_admin_verified
def test_database():
    """
    測試資料庫連線
    
    測試資料庫連線狀態並返回詳細資訊
    
    Returns:
        JSON: 測試結果
    """
    try:
        is_connected = test_connection()
        conn_info = get_connection_info()
        
        current_app.logger.info(f'管理員 {session["username"]} 測試資料庫連線')
        
        return jsonify({
            'success': True,
            'connected': is_connected,
            'connection_info': conn_info,
            'message': '資料庫連線測試完成'
        })
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'測試資料庫連線失敗: {error_message}')
        
        return jsonify({
            'success': False,
            'message': f'測試失敗: {error_message}'
        }), 500

@bp.route('/clear_sessions')
@require_admin_verified
def clear_sessions():
    """
    清除過期 Sessions
    
    清除系統中的過期 session 檔案
    
    Returns:
        JSON: 清除結果
    """
    try:
        session_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'sessions')
        cleared_count = 0
        
        if os.path.exists(session_dir):
            current_time = datetime.now()
            for filename in os.listdir(session_dir):
                if filename.startswith('flask_session_'):
                    file_path = os.path.join(session_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # 清除超過 1 小時的 session 檔案
                    if current_time - file_time > timedelta(hours=1):
                        os.remove(file_path)
                        cleared_count += 1
        
        current_app.logger.info(f'管理員 {session["username"]} 清除了 {cleared_count} 個過期 sessions')
        
        return jsonify({
            'success': True,
            'cleared_count': cleared_count,
            'message': f'清除了 {cleared_count} 個過期 sessions'
        })
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'清除 sessions 失敗: {error_message}')
        
        return jsonify({
            'success': False,
            'message': f'清除失敗: {error_message}'
        }), 500

def get_system_stats():
    """
    取得系統統計資訊
    
    Returns:
        dict: 系統統計資訊
    """
    try:
        # 這裡可以添加更多統計資訊
        stats = {
            'total_users': 0,  # 可以從資料庫取得
            'active_sessions': 0,  # 可以計算 session 檔案數量
            'total_queries': 0,  # 可以從日誌統計
            'system_uptime': 'N/A'  # 可以計算系統運行時間
        }
        
        # 計算 active sessions
        session_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'sessions')
        if os.path.exists(session_dir):
            stats['active_sessions'] = len([f for f in os.listdir(session_dir) 
                                          if f.startswith('flask_session_')])
        
        return stats
        
    except Exception as e:
        current_app.logger.error(f'取得系統統計失敗: {str(e)}')
        return {}

def get_access_logs():
    """
    取得使用者存取記錄
    
    Returns:
        list: 使用者存取記錄列表
    """
    try:
        access_log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'user_access.log')
        
        if not os.path.exists(access_log_path):
            return []
        
        logs = []
        with open(access_log_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    logs.append(line.strip())
        
        # 返回最近 100 條記錄
        return logs[-100:] if logs else []
        
    except Exception as e:
        current_app.logger.error(f'取得存取記錄失敗: {str(e)}')
        return []

def get_log_files():
    """
    取得日誌檔案列表
    
    Returns:
        list: 日誌檔案列表
    """
    try:
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        
        if not os.path.exists(log_dir):
            return []
        
        log_files = []
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                file_path = os.path.join(log_dir, filename)
                file_stat = os.stat(file_path)
                log_files.append({
                    'name': filename,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime)
                })
        
        # 按修改時間排序
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return log_files
        
    except Exception as e:
        current_app.logger.error(f'取得日誌檔案列表失敗: {str(e)}')
        return []

def get_system_info():
    """
    取得系統資訊
    
    Returns:
        dict: 系統資訊
    """
    try:
        import platform
        import psutil
        
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent
        }
        
        return system_info
        
    except ImportError:
        # 如果 psutil 未安裝，返回基本資訊
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'note': '安裝 psutil 以取得更詳細的系統資訊'
        }
    except Exception as e:
        current_app.logger.error(f'取得系統資訊失敗: {str(e)}')
        return {}

# ===========================================
# 按鈕編輯功能
# ===========================================

@bp.route('/links_editor')
@require_admin_verified
def links_editor():
    """
    按鈕編輯頁面
    
    顯示和編輯 PORTAL_LINKS 表的按鈕配置
    
    Returns:
        str: 按鈕編輯頁面 HTML
    """
    try:
        current_app.logger.info(f'管理員 {session["username"]} 存取按鈕編輯頁面')
        return render_template('admin/links_editor.html')
        
    except Exception as e:
        current_app.logger.error(f'載入按鈕編輯頁面失敗: {str(e)}')
        flash('載入按鈕編輯頁面失敗', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/add_link', methods=['POST'])
@require_admin_verified
def add_link():
    """
    新增按鈕
    
    Returns:
        JSON: 操作結果
    """
    try:
        from db_manager import execute_query
        
        # 檢查 PORTAL_LINKS 表是否存在
        create_table_sql = """
        CREATE TABLE PORTAL_LINKS (
            link_id NUMBER GENERATED ALWAYS AS IDENTITY,
            link_name VARCHAR2(100) NOT NULL,
            link_url VARCHAR2(500) NOT NULL,
            link_icon VARCHAR2(50),
            link_description VARCHAR2(200),
            link_order NUMBER DEFAULT 0,
            is_active VARCHAR2(1) DEFAULT 'Y',
            CONSTRAINT pk_portal_links PRIMARY KEY (link_id)
        )
        """
        
        try:
            execute_query(create_table_sql, db_type='system')
            current_app.logger.info('PORTAL_LINKS 表建立成功')
        except Exception as e:
            # 表可能已存在，忽略錯誤
            current_app.logger.debug(f'PORTAL_LINKS 表檢查: {str(e)}')
        
        # 插入新按鈕
        insert_sql = """
        INSERT INTO PORTAL_LINKS (link_name, link_url, link_icon, link_description, link_order, is_active)
        VALUES (:link_name, :link_url, :link_icon, :link_description, :link_order, :is_active)
        """
        
        execute_query(insert_sql, {
            'link_name': request.form.get('linkName'),
            'link_url': request.form.get('linkUrl'),
            'link_icon': request.form.get('linkIcon'),
            'link_description': request.form.get('linkDescription'),
            'link_order': int(request.form.get('linkOrder', 0)),
            'is_active': request.form.get('isActive')
        }, db_type='system')
        
        current_app.logger.info(f'管理員 {session["username"]} 新增按鈕: {request.form.get("linkName")}')
        
        return jsonify({'success': True, 'message': '按鈕新增成功'})
        
    except Exception as e:
        current_app.logger.error(f'新增按鈕失敗: {str(e)}')
        return jsonify({'success': False, 'message': f'新增按鈕失敗: {str(e)}'})

@bp.route('/update_link', methods=['POST'])
@require_admin_verified
def update_link():
    """
    更新按鈕
    
    Returns:
        JSON: 操作結果
    """
    try:
        from db_manager import execute_query
        
        # 更新按鈕
        update_sql = """
        UPDATE PORTAL_LINKS 
        SET link_name = :link_name, 
            link_url = :link_url, 
            link_icon = :link_icon, 
            link_description = :link_description, 
            link_order = :link_order, 
            is_active = :is_active
        WHERE link_id = :link_id
        """
        
        execute_query(update_sql, {
            'link_id': int(request.form.get('linkId')),
            'link_name': request.form.get('linkName'),
            'link_url': request.form.get('linkUrl'),
            'link_icon': request.form.get('linkIcon'),
            'link_description': request.form.get('linkDescription'),
            'link_order': int(request.form.get('linkOrder', 0)),
            'is_active': request.form.get('isActive')
        }, db_type='system')
        
        current_app.logger.info(f'管理員 {session["username"]} 更新按鈕: {request.form.get("linkName")}')
        
        return jsonify({'success': True, 'message': '按鈕更新成功'})
        
    except Exception as e:
        current_app.logger.error(f'更新按鈕失敗: {str(e)}')
        return jsonify({'success': False, 'message': f'更新按鈕失敗: {str(e)}'})

@bp.route('/delete_link', methods=['POST'])
@require_admin_verified
def delete_link():
    """
    刪除按鈕
    
    Returns:
        JSON: 操作結果
    """
    try:
        from db_manager import execute_query
        
        # 刪除按鈕
        delete_sql = "DELETE FROM PORTAL_LINKS WHERE link_id = :link_id"
        
        execute_query(delete_sql, {'link_id': int(request.form.get('linkId'))}, db_type='system')
        
        current_app.logger.info(f'管理員 {session["username"]} 刪除按鈕 ID: {request.form.get("linkId")}')
        
        return jsonify({'success': True, 'message': '按鈕刪除成功'})
        
    except Exception as e:
        current_app.logger.error(f'刪除按鈕失敗: {str(e)}')
        return jsonify({'success': False, 'message': f'刪除按鈕失敗: {str(e)}'})

# ===========================================
# 日誌檢視功能
# ===========================================

@bp.route('/logs_viewer')
@require_admin_verified
def logs_viewer():
    """
    日誌檢視頁面
    
    顯示 ACCESS_LOGS 表的登入記錄
    
    Returns:
        str: 日誌檢視頁面 HTML
    """
    try:
        current_app.logger.info(f'管理員 {session["username"]} 存取日誌檢視頁面')
        return render_template('admin/logs_viewer.html')
        
    except Exception as e:
        current_app.logger.error(f'載入日誌檢視頁面失敗: {str(e)}')
        flash('載入日誌檢視頁面失敗', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/get_access_logs')
@require_admin_verified
def get_access_logs():
    """
    取得登入日誌
    
    從 ACCESS_LOGS 表讀取最近 50 筆記錄
    
    Returns:
        JSON: 日誌資料
    """
    try:
        from db_manager import execute_query
        
        # 檢查 ACCESS_LOGS 表是否存在
        create_table_sql = """
        CREATE TABLE ACCESS_LOGS (
            log_id NUMBER GENERATED ALWAYS AS IDENTITY,
            username VARCHAR2(50) NOT NULL,
            action VARCHAR2(50) NOT NULL,
            ip_address VARCHAR2(45),
            access_time TIMESTAMP DEFAULT SYSDATE,
            user_agent VARCHAR2(500),
            CONSTRAINT pk_access_logs PRIMARY KEY (log_id)
        )
        """
        
        try:
            execute_query(create_table_sql, db_type='system')
            current_app.logger.info('ACCESS_LOGS 表建立成功')
        except Exception as e:
            # 表可能已存在，忽略錯誤
            current_app.logger.debug(f'ACCESS_LOGS 表檢查: {str(e)}')
        
        # 查詢最近 50 筆記錄
        logs_sql = """
        SELECT log_id, username, action, ip_address, access_time, user_agent
        FROM ACCESS_LOGS 
        ORDER BY access_time DESC
        FETCH FIRST 50 ROWS ONLY
        """
        
        logs = execute_query(logs_sql, db_type='system')
        
        current_app.logger.info(f'管理員 {session["username"]} 查詢登入日誌，共 {len(logs)} 筆記錄')
        
        return jsonify({
            'success': True,
            'data': logs,
            'count': len(logs)
        })
        
    except Exception as e:
        current_app.logger.error(f'取得登入日誌失敗: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'取得登入日誌失敗: {str(e)}'
        }), 500

# ===========================================
# 搜尋稽核管理
# ===========================================

@bp.route('/search_logs')
@require_admin_verified
def search_logs():
    """
    搜尋歷史記錄頁面
    
    顯示所有搜尋歷史記錄，支援關鍵字搜尋
    
    Returns:
        str: 搜尋歷史頁面 HTML
    """
    try:
        # 取得查詢參數
        account = request.args.get('account', '').strip()
        mode = request.args.get('mode', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        page = int(request.args.get('page', 1))
        
        # 查詢搜尋歷史
        result = get_search_history(
            account=account if account else None,
            mode=mode if mode else None,
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None,
            page=page,
            per_page=50
        )
        
        current_app.logger.info(f'管理員 {session["username"]} 查看搜尋歷史')
        
        return render_template('admin/search_logs.html',
                             search_history=result['data'],
                             pagination=result,
                             filters={
                                 'account': account,
                                 'mode': mode,
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        
    except Exception as e:
        current_app.logger.error(f'載入搜尋歷史失敗: {str(e)}')
        flash('載入搜尋歷史失敗', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/api/search_logs')
@require_admin_verified
def api_search_logs():
    """
    搜尋歷史 API
    
    提供 AJAX 查詢搜尋歷史的 API
    
    Returns:
        JSON: 搜尋歷史資料
    """
    try:
        # 取得查詢參數
        account = request.args.get('account', '').strip()
        mode = request.args.get('mode', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        page = int(request.args.get('page', 1))
        
        # 查詢搜尋歷史
        result = get_search_history(
            account=account if account else None,
            mode=mode if mode else None,
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None,
            page=page,
            per_page=50
        )
        
        return jsonify({
            'success': True,
            'data': result['data'],
            'pagination': {
                'total': result['total'],
                'page': result['page'],
                'per_page': result['per_page'],
                'total_pages': result['total_pages']
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'API 查詢搜尋歷史失敗: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'查詢失敗: {str(e)}'
        }), 500

# ===========================================
# 6 格按鈕管理
# ===========================================

@bp.route('/portal_links')
@require_admin_verified
def portal_links():
    """
    入口連結管理頁面
    
    顯示 6 格按鈕的管理介面
    
    Returns:
        str: 入口連結管理頁面 HTML
    """
    try:
        # 取得所有入口連結
        portal_links = get_portal_links(visible_only=False)
        
        current_app.logger.info(f'管理員 {session["username"]} 存取入口連結管理')
        
        return render_template('admin/portal_links.html', portal_links=portal_links)
        
    except Exception as e:
        current_app.logger.error(f'載入入口連結管理失敗: {str(e)}')
        flash('載入入口連結管理失敗', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/api/portal_links/<int:link_id>', methods=['POST'])
@require_admin_verified
def update_portal_link_api(link_id):
    """
    更新入口連結 API
    
    處理入口連結的更新請求
    
    Args:
        link_id: 連結 ID
        
    Returns:
        JSON: 更新結果
    """
    try:
        # 取得表單資料
        title = request.form.get('title', '').strip()
        icon = request.form.get('icon', '').strip()
        url = request.form.get('url', '').strip()
        description = request.form.get('description', '').strip()
        is_visible = request.form.get('is_visible', 'N')
        content_html = request.form.get('content_html', '').strip()
        
        # 驗證必要欄位
        if not title:
            return jsonify({
                'success': False,
                'message': '標題不能為空'
            }), 400
        
        # 更新連結
        success = update_portal_link(
            link_id=link_id,
            title=title,
            icon=icon,
            url=url,
            description=description,
            is_visible=is_visible,
            content_html=content_html
        )
        
        if success:
            current_app.logger.info(f'管理員 {session["username"]} 更新入口連結: ID={link_id}')
            return jsonify({
                'success': True,
                'message': '連結更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '連結更新失敗'
            }), 500
        
    except Exception as e:
        current_app.logger.error(f'更新入口連結失敗: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新失敗: {str(e)}'
        }), 500
