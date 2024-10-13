import requests
import pandas as pd
from bs4 import BeautifulSoup

def fetch_stock_tickers(url):
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception("無法獲取資料，請檢查網絡連接或URL是否正確。")

    # 解析 HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    stock_table = soup.find('table', {'class': 'h4'})

    tickers = []
    for row in stock_table.find_all('tr')[1:]:  # 略過標題行
        cols = row.find_all('td')
        if cols:
            ticker = cols[1].text.strip() + '.TW'  # 股票代碼加上 .TW
            company_name = cols[2].text.strip()  # 公司名稱
            industry = cols[3].text.strip()  # 行業
            tickers.append({'ticker': ticker, 'name': company_name, 'industry': industry})
    
    return tickers
