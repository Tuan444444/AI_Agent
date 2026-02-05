from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from core.ml_model import PricePredictor
from core.genai_chat import ReasoningAgent
import google.generativeai as genai
import os
from dotenv import load_dotenv
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import csv
from datetime import datetime
from core.backend_agent import run_agent_query
# 1. Load API Key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print(" Cảnh báo: Chưa có GOOGLE_API_KEY trong file .env")
else:
    genai.configure(api_key=api_key)

# --- KHỞI TẠO CHAT MODEL ---
print("⏳ Đang khởi tạo Chat Model...")
try:
    chat_model = genai.GenerativeModel('gemini-flash-latest')
    print(" Đã khởi tạo: gemini-flash-latest")
except Exception as e:
    print(f" Không load được bản flash-latest, chuyển sang 1.5-flash. Lỗi: {e}")
    chat_model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Import module Vision
try:
    from core.vision_agent import VisionAgent
    vision_available = True
except ImportError:
    vision_available = False
    print(" Cảnh báo: Lỗi import VisionAgent.")

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(" BẮT ĐƯỢC LỖI 422:")
    print(f" Chi tiết lỗi: {exc.errors()}")  
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
# 3. Khởi tạo các Agent

predictor = PricePredictor() 
reasoner = ReasoningAgent()
if vision_available:
    vision = VisionAgent()


class RoomInput(BaseModel):
 
    Quan_huyen: str = "Đống Đa"
    Dien_tich: float = 30.0
    Loai_hinh: str = "Trọ thường"
    Tong_so_tang: int = 5
    Tang_phong: int = 2
    Thang_may: str = "Không"
    Noi_that: str = "Cơ bản"
    Ban_cong_Cua_so: str = "Không"
    Khu_bep: str = "Kệ bếp"
    Ve_sinh: str = "Khép kín"
    May_giat: str = "Chung"
    Vi_tri_ngo: str = "Ba gác"
    Cho_nuoi_pet: str = "Không"
    Gia_dien: str = "3500"
    Khoang_cach_TT: float = 5000.0
    
class ChatRequest(BaseModel):
    question: str
    context: str = ""
    session_id: str
# --- API 1: ĐỊNH GIÁ  ---
@app.post("/predict")
async def predict_price(data: RoomInput):
    print("👉 Nhận request định giá Ultimate...")
    try:
        # 1. Chuyển đổi dữ liệu từ Pydantic sang Dictionary
        input_dict = data.dict()
        
        # 2. Gọi Model ML trực tiếp (
        raw_price = predictor.predict(input_dict)
        
        if raw_price == 0:
            return {"price_formatted": "Lỗi Model", "explanation": "Không thể dự đoán (Lỗi ML)."}

        price_str = f"{raw_price:,} VNĐ"
        
        return {
            "price_formatted": price_str,
            "explanation": f"Dự đoán dựa trên: {data.Loai_hinh}, {data.Noi_that} tại {data.Quan_huyen}."
        }
    except Exception as e:
        print(f" Lỗi API Predict: {e}")
        return {"price_formatted": "Lỗi Server", "explanation": str(e)}

# --- API 2: Quét ảnh ---
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
        print(f" Lỗi xử lý ảnh: {e}")
        return {"Mo_ta": f"Lỗi server: {str(e)}"}


@app.post("/chat")
async def chat_consultant(req: ChatRequest):
    print(f"📩 Nhận yêu cầu Chat: {req.question}")

    # 1. Kiểm tra input
    user_input = req.question if req.question else req.text
    if not user_input or not user_input.strip():
        return {"reply": "Bạn chưa nhập câu hỏi nào cả."}

    try:
        # 2. GỌI AGENT THÔNG MINH (Thay vì Chatbot thường)
        # req.context: Chứa JSON dữ liệu phòng (bao gồm cả Khoang_cach_TT người dùng nhập)
        # req.history: Lịch sử chat
        
        reply_text = run_agent_query(req.question, req.session_id, req.context)
        
        # 3. Trả về kết quả
        return {"reply": reply_text}

    except Exception as e:
        print(f"❌ Lỗi API Chat: {e}")
        return {"reply": f"Xin lỗi, hệ thống đang bận. Lỗi: {str(e)}"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


