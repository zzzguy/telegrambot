import os
import requests
from dotenv import load_dotenv

load_dotenv()

class Dispatcher:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send_telegram_document(self, file_path, caption=""):
        """텔레그램 문서(PDF) 발송"""
        if not self.bot_token or not self.chat_id:
            print("Error: TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 .env에 설정되지 않았습니다.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
        
        try:
            with open(file_path, 'rb') as doc:
                files = {'document': doc}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                response = requests.post(url, data=data, files=files)
                
                if response.status_code == 200:
                    print(f"텔레그램 문서 발송 성공: {os.path.basename(file_path)}")
                    return True
                else:
                    print(f"텔레그램 문서 발송 실패: {response.text}")
                    return False
        except Exception as e:
            print(f"텔레그램 문서 발송 중 에러 발생: {e}")
            return False

    def send_telegram_message(self, content):
        """텔레그램 메시지 발송 (길이 제한 대응을 위해 분할 발송)"""
        if not self.bot_token or not self.chat_id:
            print("Error: TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 .env에 설정되지 않았습니다.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        # 텔레그램 메시지 길이 제한(4096자) 대응
        MAX_LENGTH = 4000
        parts = [content[i:i+MAX_LENGTH] for i in range(0, len(content), MAX_LENGTH)]
        
        success = True
        for part in parts:
            payload = {
                'chat_id': self.chat_id,
                'text': part,
                'parse_mode': 'Markdown' 
            }
            try:
                response = requests.post(url, data=payload)
                if response.status_code != 200:
                    print(f"텔레그램 발송 실패: {response.text}")
                    success = False
            except Exception as e:
                print(f"텔레그램 발송 중 에러 발생: {e}")
                success = False
        
        if success:
            print("텔레그램 메시지 모든 파트 발송 성공!")
        return success

if __name__ == "__main__":
    # Test
    dispatcher = Dispatcher()
    # dispatcher.send_telegram_message("테스트 메시지입니다.")
