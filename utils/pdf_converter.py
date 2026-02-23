from fpdf import FPDF
import os
from datetime import datetime
import re

class StockPDF(FPDF):
    def __init__(self, design):
        super().__init__(orientation='L', unit='mm', format='A4') # 가로형 세팅
        self.design_config = design
        self.d_colors = design['colors']
        self.d_fonts = design['fonts']

    def header(self):
        # 헤더는 2페이지부터 표시 (표지 제외)
        if self.page_no() > 1:
            self.set_fill_color(*self.d_colors['primary'])
            self.rect(0, 0, 297, 15, 'F') # 가로폭 297mm
            self.set_y(5)
            self.set_font(self.d_fonts['main'], "B", 10)
            self.set_text_color(255, 255, 255)
            self.cell(0, 5, "AI Premium Stock Research intelligence Report (Landscape Edition)", align="C")
            self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.d_fonts['main'], "", 8)
        self.set_text_color(*self.d_colors['text_sub'])
        self.cell(0, 10, f"Page {self.page_no()} | AI Research Unit | Confidential", align="C")

    def add_cover_page(self, date_str):
        self.add_page()
        # 배경 장식 (Navy Side Bar)
        self.set_fill_color(*self.d_colors['primary'])
        self.rect(0, 0, 80, 210, 'F') # 가로형 높이 210
        
        # 제목
        self.set_xy(90, 60)
        self.set_font(self.d_fonts['main'], "B", 42)
        self.set_text_color(*self.d_colors['primary'])
        self.multi_cell(180, 18, "DAILY STOCK\nRESEARCH REPORT")
        
        # 서브 제목
        self.set_xy(92, 105)
        self.set_font(self.d_fonts['main'], "", 16)
        self.set_text_color(*self.d_colors['secondary'])
        self.cell(0, 10, "Landscape Analysis: Smart Money & Multi-Factor Intelligence")
        
        # 날짜 및 발행인
        self.set_xy(92, 160)
        self.set_font(self.d_fonts['main'], "B", 14)
        self.set_text_color(*self.d_colors['text_main'])
        self.cell(0, 10, f"Issued Date: {date_str}")
        self.set_xy(92, 168)
        self.set_font(self.d_fonts['main'], "", 12)
        self.cell(0, 10, "AI Financial Intelligence Automation Unit")

    def add_section_header(self, title, mode='afternoon'):
        self.ln(5)
        self.set_fill_color(*self.d_colors['bg_light'])
        self.set_text_color(*self.d_colors['primary'])
        self.set_font(self.d_fonts['main'], "B", 14)
        prefix = "[오전 브리핑]" if mode == 'morning' else "[오후 마감]"
        self.cell(0, 12, f"  {prefix} {title}", ln=True, fill=True)
        self.set_draw_color(*self.d_colors['primary'])
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 287, self.get_y())
        self.ln(5)

def clean_text(text):
    if not text: return ""
    text = re.sub(r'#+\s?\[?\d?\]?\s?', '', text)
    text = re.sub(r'\|.*\|', '', text)
    text = re.sub(r'\*\*', '', text) # 볼드 마크다운 제거
    text = re.sub(r'\n+', '\n', text).strip()
    return text

def convert_to_pdf_fpdf(data, output_path):
    print(f"최종 브로커리지 스타일 PDF 생성 시작: {output_path}")
    
    # Designer에서 디자인 설정 가져오기
    from agents.designer import Designer
    design = Designer().get_config()
    colors = design['colors']
    fonts = design['fonts']
    
    pdf = StockPDF(design)
    pdf.set_auto_page_break(auto=True, margin=15)
    
    font_path = os.path.join(os.getcwd(), "malgun.ttf")
    if not os.path.exists(font_path):
        font_path = r"C:\Windows\Fonts\malgun.ttf"
    
    try:
        pdf.add_font(fonts['main'], fname=font_path)
        pdf.add_font(fonts['main'], style="B", fname=font_path)
    except Exception as e:
        print(f"폰트 등록 에러: {e}")
        return False

    # 1. 표지 (Cover Page)
    today_str = datetime.now().strftime("%Y-%m-%d")
    pdf.add_cover_page(today_str)
    
    # 2. 본문 시작 (Page 2)
    pdf.add_page()
    page_width = pdf.w - 2 * pdf.l_margin

    draft_md = data.get("draft_md", "")
    sections = re.split(r'## \d\.\s', draft_md)

    mode = data.get("mode", "afternoon")
    is_morning = (mode == 'morning')
    
    # --- Section 1: 마켓 요약 (오전: 해외 / 오후: 국내 마감) ---
    s1_title = "글로벌 시장 요약 및 대응 전략" if is_morning else "데일리 마켓 마감 브리핑 & 주요 지수 추합"
    pdf.add_section_header(s1_title, mode=mode)
    
    chart_y_start = pdf.get_y()
    chart_paths = data.get("chart_paths", []) # [ks, kq, s0...s9, p0...p9]
    
    # 지수 일봉 차트 (크기 축소: 130->125, 65->60)
    if len(chart_paths) >= 2:
        if os.path.exists(chart_paths[0]): pdf.image(chart_paths[0], x=15, y=chart_y_start, w=125, h=60)
        if os.path.exists(chart_paths[1]): pdf.image(chart_paths[1], x=152, y=chart_y_start, w=125, h=60)
        pdf.set_y(chart_y_start + 62)

    # 글로벌/국내 지수 데이터 테이블
    global_status = data.get("global_status", {})
    briefing = data.get("market_briefing", {})
    
    pdf.set_font(fonts['main'], "B", 11)
    pdf.set_fill_color(*colors['table_header'])
    
    if is_morning and global_status:
        # 해외 지수 위주 테이블
        pdf.cell(60, 10, "해외 지수", border=1, align="C", fill=True) 
        pdf.cell(100, 10, "현재가 (지수)", border=1, align="C", fill=True)
        pdf.cell(117, 10, "등락률 (밤사이)", border=1, align="C", fill=True)
        pdf.ln()
        pdf.set_font(fonts['main'], "", 11)
        for name, d in global_status.items():
            pdf.cell(60, 10, name, border=1, align="C")
            pdf.cell(100, 10, f"{d.get('price', 0):,}", border=1, align="C")
            pdf.cell(117, 10, f"{d.get('change_rate', 0):+.2f}%", border=1, align="C")
            pdf.ln()
    else:
        # 기존 마감 시황 테이블
        pdf.cell(50, 10, "시장구분", border=1, align="C", fill=True) 
        pdf.cell(75, 10, "현재가", border=1, align="C", fill=True)
        pdf.cell(75, 10, "등락(률)", border=1, align="C", fill=True)
        pdf.cell(77, 10, "거래대금", border=1, align="C", fill=True)
        pdf.ln()
        pdf.set_font(fonts['main'], "", 11)
        for name, d in [("KOSPI", briefing.get('kospi', {})), ("KOSDAQ", briefing.get('kosdaq', {}))]:
            pdf.cell(50, 10, name, border=1, align="C")
            pdf.cell(75, 10, f"{d.get('now', 'N/A')}", border=1, align="C")
            pdf.cell(75, 10, f"{d.get('change', 'N/A')} ({d.get('rate', 'N/A')})", border=1, align="C")
            pdf.cell(77, 10, f"{d.get('amount', 'N/A')}", border=1, align="C")
            pdf.ln()
    
    # 자세한 마감 브리핑 텍스트 (줄간격 조절하여 1페이지 내 수용)
    if len(sections) > 1:
        pdf.ln(3)
        pdf.set_font(fonts['main'], "B", 11)
        pdf.set_text_color(*colors['primary'])
        pdf.cell(0, 8, "[ 시장 종합 분석 및 마감 코멘트 ]", ln=True)
        pdf.set_text_color(*colors['text_main'])
        pdf.set_font(fonts['main'], "", 10)
        pdf.multi_cell(page_width, 6, clean_text(sections[1])) # 8 -> 6 line spacing

    # --- Section 2: ETF 시장 동향 & 주요 ETF 분석 (Page 3 전용) ---
    pdf.add_page()
    pdf.add_section_header("2. ETF 당일 등락율 상위 10종목 분석", mode=mode)
    
    etfs = data.get("etf_trends", [])
    pdf.ln(10)
    
    # 섹터 데이터 테이블 (8열 확장)
    pdf.set_font(fonts['main'], "B", 9)
    pdf.set_fill_color(*colors['table_header'])
    # 컬럼: 종목명, 금일등락, 5일등락, 20일등락, ETF주요구성종목(TOP5), 외인순매수, 기관순매수, 개인순매수
    s_cols = [45, 20, 20, 20, 82, 30, 30, 30] 
    s_headers = ["종목명", "금일등락", "5일등락", "20일등락", "ETF주요구성종목(TOP5)", "외인순매수", "기관순매수", "개인순매수"]
    
    pdf.set_x(10)
    for i, h in enumerate(s_headers):
        pdf.cell(s_cols[i], 12, h, border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_font(fonts['main'], "", 8)
    for i, s in enumerate(etfs):
        fill = (i % 2 == 1)
        if fill: pdf.set_fill_color(*colors['table_alt'])
        else: pdf.set_fill_color(255, 255, 255)
        
        pdf.set_x(10)
        pdf.cell(s_cols[0], 11, s['name'][:20], border=1, align="C", fill=fill)
        pdf.cell(s_cols[1], 11, s['rate'], border=1, align="C", fill=fill)
        pdf.cell(s_cols[2], 11, s.get('ret_5d', 'N/A'), border=1, align="C", fill=fill)
        pdf.cell(s_cols[3], 11, s.get('ret_20d', 'N/A'), border=1, align="C", fill=fill)
        pdf.cell(s_cols[4], 11, s.get('top_stocks', 'N/A')[:55], border=1, align="L", fill=fill)
        
        # 수급 데이터 (정수형 콤마 표시)
        pdf.cell(s_cols[5], 11, f"{int(s.get('f_net', 0)):+,}", border=1, align="C", fill=fill)
        pdf.cell(s_cols[6], 11, f"{int(s.get('i_net', 0)):+,}", border=1, align="C", fill=fill)
        pdf.cell(s_cols[7], 11, f"{int(s.get('p_net', 0)):+,}", border=1, align="C", fill=fill)
        pdf.ln()

    # --- Section 3: AI-Model Picks (Page 4) ---
    pdf.add_page()
    pdf.add_section_header("3. AI-Model Picks 상세 분석 (20일 일봉 차트 및 수급 분석)", mode=mode)
    
    row_height = 18
    cols = [30, 20, 30, 22, 25, 25, 25, 100] # Total ~277mm
    pdf.set_font(fonts['main'], "B", 10) 
    pdf.set_fill_color(*colors['table_header'])
    table_headers = ["종목명", "현재가", "시가총액", "등락율", "외인순매수", "기관순매수", "개인순매수", "20일 일봉 차트 (MA5/20/60)"]
    for i, h in enumerate(table_headers):
        pdf.cell(cols[i], 12, h, border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_font(fonts['main'], "", 10) 
    for i, p in enumerate(data.get("picks", [])):
        fill = (i % 2 == 1)
        if fill: pdf.set_fill_color(*colors['table_alt'])
        else: pdf.set_fill_color(255, 255, 255)
        
        # 페이지 넘김 체크
        if pdf.get_y() + row_height > 195:
            pdf.add_page()
            pdf.set_font(fonts['main'], "B", 10)
            pdf.set_fill_color(*colors['table_header'])
            for j, h in enumerate(table_headers):
                pdf.cell(cols[j], 12, h, border=1, align="C", fill=True)
            pdf.ln()
            pdf.set_font(fonts['main'], "", 10)
            if fill: pdf.set_fill_color(*colors['table_alt'])
            else: pdf.set_fill_color(255, 255, 255)

        curr_y = pdf.get_y()
        curr_x = pdf.get_x()
        
        pdf.cell(cols[0], row_height, p['name'], border=1, align="C", fill=fill)
        pdf.cell(cols[1], row_height, f"{p['close']:,}", border=1, align="C", fill=fill)
        pdf.cell(cols[2], row_height, p.get('market_cap', 'N/A')[:12], border=1, align="C", fill=fill)
        pdf.cell(cols[3], row_height, f"{p['change_rate']:+.1f}%", border=1, align="C", fill=fill)
        
        # 주수 계산으로 출력 (콤마 포함)
        pdf.cell(cols[4], row_height, f"{int(p['f_net']):+,}", border=1, align="C", fill=fill)
        pdf.cell(cols[5], row_height, f"{int(p['i_net']):+,}", border=1, align="C", fill=fill)
        pdf.cell(cols[6], row_height, f"{int(p['p_net']):+,}", border=1, align="C", fill=fill)
        
        # 차트 셀 (인덱스 2번부터 종목 차트)
        pdf.cell(cols[7], row_height, "", border=1, fill=fill)
        chart_idx = 2 + i  # 지수 차트 2개(0,1) 다음부터 종목 차트
        if len(chart_paths) > chart_idx and os.path.exists(chart_paths[chart_idx]):
            pdf.image(chart_paths[chart_idx], x=curr_x + sum(cols[:7]) + 1, y=curr_y + 1, w=98, h=row_height-2)
        
        pdf.ln()

    # --- Section: 종목별 투자포인트 및 정성 분석 ---
    pdf.add_page()
    pdf.add_section_header("4. 종목별 투자포인트 및 정성 분석", mode=mode)
    if len(sections) > 5:
        pdf.set_font(fonts['main'], "", 11) # 10 -> 11
        # 종목 간 구분을 위해 [DIVIDER] 태그로 분리하여 처리
        raw_analysis = clean_text(sections[5])
        stock_blocks = raw_analysis.split("[DIVIDER]")
        
        for i, block in enumerate(stock_blocks):
            clean_block = block.strip()
            if not clean_block: continue
            
            pdf.multi_cell(page_width, 7, clean_block)
            
            # 마지막 블록이 아니면 구분선 긋기
            if i < len(stock_blocks) - 1:
                pdf.ln(4)
                pdf.set_draw_color(*colors['bg_light']) # 메인 테마 보조색으로 은은한 선
                pdf.set_line_width(0.3)
                pdf.line(pdf.get_x() + 5, pdf.get_y(), pdf.get_x() + page_width - 5, pdf.get_y())
                pdf.set_draw_color(*colors['primary']) # 다시 기본색으로 복구
                pdf.ln(6)

    try:
        pdf.output(output_path)
        print(f"Landscape PDF 생성 완료: {output_path}")
        return True
    except Exception as e:
        print(f"PDF 저장 실패: {e}")
        return False
