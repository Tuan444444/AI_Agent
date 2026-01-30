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
        Đóng vai chuyên gia thẩm định nhà trọ tại Hà Nội. Hãy phân tích bức ảnh này và trích xuất dữ liệu JSON.
        
        QUY TẮC QUAN TRỌNG:
        1. Chỉ trả về JSON thuần, không markdown, không giải thích.
        2. Các giá trị phải KHỚP CHÍNH XÁC (copy-paste) với danh sách lựa chọn dưới đây. Nếu không chắc, hãy chọn giá trị phổ biến nhất.

        DANH SÁCH LỰA CHỌN HỢP LỆ (Bắt buộc dùng từ ngữ này):
        - "Loai_hinh": ["Chung cư mini", "Trọ thường", "Căn hộ dịch vụ (Studio)", "Homestay (Sleepbox)"]
        - "Noi_that": ["Full đồ Luxury (Smart TV, Sofa...)", "Cơ bản (Giường, tủ, nóng lạnh, ĐH)", "Đồ cũ/Thiếu đồ", "Nhà trống"]
        - "Ban_cong_Cua_so": ["Ban công rộng thoáng", "Cửa sổ kính lớn (Big Window)", "Cửa sổ giếng trời (Nhìn tường)", "Không cửa sổ (Phòng hộp)"]
        - "Khu_bep": ["Bếp tách biệt (Ngăn mùi)", "Kệ bếp trong phòng", "Nấu ăn chung khu (Tầng 1)"]
        - "Ve_sinh": ["Khép kín (Có vách kính tắm)", "Khép kín (Cơ bản)", "Vệ sinh chung (Chung tầng)"]
        
        LOGIC SUY LUẬN:
        - Nếu thấy Sofa, Tủ lạnh lớn, Tranh treo tường -> Chọn "Full đồ Luxury (Smart TV, Sofa...)"
        - Nếu chỉ thấy Giường gỗ, Tủ tôn/gỗ ép -> Chọn "Cơ bản (Giường, tủ, nóng lạnh, ĐH)"
        - Nếu thấy cửa kính to sát sàn -> Chọn "Ban công rộng thoáng" hoặc "Cửa sổ kính lớn (Big Window)"
        
        OUTPUT JSON MẪU:
        {
            "Mo_ta": "Mô tả ngắn gọn 1 câu về phòng này (VD: Phòng sáng, decor hiện đại...)",
            "Loai_hinh": "...",
            "Noi_that": "...",
            "Ban_cong_Cua_so": "...",
            "Khu_bep": "...",
            "Ve_sinh": "..."
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