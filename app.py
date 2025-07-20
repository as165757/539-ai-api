from flask import Flask, jsonify, request
import pandas as pd
from collections import Counter
from datetime import datetime
from lunardate import LunarDate
import os

app = Flask(__name__)

# === 1. 載入資料 ===
files = [
    "今彩539_2018.csv",
    "今彩539_2019.csv",
    "今彩539_2020.csv",
    "今彩539_2021.csv",
    "今彩539_2022.csv",
    "今彩539_2023.csv",
    "今彩539_2024.csv",
    "今彩539_2025.csv"
]

def 轉農曆月份(date_obj):
    try:
        lunar = LunarDate.fromSolarDate(date_obj.year, date_obj.month, date_obj.day)
        return lunar.month
    except:
        return None

def load_data():
    dfs = []
    for file in files:
        if not os.path.exists(file):
            continue
        try:
            df = pd.read_csv(file)
            df = df[[col for col in df.columns if '期別' in col or '開獎日期' in col or '獎號' in col]]
            if len(df.columns) >= 7:
                df.columns = ['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4', '獎號5']
                df = df.dropna()
                df['開獎日期'] = pd.to_datetime(df['開獎日期'], errors='coerce')
                df.dropna(subset=['開獎日期'], inplace=True)
                df['農曆月'] = df['開獎日期'].apply(轉農曆月份)
                dfs.append(df)
        except Exception as e:
            continue
    return pd.concat(dfs, ignore_index=True)

df_all = load_data()

# 預測號碼
def predict_numbers(top_n=5, recent=200):
    data = df_all.tail(recent)
    numbers = data[['獎號1','獎號2','獎號3','獎號4','獎號5']].values.flatten()
    counter = Counter(numbers)
    most_common = counter.most_common(top_n)
    return sorted([int(num) for num, _ in most_common])

# 農曆分析
def lunar_month_analysis():
    recent = df_all.sort_values(by='開獎日期', ascending=False).head(200)
    recent = recent.dropna(subset=['農曆月'])
    top_month = recent['農曆月'].mode()[0]
    filtered = recent[recent['農曆月'] == top_month]
    numbers = filtered[['獎號1','獎號2','獎號3','獎號4','獎號5']].values.flatten()
    counter = Counter(numbers)
    result = sorted([int(num) for num, _ in counter.most_common(3)])
    return top_month, result

# API
@app.route('/predict', methods=['GET'])
def predict():
    date = request.args.get('date', datetime.now().strftime(\"%Y-%m-%d\"))
    recommended = predict_numbers()
    return jsonify({
        'predict_date': date,
        'strategy': '依照過去200期高頻號碼統計推薦',
        'recommended_numbers': recommended
    })

@app.route('/lunar', methods=['GET'])
def lunar():
    month, numbers = lunar_month_analysis()
    return jsonify({
        '熱門農曆月': month,
        '推薦號碼': numbers,
        '策略': '近200期資料中最多出現的農曆月之號碼'
    })

@app.route('/strategy', methods=['GET'])
def strategy():
    return jsonify({
        'strategies': [
            '五區分布法',
            '對角連線圖',
            '跳點補缺法',
            '尾數版路',
            '直欄重複法',
            '農曆月份分析'
        ],
        'current_logic': '目前採用「高頻統計法」與「農曆月模式分析」預測'
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
