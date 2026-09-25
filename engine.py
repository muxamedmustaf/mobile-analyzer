# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

def calculate_indicators(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    return df

def get_pivot_points(df, order=5):
    df['Peak'] = df['High'][(df['High'] == df['High'].rolling(window=2*order+1, center=True).max())]
    df['Trough'] = df['Low'][(df['Low'] == df['Low'].rolling(window=2*order+1, center=True).min())]
    
    nodes = []
    for time_idx, val in df['Peak'].dropna().items():
        nodes.append({'time': time_idx, 'price': val, 'type': 'peak', 'idx': df.index.get_loc(time_idx)})
    for time_idx, val in df['Trough'].dropna().items():
        nodes.append({'time': time_idx, 'price': val, 'type': 'trough', 'idx': df.index.get_loc(time_idx)})
        
    nodes = sorted(nodes, key=lambda x: x['idx'])
    
    clean_nodes = []
    for node in nodes:
        if not clean_nodes:
            clean_nodes.append(node)
        else:
            if clean_nodes[-1]['type'] != node['type']:
                clean_nodes.append(node)
            else:
                if node['type'] == 'peak' and node['price'] > clean_nodes[-1]['price']:
                    clean_nodes[-1] = node
                elif node['type'] == 'trough' and node['price'] < clean_nodes[-1]['price']:
                    clean_nodes[-1] = node
                    
    df.drop(columns=['Peak', 'Trough'], inplace=True)
    return clean_nodes

def detect_confirmed_patterns(df, nodes):
    patterns = []
    if len(nodes) < 5: return patterns
        
    for i in range(len(nodes) - 4):
        window = nodes[i:i+5]
        types = [n['type'] for n in window]
        
        # 1. الرأس والكتفين المعكوس (شراء)
        if types == ['trough', 'peak', 'trough', 'peak', 'trough']:
            ls, p1, head, p2, rs = window
            if head['price'] < ls['price'] and head['price'] < rs['price']:
                idx1, y1 = p1['idx'], p1['price']
                idx2, y2 = p2['idx'], p2['price']
                
                if idx1 != idx2:
                    slope = (y2 - y1) / (idx2 - idx1) # الحساب عبر الإندكس لتجاوز فجوات الإجازات
                    
                    for j in range(rs['idx'] + 1, len(df)):
                        neckline_price = y2 + slope * (j - idx2)
                        close_price = df['Close'].iloc[j]
                        
                        # الشرط الأول: شمعة الكسر تغلق أعلى خط العنق
                        if close_price > neckline_price:
                            rsi_val = df['RSI'].iloc[j]
                            ema50 = df['EMA50'].iloc[j]
                            ema200 = df['EMA200'].iloc[j]
                            
                            # الشروط في لحظة الكسر: RSI بين 30-75 و EMA50 أسفل EMA200 (اتجاه هابط مسبق)
                            if (30 <= rsi_val <= 75) and (ema50 < ema200):
                                entry = close_price
                                sl = head['price']
                                tp = entry + (neckline_price - head['price'])
                                patterns.append({
                                    'pattern': 'Inverse Head & Shoulders', 'signal': 'STRONG BUY',
                                    'nodes': [(n['time'], n['price']) for n in window],
                                    'neckline_nodes': [(p1['time'], p1['price']), (p2['time'], p2['price'])],
                                    'target_nodes': [(df.index[j], entry), (df.index[j], tp)],
                                    'entry': entry, 'sl': sl, 'tp': tp, 'end_idx': j
                                })
                            break # إنهاء البحث عن الكسر لهذا النمط بمجرد حدوث اختراق (سواء حقق الشروط أو لا)

        # 2. الرأس والكتفين الكلاسيكي (بيع)
        elif types == ['peak', 'trough', 'peak', 'trough', 'peak']:
            ls, t1, head, t2, rs = window
            if head['price'] > ls['price'] and head['price'] > rs['price']:
                idx1, y1 = t1['idx'], t1['price']
                idx2, y2 = t2['idx'], t2['price']
                
                if idx1 != idx2:
                    slope = (y2 - y1) / (idx2 - idx1)
                    
                    for j in range(rs['idx'] + 1, len(df)):
                        neckline_price = y2 + slope * (j - idx2)
                        close_price = df['Close'].iloc[j]
                        
                        # الشرط الأول: شمعة الكسر تغلق أسفل خط العنق
                        if close_price < neckline_price:
                            rsi_val = df['RSI'].iloc[j]
                            ema50 = df['EMA50'].iloc[j]
                            ema200 = df['EMA200'].iloc[j]
                            
                            # الشروط في لحظة الكسر: RSI بين 30-75 و EMA50 أعلى EMA200 (اتجاه صاعد مسبق)
                            if (30 <= rsi_val <= 75) and (ema50 > ema200):
                                entry = close_price
                                sl = head['price']
                                tp = entry - (head['price'] - neckline_price)
                                patterns.append({
                                    'pattern': 'Head & Shoulders', 'signal': 'STRONG SELL',
                                    'nodes': [(n['time'], n['price']) for n in window],
                                    'neckline_nodes': [(t1['time'], t1['price']), (t2['time'], t2['price'])],
                                    'target_nodes': [(df.index[j], entry), (df.index[j], tp)],
                                    'entry': entry, 'sl': sl, 'tp': tp, 'end_idx': j
                                })
                            break

    return patterns

def run_full_analysis(df):
    df = calculate_indicators(df)
    nodes = get_pivot_points(df, order=5)
    patterns = detect_confirmed_patterns(df, nodes)
    
    if patterns:
        latest = patterns[-1]
        return {
            "signal": latest['signal'], "pattern": latest['pattern'],
            "entry": round(latest['entry'], 5), "sl": round(latest['sl'], 5), "tp": round(latest['tp'], 5),
            "df": df, "nodes": latest['nodes'], 
            "neckline_nodes": latest.get('neckline_nodes', []), "target_nodes": latest.get('target_nodes', [])
        }
        
    return {
        "signal": "NEUTRAL", "pattern": "None", "entry": 0.0, "sl": 0.0, "tp": 0.0,
        "df": df, "nodes": [], "neckline_nodes": [], "target_nodes": []
    }
