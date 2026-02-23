import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# 에이전트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.data_analyst import DataAnalyst
from agents.strategist import Strategist
from agents.editor import ResearchEditor
from agents.designer import Designer
from agents.dispatcher import Dispatcher
import markdown
from utils.pdf_converter import convert_to_pdf_fpdf

def main():
    load_dotenv()
    
    # 0. 설정 (환경변수나 직접 입력)
    RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "recipient@example.com")
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='afternoon', choices=['morning', 'afternoon'])
    args = parser.parse_args()
    mode = args.mode
    
    print(f"[{datetime.now()}] 주식 리서치 자동화 시스템 가동 (Mode: {mode})...")
    
    # 1단계: Agent A (데이터 수집 및 분석)
    analyst = DataAnalyst()
    raw_data = analyst.run(mode=mode)
    candidates = raw_data.get('picks', [])
    
    if not candidates:
        print("분석 단계에서 후보 종목을 찾지 못했습니다. 종료합니다.")
        return

    # 2단계: Agent B (전략 수립 및 선정)
    strategist = Strategist()
    picks = strategist.run(candidates, global_status=raw_data.get('global_status'), mode=mode)
    
    # 3단계: Agent C (보고서 초안 작성)
    editor = ResearchEditor()
    draft_md = editor.run(
        mode, 
        picks, 
        raw_data.get('market_briefing', {}), 
        raw_data.get('market_news', []),
        global_status=raw_data.get('global_status')
    )
    
    # 4단계: 디자인 시스템 및 차트 생성
    designer = Designer()
    design_config = designer.get_config()
    from utils.chart_generator import ChartGenerator
    chart_gen = ChartGenerator(design_config)
    
    chart_paths = []
    print("시장 및 종목별 차트 생성 중...")
    try:
        # 1. 지수 차트 (이제 일봉 형식으로 생성)
        ks_df = analyst.get_index_history("KS11", days=120)
        kq_df = analyst.get_index_history("KQ11", days=120)
        chart1 = "chart_kospi.png"
        chart2 = "chart_kosdaq.png"
        if chart_gen.create_candle_chart(ks_df, "KS11", chart1, title="KOSPI"): chart_paths.append(chart1)
        if chart_gen.create_candle_chart(kq_df, "KQ11", chart2, title="KOSDAQ"): chart_paths.append(chart2)
        
        # 2. 섹터 분석 데이터 수집 (차트는 미생성)
        sectors = analyst.get_sector_trends()
            
        # 3. 개별 종목 일봉 차트 (10개, 120일 기준)
        for i, p in enumerate(picks):
            ticker = p['ticker']
            stock_df = analyst.get_stock_history(ticker, days=120)
            chart_filename = f"chart_stock_{i}.png"
            if chart_gen.create_candle_chart(stock_df, ticker, chart_filename, view_days=20):
                chart_paths.append(chart_filename)
            else:
                chart_paths.append("FAILED")
                
    except Exception as e:
        print(f"차트 생성 과정 대규모 오류: {e}")

    # 5단계: 보고서 생성 및 변환 (fpdf2 기반)
    pdf_data = {
        "picks": picks,
        "market_briefing": raw_data.get('market_briefing', {}),
        "market_news": raw_data.get('market_news', []),
        "sectors": sectors, # Keep for legacy or internal use if needed
        "etf_trends": raw_data.get('etf_trends', []),
        "draft_md": draft_md,
        "chart_paths": chart_paths
    }
    
    pdf_path = f"Stock_Report_{'AM' if mode=='morning' else 'PM'}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    if convert_to_pdf_fpdf(pdf_data, pdf_path):
        # 6단계: Agent E (발송 - PDF 전송)
        dispatcher = Dispatcher()
        caption = f"📑 [{'오전' if mode=='morning' else '오후'}] {datetime.now().strftime('%Y-%m-%d')} 리포트가 발간되었습니다."
        dispatcher.send_telegram_document(pdf_path, caption=caption)
    else:
        print("PDF 생성 실패로 인해 텔레그램 발송을 건너뜜.")

    # 차트 파일 일괄 정리
    for cp in chart_paths:
        if os.path.exists(cp): os.remove(cp)

    # 텍스트 백업 저장 (여전히 유지)
    with open("sample_report.md", "w", encoding="utf-8") as f:
        f.write(draft_md)
    
    print("전체 공정이 완료되었습니다.")

if __name__ == "__main__":
    main()
