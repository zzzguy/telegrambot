class Strategist:
    def __init__(self):
        pass

    def estimate_price_levels(self, stock_info):
        close = stock_info['close']
        target_price = int(close * 1.07) # 우상향 종목이므로 조금 더 높은 목표가
        stop_loss = int(close * 0.95)
        return target_price, stop_loss

    def run(self, candidates, global_status=None, mode='afternoon'):
        """Agent B 실행 지침: 모드별(오전/오후) 최적 종목 선정"""
        print(f"전략 수립 중 (Mode: {mode})...")
        
        # 해외 시장 기반 가점 세팅 (오전 모드 전용)
        semi_bonus = 0
        tech_bonus = 0
        if mode == 'morning' and global_status:
            soxx = global_status.get('SOXX', {}).get('change_rate', 0)
            xlk = global_status.get('XLK', {}).get('change_rate', 0)
            if soxx > 1.0: semi_bonus = 10
            elif soxx > 0: semi_bonus = 5
            if xlk > 1.0: tech_bonus = 5

        scored_candidates = []
        for s in candidates:
            score = 0
            
            # 1. 수급 및 매집 시그널 (40점 만점)
            score += (s.get('f_cont', 0) * 2.5) + (s.get('i_cont', 0) * 2.5) 
            if s.get('is_obv_rising'): score += 15 
            
            # 2. 밸류에이션 및 펀더멘털 (30점 만점)
            pbr = s.get('pbr', 2.0)
            if pbr < 1.0: score += 15
            elif pbr < 1.5: score += 8
            
            roe = s.get('roe', 0)
            if roe > 15: score += 15
            elif roe > 10: score += 8
            
            # 3. 기술적 추세 및 돌파 (20점 만점)
            if s.get('is_perfect'): score += 10 # 정배열
            if s.get('is_breakout'): score += 10 # 돌파
            elif s.get('is_pullback'): score += 10 # 눌림목

            # 4. 해외 시장 동조화 가점 (오전 모드 핵심)
            if mode == 'morning':
                if s.get('is_semi'): score += semi_bonus
                # 추가 테크 가점 (가령 특정 키워드나 분류 기반 - 여기서는 단순화)
                # s['is_tech'] = any(...)
            
            # 5. 기존 섹터 가점
            if s.get('is_semi'): score += 5
            
            s['final_score'] = score
            scored_candidates.append(s)
            
        # 점수 기준 정렬 후 상위 10개 선정
        final_picks = sorted(scored_candidates, key=lambda x: x['final_score'], reverse=True)[:10]
        
        for p in final_picks:
            target, stop = self.estimate_price_levels(p)
            p['target_price'] = target
            p['stop_loss'] = stop
            
            # 모드별 차별화된 사유 생성
            f_c = p.get('f_cont', 0)
            i_c = p.get('i_cont', 0)
            
            # 주체 및 패턴 서술
            who = "외국인과 기관이" if f_c >= 3 and i_c >= 3 else "외국인이" if f_c >= 3 else "기관이" if i_c >= 3 else "주요 수급 주체가"
            intensity = "강력한 상승 돌파" if p.get('is_breakout') else "안정적인 눌림목" if p.get('is_pullback') else "완벽한 정배열" if p.get('is_perfect') else "견조한 우상향"
            
            morning_context = ""
            if mode == 'morning' and p.get('is_semi') and semi_bonus > 0:
                morning_context = "특히 밤사이 미 반도체 지수(SOXX)의 강세 속에 국내 관련 섹터로의 낙수 효과가 기대되며, "

            p['reason'] = f"{morning_context}{who} 최근 꾸준히 매집 중인 종목으로 {intensity} 패턴을 형성하고 있음"

        return final_picks

        return final_picks

if __name__ == "__main__":
    # Mock data for testing
    mock_candidates = [
        {'ticker': '005930', 'name': '삼성전자', 'close': 70000, 'rsi': 55.0, 'f_net': 1000, 'i_net': 500, 'volume_surge': True, 'is_aligned': True, 'is_uptrend': True, 'profits': [100, 120, 150]},
    ]
    strategist = Strategist()
    picks = strategist.run(mock_candidates)
    for p in picks:
        print(f"추천: {p['name']} ({p['score']}점) - 사유: {p['reason']}")
