import pandas as pd
# import pandas_ta as ta  # 삭제 (설치 오류 방지)
import FinanceDataReader as fdr
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re

class DataAnalyst:
    def __init__(self):
        print("데이터 분석기 초기화 중...")

    def get_index_history(self, index_code="KS11", days=60):
        """코스피/코스닥 등의 지수 이력 수집 (차트용)"""
        print(f"지수 이력 수집 중 ({index_code})...")
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days*2)).strftime("%Y-%m-%d")
            df = fdr.DataReader(index_code, start_date, end_date)
            return df.tail(days)
        except Exception as e:
            print(f"지수 이력 수집 오류 ({index_code}): {e}")
            return pd.DataFrame()

    def get_stock_history(self, ticker, days=60):
        """개별 종목의 OHLCV 이력 수집 (일봉 차트용)"""
        print(f"종목 이력 수집 중 ({ticker})...")
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days*2)).strftime("%Y-%m-%d")
            df = fdr.DataReader(ticker, start_date, end_date)
            return df.tail(days)
        except Exception as e:
            print(f"종목 이력 수집 오류 ({ticker}): {e}")
            return pd.DataFrame()

    def get_market_briefing(self):
        """코스피/코스닥 상세 시황 수집 (종가, 등락, 거래대금)"""
        print("시장 브리핑 수집 중...")
        url = "https://finance.naver.com/sise/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        briefing = {"kospi": {}, "kosdaq": {}}
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 코스피
            kospi_area = soup.select_one("#KOSPI_now")
            if kospi_area:
                briefing["kospi"]["now"] = kospi_area.get_text().strip()
                change_area = soup.select_one("#KOSPI_change")
                if change_area:
                    briefing["kospi"]["change"] = change_area.get_text().strip().replace("\n", " ").split()[0]
                    briefing["kospi"]["rate"] = change_area.get_text().strip().replace("\n", " ").split()[-1]
                
                # 거래대금 수집 (KOSPI)
                for li in soup.select(".lst_pop li"):
                    if "거래대금" in li.get_text():
                        briefing["kospi"]["amount"] = li.select_one(".nm").next_sibling.strip() if li.select_one(".nm") else "정보없음"
            
            # 코스닥
            kosdaq_area = soup.select_one("#KOSDAQ_now")
            if kosdaq_area:
                briefing["kosdaq"]["now"] = kosdaq_area.get_text().strip()
                change_area = soup.select_one("#KOSDAQ_change")
                if change_area:
                    briefing["kosdaq"]["change"] = change_area.get_text().strip().replace("\n", " ").split()[0]
                    briefing["kosdaq"]["rate"] = change_area.get_text().strip().replace("\n", " ").split()[-1]
                
        except Exception as e:
            print(f"시장 브리핑 수집 오류: {e}")
            
        return briefing

    def get_sector_trends(self):
        """주요 섹터별 등락율 수집 (당일, 5일, 20일)"""
        print("섹터별 시계열 동향 분석 중...")
        url = "https://finance.naver.com/sise/sise_group.naver?type=upjong"
        headers = {'User-Agent': 'Mozilla/5.0'}
        sectors = []
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select("table.type_5 tr")
            
            for row in rows:
                cols = row.select("td")
                if len(cols) < 4: continue
                
                name_tag = cols[0].select_one("a")
                if not name_tag: continue
                
                name = name_tag.get_text().strip()
                change_str = cols[1].get_text().strip()
                
                try:
                    detail_url = "https://finance.naver.com" + name_tag['href']
                    detail_res = requests.get(detail_url, headers=headers)
                    detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
                    
                    stock_names = []
                    name_tags = detail_soup.select("td.name a")
                    for s_tag in name_tags[:5]:
                        stock_names.append(s_tag.get_text().strip())
                    top_stocks_str = ", ".join(stock_names)
                    
                    f_net_total = 0
                    i_net_total = 0
                    
                    rows_detail = detail_soup.select("table.type_5 tr")
                    count = 0
                    for r_detail in rows_detail:
                        cols_s = r_detail.select("td")
                        if len(cols_s) < 12: continue
                        try:
                            f_val = cols_s[10].get_text().strip().replace(",", "")
                            i_val = cols_s[11].get_text().strip().replace(",", "")
                            if f_val and f_val != "0": f_net_total += int(f_val)
                            if i_val and i_val != "0": i_net_total += int(i_val)
                            count += 1
                        except: continue
                        if count >= 5: break

                    rep_ticker = name_tags[0]['href'].split('=')[-1] if name_tags else ""
                    
                    if rep_ticker:
                        end_date = datetime.now().strftime("%Y-%m-%d")
                        start_date = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")
                        df = fdr.DataReader(rep_ticker, start_date, end_date)
                        
                        if len(df) < 20: continue
                        
                        curr_price = df['Close'].iloc[-1]
                        price_5d = df['Close'].iloc[-6] if len(df) >= 6 else df['Close'].iloc[0]
                        price_20d = df['Close'].iloc[-21] if len(df) >= 21 else df['Close'].iloc[0]
                        
                        ret_5d = ((curr_price - price_5d) / price_5d) * 100
                        ret_20d = ((curr_price - price_20d) / price_20d) * 100
                    else:
                        ret_5d, ret_20d = 0, 0
                    
                    rate_today = float(change_str.replace("%", "").replace("+", "").replace("-", ""))
                    if rate_today > 1.5: weather = "☀️"
                    elif rate_today >= 0: weather = "☁️"
                    else: weather = "🌧️"
                    
                    sectors.append({
                        "name": name,
                        "rate": change_str,
                        "ret_5d": f"{ret_5d:+.1f}%",
                        "ret_20d": f"{ret_20d:+.1f}%",
                        "weather": weather,
                        "score": rate_today,
                        "rep_ticker": rep_ticker,
                        "top_stocks": top_stocks_str,
                        "f_net": f_net_total,
                        "i_net": i_net_total,
                        "p_net": -(f_net_total + i_net_total)
                    })
                except:
                    continue
        except Exception as e:
            print(f"섹터 분석 오류: {e}")
            
        sectors.sort(key=lambda x: x['score'], reverse=True)
        return sectors[:10]

    def get_etf_holdings(self, ticker):
        """ETF 주요 구성 종목(TOP 5) 수집"""
        try:
            api_url = f"https://m.stock.naver.com/api/stock/{ticker}/integration"
            api_res = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            api_data = api_res.json()
            
            holdings = []
            cu_infos = api_data.get('etfCuInfos', [])
            for info in cu_infos[:5]:
                holdings.append(info.get('stockName', ''))
            
            return ", ".join(holdings) if holdings else "정보 미흡"
        except Exception as e:
            print(f"ETF 구성종목 수집 오류 ({ticker}): {e}")
            return "분석 중"

    def get_global_market_status(self):
        """해외 시장(미국) 동향 수집"""
        print("해외 시장(미국) 데이터 수집 중...")
        indices = {"NASDAQ": "IXIC", "S&P500": "US500", "SOXX": "SOXX"}
        global_status = {}
        try:
            for name, symbol in indices.items():
                df = fdr.DataReader(symbol)
                if len(df) >= 2:
                    current = df['Close'].iloc[-1]
                    prev = df['Close'].iloc[-2]
                    change_rate = ((current - prev) / prev) * 100
                    global_status[name] = {"price": current, "change_rate": round(change_rate, 2)}
            return global_status
        except Exception as e:
            print(f"해외 시장 데이터 수집 오류: {e}")
            return {}

    def get_etf_trends(self):
        """ETF 당일 등락율 상위 10종목 수집"""
        print("ETF 시장 동향 분석 중...")
        try:
            df_etf = fdr.StockListing('ETF/KR')
            if 'ChgRate' in df_etf.columns:
                df_etf = df_etf.sort_values(by='ChgRate', ascending=False)
            
            top_etfs = df_etf.head(15).to_dict('records')
            etf_results = []
            for item in top_etfs:
                ticker = item['Symbol']
                try:
                    df_hist = fdr.DataReader(ticker, (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d"))
                    if len(df_hist) < 2: continue
                    
                    curr_price = df_hist['Close'].iloc[-1]
                    prev_close = df_hist['Close'].iloc[-2]
                    daily_change = ((curr_price - prev_close) / prev_close) * 100
                    
                    ret_5d = ((curr_price - df_hist['Close'].iloc[-6]) / df_hist['Close'].iloc[-6] * 100) if len(df_hist) >= 6 else 0
                    ret_20d = ((curr_price - df_hist['Close'].iloc[-21]) / df_hist['Close'].iloc[-21] * 100) if len(df_hist) >= 21 else 0
                    
                    f_net, i_net, p_net, _, _ = self.get_investor_trend(ticker)
                    
                    etf_results.append({
                        "name": item['Name'], "rate": f"{daily_change:+.2f}%",
                        "ret_5d": f"{ret_5d:+.2f}%", "ret_20d": f"{ret_20d:+.2f}%",
                        "top_stocks": self.get_etf_holdings(ticker),
                        "f_net": f_net, "i_net": i_net, "p_net": p_net, "score": daily_change
                    })
                    if len(etf_results) >= 10: break
                except: continue
            return etf_results
        except: return []

    def get_top_market_news(self):
        """주요 증권 뉴스 수집"""
        print("주요 시장 뉴스 수집 중...")
        url = "https://finance.naver.com/news/mainnews.naver"
        market_news = []
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            news_titles = soup.select(".articleSubject a")
            for title in news_titles[:5]:
                market_news.append(title.get_text().strip())
        except: pass
        return market_news

    def get_semiconductor_tickers(self):
        """반도체 종목 수집"""
        url = "https://finance.naver.com/sise/sise_group_detail.naver?type=upjong&no=278"
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.select('div.name_area a')
            return [link['href'].split('=')[-1] for link in links]
        except: return []

    def get_market_rankings(self):
        """거래량 상위 종목 수집"""
        tickers = self.get_semiconductor_tickers()
        for sosok in [0, 1]:
            url = f"https://finance.naver.com/sise/sise_quant.naver?sosok={sosok}"
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.select('a.tltle')
            for link in links[:20]:
                tickers.append(link['href'].split('=')[-1])
        return list(dict.fromkeys(tickers))

    def get_financial_trend(self, ticker):
        """재무 데이터 수집"""
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        f_data = {'is_growing': False, 'profits': [], 'pbr': 0.0, 'roe': 0.0, 'per': 0.0, 'target_price': 0}
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            section = soup.select_one(".section.cop_analysis")
            if section:
                for row in section.select("tr"):
                    txt = row.get_text()
                    if "영업이익" in txt and "영업이익률" not in txt:
                        for col in row.select("td")[:3]:
                            val = col.get_text().strip().replace(",", "")
                            f_data['profits'].append(float(val) if val not in ["", "-"] else 0)
                    if "ROE" in txt:
                        cols = row.select("td")
                        if cols:
                            val = cols[2].get_text().strip().replace(",", "")
                            f_data['roe'] = float(val) if val not in ["", "-"] else 0.0
                f_data['is_growing'] = all(x < y for x, y in zip(f_data['profits'], f_data['profits'][1:])) if len(f_data['profits']) >= 2 else False
            pbr_tag = soup.select_one("#_pbr")
            if pbr_tag: f_data['pbr'] = float(pbr_tag.get_text().strip())
            per_tag = soup.select_one("#_per")
            if per_tag: f_data['per'] = float(per_tag.get_text().strip())
            target_tag = soup.select_one("em#_target_money")
            if target_tag: f_data['target_price'] = int(target_tag.get_text().strip().replace(",", ""))
        except: pass
        return f_data

    def get_investor_trend(self, ticker):
        """수급 데이터 수집"""
        url = f"https://m.stock.naver.com/api/stock/{ticker}/integration"
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = res.json()
            f_net, i_net, p_net, f_cont, i_cont = 0, 0, 0, 0, 0
            trends = data.get('dealTrendInfos', [])
            for count, item in enumerate(trends):
                if count >= 5: break
                f_val = int(item['foreignerPureBuyQuant'].replace(",", ""))
                i_val = int(item['organPureBuyQuant'].replace(",", ""))
                p_val = int(item['individualPureBuyQuant'].replace(",", ""))
                f_net += f_val; i_net += i_val; p_net += p_val
                if f_val > 0: f_cont += 1
                if i_val > 0: i_cont += 1
            return f_net, i_net, p_net, f_cont, i_cont
        except: return 0, 0, 0, 0, 0

    def get_news(self, ticker):
        """뉴스 수집"""
        url = f"https://finance.naver.com/item/news_news.naver?code={ticker}"
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            news_items = []
            titles = soup.select('.title a')
            infos = soup.select('.info')
            for i in range(min(5, len(titles))):
                news_items.append({'title': titles[i].get_text().strip(), 'source': infos[i].get_text().strip() if i < len(infos) else ""})
            return news_items
        except: return []

    def get_company_summary(self, ticker):
        """기업 개요 수집"""
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            summary_tag = soup.select_one(".summary_info")
            if summary_tag: return summary_tag.get_text().strip().replace("\n", " ")
            return "핵심 기술력과 시장 지배력을 바탕으로 지속적인 성장이 기대되는 기업입니다."
        except: return ""

    def calculate_obv(self, df):
        """OBV(On-Balance Volume) 계산"""
        try:
            obv = [0]
            for i in range(1, len(df)):
                if df['Close'].iloc[i] > df['Close'].iloc[i-1]: obv.append(obv[-1] + df['Volume'].iloc[i])
                elif df['Close'].iloc[i] < df['Close'].iloc[i-1]: obv.append(obv[-1] - df['Volume'].iloc[i])
                else: obv.append(obv[-1])
            return obv
        except: return []

    def analyze_technical(self, ticker):
        """기술적 분석 매뉴얼 계산 (RSI, ADX, OBV)"""
        try:
            df = fdr.DataReader(ticker, (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
            if len(df) < 120: return None
            
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()
            df['MA120'] = df['Close'].rolling(window=120).mean()
            df['V_MA20'] = df['Volume'].rolling(window=20).mean()

            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))

            tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean()
            up, down = df['High'].diff(), df['Low'].shift() - df['Low']
            pdm = (up.where((up > down) & (up > 0), 0)).rolling(window=14).mean()
            mdm = (down.where((down > up) & (down > 0), 0)).rolling(window=14).mean()
            pdi, mdi = 100 * (pdm / atr), 100 * (mdm / atr)
            dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
            adx_val = dx.rolling(window=14).mean().iloc[-1] if not dx.empty else 0
            
            obv = self.calculate_obv(df)
            is_obv_rising = all(x < y for x, y in zip(obv[-5:], obv[-4:])) if len(obv) >= 5 else False

            last, prev = df.iloc[-1], df.iloc[-2]
            return {
                'ticker': ticker, 'close': int(last['Close']), 'change_rate': ((last['Close']-prev['Close'])/prev['Close'])*100,
                'rsi': last['RSI'] if isinstance(last['RSI'], float) else last['RSI'].iloc[-1] if hasattr(last['RSI'], 'iloc') else last['RSI'],
                'adx': adx_val, 'is_perfect': last['MA5'] > last['MA20'] > last['MA60'] > last['MA120'],
                'is_breakout': last['Close'] > prev['Close'] and last['Volume'] > last['V_MA20'] * 2,
                'is_pullback': last['Close'] <= prev['Close'] and last['Volume'] < last['V_MA20'] * 0.5,
                'strong_trend': adx_val > 25, 'volume': last['Volume'], 'v_ma20': last['V_MA20'], 'is_obv_rising': is_obv_rising
            }
        except: return None

    def get_market_cap(self, ticker):
        """시가총액 수집"""
        try:
            res = requests.get(f"https://finance.naver.com/item/main.naver?code={ticker}", headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            cap = soup.select_one("#_market_sum")
            return cap.get_text().strip().replace("\t", "").replace("\n", "") + "억원" if cap else "정보없음"
        except: return "정보없음"

    def get_stock_name(self, ticker):
        """종목명 수집"""
        try:
            res = requests.get(f"https://finance.naver.com/item/main.naver?code={ticker}", headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            return soup.select_one('.wrap_company h2 a').get_text()
        except: return ticker

    def run(self, mode='afternoon'):
        print(f"--- {mode.capitalize()} Mode 가동 ---")
        market_news = self.get_top_market_news()
        global_status = self.get_global_market_status() if mode == 'morning' else {}
        market_briefing = self.get_market_briefing()
            
        sector_trends = self.get_sector_trends()
        etf_trends = self.get_etf_trends()
        candidate_tickers = self.get_market_rankings()
        
        results = []
        semi_tickers = self.get_semiconductor_tickers()

        for ticker in candidate_tickers:
            f_data = self.get_financial_trend(ticker)
            if not f_data['is_growing']: continue
            tech = self.analyze_technical(ticker)
            if not tech: continue
            f_net, i_net, p_net, f_cont, i_cont = self.get_investor_trend(ticker)
            
            tech.update({
                'name': self.get_stock_name(ticker), 'market_cap': self.get_market_cap(ticker),
                'profits': f_data['profits'], 'pbr': f_data['pbr'], 'roe': f_data['roe'],
                'per': f_data['per'], 'target_price_analyst': f_data['target_price'],
                'f_net': f_net, 'i_net': i_net, 'p_net': p_net, 'f_cont': f_cont, 'i_cont': i_cont,
                'summary': self.get_company_summary(ticker), 'news': self.get_news(ticker),
                'is_semi': ticker in semi_tickers
            })
            
            score = (f_cont * 1.5) + (i_cont * 1.5)
            if tech['is_perfect']: score += 4
            if tech['strong_trend']: score += 3
            if tech['is_breakout']: score += 3
            if tech['is_semi']: score += 5
            if f_net > 0 and i_net > 0: score += 3
            tech['score'] = score
            
            if (f_cont >= 3 or i_cont >= 3) or tech['is_breakout']:
                if tech['change_rate'] > -2: results.append(tech)
            time.sleep(0.05)
            
        results.sort(key=lambda x: x['score'], reverse=True)
        return {"picks": results[:10], "market_briefing": market_briefing, "market_news": market_news, "sectors": sector_trends, "etf_trends": etf_trends, "global_status": global_status, "mode": mode}

if __name__ == "__main__":
    analyst = DataAnalyst()
    top_picks = analyst.run()
    for i, s in enumerate(top_picks['picks']):
        print(f"{i+1}. {s['name']} - 스코어: {s['score']}")
