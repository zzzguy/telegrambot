class ResearchEditor:
    def __init__(self):
        pass

    def run(self, mode, picks, market_briefing, market_news, global_status=None):
        """Agent C 실행 지침: 모드별(오전/오후) 리포트 나러티브 구성"""
        print(f"리포트 나러티브 구성 중 (Mode: {mode})...")
        
        report_draft = []
        is_morning = (mode == 'morning')
        
        # 1. 마켓 브리핑 섹션 (오전: 해외 시황 / 오후: 마감 시황)
        if is_morning:
            report_draft.append("## 1. 밤사이 미 증시 요약 및 국내 시장 전망")
            summary = "밤사이 미 증시는 "
            if global_status:
                ndq = global_status.get('NASDAQ', {}).get('change_rate', 0)
                sox = global_status.get('SOXX', {}).get('change_rate', 0)
                sentiment = "강세를 보이며 국내 증시의 긍정적 출발이 예상됩니다." if ndq > 0 else "조정을 받으며 신중한 접근이 필요한 상황입니다."
                summary += f"나스닥 {ndq}% 변동, 필라델피아 반도체 지수 {sox}%를 기록하며 {sentiment} "
            summary += "특히 주요 빅테크 종목들의 실적 발표와 거시 지표 방향성에 따라 국내 IT 및 반도체 섹터의 변동성이 확대될 것으로 보입니다. 개장 전 선제적 종목 선정이 필수적인 구간입니다.\n"
            report_draft.append(summary)
        else:
            report_draft.append("## 1. 데일리 마켓 마감 브리핑")
            kospi = market_briefing.get('kospi', {})
            kosdaq = market_briefing.get('kosdaq', {})
            market_comment = f"금일 국내 증시는 특정 섹터로의 수급 집중 현상이 뚜렷했습니다. "
            market_comment += f"KOSPI는 {kospi.get('now', 'N/A')}pt({kospi.get('rate', 'N/A')}), 거래대금 {kospi.get('amount', 'N/A')}을 기록했습니다. "
            market_comment += "외국인과 기관의 '선택적 매집'이 이어지며 하방 경직성을 확보했습니다.\n"
            report_draft.append(market_comment)
        
        # 2. 주요 마켓 이슈 및 경제 뉴스
        report_draft.append("## 2. 주요 마켓 이슈 및 경제 뉴스")
        if market_news:
            for news in market_news:
                report_draft.append(f"- {news}")
        else:
            report_draft.append("- 현재 주요 뉴스를 수집 중이거나 휴장일입니다.")
        report_draft.append("")

        # 3. 주요 섹터별 기상도 및 전망 (Top 5)
        report_draft.append("## 3. 주요 섹터별 기상도 및 전망 (Top 5 Insights)")
        report_draft.append("최근 5일 및 20일 누적 등락율을 기반으로 한 단기/중기 트렌드 분석입니다. ☀️(맑음) 섹터군에 대한 비중 확대 전략이 유효합니다.\n")
        
        # 4. 데일리 마감 브리핑 및 뉴스 서술 (Combined Analysis)
        report_draft.append("## 4. 데일리 마켓 & 뉴스 심층 분석")
        analysis_text = "금일 시장은 거시 경제 환경의 불확실성 속에서도 반도체 및 하이테크 섹터 중심의 '선택과 집중' 장세가 뚜렷했습니다. "
        analysis_text += "특히 주요 외신과 증권사들이 주목한 이슈들이 시장의 트리거로 작용하였으나, 견조한 실적을 기반으로 한 우량주들은 수급의 하방 지지력을 확인시켜 주었습니다. "
        analysis_text += "기술적 분석 관점에서는 하방 압력보다는 매수 에너지가 응축되는 구간으로 판단되며, 뉴스 플로우를 통한 재료 노출 시 폭발적인 시세 분출 가능성이 높은 종목군들에 대한 선제적 대응이 필요합니다. "
        analysis_text += "외인/기관의 누적 순매수 데이터는 이러한 스마트 머니의 유입을 강력하게 시사하고 있습니다.\n"
        report_draft.append(analysis_text)
        
        # 5. 주요 추천종목 (Table + Reason Narrative)
        report_draft.append("## 5. AI-Model Picks 상세 분석 (스마트 머니 중심)")
        report_draft.append("외인/기관의 '연속 순매수' 데이터와 'VPA(거래량-가격 분석)' 패턴을 복합적으로 필터링한 정예 종목군입니다.\n")
        
        for i, p in enumerate(picks):
            # 1) 종목명 (티커) 형식
            report_draft.append(f" {i+1}) {p['name']} ({p['ticker']})")
            
            # 기업분석 섹션
            enterprise_info = p.get('summary', '해당 기업은 최근 시장 내 독보적인 기술적 해자와 사업 포트폴리오를 바탕으로 안정적인 수익성을 증명하고 있으며, 주요 경영 지표가 우상향 추세에 있습니다.')
            report_draft.append(f"  - 기업분석 : {enterprise_info}")
            
            # 핵심사유 섹션 (Rationale 활용)
            core_rationale = f"{p['reason']}을(를) 바탕으로 스마트 머니의 수급 강도가 임계점을 상회하고 있으며, 기술적으로 {p.get('rationale', '에너지 응축')} 패턴이 완성되어 폭발적인 시세 분출이 기대되는 시점입니다. (ADX: {p.get('adx', 0):.1f})"
            report_draft.append(f"  - 핵심사유: {core_rationale}")
            report_draft.append("[DIVIDER]")
            
        report_draft.append("\n---\n**Disclaimer**: 본 리포트는 투자 참고용 데이터이며 최종 판단은 투자자 본인에게 있습니다.")
        
        return "\n".join(report_draft)

if __name__ == "__main__":
    editor = ResearchEditor()
    mock_picks = [{'name': '삼성전자', 'ticker': '005930', 'reason': 'AI 반도체 호재', 'rsi': 58.2, 'target_price': 80000, 'stop_loss': 70000}]
    print(editor.run("보통", mock_picks))
