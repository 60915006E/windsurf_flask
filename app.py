"""
Flask 查詢系統主程式
遵循 Windows Server 2022 離線環境開發規範
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pathlib import Path

# 導入資料庫連線模組
from database import initialize_database, get_database, close_database

# 資料庫欄位對應表
SEARCH_MAPPING = {
    'all': 'ALL',           # 全部欄位
    'title': 'title',       # 題名
    'author': 'author',     # 撰寫人
    'number': 'DOC_ID'      # 編號
}

# 資料類型對應表
TYPE_MAPPING = {
    'tech_report': '技術報告',      # 技術報告
    'history_politics': '史政',      # 史政
    'history_photos': '史政照片',    # 史政照片
    'yiguang_report': '逸光報'      # 逸光報
}

# 設定日誌系統
def setup_logging():
    """設定應用程式日誌記錄"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / 'app.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# 初始化 Flask 應用程式
app = Flask(__name__)

# 設定正確的模板和靜態檔案路徑
# 確保在虛擬環境下也能正確找到 templates 和 static 目錄
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# 設定靜態檔案 URL 路徑
app.static_url_path = '/static'

logger = setup_logging()

def initialize_app():
    """初始化應用程式，包含資料庫連線"""
    try:
        # 資料庫配置（可從環境變數或設定檔讀取）
        db_config = {
            'user': os.getenv('DB_USER', 'your_username'),
            'password': os.getenv('DB_PASSWORD', 'your_password'),
            'dsn': os.getenv('DB_DSN', 'localhost:1521/XEPDB1'),
            'min_connections': int(os.getenv('DB_MIN_CONNECTIONS', '2')),
            'max_connections': int(os.getenv('DB_MAX_CONNECTIONS', '10')),
            'increment': int(os.getenv('DB_INCREMENT', '1'))
        }
        
        # 初始化資料庫連線
        if initialize_database(db_config):
            logger.info("資料庫連線初始化成功")
            
            # 測試連線
            db = get_database()
            if db:
                success, msg = db.test_connection()
                if success:
                    logger.info(f"資料庫連線測試成功: {msg}")
                else:
                    logger.warning(f"資料庫連線測試失敗: {msg}")
        else:
            logger.error("資料庫連線初始化失敗")
            
    except Exception as e:
        logger.error(f"應用程式初始化錯誤: {str(e)}")

# 在應用程式啟動時初始化
initialize_app()

@app.route('/')
def index():
    """首頁路由"""
    return render_template('index.html')

@app.route('/advanced')
def advanced():
    """進階搜尋頁面路由"""
    return render_template('advanced.html')

@app.route('/health')
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/search', methods=['POST'])
def search():
    """搜尋路由處理函數"""
    try:
        # 接收表單資料
        keyword = request.form.get('searchKeyword', '').strip()
        field = request.form.get('searchField', 'all')
        types = request.form.getlist('document_types')
        
        # 記錄搜尋請求
        logger.info(f"搜尋請求 - 關鍵字: '{keyword}', 欄位: '{field}', 類型: {types}")
        
        # 驗證輸入資料
        if not keyword:
            logger.warning("搜尋請求缺少關鍵字")
            return render_template('results.html', 
                                error="請輸入搜尋關鍵字",
                                search_params={})
        
        # 根據對應表翻譯搜尋欄位
        db_field = SEARCH_MAPPING.get(field, 'ALL')
        logger.info(f"搜尋欄位對應: {field} -> {db_field}")
        
        # 處理資料類型篩選
        selected_types = []
        for type_key in types:
            if type_key in TYPE_MAPPING:
                selected_types.append(TYPE_MAPPING[type_key])
        
        logger.info(f"選中的資料類型: {selected_types}")
        
        # 取得資料庫連線
        db = get_database()
        if not db:
            logger.error("資料庫連線未初始化")
            return render_template('results.html', 
                                error="資料庫連線失敗，請聯繫管理員",
                                search_params={})
        
        # 執行實際的資料庫搜尋
        search_results, error_msg = db.execute_search(
            keyword=keyword,
            search_field=db_field,
            document_types=selected_types,
            limit=100
        )
        
        if error_msg:
            logger.error(f"資料庫搜尋錯誤: {error_msg}")
            return render_template('results.html', 
                                error=f"搜尋失敗: {error_msg}",
                                search_params={})
        
        # 如果沒有真實資料，使用模擬測試資料
        if not search_results:
            search_results = generate_mock_results(keyword, selected_types)
            logger.info(f"使用模擬測試資料，共 {len(search_results)} 筆")
        
        # 建構搜尋條件（用於顯示）
        search_conditions = build_search_conditions(db_field, keyword, selected_types)
        
        # 準備傳遞給結果頁面的參數
        search_params = {
            'keyword': keyword,
            'field': field,
            'field_display': field,
            'types': types,
            'type_display': [TYPE_MAPPING.get(t, t) for t in types],
            'db_field': db_field,
            'selected_types': selected_types,
            'search_conditions': search_conditions,
            'results_count': len(search_results),
            'results': search_results
        }
        
        logger.info(f"搜尋完成，找到 {len(search_results)} 筆結果")
        return render_template('results.html', search_params=search_params)
        
    except Exception as e:
        logger.error(f"搜尋處理錯誤: {str(e)}")
        return render_template('results.html', 
                            error="搜尋處理時發生錯誤，請稍後再試",
                            search_params={})

@app.route('/search_advanced', methods=['POST'])
def search_advanced():
    """進階搜尋路由"""
    try:
        # 取得表單資料
        conditions_json = request.form.get('conditions', '[]')
        logic = request.form.get('logic', 'AND')
        types = request.form.getlist('types', [])
        
        logger.info(f"進階搜尋請求: 條件={conditions_json}, 邏輯={logic}, 類型={types}")
        
        # 解析條件 JSON
        try:
            import json
            conditions = json.loads(conditions_json)
        except json.JSONDecodeError as e:
            logger.error(f"條件 JSON 解析錯誤: {str(e)}")
            return render_template('results.html', 
                                error="搜尋條件格式錯誤",
                                search_params={})
        
        # 驗證條件
        if not conditions or len(conditions) == 0:
            return render_template('results.html', 
                                error="請至少設定一個搜尋條件",
                                search_params={})
        
        # 映射類型名稱
        selected_types = [TYPE_MAPPING.get(t, t) for t in types]
        
        # 執行進階搜尋
        search_results, error_msg = execute_advanced_search(conditions, logic, selected_types)
        
        if error_msg:
            logger.error(f"進階搜尋錯誤: {error_msg}")
            return render_template('results.html', 
                                error=f"搜尋失敗: {error_msg}",
                                search_params={})
        
        # 如果沒有真實資料，使用模擬測試資料
        if not search_results:
            search_results = generate_advanced_mock_results(conditions, logic, selected_types)
            logger.info(f"使用模擬進階搜尋資料，共 {len(search_results)} 筆")
        
        # 建構進階搜尋條件（用於顯示）
        search_conditions = build_advanced_search_conditions(conditions, logic, selected_types)
        
        # 準備傳遞給結果頁面的參數
        search_params = {
            'is_advanced': True,
            'conditions': conditions,
            'logic': logic,
            'logic_display': 'AND 邏輯' if logic == 'AND' else 'OR 邏輯',
            'types': types,
            'type_display': [TYPE_MAPPING.get(t, t) for t in types],
            'selected_types': selected_types,
            'search_conditions': search_conditions,
            'results': search_results,
            'results_count': len(search_results)
        }
        
        logger.info(f"進階搜尋完成，找到 {len(search_results)} 筆結果")
        return render_template('results.html', search_params=search_params)
        
    except Exception as e:
        logger.error(f"進階搜尋處理錯誤: {str(e)}")
        return render_template('results.html', 
                            error="進階搜尋處理時發生錯誤，請稍後再試",
                            search_params={})

@app.route('/export', methods=['POST'])
def export_results():
    """匯出搜尋結果路由"""
    try:
        # 取得匯出格式
        export_format = request.form.get('format', 'excel')
        search_params_str = request.form.get('search_params', '')
        
        # 解析搜尋參數
        search_params = {}
        if search_params_str:
            from urllib.parse import parse_qs
            parsed_params = parse_qs(search_params_str)
            search_params = {k: v[0] if v else '' for k, v in parsed_params.items()}
        
        # 取得搜尋資料
        keyword = search_params.get('keyword', '')
        field = search_params.get('field', 'all')
        types = search_params.get('types', [])
        if isinstance(types, str):
            types = [types]
        
        # 映射欄位名稱
        db_field = SEARCH_MAPPING.get(field, 'ALL')
        
        # 映射類型名稱
        selected_types = []
        for type_key in types:
            if type_key in TYPE_MAPPING:
                selected_types.append(TYPE_MAPPING[type_key])
        
        # 執行搜尋
        db = get_database()
        if not db:
            logger.error("資料庫連線未初始化")
            return jsonify({'error': '資料庫連線失敗，請聯繫管理員'}), 500
        
        search_results, error_msg = db.execute_search(
            keyword=keyword,
            search_field=db_field,
            document_types=selected_types,
            limit=1000  # 匯出時增加限制
        )
        
        if error_msg:
            logger.error(f"匯出搜尋錯誤: {error_msg}")
            return jsonify({'error': f'搜尋失敗: {error_msg}'}), 500
        
        # 如果沒有真實資料，使用模擬測試資料
        if not search_results:
            search_results = generate_mock_results(keyword, selected_types)
        
        # 生成檔案
        if export_format == 'excel':
            filename = generate_excel_file(search_results, keyword)
        else:  # csv
            filename = generate_csv_file(search_results, keyword)
        
        # 傳送檔案
        return send_file(
            filename,
            as_attachment=True,
            download_name=os.path.basename(filename),
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"匯出處理錯誤: {str(e)}")
        return jsonify({'error': '匯出處理發生錯誤，請稍後再試'}), 500

def generate_excel_file(data, keyword):
    """生成 Excel 檔案"""
    try:
        import pandas as pd
        
        # 準備資料
        df_data = []
        for item in data:
            df_data.append({
                '題名': item.get('title', ''),
                '撰寫人': item.get('author', ''),
                '報告編號': item.get('DOC_ID', ''),
                '資料類型': item.get('document_type', ''),
                '建立日期': item.get('create_date', ''),
                '詳細摘要': item.get('description', '')
            })
        
        # 建立 DataFrame
        df = pd.DataFrame(df_data)
        
        # 生成檔名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Search_Results_{timestamp}.xlsx'
        filepath = os.path.join('temp', filename)
        
        # 建立 temp 目錄
        Path('temp').mkdir(exist_ok=True)
        
        # 匯出 Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='搜尋結果', index=False)
            
            # 調整欄位寬度
            worksheet = writer.sheets['搜尋結果']
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
        
        logger.info(f"Excel 檔案生成成功: {filename}")
        return filepath
        
    except ImportError:
        # 如果沒有 pandas，使用 CSV 方式
        logger.warning("pandas 未安裝，使用 CSV 格式匯出")
        return generate_csv_file(data, keyword)
    except Exception as e:
        logger.error(f"Excel 檔案生成失敗: {str(e)}")
        raise

def generate_csv_file(data, keyword):
    """生成 CSV 檔案"""
    try:
        import csv
        
        # 生成檔名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Search_Results_{timestamp}.csv'
        filepath = os.path.join('temp', filename)
        
        # 建立 temp 目錄
        Path('temp').mkdir(exist_ok=True)
        
        # 寫入 CSV
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['題名', '撰寫人', '報告編號', '資料類型', '建立日期', '詳細摘要']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for item in data:
                writer.writerow({
                    '題名': item.get('title', ''),
                    '撰寫人': item.get('author', ''),
                    '報告編號': item.get('DOC_ID', ''),
                    '資料類型': item.get('document_type', ''),
                    '建立日期': item.get('create_date', ''),
                    '詳細摘要': item.get('description', '')
                })
        
        logger.info(f"CSV 檔案生成成功: {filename}")
        return filepath
        
    except Exception as e:
        logger.error(f"CSV 檔案生成失敗: {str(e)}")
        raise

def generate_advanced_mock_results(conditions, logic, selected_types):
    """
    生成進階搜尋的模擬資料
    根據多條件和邏輯運算子生成相關資料
    
    Args:
        conditions: 搜尋條件列表
        logic: 邏輯運算子 ('AND' 或 'OR')
        selected_types: 選中的資料類型列表
        
    Returns:
        list: 模擬的搜尋結果字典列表
    """
    import random
    from datetime import datetime, timedelta
    
    # 基礎測試資料
    base_data = [
        {
            'title': 'Oracle 資料庫系統設計',
            'author': '張工程師',
            'DOC_ID': f'TECH-{random.randint(1000, 9999)}',
            'document_type': '技術報告',
            'create_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S'),
            'description': '關於 Oracle 資料庫系統設計的詳細技術分析報告'
        },
        {
            'title': '歷史文件管理系統',
            'author': '李分析師',
            'DOC_ID': f'CASE-{random.randint(1000, 9999)}',
            'document_type': '史政',
            'create_date': (datetime.now() - timedelta(days=random.randint(31, 60))).strftime('%Y-%m-%d %H:%M:%S'),
            'description': '歷史文件管理系統的應用案例分析'
        },
        {
            'title': '系統架構最佳實務',
            'author': '王架構師',
            'DOC_ID': f'GUIDE-{random.randint(1000, 9999)}',
            'document_type': '技術報告',
            'create_date': (datetime.now() - timedelta(days=random.randint(61, 90))).strftime('%Y-%m-%d %H:%M:%S'),
            'description': '系統架構設計的最佳實務指南'
        },
        {
            'title': '逸光特刊專題報導',
            'author': '陳編輯',
            'DOC_ID': f'YIGUANG-{random.randint(1000, 9999)}',
            'document_type': '逸光報',
            'create_date': (datetime.now() - timedelta(days=random.randint(91, 120))).strftime('%Y-%m-%d %H:%M:%S'),
            'description': '逸光報導的專題報導內容'
        },
        {
            'title': '數位化檔案管理',
            'author': '林管理員',
            'DOC_ID': f'PHOTO-{random.randint(1000, 9999)}',
            'document_type': '史政照片',
            'create_date': (datetime.now() - timedelta(days=random.randint(121, 150))).strftime('%Y-%m-%d %H:%M:%S'),
            'description': '數位化檔案管理的照片記錄'
        }
    ]
    
    # 根據選中的類型篩選資料
    if selected_types:
        filtered_data = [item for item in base_data if item['document_type'] in selected_types]
    else:
        filtered_data = base_data
    
    # 根據條件進行簡單匹配（模擬）
    # 在實際應用中，這裡會是真正的資料庫查詢
    matched_data = []
    for item in filtered_data:
        match_score = 0
        
        for condition in conditions:
            field = condition.get('field', '')
            operator = condition.get('operator', '')
            value = condition.get('value', '').lower()
            
            if not value:
                continue
            
            # 根據欄位進行匹配
            if field == 'title':
                field_value = item['title'].lower()
            elif field == 'author':
                field_value = item['author'].lower()
            elif field == 'DOC_ID':
                field_value = item['DOC_ID'].lower()
            else:
                field_value = f"{item['title']} {item['author']} {item['DOC_ID']}".lower()
            
            # 簡單的匹配邏輯
            if operator == 'LIKE' or operator == 'LIKE_START' or operator == 'LIKE_END':
                if value in field_value:
                    match_score += 1
            elif operator == '=':
                if value == field_value:
                    match_score += 1
            elif operator == '!=':
                if value != field_value:
                    match_score += 1
            else:
                # 對於其他運算子，簡單處理
                if value in field_value:
                    match_score += 1
        
        # 根據邏輯決定是否匹配
        if logic == 'AND':
            if match_score == len(conditions):
                matched_data.append(item)
        else:  # OR
            if match_score > 0:
                matched_data.append(item)
    
    # 如果沒有匹配的資料，返回部分資料模擬結果
    if not matched_data:
        matched_data = filtered_data[:random.randint(1, 3)]
    
    # 隨機打亂並返回部分結果
    random.shuffle(matched_data)
    return matched_data[:random.randint(3, len(matched_data))]

def build_advanced_search_conditions(conditions, logic, selected_types):
    """
    建構進階搜尋條件 SQL（用於顯示）
    
    Args:
        conditions: 搜尋條件列表
        logic: 邏輯運算子
        selected_types: 選中的資料類型列表
        
    Returns:
        dict: 包含 SQL 查詢和綁定參數的字典
    """
    conditions_list = []
    bind_params = {}
    
    # 處理每個搜尋條件
    for i, condition in enumerate(conditions):
        field = condition.get('field', 'title')
        operator = condition.get('operator', 'LIKE')
        value = condition.get('value', '')
        
        if not value:
            continue
        
        # 建構條件
        if operator == 'LIKE':
            condition_sql = f"{field} LIKE :value_{i}"
            bind_params[f"value_{i}"] = f'%{value}%'
        elif operator == 'LIKE_START':
            condition_sql = f"{field} LIKE :value_{i}"
            bind_params[f"value_{i}"] = f'{value}%'
        elif operator == 'LIKE_END':
            condition_sql = f"{field} LIKE :value_{i}"
            bind_params[f"value_{i}"] = f'%{value}'
        elif operator == '=':
            condition_sql = f"{field} = :value_{i}"
            bind_params[f"value_{i}"] = value
        elif operator == '!=':
            condition_sql = f"{field} != :value_{i}"
            bind_params[f"value_{i}"] = value
        elif operator == '>':
            condition_sql = f"{field} > :value_{i}"
            bind_params[f"value_{i}"] = value
        elif operator == '<':
            condition_sql = f"{field} < :value_{i}"
            bind_params[f"value_{i}"] = value
        elif operator == '>=':
            condition_sql = f"{field} >= :value_{i}"
            bind_params[f"value_{i}"] = value
        elif operator == '<=':
            condition_sql = f"{field} <= :value_{i}"
            bind_params[f"value_{i}"] = value
        else:
            condition_sql = f"{field} LIKE :value_{i}"
            bind_params[f"value_{i}"] = f'%{value}%'
        
        conditions_list.append(condition_sql)
    
    # 處理文件類型篩選
    if selected_types:
        type_conditions = []
        for i, type_name in enumerate(selected_types):
            type_conditions.append(f"document_type = :type_{i}")
            bind_params[f"type_{i}"] = type_name
        
        if conditions_list:
            conditions_list.append(f"({' OR '.join(type_conditions)})")
        else:
            conditions_list = type_conditions
    
    # 組合 WHERE 子句
    if conditions_list:
        if logic == 'AND':
            where_clause = " WHERE " + " AND ".join(conditions_list)
        else:
            where_clause = " WHERE " + " OR ".join(conditions_list)
    else:
        where_clause = ""
    
    # 建構完整 SQL 查詢
    sql_example = f"""
    SELECT title, author, DOC_ID, document_type, create_date 
    FROM documents 
    {where_clause}
    ORDER BY create_date DESC
    """
    
    return {
        'sql_query': sql_example.strip(),
        'bind_params': bind_params,
        'where_clause': where_clause.strip(),
        'conditions_count': len(conditions),
        'logic': logic
    }

def execute_advanced_search(conditions, logic, selected_types):
    """
    執行進階搜尋
    
    Args:
        conditions: 搜尋條件列表
        logic: 邏輯運算子
        selected_types: 選中的資料類型列表
        
    Returns:
        tuple: (搜尋結果列表, 錯誤訊息)
    """
    try:
        # 在實際應用中，這裡會執行真正的資料庫查詢
        # 目前返回空結果，讓系統使用模擬資料
        return [], None
        
    except Exception as e:
        error_msg = f"進階搜尋執行失敗: {str(e)}"
        logger.error(error_msg)
        return [], error_msg

def build_search_conditions(db_field, keyword, selected_types):
    """
    建構搜尋條件邏輯
    遵循安全規範：使用綁定變數，避免字串拼接
    """
    conditions = []
    bind_params = {}
    
    # 基礎關鍵字搜尋條件
    if db_field == 'ALL':
        # 全部欄位搜尋邏輯
        keyword_conditions = [f"{field_name} LIKE :keyword" for field_name in ['title', 'author', 'DOC_ID']]
        conditions.append(f"({' OR '.join(keyword_conditions)})")
        bind_params['keyword'] = f'%{keyword}%'
    else:
        # 特定欄位搜尋邏輯
        conditions.append(f"{db_field} LIKE :keyword")
        bind_params['keyword'] = f'%{keyword}%'
    
    # 文件類型篩選條件
    if selected_types:
        type_placeholders = [f":type_{i}" for i in range(len(selected_types))]
        conditions.append(f"document_type IN ({', '.join(type_placeholders)})")
        for i, type_name in enumerate(selected_types):
            bind_params[f"type_{i}"] = type_name
    
    # 組合 WHERE 子句
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    # 完整的 SQL 查詢範例（使用綁定變數）
    sql_example = f"""
    SELECT title, author, DOC_ID, document_type, create_date 
    FROM documents 
    {where_clause}
    ORDER BY create_date DESC
    """
    
    return {
        'sql_query': sql_example.strip(),
        'bind_params': bind_params,
        'where_clause': where_clause.strip()
    }

def generate_mock_results(keyword, selected_types):
    """
    生成模擬搜尋結果資料
    用於測試和開發階段
    
    Args:
        keyword: 搜尋關鍵字
        selected_types: 選中的資料類型列表
        
    Returns:
        list: 模擬的搜尋結果字典列表
    """
    import random
    from datetime import datetime, timedelta
    
    # 基礎測試資料
    base_data = [
        {
            'title': f'{keyword} 系統設計與實作',
            'author': '張工程師',
            'DOC_ID': f'TECH-{random.randint(1000, 9999)}',
            'document_type': '技術報告',
            'create_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S'),
            'description': f'關於 {keyword} 的詳細技術分析報告'
        },
        {
            'title': f'{keyword} 應用案例研究',
            'author': '李分析師',
            'DOC_ID': f'CASE-{random.randint(1000, 9999)}',
            'document_type': '史政',
            'create_date': (datetime.now() - timedelta(days=random.randint(31, 60))).strftime('%Y-%m-%d %H:%M:%S'),
            'description': f'{keyword} 在歷史事件中的應用分析'
        },
        {
            'title': f'{keyword} 相關照片集',
            'author': '王攝影師',
            'DOC_ID': f'PHOTO-{random.randint(1000, 9999)}',
            'document_type': '史政照片',
            'create_date': (datetime.now() - timedelta(days=random.randint(61, 90))).strftime('%Y-%m-%d %H:%M:%S'),
            'description': f'記錄 {keyword} 相關的歷史照片'
        },
        {
            'title': f'{keyword} 逸光特刊',
            'author': '陳編輯',
            'DOC_ID': f'YIGUANG-{random.randint(1000, 9999)}',
            'document_type': '逸光報',
            'create_date': (datetime.now() - timedelta(days=random.randint(91, 120))).strftime('%Y-%m-%d %H:%M:%S'),
            'description': f'逸光報導關於 {keyword} 的專題報導'
        },
        {
            'title': f'{keyword} 最佳實務指南',
            'author': '林顧問',
            'DOC_ID': f'GUIDE-{random.randint(1000, 9999)}',
            'document_type': '技術報告',
            'create_date': (datetime.now() - timedelta(days=random.randint(121, 150))).strftime('%Y-%m-%d %H:%M:%S'),
            'description': f'{keyword} 實施的最佳實務與建議'
        }
    ]
    
    # 根據選中的類型篩選資料
    if selected_types:
        filtered_data = [item for item in base_data if item['document_type'] in selected_types]
    else:
        filtered_data = base_data
    
    # 隨機打亂並返回部分結果
    random.shuffle(filtered_data)
    return filtered_data[:random.randint(3, len(filtered_data))]

@app.errorhandler(500)
def internal_error(error):
    """內部伺服器錯誤處理"""
    logger.error(f"內部錯誤: {str(error)}")
    return render_template('error.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    """404 錯誤處理"""
    logger.warning(f"頁面未找到: {request.url}")
    return render_template('error.html'), 404

@app.teardown_appcontext
def teardown_db(exception=None):
    """應用程式上下文結束時的清理工作"""
    # 這裡可以添加每個請求結束時的清理邏輯
    pass

@app.teardown_request
def teardown_request(exception=None):
    """請求結束時的清理工作"""
    # 這裡可以添加請求結束時的清理邏輯
    pass

def cleanup_on_exit():
    """應用程式退出時的清理工作"""
    try:
        logger.info("應用程式關閉中，清理資源...")
        close_database()
        logger.info("資源清理完成")
    except Exception as e:
        logger.error(f"資源清理錯誤: {str(e)}")

import atexit
atexit.register(cleanup_on_exit)

if __name__ == '__main__':
    logger.info("Flask 應用程式啟動")
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        logger.info("收到中斷信號，關閉應用程式")
    finally:
        cleanup_on_exit()
