#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜尋路由模組

遵循 .windsurfrules 規範：
- 主搜尋頁面
- 進階搜尋功能
- 查詢結果處理
- 錯誤處理機制

作者：系統管理員
建立日期：2026-03-03
版本：1.0.0
"""

from flask import render_template, request, redirect, url_for, session, flash, current_app, jsonify, send_from_directory
from app.search import bp
from app.auth.routes import require_login
from db_manager import execute_query, test_connection, execute_paginated_query, log_search_history, get_portal_links, get_portal_link, increment_detail_view, get_popular_books, get_newest_books
from werkzeug.utils import secure_filename
import os
import json
import time
from config import FILE_STORAGE_PATH, ALLOWED_EXTENSIONS

@bp.route('/')
@require_login
def index():
    """
    主頁面路由
    
    顯示搜尋頁面，需要登入
    
    Returns:
        str: 主頁面 HTML
    """
    try:
        # 取得可見的入口連結
        portal_links = get_portal_links(visible_only=True)
        
        # 取得熱門書目
        try:
            popular_books = get_popular_books(limit=10)
        except Exception as e:
            current_app.logger.error(f'取得熱門書目失敗: {str(e)}')
            popular_books = []
        
        # 取得最新書目
        try:
            newest_books = get_newest_books(limit=10)
        except Exception as e:
            current_app.logger.error(f'取得最新書目失敗: {str(e)}')
            newest_books = []
        
        current_app.logger.info(f'使用者 {session["username"]} 存取主頁面')
        
        return render_template('search/index.html', 
                             portal_links=portal_links,
                             popular_books=popular_books,
                             newest_books=newest_books)
        
    except Exception as e:
        current_app.logger.error(f'載入主頁面失敗: {str(e)}')
        flash('載入主頁面失敗', 'error')
        return redirect(url_for('auth.choice'))

@bp.route('/advanced')
@require_login
def advanced():
    """
    進階搜尋頁面
    
    顯示進階搜尋選項
    
    Returns:
        str: 進階搜尋頁面 HTML
    """
    return render_template('search/advanced.html')

@bp.route('/results')
@require_login
def results():
    """
    搜尋結果頁面
    
    處理快速搜尋和進階搜尋的結果顯示
    
    Returns:
        str: 搜尋結果頁面 HTML
    """
    try:
        # 記錄存取
        current_app.logger.info(f'使用者 {session["username"]} 存取搜尋結果頁面')
        
        # 取得搜尋參數
        search_params = request.args.to_dict()
        
        # 建立搜尋條件
        conditions = []
        
        # 處理快速搜尋 (q 參數)
        if search_params.get('q'):
            keyword = search_params.get('q').strip()
            if keyword:
                conditions.append({
                    'field': 'title',
                    'operator': '包含',
                    'value': keyword
                })
                conditions.append({
                    'field': 'summary', 
                    'operator': '包含',
                    'value': keyword,
                    'connector': 'OR'
                })
        
        # 處理進階搜尋參數
        if search_params.get('keyword'):
            keyword = search_params.get('keyword').strip()
            if keyword:
                conditions.append({
                    'field': 'title',
                    'operator': '包含',
                    'value': keyword
                })
                conditions.append({
                    'field': 'summary',
                    'operator': '包含', 
                    'value': keyword,
                    'connector': 'OR'
                })
        
        if search_params.get('category'):
            conditions.append({
                'field': 'type',
                'operator': '等於',
                'value': search_params.get('category')
            })
        
        if search_params.get('csiName'):
            conditions.append({
                'field': 'csi_name',
                'operator': '包含',
                'value': search_params.get('csiName')
            })
        
        if search_params.get('author'):
            conditions.append({
                'field': 'main_author',
                'operator': '包含',
                'value': search_params.get('author')
            })
        
        if search_params.get('securityLevel'):
            conditions.append({
                'field': 'security_level',
                'operator': '等於',
                'value': search_params.get('securityLevel')
            })
        
        if search_params.get('trainType'):
            conditions.append({
                'field': 'train_type',
                'operator': '等於',
                'value': search_params.get('trainType')
            })
        
        # 處理日期區間
        if search_params.get('dateFrom'):
            conditions.append({
                'field': 'public_date',
                'operator': '大於等於',
                'value': search_params.get('dateFrom')
            })
        
        if search_params.get('dateTo'):
            conditions.append({
                'field': 'public_date',
                'operator': '小於等於',
                'value': search_params.get('dateTo')
            })
        
        # 執行搜尋
        results = []
        if conditions:
            try:
                from db_manager import search_reports_dynamic
                results = search_reports_dynamic(conditions, limit=100, show_type='list')
                current_app.logger.info(f'搜尋成功，返回 {len(results)} 筆資料')
            except Exception as search_error:
                current_app.logger.error(f'搜尋失敗: {search_error}')
                flash('搜尋失敗，請稍後再試', 'error')
        
        # 取得動態欄位設定
        try:
            from db_manager import get_dynamic_field_list
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
        
        return render_template('search/results.html', 
                             results=results,
                             field_settings=field_settings,
                             search_params=search_params)
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'搜尋結果頁面失敗: {error_message}')
        flash('搜尋結果頁面載入失敗', 'error')
        return redirect(url_for('search.index'))

@bp.route('/export_excel', methods=['POST'])
@require_login
def export_excel():
    """
    匯出 Excel 功能
    
    接收搜尋條件，生成 Excel 檔案並回傳下載
    
    Returns:
        Response: Excel 檔案下載
    """
    try:
        # 記錄存取
        current_app.logger.info(f'使用者 {session["username"]} 請求匯出 Excel')
        
        # 取得搜尋參數
        request_data = request.get_json()
        search_params = request_data.get('searchParams', {})
        
        # 建立搜尋條件
        conditions = []
        
        # 處理快速搜尋 (q 參數)
        if search_params.get('q'):
            keyword = search_params.get('q').strip()
            if keyword:
                conditions.append({
                    'field': 'title',
                    'operator': '包含',
                    'value': keyword
                })
                conditions.append({
                    'field': 'summary', 
                    'operator': '包含',
                    'value': keyword,
                    'connector': 'OR'
                })
        
        # 處理其他搜尋參數
        if search_params.get('keyword'):
            keyword = search_params.get('keyword').strip()
            if keyword:
                conditions.append({
                    'field': 'title',
                    'operator': '包含',
                    'value': keyword
                })
                conditions.append({
                    'field': 'summary',
                    'operator': '包含', 
                    'value': keyword,
                    'connector': 'OR'
                })
        
        if search_params.get('category'):
            conditions.append({
                'field': 'type',
                'operator': '等於',
                'value': search_params.get('category')
            })
        
        if search_params.get('csiName'):
            conditions.append({
                'field': 'csi_name',
                'operator': '包含',
                'value': search_params.get('csiName')
            })
        
        if search_params.get('author'):
            conditions.append({
                'field': 'main_author',
                'operator': '包含',
                'value': search_params.get('author')
            })
        
        if search_params.get('securityLevel'):
            conditions.append({
                'field': 'security_level',
                'operator': '等於',
                'value': search_params.get('securityLevel')
            })
        
        if search_params.get('trainType'):
            conditions.append({
                'field': 'train_type',
                'operator': '等於',
                'value': search_params.get('trainType')
            })
        
        # 處理日期區間
        if search_params.get('dateFrom'):
            conditions.append({
                'field': 'public_date',
                'operator': '大於等於',
                'value': search_params.get('dateFrom')
            })
        
        if search_params.get('dateTo'):
            conditions.append({
                'field': 'public_date',
                'operator': '小於等於',
                'value': search_params.get('dateTo')
            })
        
        # 執行搜尋（取得所有欄位，不受前台隱藏限制）
        results = []
        if conditions:
            try:
                from db_manager import search_reports_dynamic
                # 使用 detail 類型取得所有欄位
                results = search_reports_dynamic(conditions, limit=1000, show_type='detail')
                current_app.logger.info(f'Excel 匯出搜尋成功，返回 {len(results)} 筆資料')
            except Exception as search_error:
                current_app.logger.error(f'Excel 匯出搜尋失敗: {search_error}')
                return jsonify({'success': False, 'message': '搜尋失敗，無法匯出'}), 500
        else:
            return jsonify({'success': False, 'message': '沒有搜尋條件，無法匯出'}), 400
        
        if not results:
            return jsonify({'success': False, 'message': '沒有符合條件的資料'}), 404
        
        # 生成 Excel 檔案
        try:
            import pandas as pd
            from io import BytesIO
            from datetime import datetime
            
            # 取得所有欄位設定
            try:
                from db_manager import get_dynamic_field_list
                all_fields = get_dynamic_field_list('detail')
            except Exception as field_error:
                current_app.logger.error(f'取得欄位設定失敗: {field_error}')
                # 使用預設欄位
                all_fields = [
                    {'field_id': 'RP_NO', 'display_name': '報告編號', 'field_type': 'TEXT'},
                    {'field_id': 'RP_NAME', 'display_name': '報告名稱', 'field_type': 'TEXT'},
                    {'field_id': 'MAIN_AUTHOR', 'display_name': '主要作者', 'field_type': 'TEXT'},
                    {'field_id': 'CAT_NAME', 'display_name': '性質', 'field_type': 'TEXT'},
                    {'field_id': 'TYPE_NAME', 'display_name': '分類', 'field_type': 'TEXT'},
                    {'field_id': 'PUBLIC_DATE', 'display_name': '發布日期', 'field_type': 'DATE'}
                ]
            
            # 轉換資料為 DataFrame
            df_data = []
            for result in results:
                row = {}
                for field in all_fields:
                    field_id = field['field_id']
                    display_name = field['display_name']
                    value = result.get(field_id, '')
                    
                    # 處理日期欄位
                    if field['field_type'] == 'DATE' and value:
                        try:
                            # 如果是字串格式的日期，保持原樣
                            if isinstance(value, str):
                                row[display_name] = value
                            else:
                                # 如果是 datetime 對象，格式化為字串
                                row[display_name] = value.strftime('%Y-%m-%d')
                        except:
                            row[display_name] = value
                    else:
                        row[display_name] = value if value else ''
                
                df_data.append(row)
            
            # 建立 DataFrame
            df = pd.DataFrame(df_data)
            
            # 建立 Excel 檔案
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='搜尋結果', index=False)
                
                # 取得工作表
                worksheet = writer.sheets['搜尋結果']
                
                # 調整欄位寬度
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # 設定標題樣式
                for cell in worksheet[1]:
                    cell.font = pd.ExcelWriter().book.add_format({'bold': True})
                    cell.fill = pd.ExcelWriter().book.add_format({'bg_color': '#FFD700'})
            
            # 準備回應
            output.seek(0)
            
            # 生成檔名
            filename = f'報告搜尋結果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            
            current_app.logger.info(f'Excel 檔案生成成功: {filename}')
            
            # 回傳檔案
            return output.getvalue(), 200, {
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': len(output.getvalue())
            }
            
        except ImportError as ie:
            current_app.logger.error(f'缺少 pandas 或 openpyxl 套件: {ie}')
            return jsonify({'success': False, 'message': '系統缺少 Excel 匯出功能，請安裝 pandas 和 openpyxl'}), 500
        except Exception as excel_error:
            current_app.logger.error(f'Excel 生成失敗: {excel_error}')
            return jsonify({'success': False, 'message': 'Excel 檔案生成失敗'}), 500
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'Excel 匯出失敗: {error_message}')
        return jsonify({'success': False, 'message': '匯出失敗，請稍後再試'}), 500

@bp.route('/search_advanced', methods=['POST'])
@require_login
def search_advanced():
    """
    進階搜尋處理路由
    
    接收動態條件清單並生成 SQL 查詢
    支援正式資料庫欄位映射和隱形過濾
    
    Returns:
        JSON: 查詢結果或錯誤訊息
    """
    start_time = time.time()
    account = session.get('username', 'unknown')
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    session_id = session.get('session_id', '')
    
    try:
        # 取得前端傳來的資料
        conditions = request.json.get('conditions', [])
        global_logic = request.json.get('globalLogic', 'AND')  # AND 或 OR
        table_name = request.json.get('tableName', '')
        selected_columns = request.json.get('selectedColumns', [])
        
        if not conditions and not table_name:
            return jsonify({
                'success': False,
                'message': '請提供搜尋條件或選擇表格'
            })
        
        # 從配置檔案取得正式欄位映射
        from config import (
            MAIN_TABLE_FULL, SEARCH_FIELDS, FILTER_FIELDS,
            STATUS_CODE_FIELD, STATUS_OPEN_CODE
        )
        
        # 搜尋條件映射表
        SEARCH_MAPPING = {
            '包含': 'LIKE :{param}',
            '等於': '= :{param}',
            '開頭為': 'LIKE :{param}',
            '大於': '> :{param}',
            '小於': '< :{param}',
            '大於等於': '>= :{param}',
            '小於等於': '<= :{param}'
        }
        
        # 建立 WHERE 子句
        where_clauses = []
        params = {}
        
        for i, condition in enumerate(conditions, 1):
            field = condition.get('field', '')
            operator = condition.get('operator', '')
            value = condition.get('value', '')
            connector = condition.get('connector', 'AND')
            
            if not field or not operator or not value:
                continue
            
            # 映射搜尋欄位到正式資料庫欄位
            mapped_field = SEARCH_FIELDS.get(field, field)
            
            # 取得對應的 SQL 操作符
            sql_operator = SEARCH_MAPPING.get(operator, '= :{param}')
            
            # 處理 LIKE 操作符的值
            if operator in ['包含', '開頭為']:
                param_value = f'%{value}%'
            else:
                param_value = value
            
            # 建立條件子句
            param_name = f'param{i}'
            where_clause = f'{mapped_field} {sql_operator}'
            where_clauses.append(where_clause)
            params[param_name] = param_value
        
        # 處理選定的欄位（資料類型過濾）
        column_clause = '*'
        if selected_columns:
            # 映射選定的欄位到正式資料庫欄位
            mapped_columns = []
            for col in selected_columns:
                mapped_col = SEARCH_FIELDS.get(col, FILTER_FIELDS.get(col, col))
                mapped_columns.append(mapped_col)
            column_clause = ', '.join(mapped_columns)
        
        # 加入隱形過濾條件 - 確保只顯示狀態為 'open' 的報告
        hidden_filter_clause = f'{STATUS_CODE_FIELD} = :status_filter'
        where_clauses.append(hidden_filter_clause)
        params['status_filter'] = STATUS_OPEN_CODE
        
        # 建立完整的 SQL 查詢
        if where_clauses:
            where_sql = f' {global_logic} '.join(where_clauses)
            sql = f'SELECT {column_clause} FROM {MAIN_TABLE_FULL} WHERE {where_sql}'
        else:
            # 即使沒有其他條件，也要加入隱形過濾
            sql = f'SELECT {column_clause} FROM {MAIN_TABLE_FULL} WHERE {hidden_filter_clause}'
        
        # 記錄生成的 SQL
        current_app.logger.info(f'進階搜尋生成的 SQL: {sql}')
        current_app.logger.info(f'進階搜尋參數: {params}')
        
        # 執行查詢
        results = execute_query(sql, params if params else None)
        
        # 記錄查詢結果
        current_app.logger.info(f'進階搜尋成功，返回 {len(results)} 筆資料')
        
        # 準備稽核記錄的查詢詳細資訊
        query_details = json.dumps({
            'conditions': conditions,
            'global_logic': global_logic,
            'table_name': table_name,
            'selected_columns': selected_columns,
            'sql': sql,
            'params': params,
            'field_mapping': SEARCH_FIELDS,
            'filter_fields': FILTER_FIELDS
        }, ensure_ascii=False)
        
        # 記錄搜尋歷史（非同步，不影響主要功能）
        try:
            log_search_history(
                account=account,
                mode='advanced',
                query_details=query_details,
                result_count=len(results),
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                execution_time=time.time() - start_time,
                success_flag='Y'
            )
        except Exception as audit_error:
            # 稽核記錄失敗不影響主要功能
            current_app.logger.error(f'進階搜尋稽核記錄失敗: {audit_error}')
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results),
            'sql': sql,  # 用於除錯
            'params': params,  # 用於除錯
            'field_mapping': SEARCH_FIELDS,  # 前端參考
            'filter_fields': FILTER_FIELDS,  # 前端參考
            'message': f'搜尋成功，找到 {len(results)} 筆資料'
        })
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'進階搜尋失敗: {error_message}')
        current_app.logger.error(f'生成的 SQL: {sql if "sql" in locals() else "N/A"}')
        current_app.logger.error(f'使用的參數: {params if "params" in locals() else "N/A"}')
        
        # 記錄失敗的搜尋歷史
        try:
            query_details = json.dumps({
                'conditions': conditions if 'conditions' in locals() else [],
                'global_logic': global_logic if 'global_logic' in locals() else '',
                'table_name': table_name if 'table_name' in locals() else '',
                'error': error_message
            }, ensure_ascii=False)
            
            log_search_history(
                account=account,
                mode='advanced',
                query_details=query_details,
                result_count=0,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                execution_time=time.time() - start_time,
                success_flag='N',
                error_message=error_message
            )
        except Exception as audit_error:
            current_app.logger.error(f'失敗進階搜尋稽核記錄失敗: {audit_error}')
        
        return jsonify({
            'success': False,
            'message': '搜尋失敗，請稍後再試',
            'error': error_message
        }), 500

@bp.route('/query', methods=['POST'])
@require_login
def query():
    """
    執行查詢路由
    
    處理使用者查詢請求，支援分頁和稽核記錄
    
    Returns:
        JSON: 查詢結果或錯誤訊息
    """
    start_time = time.time()
    account = session.get('username', 'unknown')
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    session_id = session.get('session_id', '')
    
    try:
        # 取得查詢參數
        sql = request.form.get('sql', '').strip()
        page = int(request.form.get('page', 1))
        per_page = int(request.form.get('per_page', 50))
        use_pagination = request.form.get('use_pagination', 'false').lower() == 'true'
        
        params = {}
        
        # 解析綁定參數
        if ':' in sql:
            # 簡單的參數解析 (實際應該更安全)
            for key in request.form:
                if key.startswith('param_'):
                    param_name = key[6:]  # 移除 'param_' 前綴
                    param_value = request.form.get(key, '').strip()
                    if param_value:
                        params[param_name] = param_value
        
        # 記錄查詢
        current_app.logger.info(f'使用者 {account} 執行查詢: {sql}')
        current_app.logger.info(f'分頁資訊: 第 {page} 頁，每頁 {per_page} 筆')
        
        # 執行查詢
        if use_pagination:
            # 使用分頁查詢
            result = execute_paginated_query(sql, params if params else None, page, per_page)
            results = result['data']
            pagination_info = {
                'total': result['total'],
                'page': result['page'],
                'per_page': result['per_page'],
                'total_pages': result['total_pages'],
                'has_next': result['has_next'],
                'has_prev': result['has_prev']
            }
        else:
            # 使用傳統查詢
            results = execute_query(sql, params if params else None)
            pagination_info = None
        
        # 計算執行時間
        execution_time = time.time() - start_time
        
        # 記錄結果
        current_app.logger.info(f'查詢成功，返回 {len(results)} 筆資料')
        
        # 準備稽核記錄的查詢詳細資訊
        query_details = json.dumps({
            'sql': sql,
            'params': params,
            'page': page,
            'per_page': per_page,
            'use_pagination': use_pagination
        }, ensure_ascii=False)
        
        # 記錄搜尋歷史（非同步，不影響主要功能）
        try:
            log_search_history(
                account=account,
                mode='simple',
                query_details=query_details,
                result_count=len(results),
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                execution_time=execution_time,
                success_flag='Y'
            )
        except Exception as audit_error:
            # 稽核記錄失敗不影響主要功能
            current_app.logger.error(f'搜尋稽核記錄失敗: {audit_error}')
        
        response_data = {
            'success': True,
            'data': results,
            'count': len(results),
            'message': f'查詢成功，找到 {len(results)} 筆資料'
        }
        
        # 加入分頁資訊
        if pagination_info:
            response_data['pagination'] = pagination_info
        
        return jsonify(response_data)
        
    except Exception as e:
        error_message = str(e)
        execution_time = time.time() - start_time
        
        current_app.logger.error(f'查詢失敗: {error_message}')
        
        # 記錄失敗的搜尋歷史
        try:
            query_details = json.dumps({
                'sql': sql if 'sql' in locals() else '',
                'params': params if 'params' in locals() else {},
                'error': error_message
            }, ensure_ascii=False)
            
            log_search_history(
                account=account,
                mode='simple',
                query_details=query_details,
                result_count=0,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                execution_time=execution_time,
                success_flag='N',
                error_message=error_message
            )
        except Exception as audit_error:
            current_app.logger.error(f'失敗搜尋稽核記錄失敗: {audit_error}')
        
        return jsonify({
            'success': False,
            'message': f'查詢失敗: {error_message}'
        }), 500

@bp.route('/test_connection')
@require_login
def test_db_connection():
    """
    測試資料庫連線
    
    測試當前資料庫連線狀態
    
    Returns:
        JSON: 連線測試結果
    """
    try:
        is_connected = test_connection()
        
        if is_connected:
            current_app.logger.info(f'使用者 {session["username"]} 測試資料庫連線成功')
            return jsonify({
                'success': True,
                'message': '資料庫連線正常'
            })
        else:
            current_app.logger.warning(f'使用者 {session["username"]} 測試資料庫連線失敗')
            return jsonify({
                'success': False,
                'message': '資料庫連線失敗'
            })
            
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'測試連線時發生錯誤: {error_message}')
        
        return jsonify({
            'success': False,
            'message': f'測試連線失敗: {error_message}'
        }), 500

@bp.route('/schema')
@require_login
def get_schema():
    """
    取得資料庫架構資訊
    
    顯示可用的表格和欄位資訊
    
    Returns:
        JSON: 資料庫架構資訊
    """
    try:
        # 查詢所有表格
        tables_sql = """
        SELECT table_name, comments 
        FROM user_tab_comments 
        WHERE table_type = 'TABLE' 
        ORDER BY table_name
        """
        tables = execute_query(tables_sql)
        
        # 查詢每個表格的欄位
        schema = {}
        for table in tables:
            table_name = table['TABLE_NAME']
            columns_sql = f"""
            SELECT column_name, data_type, nullable, comments
            FROM user_col_comments
            WHERE table_name = '{table_name}'
            ORDER BY column_id
            """
            columns = execute_query(columns_sql)
            schema[table_name] = {
                'comment': table.get('COMMENTS', ''),
                'columns': columns
            }
        
        current_app.logger.info(f'使用者 {session["username"]} 取得資料庫架構資訊')
        
        return jsonify({
            'success': True,
            'data': schema,
            'message': f'取得 {len(tables)} 個表格的架構資訊'
        })
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'取得資料庫架構失敗: {error_message}')
        
        return jsonify({
            'success': False,
            'message': f'取得資料庫架構失敗: {error_message}'
        }), 500

@bp.route('/history')
@require_login
def query_history():
    """
    查詢歷史記錄
    
    顯示使用者的查詢歷史
    
    Returns:
        str: 查詢歷史頁面 HTML
    """
    # 這裡可以從資料庫或檔案中讀取查詢歷史
    # 目前為測試版本，返回空歷史
    return render_template('search/history.html')

@bp.route('/export', methods=['POST'])
@require_login
def export_results():
    """
    匯出查詢結果
    
    將查詢結果匯出為 CSV 或 Excel 格式
    
    Returns:
        File: 匯出檔案
    """
    try:
        export_format = request.form.get('format', 'csv')
        data = request.form.get('data', '[]')
        
        # 解析資料
        import json
        results = json.loads(data)
        
        if not results:
            return jsonify({
                'success': False,
                'message': '沒有資料可以匯出'
            })
        
        if export_format == 'csv':
            # 匯出為 CSV
            import csv
            import io
            
            output = io.StringIO()
            if results:
                writer = csv.DictWriter(output, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            
            output.seek(0)
            
            current_app.logger.info(f'使用者 {session["username"]} 匯出 CSV 檔案')
            
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=query_results.csv'
            }
        
        # 可以添加其他格式的支援
        return jsonify({
            'success': False,
            'message': '不支援的匯出格式'
        })
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'匯出結果失敗: {error_message}')
        
        return jsonify({
            'success': False,
            'message': f'匯出失敗: {error_message}'
        }), 500

# ===========================================
# 詳情檢視功能
# ===========================================

@bp.route('/detail/<doc_id>')
@require_login
def detail(doc_id):
    """
    報告詳情頁面
    
    Args:
        doc_id: 報告 ID
        
    Returns:
        str: 詳情頁面 HTML
    """
    try:
        # 記錄存取
        current_app.logger.info(f'使用者 {session["username"]} 查看詳情: {doc_id}')
        
        # 從配置檔案取得正式欄位映射
        from config import (
            MAIN_TABLE_FULL, STATUS_CODE_FIELD, STATUS_OPEN_CODE,
            DETAIL_FIELDS, DATE_FIELDS
        )
        
        # 使用新的 get_report_detail_dynamic 函數
        from db_manager import get_report_detail_dynamic
        
        document = get_report_detail_dynamic(doc_id)
        
        if not document:
            flash('找不到指定的報告', 'error')
            return redirect(url_for('search.index'))
        
        # 記錄瀏覽次數（非同步，不影響主要功能）
        try:
            increment_detail_view(doc_id, document.get('OVN_RP_NAME', f'報告 {doc_id}'))
        except Exception as view_error:
            current_app.logger.error(f'記錄瀏覽次數失敗: {view_error}')
        
        # 查詢相關附件（根據安全等級判斷）
        attachments = []
        try:
            # 取得安全等級
            security_level = document.get('OVC_SECERT_LV_NAME', '未知')
            
            # 使用新的附件查詢函數
            from db_manager import get_attachment_files
            attachments = get_attachment_files(doc_id, security_level)
            
            current_app.logger.info(f'附件查詢完成: {doc_id}, 安全等級: {security_level}, 檔案數: {len(attachments)}')
            
        except Exception as attach_error:
            current_app.logger.error(f'查詢附件失敗: {attach_error}')
            attachments = []  # 附件查詢失敗不影響主要功能
        
        current_app.logger.info(f'詳情查詢成功: {doc_id}')
        
        # 取得動態欄位設定
        try:
            from db_manager import get_dynamic_field_list
            detail_fields = get_dynamic_field_list('detail')
        except Exception as field_error:
            current_app.logger.error(f'取得詳情欄位設定失敗: {field_error}')
            # 使用預設欄位
            detail_fields = [
                {'field_id': 'RP_NO', 'display_name': '報告編號', 'field_type': 'TEXT'},
                {'field_id': 'RP_NAME', 'display_name': '報告名稱', 'field_type': 'TEXT'},
                {'field_id': 'MAIN_AUTHOR', 'display_name': '主要作者', 'field_type': 'TEXT'},
                {'field_id': 'CAT_NAME', 'display_name': '性質', 'field_type': 'TEXT'},
                {'field_id': 'TYPE_NAME', 'display_name': '分類', 'field_type': 'TEXT'},
                {'field_id': 'PUBLIC_DATE', 'display_name': '發布日期', 'field_type': 'DATE'}
            ]
        
        return render_template('search/detail.html', 
                             document=document, 
                             attachments=attachments,
                             doc_id=doc_id,
                             detail_fields=detail_fields)
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'查詢詳情失敗: {error_message}')
        flash('查詢詳情失敗', 'error')
        return redirect(url_for('search.index'))

# ===========================================
# 附件下載功能
# ===========================================

@bp.route('/download/<filename>')
@require_login
def download_file(filename):
    """
    附件下載路由
    
    安全下載檔案，包含副檔名檢查和路徑驗證
    
    Args:
        filename: 檔案名稱
        
    Returns:
        File: 下載檔案
    """
    try:
        # 記錄下載請求
        current_app.logger.info(f'使用者 {session["username"]} 請求下載檔案: {filename}')
        
        # 安全性檢查：檔名處理
        safe_filename = secure_filename(filename)
        
        if not safe_filename:
            current_app.logger.warning(f'檔名安全性檢查失敗: {filename}')
            flash('檔名包含不安全字元', 'error')
            return redirect(url_for('search.index'))
        
        # 副檔名檢查
        file_extension = safe_filename.rsplit('.', 1)[1].lower() if '.' in safe_filename else ''
        if file_extension not in ALLOWED_EXTENSIONS:
            current_app.logger.warning(f'不允許的檔案類型: {file_extension}')
            flash('不允許下載此類型的檔案', 'error')
            return redirect(url_for('search.index'))
        
        # 檢查檔案是否存在
        file_path = os.path.join(FILE_STORAGE_PATH, safe_filename)
        if not os.path.exists(file_path):
            current_app.logger.warning(f'檔案不存在: {file_path}')
            flash('檔案不存在', 'error')
            return redirect(url_for('search.index'))
        
        # 檢查檔案是否在允許的目錄內（防止目錄遍歷攻擊）
        real_file_path = os.path.realpath(file_path)
        real_storage_path = os.path.realpath(FILE_STORAGE_PATH)
        
        if not real_file_path.startswith(real_storage_path):
            current_app.logger.warning(f'檢測到目錄遍歷攻擊: {file_path}')
            flash('檔案路徑不安全', 'error')
            return redirect(url_for('search.index'))
        
        # 記錄成功下載
        current_app.logger.info(f'檔案下載成功: {safe_filename} by {session["username"]}')
        
        # 使用 send_from_directory 安全下載
        return send_from_directory(
            FILE_STORAGE_PATH, 
            safe_filename, 
            as_attachment=True,
            download_filename=safe_filename
        )
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'檔案下載失敗: {error_message}')
        flash('檔案下載失敗', 'error')
        return redirect(url_for('search.index'))

def allowed_file(filename):
    """
    檢查檔案副檔名是否允許
    
    Args:
        filename: 檔案名稱
        
    Returns:
        bool: 是否允許
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===========================================
# 動態頁面路由
# ===========================================

@bp.route('/portal/page/<int:page_id>')
@require_login
def portal_page(page_id):
    """
    動態入口頁面路由
    
    根據 ID 從資料庫讀取 HTML 內容並動態渲染
    
    Args:
        page_id: 頁面 ID
        
    Returns:
        str: 動態頁面 HTML
    """
    try:
        # 記錄存取
        current_app.logger.info(f'使用者 {session["username"]} 存取動態頁面: {page_id}')
        
        # 查詢頁面資訊
        portal_link = get_portal_link(page_id)
        
        if not portal_link:
            current_app.logger.warning(f'找不到入口連結: ID={page_id}')
            flash('找不到指定的頁面', 'error')
            return redirect(url_for('search.index'))
        
        # 檢查是否可見
        if portal_link.get('IS_VISIBLE') != 'Y':
            current_app.logger.warning(f'頁面不可見: ID={page_id}')
            flash('此頁面目前不可用', 'error')
            return redirect(url_for('search.index'))
        
        current_app.logger.info(f'動態頁面載入成功: ID={page_id}')
        
        return render_template('search/portal_page.html', 
                             portal_link=portal_link,
                             page_id=page_id)
        
    except Exception as e:
        current_app.logger.error(f'載入動態頁面失敗: {str(e)}')
        flash('載入頁面失敗', 'error')
        return redirect(url_for('search.index'))

# ===========================================
# 跨資料表聯合搜尋路由
# ===========================================

@bp.route('/unified', methods=['GET', 'POST'])
@require_login
def unified_search():
    """
    跨資料表聯合搜尋
    
    四種資料類型的聯合檢索：
    1. 技術報告 (TBIRLIB_REPORT_MAIN) - 背景色：淡藍色
    2. 史政 (TRIRLIB_HISTORY_MAIN) - 背景色：淡綠色
    3. 逸光報 (TRIRLIB_PAPER_MAIN) - 背景色：淡灰色
    4. 史政照片 (TRIRLIB_PHOTO_MAIN) - 背景色：淡黃色
    """
    try:
        current_app.logger.info(f'使用者 {session["username"]} 進行跨表聯合搜尋')
        
        # 取得搜尋參數
        keyword = request.args.get('q', '').strip() if request.method == 'GET' else request.form.get('keyword', '').strip()
        page = int(request.args.get('page', 1)) if request.method == 'GET' else 1
        
        # 限制頁碼範圍
        if page < 1:
            page = 1
        
        # 執行跨表搜尋
        from db_manager import search_cross_table_unified
        search_result = search_cross_table_unified(
            keyword=keyword if keyword else None,
            page=page,
            page_size=50
        )
        
        # 取得簡目欄位設定
        from db_manager import get_field_settings
        list_fields = get_field_settings('unified_list')
        
        # 處理結果
        results = search_result['results']
        total_count = search_result['total_count']
        current_page = search_result['page']
        total_pages = search_result['total_pages']
        has_next = search_result['has_next']
        has_prev = search_result['has_prev']
        
        # 記錄搜尋歷史
        account = session.get('username', 'unknown')
        query_details = {
            'keyword': keyword,
            'page': page,
            'page_size': 50
        }
        
        try:
            from db_manager import log_search_history
            log_search_history(
                account=account,
                mode='unified',
                query_details=query_details,
                result_count=total_count
            )
        except Exception as log_error:
            current_app.logger.error(f'記錄搜尋歷史失敗: {log_error}')
        
        # 計算分頁資訊
        pagination = {
            'current_page': current_page,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev,
            'total_count': total_count,
            'page_size': 50
        }
        
        # 計算頁碼範圍（當前頁前後各3頁）
        start_page = max(1, current_page - 3)
        end_page = min(total_pages, current_page + 3)
        page_range = list(range(start_page, end_page + 1))
        
        pagination['page_range'] = page_range
        pagination['start_page'] = start_page
        pagination['end_page'] = end_page
        
        # 如果是 AJAX 請求，返回 JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'results': results,
                'pagination': pagination,
                'total_count': total_count
            })
        
        return render_template('search/unified_results.html',
                            keyword=keyword,
                            results=results,
                            pagination=pagination,
                            total_count=total_count,
                            list_fields=list_fields)
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'跨表聯合搜尋失敗: {error_message}')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f'搜尋失敗: {error_message}'
            }), 500
        
        flash(f'搜尋失敗: {error_message}', 'error')
        return redirect(url_for('search.index'))

@bp.route('/unified/detail/<data_type>/<unique_id>')
@require_login
def unified_detail(data_type, unique_id):
    """
    跨表資料詳情頁面
    
    Args:
        data_type: 資料類型 ('1'=技術報告, '2'=史政, '3'=逸光報, '4'=史政照片)
        unique_id: 唯一識別碼
    """
    try:
        current_app.logger.info(f'使用者 {session["username"]} 查看跨表詳情: {data_type}-{unique_id}')
        
        # 取得詳情資料
        from db_manager import get_cross_table_detail
        document = get_cross_table_detail(data_type, unique_id)
        
        # 取得附件資訊
        from db_manager import get_cross_table_attachments
        attachments = get_cross_table_attachments(data_type, unique_id)
        
        # 取得詳情欄位設定
        from db_manager import get_field_settings
        detail_fields = get_field_settings(f'unified_detail_{data_type}')
        
        # 記錄瀏覽次數
        try:
            from db_manager import increment_detail_view
            increment_detail_view(data_type, unique_id)
        except Exception as view_error:
            current_app.logger.error(f'記錄瀏覽次數失敗: {view_error}')
        
        return render_template('search/unified_detail.html',
                            document=document,
                            attachments=attachments,
                            detail_fields=detail_fields)
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'跨表詳情頁面載入失敗: {error_message}')
        flash(f'載入詳情失敗: {error_message}', 'error')
        return redirect(url_for('search.unified_search'))

@bp.route('/unified/download/<data_type>/<unique_id>/<filename>')
@require_login
def unified_download_attachment(data_type, unique_id, filename):
    """
    跨表附件下載
    
    Args:
        data_type: 資料類型
        unique_id: 唯一識別碼
        filename: 檔案名稱
    """
    try:
        current_app.logger.info(f'使用者 {session["username"]} 請求下載跨表附件: {data_type}-{unique_id}-{filename}')
        
        # 使用現有的附件下載函數
        from db_manager import download_attachment_from_api
        
        # 根據資料類型設定不同的參數
        if data_type == '1':  # 技術報告
            doc_id = unique_id
        else:
            doc_id = unique_id
        
        # 呼叫下載 API
        file_stream, content_type, download_filename = download_attachment_from_api(
            doc_id=doc_id,
            filename=filename,
            account=session.get('username', 'unknown')
        )
        
        current_app.logger.info(f'跨表附件下載成功: {filename}')
        
        from flask import send_file
        return send_file(
            file_stream,
            as_attachment=True,
            download_name=download_filename,
            mimetype=content_type
        )
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'跨表附件下載失敗: {error_message}')
        flash(f'附件下載失敗: {error_message}', 'error')
        return redirect(url_for('search.unified_detail', data_type=data_type, unique_id=unique_id))

@bp.route('/unified/export', methods=['POST'])
@require_login
def unified_export_excel():
    """
    跨表搜尋結果 Excel 匯出
    """
    try:
        current_app.logger.info(f'使用者 {session["username"]} 請求跨表 Excel 匯出')
        
        # 取得搜尋條件
        search_params = request.get_json() or {}
        keyword = search_params.get('keyword', '').strip()
        
        # 執行搜尋（不分頁，取得全部資料）
        from db_manager import search_cross_table_unified
        search_result = search_cross_table_unified(
            keyword=keyword if keyword else None,
            page=1,
            page_size=10000  # 設定大數量取得所有資料
        )
        
        results = search_result['results']
        
        if not results:
            current_app.logger.warning('沒有符合條件的資料可以匯出')
            return jsonify({'success': False, 'message': '沒有符合條件的資料可以匯出'}), 400
        
        # 建立欄位映射
        field_mapping = {
            'DATA_TYPE_NAME': '資料類型',
            'UNIQUE_ID': '唯一識別碼',
            'TITLE': '標題',
            'RP_CSI_NAME': '報告主號',
            'HOST_NAME': '報告單位',
            'YEAR': '報告年度',
            'PUBLIC_DATE': '日期',
            'HS_NAME': '名稱',
            'TO_NAME': '照片名稱',
            'TO_DATE': '照片日期',
            'PAPER_NAME': '報紙名稱',
            'PAPER_AUTHOR': '報紙作者'
        }
        
        # 匯出 Excel
        from excel_exporter import export_search_results
        excel_file, filename = export_search_results(results, field_mapping, "跨表聯合搜尋結果")
        
        current_app.logger.info(f'跨表 Excel 匯出成功: {filename}, 資料筆數: {len(results)}')
        
        from flask import send_file
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'跨表 Excel 匯出失敗: {error_message}')
        return jsonify({'success': False, 'message': f'匯出失敗: {error_message}'}), 500

@bp.route('/export', methods=['POST'])
@require_login
def export_excel():
    """
    Excel 匯出路由
    
    接收前端傳來的搜尋條件，匯出全部符合條件的資料到 Excel
    
    Returns:
        Response: Excel 檔案下載回應
    """
    try:
        current_app.logger.info(f'使用者 {session["username"]} 請求 Excel 匯出')
        
        # 取得前端傳來的搜尋條件
        search_params = request.get_json() or {}
        
        # 建立搜尋條件
        conditions = []
        
        # 處理快速搜尋 (q 參數)
        if search_params.get('q'):
            keyword = search_params.get('q').strip()
            if keyword:
                conditions.append({
                    'field': 'title',
                    'operator': '包含',
                    'value': keyword
                })
                conditions.append({
                    'field': 'summary', 
                    'operator': '包含',
                    'value': keyword,
                    'connector': 'OR'
                })
        
        # 處理進階搜尋條件
        if search_params.get('keyword'):
            keyword = search_params.get('keyword').strip()
            if keyword:
                conditions.append({
                    'field': 'title',
                    'operator': '包含',
                    'value': keyword
                })
                conditions.append({
                    'field': 'summary', 
                    'operator': '包含',
                    'value': keyword,
                    'connector': 'OR'
                })
        
        if search_params.get('category'):
            category = search_params.get('category').strip()
            if category:
                conditions.append({
                    'field': 'category',
                    'operator': '等於',
                    'value': category
                })
        
        if search_params.get('csiName'):
            csi_name = search_params.get('csiName').strip()
            if csi_name:
                conditions.append({
                    'field': 'csi_name',
                    'operator': '包含',
                    'value': csi_name
                })
        
        if search_params.get('author'):
            author = search_params.get('author').strip()
            if author:
                conditions.append({
                    'field': 'author',
                    'operator': '包含',
                    'value': author
                })
        
        if search_params.get('securityLevel'):
            security_level = search_params.get('securityLevel').strip()
            if security_level:
                conditions.append({
                    'field': 'security_level',
                    'operator': '等於',
                    'value': security_level
                })
        
        if search_params.get('trainType'):
            train_type = search_params.get('trainType').strip()
            if train_type:
                conditions.append({
                    'field': 'train_type',
                    'operator': '等於',
                    'value': train_type
                })
        
        if search_params.get('dateFrom'):
            date_from = search_params.get('dateFrom').strip()
            if date_from:
                conditions.append({
                    'field': 'public_date',
                    'operator': '大於等於',
                    'value': date_from
                })
        
        if search_params.get('dateTo'):
            date_to = search_params.get('dateTo').strip()
            if date_to:
                conditions.append({
                    'field': 'public_date',
                    'operator': '小於等於',
                    'value': date_to
                })
        
        # 執行搜尋（不分頁，取得全部資料）
        from db_manager import search_reports_dynamic
        results = search_reports_dynamic(conditions, limit=10000, show_type='list')
        
        if not results:
            current_app.logger.warning('沒有符合條件的資料可以匯出')
            return jsonify({'success': False, 'message': '沒有符合條件的資料可以匯出'}), 400
        
        # 取得欄位顯示設定
        from db_manager import get_field_settings
        field_settings = get_field_settings('list')
        
        # 建立欄位映射
        field_mapping = {}
        for field in field_settings:
            field_id = field.get('FIELD_ID', '')
            display_name = field.get('DISPLAY_NAME', '')
            if field_id and display_name:
                field_mapping[field_id] = display_name
        
        # 匯出 Excel
        from excel_exporter import export_search_results
        excel_file, filename = export_search_results(results, field_mapping, "搜尋結果")
        
        current_app.logger.info(f'Excel 匯出成功: {filename}, 資料筆數: {len(results)}')
        
        # 使用 send_file 回傳檔案
        from flask import send_file
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'Excel 匯出失敗: {error_message}')
        return jsonify({'success': False, 'message': f'匯出失敗: {error_message}'}), 500

# ===========================================
# 附件下載路由
# ===========================================

@bp.route('/download_attachment/<filename>')
@require_login
def download_attachment(filename):
    """
    附件下載路由
    
    Args:
        filename: 檔案名稱（實際為 OVC_GUID）
        
    Returns:
        Response: 檔案下載回應
    """
    try:
        from db_manager import download_attachment_from_api
        
        current_app.logger.info(f'使用者 {session["username"]} 請求下載附件: {filename}')
        
        # 從 API 下載檔案
        file_content = download_attachment_from_api(filename)
        
        if not file_content:
            flash('檔案下載失敗', 'error')
            return redirect(url_for('search.index'))
        
        # 嘗試從檔案內容或檔名推斷 MIME 類型
        import mimetypes
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        current_app.logger.info(f'附件下載成功: {filename}, 大小: {len(file_content)} bytes')
        
        # 返回檔案下載回應
        from flask import Response
        return Response(
            file_content,
            mimetype=mime_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(len(file_content))
            }
        )
        
    except Exception as e:
        error_message = str(e)
        current_app.logger.error(f'附件下載失敗: {error_message}')
        flash('附件下載失敗', 'error')
        return redirect(url_for('search.index'))
