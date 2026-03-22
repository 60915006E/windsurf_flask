#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
認證路由模組

遵循 .windsurfrules 規範：
- 登入頁面路由
- Session 機制實作
- 使用者存取記錄
- 管理員轉向邏輯

作者：系統管理員
建立日期：2026-03-03
版本：1.0.0
"""

from datetime import datetime
from flask import render_template, request, redirect, url_for, session, flash, current_app, jsonify
from app.auth import bp

# 管理員帳號 (測試期僅使用 admin)
ADMIN_USER = 'admin'

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    登入路由
    
    處理使用者登入請求：
    - GET: 顯示登入頁面
    - POST: 處理登入表入表單，驗證使用者並分流
    
    Returns:
        str: 登入頁面 HTML 或重定向
    """
    # 如果已登入，重定向到首頁
    if 'username' in session:
        return redirect(url_for('search.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        
        # 基本驗證 - 測試階段僅需輸入帳號
        if not username:
            flash('請輸入帳號', 'error')
            return render_template('auth/login.html')
        
        # 記錄登入嘗試
        current_app.logger.info(f'登入嘗試: {username} from {request.remote_addr}')
        
        # 測試期：直接接受任何帳號
        # 設定 Session
        session['username'] = username
        session['login_time'] = datetime.now()
        session['is_admin'] = (username == ADMIN_USER)
        session.permanent = True
        
        # 記錄登入成功到 ACCESS_LOGS 表
        log_access_to_db(username, 'login_success', request.remote_addr)
        
        # 管理員分流
        if username == ADMIN_USER:
            current_app.logger.info(f'管理員 {username} 登入成功')
            flash('登入成功！您是管理員', 'success')
            return redirect(url_for('auth.choice'))
        else:
            current_app.logger.info(f'一般使用者 {username} 登入成功')
            flash('登入成功！', 'success')
            return redirect(url_for('search.index'))
    
    return render_template('auth/login.html')

def log_access_to_db(username, action, ip_address):
    """
    記錄使用者存取到 SYSTEM_DB 的 ACCESS_LOGS 表
    
    Args:
        username: 使用者名稱
        action: 操作類型
        ip_address: IP 位址
    """
    try:
        from db_manager import execute_query
        
        # 檢查 ACCESS_LOGS 表是否存在，若不存在則建立
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
        
        # 插入存取記錄
        insert_sql = """
        INSERT INTO ACCESS_LOGS (username, action, ip_address, user_agent)
        VALUES (:username, :action, :ip_address, :user_agent)
        """
        
        # 取得 User-Agent
        user_agent = getattr(request, 'user_agent', None)
        user_agent_str = user_agent.string if user_agent else 'Unknown'
        
        execute_query(insert_sql, {
            'username': username,
            'action': action,
            'ip_address': ip_address,
            'user_agent': user_agent_str
        }, db_type='system')
        
        current_app.logger.info(f'使用者存取記錄已寫入 ACCESS_LOGS: {username} - {action}')
        
    except Exception as e:
        current_app.logger.error(f'寫入 ACCESS_LOGS 失敗: {str(e)}')
        # 即使資料庫寫入失敗，仍繼續處理

@bp.route('/choice')
def choice():
    """
    管理員選擇頁面
    
    讓管理員選擇進入一般模式或系統管理
    
    Returns:
        str: 管理員選擇頁面 HTML
    """
    # 檢查是否為管理員
    if 'username' not in session or not session.get('is_admin', False):
        flash('您沒有權限存取此頁面', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/choice.html')

@bp.route('/admin_choice')
def admin_choice():
    """
    管理員選擇頁面
    
    讓管理員選擇進入主畫面或後台管理
    
    Returns:
        str: 管理員選擇頁面 HTML
    """
    # 檢查是否為管理員
    if 'username' not in session or not session.get('is_admin', False):
        flash('您沒有權限存取此頁面', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/admin_choice.html')

@bp.route('/admin_verify', methods=['POST'])
def admin_verify():
    """
    管理員後台驗證
    
    驗證儲存在 SYSTEM_DB 的管理員密碼
    
    Returns:
        JSON: 驗證結果
    """
    # 檢查是否為管理員
    if 'username' not in session or not session.get('is_admin', False):
        return jsonify({'success': False, 'message': '沒有管理員權限'})
    
    password = request.form.get('password', '').strip()
    
    if not password:
        return jsonify({'success': False, 'message': '請輸入驗證密碼'})
    
    try:
        from db_manager import execute_query
        
        # 查詢管理員密碼 (從 SYSTEM_DB)
        admin_sql = """
        SELECT admin_password 
        FROM ADMIN_CONFIG 
        WHERE admin_username = :username AND status = 'ACTIVE'
        """
        
        admins = execute_query(admin_sql, {'username': session['username']}, db_type='system')
        
        if not admins:
            # 測試期：使用預設密碼
            test_password = 'admin123'
            if password == test_password:
                session['admin_verified'] = True
                session['admin_verify_time'] = datetime.now()
                
                # 記錄後台存取
                log_access_to_db(session['username'], 'admin_access', request.remote_addr)
                
                current_app.logger.info(f'管理員 {session["username"]} 後台驗證成功')
                return jsonify({'success': True, 'redirect': url_for('admin.dashboard')})
            else:
                return jsonify({'success': False, 'message': '驗證密碼錯誤'})
        else:
            admin = admins[0]
            stored_password = admin.get('ADMIN_PASSWORD', '')
            
            # 實際環境應該使用密碼雜湊比較
            if password == stored_password:  # 簡化比較，實際應使用 bcrypt
                session['admin_verified'] = True
                session['admin_verify_time'] = datetime.now()
                
                # 記錄後台存取
                log_access_to_db(session['username'], 'admin_access', request.remote_addr)
                
                current_app.logger.info(f'管理員 {session["username"]} 後台驗證成功')
                return jsonify({'success': True, 'redirect': url_for('admin.dashboard')})
            else:
                current_app.logger.warning(f'管理員 {session["username"]} 後台驗證失敗')
                return jsonify({'success': False, 'message': '驗證密碼錯誤'})
                
    except Exception as e:
        current_app.logger.error(f'管理員驗證失敗: {str(e)}')
        return jsonify({'success': False, 'message': '驗證過程發生錯誤'})

@bp.route('/get_portal_links')
def get_portal_links():
    """
    取得入口連結配置
    
    從 SYSTEM_DB 的 PORTAL_LINKS 表讀取連結配置
    
    Returns:
        JSON: 連結配置資訊
    """
    try:
        from db_manager import execute_query
        
        # 檢查 PORTAL_LINKS 表是否存在，若不存在則建立
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
        
        # 查詢連結配置
        links_sql = """
        SELECT link_id, link_name, link_url, link_icon, link_description, link_order, is_active
        FROM PORTAL_LINKS 
        WHERE is_active = 'Y'
        ORDER BY link_order
        """
        
        links = execute_query(links_sql, db_type='system')
        
        current_app.logger.info(f'取得 {len(links)} 個入口連結配置')
        
        return jsonify({
            'success': True,
            'data': links,
            'count': len(links)
        })
        
    except Exception as e:
        current_app.logger.error(f'取得連結配置失敗: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'取得連結配置失敗: {str(e)}'
        }), 500

@bp.route('/logout')
def logout():
    """
    登出路由
    
    清除 session 並重定向到登入頁面
    
    Returns:
        str: 重定向到登入頁面
    """
    username = session.get('username', 'unknown')
    
    # 記錄登出
    log_user_access(username, 'logout', request.remote_addr)
    current_app.logger.info(f'使用者 {username} 登出')
    
    # 清除 session
    session.clear()
    
    flash('已成功登出', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/check_session')
def check_session():
    """
    檢查 Session 狀態
    
    檢查使用者是否仍在登入狀態
    
    Returns:
        JSON: Session 狀態資訊
    """
    if 'username' not in session:
        return jsonify({
            'logged_in': False,
            'message': '未登入'
        })
    
    # 檢查 session 是否過期
    login_time = session.get('login_time')
    if login_time:
        # 計算登入時間
        elapsed = datetime.now() - login_time
        if elapsed.total_seconds() > 1800:  # 30 分鐘
            session.clear()
            return jsonify({
                'logged_in': False,
                'message': 'Session 已過期，請重新登入'
            })
    
    return jsonify({
        'logged_in': True,
        'username': session['username'],
        'is_admin': session.get('is_admin', False),
        'login_time': session['login_time'].strftime('%Y-%m-%d %H:%M:%S') if session.get('login_time') else None
    })

def log_user_access(username, action, ip_address):
    """
    記錄使用者存取日誌到 SYSTEM_DB 的 SYS_LOGS 表
    
    Args:
        username: 使用者名稱
        action: 操作類型 (login_success, login_failed, logout, admin_access)
        ip_address: IP 位址
    """
    try:
        # 記錄到檔案日誌
        log_message = f"使用者: {username} | 操作: {action} | IP: {ip_address} | 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        current_app.access_logger.info(log_message)
        
        # 記錄到 SYSTEM_DB 的 SYS_LOGS 表
        try:
            from db_manager import execute_query
            
            # 插入日誌記錄
            log_sql = """
            INSERT INTO SYS_LOGS (log_id, username, action, ip_address, log_time, user_agent)
            VALUES (SYS_LOGS_SEQ.NEXTVAL, :username, :action, :ip_address, SYSDATE, :user_agent)
            """
            
            # 取得 User-Agent (如果有的話)
            from flask import request
            user_agent = getattr(request, 'user_agent', None)
            user_agent_str = user_agent.string if user_agent else 'Unknown'
            
            execute_query(log_sql, {
                'username': username,
                'action': action,
                'ip_address': ip_address,
                'user_agent': user_agent_str
            }, db_type='system')
            
            current_app.logger.info(f'使用者存取記錄已寫入 SYS_LOGS: {username} - {action}')
            
        except Exception as db_error:
            current_app.logger.error(f'寫入 SYS_LOGS 失敗: {str(db_error)}')
            # 即使資料庫寫入失敗，檔案日誌已經記錄了
            
    except Exception as e:
        current_app.logger.error(f'記錄使用者存取日誌失敗: {str(e)}')

def require_login(f):
    """
    登入裝飾器
    
    確保使用者已登入，檢查 Session 是否超過 30 分鐘
    
    Args:
        f: 被裝飾的函數
        
    Returns:
        function: 裝飾後的函數
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 檢查是否已登入
        if 'username' not in session:
            flash('請先登入', 'warning')
            return redirect(url_for('auth.login'))
        
        # 檢查 session 是否過期 (30 分鐘)
        login_time = session.get('login_time')
        if login_time:
            elapsed = datetime.now() - login_time
            if elapsed.total_seconds() > 1800:  # 30 分鐘
                session.clear()
                flash('Session 已過期，請重新登入', 'warning')
                return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """
    管理員權限裝飾器
    
    確保使用者為管理員
    
    Args:
        f: 被裝飾的函數
        
    Returns:
        function: 裝飾後的函數
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 檢查是否已登入
        if 'username' not in session:
            flash('請先登入', 'warning')
            return redirect(url_for('auth.login'))
        
        # 檢查是否為管理員
        if not session.get('is_admin', False):
            flash('您沒有管理員權限', 'error')
            return redirect(url_for('auth.login'))
        
        # 檢查 session 是否過期 (30 分鐘)
        login_time = session.get('login_time')
        if login_time:
            elapsed = datetime.now() - login_time
            if elapsed.total_seconds() > 1800:  # 30 分鐘
                session.clear()
                flash('Session 已過期，請重新登入', 'warning')
                return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin_verified(f):
    """
    管理員權限裝飾器
    
    確保使用者為管理員且已通過二次驗證
    
    Args:
        f: 被裝飾的函數
        
    Returns:
        function: 裝飾後的函數
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 檢查是否已登入
        if 'username' not in session:
            flash('請先登入', 'warning')
            return redirect(url_for('auth.login'))
        
        # 檢查是否為管理員
        if not session.get('is_admin', False):
            flash('您沒有管理員權限', 'error')
            return redirect(url_for('auth.login'))
        
        # 檢查是否已通過二次驗證
        if not session.get('admin_verified', False):
            flash('需要管理員二次驗證', 'error')
            return redirect(url_for('auth.choice'))
        
        # 檢查 session 是否過期 (30 分鐘)
        login_time = session.get('login_time')
        if login_time:
            elapsed = datetime.now() - login_time
            if elapsed.total_seconds() > 1800:  # 30 分鐘
                session.clear()
                flash('Session 已過期，請重新登入', 'warning')
                return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function
