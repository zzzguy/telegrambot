import pandas as pd
#import pandas_ta as ta
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
                amount_tag = soup.select_one(".lst_pop li:nth-of-type(1) .desc")
                # 위 선택자가 부정확할 수 있으므로 텍스트로 찾기
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
            
            valid_count = 0
            for row in rows:
                cols = row.select("td")
                if len(cols) < 4: continue
                
                name_tag = cols[0].select_one("a")
                if not name_tag: continue
                
                name = name_tag.get_text().strip()
                change_str = cols[1].get_text().strip()
                
                try:
                    # 섹터 내 종목 및 수급 데이터 추출
                    detail_url = "https://finance.naver.com" + name_tag['href']
                    detail_res = requests.get(detail_url, headers=headers)
                    detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
                    
                    # 1. 상위 5개 종목 추출
                    stock_names = []
                    name_tags = detail_soup.select("td.name a")
                    for s_tag in name_tags[:5]:
                        stock_names.append(s_tag.get_text().strip())
                    top_stocks_str = ", ".join(stock_names)
                    
                    # 2. 업종별 투자자 매매 현황 (최근 1일 합산 추정치 또는 첫 페이지 비중 활용)
                    # 네이버 업종 상세 페이지에는 보통 하단에 투자자별 동향이 있으나, 
                    # 여기서는 상위 종목들의 수급 성향을 파악하거나 대표값을 추출
                    # 실시간 업종 수급은 다른 페이지 권장되나, 여기서는 등락과 연동된 '기상도' 보강용으로 
                    # 상세 페이지 테이블에서 외국인/기관 비율 등을 긁어올 수 있음.
                    # 사용자 요청에 따라 '외인순매수/기관순매수/개인순매수'를 '비중' 또는 '강도'로 표현
                    
                    f_net_total = 0
                    i_net_total = 0
                    p_net_total = 0
                    
                    # 테이블에서 상위 5개 종목의 수급을 합산하여 섹터 수급 지표로 사용 (Proxy)
                    rows = detail_soup.select("table.type_5 tr")
                    count = 0
                    for row in rows:
                        cols_s = row.select("td")
                        if len(cols_s) < 12: continue # 수급 데이터가 있는 열까지 확보
                        try:
                            # 네이버 상세 테이블: [종목명, 현재가, 등락, 전일비, 등락률, 거래량, 거래대금, 전일거래량, 외인비율, 외인보유, 외인순매수, 기관순매수]
                            # 실제 인덱스는 페이지마다 다를 수 있으나 보통 뒤쪽에 매수 데이터 위치
                            # 외국인순매수(10), 기관순매수(11)
                            f_val = cols_s[10].get_text().strip().replace(",", "")
                            i_val = cols_s[11].get_text().strip().replace(",", "")
                            # 개인은 보통 계산 (전체량 - 외인 - 기관) 또는 별도 컬럼
                            # 여기서는 데이터가 있는 만큼만 가져옴
                            if f_val and f_val != "0": f_net_total += int(f_val)
                            if i_val and i_val != "0": i_net_total += int(i_val)
                            count += 1
                        except: continue
                        if count >= 5: break

                    # 개인은 섹터 등락이 정방향일 때 외인/기관 합의 반대 방향으로 추정하거나 0으로 세팅 (네이버 업종 상세에 개인은 잘 안나옴)
                    p_net_total = -(f_net_total + i_net_total) # 단순 추정 (제로섬 가정)

                    rep_ticker = name_tags[0]['href'].split('=')[-1] if name_tags else ""
                    
                    # fdr로 이력 데이터 수집
                    if rep_ticker:
                        end_date = datetime.now().strftime("%Y-%m-%d")
                        start_date = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")
                        df = fdr.DataReader(rep_ticker, start_date, end_date)
                        
                        if len(df) < 20: continue
                        
                        # 수익률 계산
                        curr_price = df['Close'].iloc[-1]
                        price_5d = df['Close'].iloc[-6] if len(df) >= 6 else df['Close'].iloc[0]
                        price_20d = df['Close'].iloc[-21] if len(df) >= 21 else df['Close'].iloc[0]
                        
                        ret_5d = ((curr_price - price_5d) / price_5d) * 100
                        ret_20d = ((curr_price - price_20d) / price_20d) * 100
                    else:
                        ret_5d, ret_20d = 0, 0
                    
                    # 날씨 기호
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
                        "p_net": p_net_total
                    })
                except:
                    continue
        except Exception as e:
            print(f"섹터 분석 오류: {e}")
            
        # 당일 등락 상위 10개 선정
        sectors.sort(key=lambda x: x['score'], reverse=True)
        return sectors[:10]

    def get_etf_holdings(self, ticker):
        """ETF 주요 구성 종목(TOP 5) 수집 (네이버 금융 정보 활용)"""
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers)
            # UTF-8 또는 EUC-KR 인코딩 처리 (네이버는 EUC-KR인 경우가 많음)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 구성 종목 정보는 'cu_list' 클래스 내부에 있을 수 있음
            # 데이터 수집이 까다로우면 텍스트에서 추출 시도
            holdings = []
            
            # 페이지 하단 또는 특정 섹션에서 종목명 패턴 추출
            # ETF 페이지 내 '구성종목' 테이블 또는 리스트 탐색
            # Naver ETF 페이지의 구성종목은 iframe이나 JS로 로드되는 경우가 많아 
            # 메인 페이지에서 일부 텍스트를 파싱하거나 모바일 API 활용 권장
            
            # 모바일 API 활용 (더 안정적)
            api_url = f"https://m.stock.naver.com/api/stock/{ticker}/integration"
            api_res = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)'})
            api_data = api_res.json()
            
            # etfCuInfos 또는 비슷한 필드 확인
            # 실제 Naver 모바일 API 구조에 따라 etfCuInfos 필드가 구성종목 정보를 담고 있음
            cu_infos = api_data.get('etfCuInfos', [])
            for info in cu_infos[:5]:
                holdings.append(info.get('stockName', ''))
            
            if not holdings:
                # 텍스트 파싱 폴백 (메인 페이지에서 종목명/비중 패턴 찾기)
                patterns = re.findall(r'\"stockName\":\"([^\"]+)\"', res.text)
                holdings = list(dict.fromkeys(patterns))[:5]

            return ", ".join(holdings) if holdings else "정보 미흡"
        except Exception as e:
            print(f"ETF 구성종목 수집 오류 ({ticker}): {e}")
            return "분석 중"

    def get_global_market_status(self):
        """해외 시장(미국) 동향 및 섹터별 수익률 수집 (Morning 모드 필수)"""
        print("해외 시장(미국) 데이터 수집 중...")
        indices = {
            "NASDAQ": "IXIC",
            "S&P500": "US500",
            "SOXX": "SOXX", # 반도체
            "XLK": "XLK",   # 테크
            "XLE": "XLE"    # 에너지
        }
        global_status = {}
        try:
            for name, symbol in indices.items():
                # 전일 종가와 현재가(또는 최신 데이터) 비교
                df = fdr.DataReader(symbol)
                if len(df) >= 2:
                    current = df['Close'].iloc[-1]
                    prev = df['Close'].iloc[-2]
                    change_rate = ((current - prev) / prev) * 100
                    global_status[name] = {
                        "price": current,
                        "change_rate": round(change_rate, 2)
                    }
            return global_status
        except Exception as e:
            print(f"해외 시장 데이터 수집 오류: {e}")
            return {}

    def get_etf_trends(self):
        """ETF 당일 등락율 상위 10종목 및 상세 정보 수집"""
        print("ETF 시장 동향 분석 중...")
        try:
            # 1. ETF 전체 상장 리스트 및 당일 시세 수집
            df_etf = fdr.StockListing('ETF/KR')
            
            # 2. 등락율 계산을 위해 시세 데이터 보강 (Listing 데이터에 등락율이 없을 수 있음)
            # FDR Listing 결과에 'ChgRate' 또는 'Change'가 있는지 확인
            # 없으면 당일 종가와 전일 종가로 계산
            
            # 등락율 기준 정렬
            if 'ChgRate' in df_etf.columns:
                df_etf = df_etf.sort_values(by='ChgRate', ascending=False)
            elif 'ChangeCode' in df_etf.columns:
                # ChangeCode가 2(상승), 5(하락) 등일 수 있음. 
                # 정확한 등락율은 DataReader로 가져오는 것이 확실
                pass
            
            # 상위 15개 정도를 먼저 뽑아서 상세 데이터(5일, 20일, 수급) 수집
            top_etfs = df_etf.head(15).to_dict('records')
            
            etf_results = []
            for item in top_etfs:
                ticker = item['Symbol']
                name = item['Name']
                
                try:
                    # 상세 히스토리 수집 (5일, 20일 수익률 계산)
                    end_date = datetime.now().strftime("%Y-%m-%d")
                    start_date = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")
                    df_hist = fdr.DataReader(ticker, start_date, end_date)
                    
                    if len(df_hist) < 2: continue
                    
                    curr_price = df_hist['Close'].iloc[-1]
                    prev_close = df_hist['Close'].iloc[-2]
                    daily_change = ((curr_price - prev_close) / prev_close) * 100
                    
                    ret_5d = ((curr_price - df_hist['Close'].iloc[-6]) / df_hist['Close'].iloc[-6] * 100) if len(df_hist) >= 6 else 0
                    ret_20d = ((curr_price - df_hist['Close'].iloc[-21]) / df_hist['Close'].iloc[-21] * 100) if len(df_hist) >= 21 else 0
                    
                    # 구성종목(TOP 5) 수집
                    top_holdings = self.get_etf_holdings(ticker)
                    
                    # 수급 데이터 (기존 get_investor_trend 활용)
                    f_net, i_net, p_net, _, _ = self.get_investor_trend(ticker)
                    
                    etf_results.append({
                        "name": name,
                        "rate": f"{daily_change:+.2f}%",
                        "ret_5d": f"{ret_5d:+.2f}%",
                        "ret_20d": f"{ret_20d:+.2f}%",
                        "top_stocks": top_holdings,
                        "f_net": f_net,
                        "i_net": i_net,
                        "p_net": p_net,
                        "score": daily_change # 정렬용
                    })
                    
                    if len(etf_results) >= 10: break
                    time.sleep(0.1) # 속도 제어
                except Exception as e:
                    print(f"ETF 개별 분석 오류 ({name}): {e}")
                    continue
            
            return etf_results
        except Exception as e:
            print(f"ETF 전체 분석 오류: {e}")
            return []

    def get_top_market_news(self):
        """주요 증권 뉴스 수집"""
        print("주요 시장 뉴스 수집 중...")
        url = "https://finance.naver.com/news/mainnews.naver"
        headers = {'User-Agent': 'Mozilla/5.0'}
        market_news = []
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            news_titles = soup.select(".articleSubject a")
            for title in news_titles[:5]:
                market_news.append(title.get_text().strip())
        except Exception as e:
            print(f"시장 뉴스 수집 오류: {e}")
            
        return market_news

    def get_semiconductor_tickers(self):
        """네이버 증권 업종별 시세에서 반도체 종목 수집"""
        print("반도체 섹터 종목 수집 중...")
        url = "https://finance.naver.com/sise/sise_group_detail.naver?type=upjong&no=278"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.select('div.name_area a')
            tickers = []
            for link in links:
                code = link['href'].split('=')[-1]
                tickers.append(code)
            return tickers
        except:
            return []

    def get_market_rankings(self):
        """네이버 증권에서 거래대금 상위 종목 및 반도체 섹터 수집"""
        print("시장 랭킹 및 섹터 데이터 수집 중...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        tickers = self.get_semiconductor_tickers() # 반도체 우선
        
        # 추가로 거래대금 상위 일부 추가 (보완용)
        for sosok in [0, 1]:
            url = f"https://finance.naver.com/sise/sise_quant.naver?sosok={sosok}"
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.select('a.tltle')
            for link in links[:20]:
                code = link['href'].split('=')[-1]
                tickers.append(code)
        return list(dict.fromkeys(tickers)) # 중복 제거 및 순서 유지

    def get_financial_trend(self, ticker):
        """영업이익 추세 및 PBR, ROE, PER 등 밸류에이션 수집 (네이버 증권)"""
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        f_data = {
            'is_growing': False, 'profits': [], 
            'pbr': 0.0, 'roe': 0.0, 'per': 0.0, 
            'target_price': 0
        }
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 1. 영업이익 추세
            section = soup.select_one(".section.cop_analysis")
            if section:
                rows = section.select("tr")
                for row in rows:
                    txt = row.get_text()
                    # 영업이익 (연간)
                    if "영업이익" in txt and "영업이익률" not in txt:
                        cols = row.select("td")
                        for col in cols[:3]:
                            val = col.get_text().strip().replace(",", "")
                            f_data['profits'].append(float(val) if val not in ["", "-"] else 0)
                    # ROE (최근 연간)
                    if "ROE" in txt:
                        cols = row.select("td")
                        if cols:
                            val = cols[2].get_text().strip().replace(",", "") # 최근 확정 연도
                            f_data['roe'] = float(val) if val not in ["", "-"] else 0.0
                
                f_data['is_growing'] = all(x < y for x, y in zip(f_data['profits'], f_data['profits'][1:])) if len(f_data['profits']) >= 2 else False

            # 2. PBR, PER, 목표주가 (우측 퀵박스)
            pbr_tag = soup.select_one("#_pbr")
            if pbr_tag: f_data['pbr'] = float(pbr_tag.get_text().strip())
            
            per_tag = soup.select_one("#_per")
            if per_tag: f_data['per'] = float(per_tag.get_text().strip())
            
            target_tag = soup.select_one("em#_target_money")
            if target_tag:
                f_data['target_price'] = int(target_tag.get_text().strip().replace(",", ""))
            
            return f_data
        except:
            return f_data

    def get_investor_trend(self, ticker):
        """최근 5일 매매주체별 수급 및 연속성 분석 (Mobile API 사용)"""
        url = f"https://m.stock.naver.com/api/stock/{ticker}/integration"
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/04.1'
        }
        try:
            res = requests.get(url, headers=headers)
            data = res.json()
            
            f_net, i_net, p_net = 0, 0, 0
            f_cont, i_cont = 0, 0
            
            trends = data.get('dealTrendInfos', [])
            if not trends:
                return 0, 0, 0, 0, 0
                
            # 최근 5일 데이터 합산 및 연속성 체크
            count = 0
            for item in trends:
                try:
                    # 데이터 예시: '+49,320'
                    f_val = int(item['foreignerPureBuyQuant'].replace(",", ""))
                    i_val = int(item['organPureBuyQuant'].replace(",", ""))
                    p_val = int(item['individualPureBuyQuant'].replace(",", ""))
                    
                    if count < 5:
                        f_net += f_val
                        i_net += i_val
                        p_net += p_val
                        if f_val > 0: f_cont += 1
                        if i_val > 0: i_cont += 1
                    
                    count += 1
                    if count >= 5: break
                except:
                    continue
            
            return f_net, i_net, p_net, f_cont, i_cont
        except Exception as e:
            print(f"수급 분석 API 오류 ({ticker}): {e}")
            return 0, 0, 0, 0, 0

    def get_news(self, ticker):
        """뉴스 헤드라인 및 간단한 내용 수집"""
        url = f"https://finance.naver.com/item/news_news.naver?code={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            news_items = []
            titles = soup.select('.title a')
            infos = soup.select('.info')
            
            for i in range(min(5, len(titles))):
                news_items.append({
                    'title': titles[i].get_text().strip(),
                    'source': infos[i].get_text().strip() if i < len(infos) else ""
                })
            return news_items
        except:
            return []

    def get_company_summary(self, ticker):
        """기업 개요 및 주요 사업 내용 수집"""
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            summary_tag = soup.select_one(".summary_info")
            if summary_tag:
                return summary_tag.get_text().strip().replace("\n", " ")
            return "핵심 기술력과 시장 지배력을 바탕으로 지속적인 성장이 기대되는 기업입니다."
        except:
            return ""

    def calculate_obv(self, df):
        """OBV (On-Balance Volume) 계산: 세력 매집 시그널"""
        try:
            obv = [0]
            for i in range(1, len(df)):
                if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                    obv.append(obv[-1] + df['Volume'].iloc[i])
                elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                    obv.append(obv[-1] - df['Volume'].iloc[i])
                else:
                    obv.append(obv[-1])
            return obv
        except:
            return []

      def analyze_technical(self, ticker):
        """기술적 지표 및 VPA(Volume Price Action) + OBV 분석 (라이브러리 없이 직접 계산)"""
        try:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            df = fdr.DataReader(ticker, start_date)
            
            if len(df) < 120: return None
            
            # 이동평균선 계산
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()
            df['MA120'] = df['Close'].rolling(window=120).mean()
            df['V_MA20'] = df['Volume'].rolling(window=20).mean()

            # RSI 매뉴얼 계산 (14일 기준)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # ADX 매뉴얼 계산
            high_low = df['High'] - df['Low']
            high_close = (df['High'] - df['Close'].shift()).abs()
            low_close = (df['Low'] - df['Close'].shift()).abs()
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean()
            up_move = df['High'] - df['High'].shift()
            down_move = df['Low'].shift() - df['Low']
            plus_dm = (up_move.where((up_move > down_move) & (up_move > 0), 0)).rolling(window=14).mean()
            minus_dm = (down_move.where((down_move > up_move) & (down_move > 0), 0)).rolling(window=14).mean()
            plus_di = 100 * (plus_dm / atr)
            minus_di = 100 * (minus_dm / atr)
            dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
            adx_val = dx.rolling(window=14).mean().iloc[-1] if not dx.empty else 0
            
            # OBV 매집 분석
            obv_values = self.calculate_obv(df)
            if obv_values:
                df['OBV'] = obv_values
                obv_recent = df['OBV'].tail(5).tolist()
                is_obv_rising = all(x < y for x, y in zip(obv_recent, obv_recent[1:]))
            else:
                is_obv_rising = False

            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            return {
                'ticker': ticker,
                'close': int(last['Close']),
                'change_rate': ((last['Close'] - prev['Close']) / prev['Close']) * 100,
                'rsi': last['RSI'] if isinstance(last['RSI'], float) else last['RSI'].iloc[-1],
                'adx': adx_val,
                'is_perfect': last['MA5'] > last['MA20'] > last['MA60'] > last['MA120'],
                'is_breakout': last['Close'] > prev['Close'] and last['Volume'] > last['V_MA20'] * 2,
                'is_pullback': last['Close'] <= prev['Close'] and last['Volume'] < last['V_MA20'] * 0.5,
                'strong_trend': adx_val > 25,
                'volume': last['Volume'],
                'v_ma20': last['V_MA20'],
                'is_obv_rising': is_obv_rising
            }
        except Exception as e:
            print(f"기술적 분석 상세 오류 ({ticker}): {e}")
            return None
            
    def get_market_cap(self, ticker):
        """시가총액 정보 수집"""
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            cap_area = soup.select_one("#_market_sum")
            if cap_area:
                return cap_area.get_text().strip().replace("\t", "").replace("\n", "") + "억원"
            return "정보없음"
        except:
            return "정보없음"

    def get_stock_name(self, ticker):
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            name = soup.select_one('.wrap_company h2 a').get_text()
            return name
        except:
            return ticker

    def run(self, mode='afternoon'):
        # 0. 공통 데이터 수집 (시장 뉴스 등)
        market_news = self.get_top_market_news()
        
        # 모드별 특화 데이터 수집
        global_status = {}
        if mode == 'morning':
            print("--- Morning Mode 가동 (7 AM) ---")
            global_status = self.get_global_market_status()
            market_briefing = self.get_market_briefing() # 어제 종가 데이터
        else:
            print("--- Afternoon Mode 가동 (5 PM) ---")
            market_briefing = self.get_market_briefing()
            
        sector_trends = self.get_sector_trends()
        etf_trends = self.get_etf_trends()

        candidate_tickers = self.get_market_rankings()
        results = []
        print(f"총 {len(candidate_tickers)}개 종목 스마트 분석 중...")
        
        semi_tickers = self.get_semiconductor_tickers()

        for ticker in candidate_tickers:
            # 1. 재무 및 밸류에이션 추세
            f_data = self.get_financial_trend(ticker)
            if not f_data['is_growing']: continue
            
            # 2. 기술적 분석 (VPA 포함)
            tech = self.analyze_technical(ticker)
            if not tech: continue
            
            # 3. 수급 분석 (연속성 포함)
            f_net, i_net, p_net, f_cont, i_cont = self.get_investor_trend(ticker)
            
            # 결과 저장
            tech['name'] = self.get_stock_name(ticker)
            tech['market_cap'] = self.get_market_cap(ticker)
            tech['profits'] = f_data['profits']
            tech['pbr'] = f_data['pbr']
            tech['roe'] = f_data['roe']
            tech['per'] = f_data['per']
            tech['target_price_analyst'] = f_data['target_price']
            tech['f_net'] = f_net
            tech['i_net'] = i_net
            tech['p_net'] = p_net
            tech['f_cont'] = f_cont
            tech['i_cont'] = i_cont
            tech['summary'] = self.get_company_summary(ticker)
            tech['news'] = self.get_news(ticker)
            tech['is_semi'] = ticker in semi_tickers
            
            # --- 고도화된 스코어링 시스템 ---
            score = 0
            # A. 수급 연속성 가점 (최대 10점)
            score += (f_cont * 1.5) + (i_cont * 1.5)
            
            # B. 기술적 강도 (최대 10점)
            if tech['is_perfect']: score += 4
            if tech['strong_trend']: score += 3
            if tech['is_breakout']: score += 3
            if tech['is_pullback']: score += 2 # 눌림목은 가점 작음 (안전마진 위주)
            
            # C. 반도체 주도주 가점
            if tech['is_semi']: score += 5
            
            # D. 기관 유입 강도 (금액 기준 가중치 - 단순화)
            if f_net > 0 and i_net > 0: score += 3 # 양매수 가점
            
            tech['score'] = score
            
            # --- 엄격한 필터링 ---
            # 1. 외인/기관 중 최소 하나는 최근 5일 중 3회 이상 순매수
            # 2. 혹은 강력한 돌파(breakout)가 발생한 경우
            if (f_cont >= 3 or i_cont >= 3) or tech['is_breakout']:
                if tech['change_rate'] > -2: # 급락주는 제외
                    results.append(tech)
            
            time.sleep(0.05)
            
        # 정렬: 스코어 높은 순
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"최종 스마트 픽 {len(results)}개 종목 선별 완료.")
        
        return {
            "picks": results[:10],
            "market_briefing": market_briefing,
            "market_news": market_news,
            "sectors": sector_trends,
            "etf_trends": etf_trends,
            "global_status": global_status,
            "mode": mode
        }

if __name__ == "__main__":
    analyst = DataAnalyst()
    top_picks = analyst.run()
    for i, s in enumerate(top_picks['picks']):
        print(f"{i+1}. {s['name']} ({'반도체' if s['is_semi'] else '기타'}) - 스코어: {s['score']}")

if __name__ == "__main__":
    analyst = DataAnalyst()
    top_picks = analyst.run()
    for i, s in enumerate(top_picks[:10]):
        print(f"{i+1}. {s['name']} - 영업이익: {s['profits']}, 외인: {s['f_net']}, 기관: {s['i_net']}")

