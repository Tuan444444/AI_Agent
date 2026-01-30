import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

class VisionAgent:
    def __init__(self):
        # --- CẬP NHẬT DANH SÁCH MODEL (Dựa trên list bạn gửi) ---
        self.backup_models = [
            "gemini-2.0-flash",       # Ưu tiên số 1: Bản 2.0 mới nhất, siêu nhanh
            "gemini-2.0-flash-lite",  # Ưu tiên số 2: Bản nhẹ
            "gemini-exp-1206",        # Ưu tiên số 3: Bản thử nghiệm (rất thông minh)
            "gemini-flash-latest"     # Cuối cùng: Bản ổn định
        ]

    def analyze_image(self, image_bytes):
        image = Image.open(io.BytesIO(image_bytes))
        
        prompt = """
        Bạn là chuyên gia Bất động sản. Hãy nhìn ảnh này và trích xuất dữ liệu JSON.
        Cấu trúc JSON bắt buộc:
        {
            "Loai_phong": "Chọn 1: [Trọ thường, Chung cư mini, Ký túc xá, Căn hộ dịch vụ, Nhà nguyên căn]",
            "Tien_ich_co_ban": "Chọn 1: [Cơ bản, Đầy đủ, Cao cấp, Thiếu]",
            "Dien_tich": 25,
            "Mo_ta": "Mô tả ngắn gọn 1 câu về nội thất"
        }
        """

        # --- VÒNG LẶP THỬ MODEL ---
        last_error = ""
        for model_name in self.backup_models:
            try:
                print(f"🔄 Đang thử model: {model_name}...")
                model = genai.GenerativeModel(model_name)
                
                # Gửi request
                response = model.generate_content([prompt, image])
                
                raw_text = response.text
                print(f"✅ Model {model_name} trả lời: {raw_text}")
                
                # --- XỬ LÝ JSON ---
                # 1. Tìm đoạn JSON trong câu trả lời
                json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(0)
                    # 2. Xử lý lỗi phổ biến của Gemini 2.0 (hay thêm comments // trong JSON)
                    # Xóa comment kiểu // ... hoặc /* ... */ nếu có
                    json_str = re.sub(r'//.*', '', json_str) 
                    return json.loads(json_str)
                else:
                    print(f"⚠️ Model {model_name} không trả về JSON đúng định dạng.")
                    last_error = "AI không trả về JSON"
                    continue # Thử model tiếp theo

            except Exception as e:
                print(f"❌ Model {model_name} bị lỗi: {e}")
                last_error = str(e)
                continue # Thử model tiếp theo
        
        # Nếu thử hết mà vẫn tạch
        return {
            "Loai_phong": "Trọ thường", 
            "Tien_ich_co_ban": "Cơ bản",
            "Dien_tich": 20,
            "Mo_ta": f"Lỗi hệ thống AI: {last_error}. Hãy kiểm tra lại ảnh."
        }