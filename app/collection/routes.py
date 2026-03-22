"""
專題館路由模組

提供專題館的前台顯示和後台管理功能
"""

from flask import render_template, request, redirect, url_for, session, flash, current_app, jsonify
from app.collection import bp
from app.auth.routes import require_login
from app.collection.services import (
    get_collection_config, create_collection_config, update_collection_config, delete_collection_config,
    get_collection_items, add_collection_item, remove_collection_item, update_collection_items,
    get_collection_status, get_pending_collections
)
from db_manager import search_reports_dynamic, get_dynamic_field_list
import logging

logger = logging.getLogger(__name__)

# ===========================================
# 前台顯示功能
# ===========================================

@bp.route('/<collection_id>')
@require_login
def view_collection(collection_id):
    """
    專題館顯示頁面
    
    Args:
        collection_id: 專題館 ID
        
    Returns:
        str: 專題館頁面 HTML
    """
    try:
        # 記錄存取
        current_app.logger.info(f'使用者 {session["username"]} 存取專題館: {collection_id}')
        
        # 取得專題館設定
        configs = get_collection_config(collection_id)
        if not configs:
            flash('找不到指定的專題館', 'error')
            return redirect(url_for('search.index'))
        
        config = configs[0]
        
        # 檢查是否啟用
        if config['IS_ACTIVE'] != 'Y':
            flash('此專題館目前未啟用', 'warning')
            return redirect(url_for('search.index'))
        
        # 取得專題館項目
        items = get_collection_items(collection_id, active_only=True)
        
        if not items:
            flash('此專題館目前沒有項目', 'info')
            return render_template('collection/view.html', 
                                 config=config, 
                                 items=[],
                                 field_settings=[],
                                 results=[])
        
        # 取得報告編號列表
        rp_nos = [item['OVC_RP_NO'] for item in items]
        
        # 建立搜尋條件（使用 IN 查詢）
        if len(rp_nos) == 1:
            conditions = [{'field': 'rp_no', 'operator': '等於', 'value': rp_nos[0]}]
        else:
            # 多個報告編號，使用多個 OR 條件
            conditions = []
            for i, rp_no in enumerate(rp_nos):
                condition = {'field': 'rp_no', 'operator': '等於', 'value': rp_no}
                if i > 0:
                    condition['connector'] = 'OR'
                conditions.append(condition)
        
        # 執行搜尋
        try:
            results = search_reports_dynamic(conditions, limit=1000, show_type='list')
            current_app.logger.info(f'專題館搜尋成功: {collection_id}, 返回 {len(results)} 筆資料')
        except Exception as search_error:
            current_app.logger.error(f'專題館搜尋失敗: {collection_id}, 錯誤: {search_error}')
            flash('搜尋專題館資料失敗', 'error')
            results = []
        
        # 取得動態欄位設定
        try:
            field_settings = get_dynamic_field_list('list')
        except Exception as field_error:
            current_app.logger.error(f'取得欄位設定失敗: {field_error}')
            # 使用預設欄位
            field_settings = [
                {'field_id': 'CAT_NAME', 'display_name': '性質', 'field_type': 'TEXT'},
                {'field_id': 'TYPE_NAME', 'display_name': '分類', 'field_type': 'TEXT'},
                {'field_id': 'CSI_NAME', 'display_name': '報告主號', 'field_type': 'TEXT'},
                {'field_id': 'SECERT_LV_NAME', 'display_name': '機密等級', 'field_type': 'TEXT'},
                {'field_id': 'MAIN_AUTHOR', 'display_name': '主要作者', 'field_type': 'TEXT'}
            ]
        
        return render_template('collection/view.html', 
                             config=config, 
                             items=items,
                             field_settings=field_settings,
                             results=results)
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'專題館顯示失敗: {error_message}')
        flash('專題館載入失敗', 'error')
        return redirect(url_for('search.index'))

@bp.route('/list')
@require_login
def list_collections():
    """
    專題館列表頁面
    
    Returns:
        str: 專題館列表頁面 HTML
    """
    try:
        # 取得所有專題館狀態
        collections = get_collection_status()
        
        return render_template('collection/list.html', collections=collections)
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'專題館列表失敗: {error_message}')
        flash('專題館列表載入失敗', 'error')
        return redirect(url_for('search.index'))

# ===========================================
# 後台管理功能
# ===========================================

@bp.route('/admin')
@require_login
def admin():
    """
    專題館管理首頁
    
    Returns:
        str: 管理頁面 HTML
    """
    try:
        # 取得所有專題館狀態
        collections = get_collection_status()
        
        return render_template('collection/admin.html', collections=collections)
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'專題館管理頁面失敗: {error_message}')
        flash('管理頁面載入失敗', 'error')
        return redirect(url_for('search.index'))

@bp.route('/admin/create', methods=['GET', 'POST'])
@require_login
def create_collection():
    """
    建立專題館
    
    Returns:
        str: 建立頁面 HTML 或重定向
    """
    if request.method == 'GET':
        return render_template('collection/form.html', action='create', collection=None)
    
    try:
        # 取得表單資料
        collection_data = {
            'collection_id': request.form.get('collection_id', '').strip().upper(),
            'collection_name': request.form.get('collection_name', '').strip(),
            'description': request.form.get('description', '').strip(),
            'sql_filter_condition': request.form.get('sql_filter_condition', '').strip(),
            'schedule_type': request.form.get('schedule_type', 'DAILY'),
            'schedule_interval': int(request.form.get('schedule_interval', 1)),
            'is_active': 'Y' if request.form.get('is_active') else 'N',
            'auto_update': 'Y' if request.form.get('auto_update') else 'N'
        }
        
        # 驗證必要欄位
        if not collection_data['collection_id'] or not collection_data['collection_name']:
            flash('專題館 ID 和名稱為必填欄位', 'error')
            return render_template('collection/form.html', action='create', collection=None)
        
        # 建立專題館
        create_collection_config(collection_data, session.get('username', 'SYSTEM'))
        
        flash('專題館建立成功', 'success')
        return redirect(url_for('collection.admin'))
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'建立專題館失敗: {error_message}')
        flash(f'建立專題館失敗: {error_message}', 'error')
        return render_template('collection/form.html', action='create', collection=None)

@bp.route('/admin/edit/<collection_id>', methods=['GET', 'POST'])
@require_login
def edit_collection(collection_id):
    """
    編輯專題館
    
    Args:
        collection_id: 專題館 ID
        
    Returns:
        str: 編輯頁面 HTML 或重定向
    """
    if request.method == 'GET':
        try:
            configs = get_collection_config(collection_id)
            if not configs:
                flash('找不到指定的專題館', 'error')
                return redirect(url_for('collection.admin'))
            
            return render_template('collection/form.html', action='edit', collection=configs[0])
            
        except Exception as e:
            error_message = str(e)
            current_app.logger.error(f'載入專題館編輯頁面失敗: {error_message}')
            flash('載入編輯頁面失敗', 'error')
            return redirect(url_for('collection.admin'))
    
    try:
        # 取得表單資料
        collection_data = {
            'collection_name': request.form.get('collection_name', '').strip(),
            'description': request.form.get('description', '').strip(),
            'sql_filter_condition': request.form.get('sql_filter_condition', '').strip(),
            'schedule_type': request.form.get('schedule_type', 'DAILY'),
            'schedule_interval': int(request.form.get('schedule_interval', 1)),
            'is_active': 'Y' if request.form.get('is_active') else 'N',
            'auto_update': 'Y' if request.form.get('auto_update') else 'N'
        }
        
        # 驗證必要欄位
        if not collection_data['collection_name']:
            flash('專題館名稱為必填欄位', 'error')
            return render_template('collection/form.html', action='edit', collection=None)
        
        # 更新專題館
        update_collection_config(collection_id, collection_data, session.get('username', 'SYSTEM'))
        
        flash('專題館更新成功', 'success')
        return redirect(url_for('collection.admin'))
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'更新專題館失敗: {error_message}')
        flash(f'更新專題館失敗: {error_message}', 'error')
        return redirect(url_for('collection.admin'))

@bp.route('/admin/delete/<collection_id>', methods=['POST'])
@require_login
def delete_collection(collection_id):
    """
    刪除專題館
    
    Args:
        collection_id: 專題館 ID
        
    Returns:
        redirect: 重定向到管理頁面
    """
    try:
        delete_collection_config(collection_id)
        flash('專題館刪除成功', 'success')
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'刪除專題館失敗: {error_message}')
        flash(f'刪除專題館失敗: {error_message}', 'error')
    
    return redirect(url_for('collection.admin'))

@bp.route('/admin/items/<collection_id>')
@require_login
def manage_items(collection_id):
    """
    管理專題館項目
    
    Args:
        collection_id: 專題館 ID
        
    Returns:
        str: 項目管理頁面 HTML
    """
    try:
        # 取得專題館設定
        configs = get_collection_config(collection_id)
        if not configs:
            flash('找不到指定的專題館', 'error')
            return redirect(url_for('collection.admin'))
        
        config = configs[0]
        
        # 取得專題館項目
        items = get_collection_items(collection_id, active_only=False)
        
        return render_template('collection/items.html', config=config, items=items)
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'載入專題館項目管理失敗: {error_message}')
        flash('載入項目管理失敗', 'error')
        return redirect(url_for('collection.admin'))

@bp.route('/admin/add_item', methods=['POST'])
@require_login
def add_item():
    """
    新增專題館項目（手動微調）
    
    Returns:
        JSON: 操作結果
    """
    try:
        collection_id = request.form.get('collection_id', '').strip()
        ovc_rp_no = request.form.get('ovc_rp_no', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not collection_id or not ovc_rp_no:
            return jsonify({'success': False, 'message': '專題館 ID 和報告編號為必填欄位'})
        
        # 新增項目
        success = add_collection_item(
            collection_id, ovc_rp_no, 
            added_by=session.get('username', 'SYSTEM'),
            add_type='MANUAL',
            notes=notes
        )
        
        if success:
            return jsonify({'success': True, 'message': '項目新增成功'})
        else:
            return jsonify({'success': False, 'message': '項目已存在或新增失敗'})
            
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'新增專題館項目失敗: {error_message}')
        return jsonify({'success': False, 'message': f'新增失敗: {error_message}'})

@bp.route('/admin/remove_item', methods=['POST'])
@require_login
def remove_item():
    """
    移除專題館項目
    
    Returns:
        JSON: 操作結果
    """
    try:
        collection_id = request.form.get('collection_id', '').strip()
        ovc_rp_no = request.form.get('ovc_rp_no', '').strip()
        
        if not collection_id or not ovc_rp_no:
            return jsonify({'success': False, 'message': '專題館 ID 和報告編號為必填欄位'})
        
        # 移除項目
        success = remove_collection_item(collection_id, ovc_rp_no, session.get('username', 'SYSTEM'))
        
        if success:
            return jsonify({'success': True, 'message': '項目移除成功'})
        else:
            return jsonify({'success': False, 'message': '項目移除失敗'})
            
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'移除專題館項目失敗: {error_message}')
        return jsonify({'success': False, 'message': f'移除失敗: {error_message}'})

@bp.route('/admin/update_now', methods=['POST'])
@require_login
def update_now():
    """
    立即更新專題館
    
    Returns:
        JSON: 操作結果
    """
    try:
        collection_id = request.form.get('collection_id', '').strip()
        
        if not collection_id:
            return jsonify({'success': False, 'message': '專題館 ID 為必填欄位'})
        
        # 執行更新
        result = update_collection_items(collection_id, auto_mode=False)
        
        if result['success']:
            return jsonify({
                'success': True, 
                'message': f'更新成功，新增 {result["added_count"]} 筆，移除 {result["removed_count"]} 筆'
            })
        else:
            return jsonify({'success': False, 'message': f'更新失敗: {result["error"]}'})
            
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'立即更新專題館失敗: {error_message}')
        return jsonify({'success': False, 'message': f'更新失敗: {error_message}'})

@bp.route('/admin/status')
@require_login
def status():
    """
    專題館狀態 API
    
    Returns:
        JSON: 專題館狀態資訊
    """
    try:
        collections = get_collection_status()
        pending = get_pending_collections()
        
        return jsonify({
            'success': True,
            'collections': collections,
            'pending_count': len(pending),
            'pending_collections': pending
        })
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'取得專題館狀態失敗: {error_message}')
        return jsonify({'success': False, 'message': f'取得狀態失敗: {error_message}'})
