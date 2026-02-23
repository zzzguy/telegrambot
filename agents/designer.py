class Designer:
    """Agent D: 브로커리지 스타일 디자인 시스템 제공자"""
    def __init__(self):
        # 프로페셔널 컬러 팔레트 (대형 증권사 톤앤매너)
        self.colors = {
            'primary': (18, 52, 86),      # Deep Navy (신뢰감)
            'secondary': (70, 130, 180),  # Steel Blue (보조 포인트)
            'accent': (217, 48, 37),      # Google Red (하방 경고)
            'up': (231, 76, 60),          # Red (상승)
            'down': (41, 128, 185),       # Blue (하락)
            'bg_light': (245, 247, 250),  # Light Gray BG
            'text_main': (44, 62, 80),    # Dark Gray Text
            'text_sub': (127, 140, 141),  # Gray Text
            'table_header': (232, 240, 254),
            'table_alt': (248, 249, 251)
        }
        
        self.fonts = {
            'main': 'MalgunGothic',
            'base_size': 10,
            'title_size': 22,
            'section_size': 14,
            'table_size': 8
        }

    def get_config(self):
        return {
            'colors': self.colors,
            'fonts': self.fonts
        }

    def run(self, draft_html=None, picks=None):
        """하위 호환성 유지 및 설정 반환"""
        return self.get_config()
