from flask import Flask, request, jsonify
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from fetch_stock_data.tw import fetch_stock_tickers
import os
from datetime import datetime
import logging

app = Flask(__name__)

# 配置日志记录
logging.basicConfig(level=logging.INFO)

def validate_date(date_text):
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        return False
    return True

@app.route('/fetch-stock-data', methods=['POST'])
def fetch_stock_data():
    data = request.get_json()
    
    # 取得輸入參數
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    output_format = data.get('output_format')
    save_path = data.get('save_path')
    filter_industry = data.get('industry', None)
    sort_by = data.get('sort_by', 'date')  # 默認按日期排序
    
    # 日期格式验证
    if not (validate_date(start_date) and validate_date(end_date)):
        return jsonify({'error': '日期格式不正確，請使用YYYY-MM-DD格式。'}), 400

    # 設定URL
    url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'
    
    # 取得台灣所有股票代碼
    stock_data = fetch_stock_tickers(url)
    
    # 如果提供了行業過濾條件，則過濾股票
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
            logging.error(f"無法獲取 {ticker} 的數據: {e}")

    if not df_list:
        return jsonify({'error': '未獲取到任何股票數據'}), 404

    df = pd.concat(df_list)

    # 根据排序条件进行排序
    if sort_by == 'price':
        df = df.sort_values(by='Close')
    else:  # 默认按日期排序
        df = df.sort_index()

    # 輸出格式處理
    file_name = f'stock_data_{start_date}_{end_date}.{output_format}'
    if output_format == 'csv':
        df.to_csv(os.path.join(save_path, file_name))
        return jsonify({'status': 'CSV saved successfully', 'file': file_name})
    
    elif output_format == 'json':
        result = df.to_json(orient='records')
        with open(os.path.join(save_path, file_name), 'w') as f:
            f.write(result)
        return jsonify({'status': 'JSON saved successfully', 'file': file_name})
    
    elif output_format == 'html':
        html_content = df.to_html()
        with open(os.path.join(save_path, file_name), 'w') as f:
            f.write(html_content)
        return jsonify({'status': 'HTML saved successfully', 'file': file_name})
    
    elif output_format == 'chart':
        df['Close'].plot()
        plt.title('Stock Prices')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.savefig(os.path.join(save_path, file_name))
        return jsonify({'status': 'Chart saved successfully', 'file': file_name})
    
    return jsonify({'error': '無效的輸出格式'}), 400

@app.route('/get-live-price/<ticker>', methods=['GET'])
def get_live_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        last_quote = data['Close'].iloc[-1]
        return jsonify({'ticker': ticker, 'last_price': last_quote})
    except Exception as e:
        logging.error(f"獲取 {ticker} 的即時價格失敗: {str(e)}")
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True)
