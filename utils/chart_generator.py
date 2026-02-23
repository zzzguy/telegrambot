import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import pandas as pd

class ChartGenerator:
    def __init__(self, design_config):
        self.colors = design_config['colors']
        self.fonts = design_config['fonts']
        
        # 0-255 RGB를 matplotlib을 위한 0-1 스케일로 변환
        self.m_colors = {k: tuple(c/255 for c in v) for k, v in self.colors.items() if isinstance(v, tuple) and len(v) == 3}
        
        # 폰트 설정 (한글 깨짐 방지)
        font_path = os.path.join(os.getcwd(), "malgun.ttf")
        if not os.path.exists(font_path):
            font_path = r"C:\Windows\Fonts\malgun.ttf"
            
        if os.path.exists(font_path):
            font_prop = fm.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = font_prop.get_name()
        
        plt.rcParams['axes.unicode_minus'] = False

    def create_candle_chart(self, df, ticker, output_path, title=None, view_days=None):
        """Standardized daily candle chart (Calculates MAs on full data, plots view_days)"""
        if len(df) < 5:
            print(f"Chart data insufficient ({ticker})")
            return False

        # Moving Averages (Calculated on full data)
        df = df.copy()
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()

        # Slice for viewing
        if view_days:
            plot_df = df.tail(view_days).reset_index(drop=True)
        else:
            plot_df = df.reset_index(drop=True)

        # Dynamic figure size based on context (Main vs Table)
        plt.figure(figsize=(8, 4) if title else (6, 3))
        
        # Candles
        for i in range(len(plot_df)):
            open_p, close_p = plot_df['Open'].iloc[i], plot_df['Close'].iloc[i]
            high_p, low_p = plot_df['High'].iloc[i], plot_df['Low'].iloc[i]
            
            color = self.m_colors['up'] if close_p >= open_p else self.m_colors['down']
            plt.vlines(i, low_p, high_p, color=color, linewidth=1)
            # Body width: thicker for main chart
            box_width = 5 if title else (8 if len(plot_df) <= 20 else 4)
            plt.vlines(i, min(open_p, close_p), max(open_p, close_p), color=color, linewidth=box_width)

        # MA Lines
        plt.plot(plot_df['MA5'].values, color='gold', linewidth=1.5, label='MA5', alpha=0.9)
        plt.plot(plot_df['MA20'].values, color='magenta', linewidth=1.5, label='MA20', alpha=0.9)
        plt.plot(plot_df['MA60'].values, color='cyan', linewidth=1.5, label='MA60', alpha=0.9)

        if title:
            plt.title(f"{title} (Dynamic Trend)", fontsize=14, fontweight='bold', color=self.m_colors['primary'])
            plt.legend(loc='upper left', fontsize=9)
            plt.grid(True, linestyle='--', alpha=0.3)
            plt.tick_params(labelsize=9)
        else:
            plt.axis('off') # Clean look for table embedding
            
        plt.tight_layout(pad=0.5 if title else 0)
        
        try:
            plt.savefig(output_path, dpi=120, bbox_inches='tight', transparent=not title)
            plt.close()
            return True
        except Exception as e:
            print(f"Chart save failed ({ticker}): {e}")
            return False

    def create_sector_chart(self, sectors, output_path):
        """Sector performance bar chart (Top 10)"""
        if not sectors: return False
        
        names = [s['name'] for s in sectors[:10]][::-1] 
        values = []
        for s in sectors[:10]:
            try:
                values.append(float(s['rate'].replace('%','')))
            except:
                values.append(0)
        values = values[::-1]
        
        colors = [self.m_colors['up'] if v > 0 else self.m_colors['down'] for v in values]
        
        plt.figure(figsize=(8, 5))
        bars = plt.barh(names, values, color=colors, alpha=0.8)
        
        plt.title("Top Sectors Performance (Today)", fontsize=13, fontweight='bold', color=self.m_colors['primary'])
        plt.axvline(0, color='black', linewidth=0.8)
        plt.grid(axis='x', linestyle='--', alpha=0.3)
        plt.tick_params(labelsize=10)
        plt.tight_layout()
        
        try:
            plt.savefig(output_path, dpi=120)
            plt.close()
            return True
        except Exception as e:
            print(f"Sector chart save failed: {e}")
            return False

