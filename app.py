from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from fetch_stock_data import fetch_stock_tickers
import os
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)  # 允许所有来源的跨域请求

# 配置日志记录
logging.basicConfig(level=logging.INFO)

# 用于跟踪API请求的数量
request_count = 0

def validate_date(date_text):
    """验证日期格式"""
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        return False
    return True

@app.route('/')
def index():
    """返回主页面"""
    return render_template('index.html')

@app.route('/fetch-stock-data-web', methods=['POST'])
def fetch_stock_data_web():
    """处理来自前端的股票数据请求（网页版本）"""
    data = request.get_json()

    # 获取输入参数
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    output_format = data.get('output_format')
    filter_industry = data.get('industry', None)
    sort_by = data.get('sort_by', 'date')  # 默认按日期排序

    # 日期格式验证
    if not (validate_date(start_date) and validate_date(end_date)):
        return jsonify({'error': '日期格式不正确，请使用YYYY-MM-DD格式。'}), 400

    # 设置URL
    url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'
    
    # 获取台湾所有股票代码
    stock_data = fetch_stock_tickers(url)
    
    # 如果提供了行业过滤条件，则过滤股票
    if filter_industry:
        stock_data = [stock for stock in stock_data if stock['industry'] == filter_industry]
    
    tickers = [stock['ticker'] for stock in stock_data]

    df_list = []
    for ticker in tickers:
        try:
            stock_history = yf.download(ticker, start=start_date, end=end_date)
            stock_history['Ticker'] = ticker
            df_list.append(stock_history)
        except Exception as e:
            logging.error(f"无法获取 {ticker} 的数据: {e}")

    if not df_list:
        return jsonify({'error': '未获取到任何股票数据'}), 404

    df = pd.concat(df_list)

    # 根据排序条件进行排序
    df = df.sort_values(by='Close') if sort_by == 'price' else df.sort_index()

    # 输出格式处理
    file_name = f'stock_data_{start_date}_{end_date}.{output_format}'
    file_path = os.path.join(os.getcwd(), file_name)

    try:
        if output_format == 'csv':
            df.to_csv(file_path)
        elif output_format == 'json':
            result = df.to_json(orient='records')
            with open(file_path, 'w') as f:
                f.write(result)
        elif output_format == 'html':
            html_content = df.to_html()
            with open(file_path, 'w') as f:
                f.write(html_content)
        elif output_format == 'chart':
            plt.figure(figsize=(10, 5))
            df['Close'].plot(title='Stock Prices')
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.grid()
            plt.savefig(file_path)
            plt.close()  # 关闭图形以释放内存
        else:
            return jsonify({'error': '无效的输出格式'}), 400

        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        logging.error(f"文件处理失败: {e}")
        return jsonify({'error': '文件处理失败'}), 500

@app.route('/fetch-stock-data', methods=['POST'])
def fetch_stock_data():
    """处理来自前端的股票数据请求"""
    global request_count
    request_count += 1  # 增加请求计数

    data = request.get_json()

    # 获取输入参数
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    output_format = data.get('output_format')
    save_path = os.getcwd()  # 使用当前工作目录
    filter_industry = data.get('industry', None)
    sort_by = data.get('sort_by', 'date')  # 默认按日期排序

    # 日期格式验证
    if not (validate_date(start_date) and validate_date(end_date)):
        return jsonify({'error': '日期格式不正确，请使用YYYY-MM-DD格式。'}), 400

    # 设置URL
    url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'
    
    # 获取台湾所有股票代码
    stock_data = fetch_stock_tickers(url)
    
    # 如果提供了行业过滤条件，则过滤股票
    if filter_industry:
        stock_data = [stock for stock in stock_data if stock['industry'] == filter_industry]
    
    tickers = [stock['ticker'] for stock in stock_data]

    df_list = []
    for ticker in tickers:
        try:
            stock_history = yf.download(ticker, start=start_date, end=end_date)
            stock_history['Ticker'] = ticker
            df_list.append(stock_history)
        except Exception as e:
            logging.error(f"无法获取 {ticker} 的数据: {e}")

    if not df_list:
        return jsonify({'error': '未获取到任何股票数据'}), 404

    df = pd.concat(df_list)

    # 根据排序条件进行排序
    df = df.sort_values(by='Close') if sort_by == 'price' else df.sort_index()

    # 输出格式处理
    file_name = f'stock_data_{start_date}_{end_date}.{output_format}'
    try:
        if output_format == 'csv':
            df.to_csv(os.path.join(save_path, file_name))
        elif output_format == 'json':
            result = df.to_json(orient='records')
            with open(os.path.join(save_path, file_name), 'w') as f:
                f.write(result)
        elif output_format == 'html':
            html_content = df.to_html()
            with open(os.path.join(save_path, file_name), 'w') as f:
                f.write(html_content)
        elif output_format == 'chart':
            df['Close'].plot()
            plt.title('Stock Prices')
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.savefig(os.path.join(save_path, file_name))
        else:
            return jsonify({'error': '无效的输出格式'}), 400

        return jsonify({'status': f'{output_format.upper()} saved successfully', 'file': file_name})
    
    except Exception as e:
        logging.error(f"文件处理失败: {e}")
        return jsonify({'error': '文件处理失败'}), 500

@app.route('/get-live-price/<ticker>', methods=['GET'])
def get_live_price(ticker):
    """获取实时股票价格"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        last_quote = data['Close'].iloc[-1]
        return jsonify({'ticker': ticker, 'last_price': last_quote})
    except Exception as e:
        logging.error(f"获取 {ticker} 的即时价格失败: {str(e)}")
        return jsonify({'error': str(e)}), 404

@app.route('/monitor', methods=['GET'])
def monitor():
    """监控API请求数量"""
    plt.figure(figsize=(10, 5))
    plt.bar([0], [request_count], color='blue')
    plt.title('API Requests Monitor')
    plt.xlabel('API Call Count')
    plt.ylabel('Number of Requests')
    
    # 保存为PNG文件
    image_path = 'static/api_monitor.png'
    plt.savefig(image_path)
    plt.close()  # 关闭图形，以免内存泄露
    
    return send_file(image_path, mimetype='image/png')

if __name__ == '__main__':
    # 确保保存PNG的目录存在
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True, port=10000, host='0.0.0.0')
