# from fastapi import FastAPI,UploadFile, File, HTTPException
# from pydantic import BaseModel
# from core.ml_model import PricePredictor
# from core.genai_chat import ReasoningAgent
# from core.vision_agent import VisionAgent

# app = FastAPI()
# predictor = PricePredictor()
# reasoner = ReasoningAgent()
# vision = VisionAgent()

# # --- CẬP NHẬT INPUT ---
# class RoomInput(BaseModel):
#     Quan_huyen: str
#     Loai_phong: str
#     Dien_tich: float
#     Tien_ich_co_ban: str
#     Cho_de_xe: str
#     Khoang_cach_TT: float   # <-- Nhập khoảng cách (mét)
#     Gan_truong_DH: float    # <-- Nhập khoảng cách (mét)

# @app.post("/predict")
# async def predict_price(data: RoomInput):
#     # 1. Tính giá (Truyền đủ 7 tham số)
#     price = predictor.predict(
#         data.Quan_huyen, 
#         data.Loai_phong, 
#         data.Dien_tich, 
#         data.Tien_ich_co_ban, 
#         data.Cho_de_xe,
#         data.Khoang_cach_TT,
#         data.Gan_truong_DH
#     )
    
#     # 2. Giải thích (Update thêm thông tin cho Gemini chém gió hay hơn)
#     explanation = reasoner.explain(
#         data.Quan_huyen, 
#         data.Loai_phong, 
#         data.Dien_tich, 
#         data.Tien_ich_co_ban, 
#         price
#     )
    
#     return {
#         "price": price,
#         "price_formatted": "{:,.0f} VND".format(price),
#         "explanation": explanation
#     }
# @app.post("/analyze-image")
# async def analyze_room_image(file: UploadFile = File(...)):
#     """
#     API nhận file ảnh -> Trả về thông tin phòng (JSON) để tự điền form
#     """
#     # 1. Kiểm tra định dạng file
#     if not file.content_type.startswith("image/"):
#         raise HTTPException(status_code=400, detail="File không phải là ảnh")
    
#     # 2. Đọc dữ liệu ảnh
#     image_bytes = await file.read()
    
#     # 3. Gọi Vision Agent phân tích
#     result = vision.analyze_image(image_bytes)
    
#     return result

# class ChatRequest(BaseModel):
#     question: str
#     context: str  # Chứa thông tin phòng, giá tiền đã tính được...

# @app.post("/chat")
# async def chat_consultant(req: ChatRequest):
#     try:
#         # Prompt đóng vai chuyên gia
#         prompt = f"""
#         Bạn là một chuyên gia tư vấn Bất động sản tại Hà Nội/TP.HCM.
#         Dưới đây là thông tin căn phòng khách hàng đang quan tâm:
#         {req.context}
        
#         Khách hàng hỏi: "{req.question}"
        
#         Hãy trả lời ngắn gọn, thân thiện, tư vấn dựa trên số liệu thực tế. 
#         Nếu giá đắt, hãy giải thích tại sao. Nếu rẻ, hãy cảnh báo rủi ro hoặc khen ngợi deal hời.
#         Trả lời bằng tiếng Việt tự nhiên.
#         """
        
#         response = chat_model.generate_content(prompt)
#         return {"reply": response.text}
#     except Exception as e:
#         return {"reply": f"Xin lỗi, tôi đang mất kết nối với não bộ AI. Lỗi: {str(e)}"}
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from core.ml_model import PricePredictor
from core.genai_chat import ReasoningAgent
import google.generativeai as genai

import os
from dotenv import load_dotenv

# 1. Load API Key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("⚠️ Cảnh báo: Chưa có GOOGLE_API_KEY trong file .env")
else:
    genai.configure(api_key=api_key)

# --- KHỞI TẠO CHAT MODEL (SỬA LỖI TẠI ĐÂY) ---
# Biến này phải nằm ngoài cùng (Global) để các hàm bên dưới gọi được
print("⏳ Đang khởi tạo Chat Model...")
try:
    # Ưu tiên dùng model xịn nhất bạn có
    chat_model = genai.GenerativeModel('gemini-flash-latest')
    print("✅ Đã khởi tạo: gemini-flash-latest")
except Exception as e:
    print(f"⚠️ Không load được bản 2.0, chuyển sang 1.5. Lỗi: {e}")
    chat_model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Import module Vision (Mắt thần)
try:
    from core.vision_agent import VisionAgent
    vision_available = True
except ImportError:
    vision_available = False
    print("⚠️ Cảnh báo: Lỗi import VisionAgent. Kiểm tra lại file core/vision_agent.py")

app = FastAPI()

# 3. Khởi tạo các Agent khác
predictor = PricePredictor()
reasoner = ReasoningAgent()
if vision_available:
    vision = VisionAgent()

# --- INPUT DATA MODELS ---
class RoomInput(BaseModel):
    Quan_huyen: str
    Loai_phong: str
    Dien_tich: float
    Tien_ich_co_ban: str
    Cho_de_xe: str
    Khoang_cach_TT: float
    Gan_truong_DH: float

class ChatRequest(BaseModel):
    question: str
    context: str

# --- API 1: DỰ ĐOÁN GIÁ ---
@app.post("/predict")
async def predict_price(data: RoomInput):
    price = predictor.predict(
        data.Quan_huyen, data.Loai_phong, data.Dien_tich, 
        data.Tien_ich_co_ban, data.Cho_de_xe, 
        data.Khoang_cach_TT, data.Gan_truong_DH
    )
    explanation = reasoner.explain(
        data.Quan_huyen, data.Loai_phong, data.Dien_tich, 
        data.Tien_ich_co_ban, price
    )
    return {
        "price": price,
        "price_formatted": "{:,.0f} VND".format(price),
        "explanation": explanation
    }

# --- API 2: MẮT THẦN (VISION) ---
@app.post("/analyze-image")
async def analyze_room_image(file: UploadFile = File(...)):
    if not vision_available:
        return {"Mo_ta": "Lỗi: Hệ thống Vision chưa khởi tạo được."}

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File phải là ảnh.")
    
    try:
        image_bytes = await file.read()
        result = vision.analyze_image(image_bytes)
        return result
    except Exception as e:
        print(f"❌ Lỗi xử lý ảnh: {e}")
        return {"Mo_ta": f"Lỗi server: {str(e)}"}

# --- API 3: CHAT TƯ VẤN (FIX LỖI) ---
@app.post("/chat")
async def chat_consultant(req: ChatRequest):
    # Kiểm tra xem chat_model đã có chưa
    if 'chat_model' not in globals():
        return {"reply": "Lỗi: Chat Model chưa được khởi tạo. Hãy kiểm tra lại API Key."}

    try:
        prompt = f"""
        Bạn là chuyên gia Bất động sản thân thiện.
        THÔNG TIN PHÒNG: {req.context}
        CÂU HỎI: "{req.question}"
        
        Hãy trả lời ngắn gọn, tư vấn nhiệt tình bằng tiếng Việt.
        """
        
        response = chat_model.generate_content(prompt)
        return {"reply": response.text}
    except Exception as e:
        print(f"❌ Lỗi Chat: {e}")
        return {"reply": f"Xin lỗi, tôi đang mất kết nối. Lỗi: {str(e)}"}