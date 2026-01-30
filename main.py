from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from core.ml_model import PricePredictor
from core.genai_chat import ReasoningAgent
import google.generativeai as genai
import os
from dotenv import load_dotenv
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
# 1. Load API Key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("⚠️ Cảnh báo: Chưa có GOOGLE_API_KEY trong file .env")
else:
    genai.configure(api_key=api_key)

# --- KHỞI TẠO CHAT MODEL ---
print("⏳ Đang khởi tạo Chat Model...")
try:
    chat_model = genai.GenerativeModel('gemini-flash-latest')
    print("✅ Đã khởi tạo: gemini-flash-latest")
except Exception as e:
    print(f"⚠️ Không load được bản flash-latest, chuyển sang 1.5-flash. Lỗi: {e}")
    chat_model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Import module Vision
try:
    from core.vision_agent import VisionAgent
    vision_available = True
except ImportError:
    vision_available = False
    print("⚠️ Cảnh báo: Lỗi import VisionAgent.")

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print("🔥 BẮT ĐƯỢC LỖI 422:")
    print(f"👉 Chi tiết lỗi: {exc.errors()}")  # Nó sẽ in rõ ràng thiếu trường nào
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
# 3. Khởi tạo các Agent
# Lưu ý: Class PricePredictor trong ml_model.py cũng phải được cập nhật code mới
predictor = PricePredictor() 
reasoner = ReasoningAgent()
if vision_available:
    vision = VisionAgent()

# --- INPUT DATA MODELS (ĐÚNG 15 TRƯỜNG CỦA ULTIMATE DATA) ---
class RoomInput(BaseModel):
    # Đặt giá trị mặc định cho TẤT CẢ để "miễn nhiễm" với lỗi 422
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
    question: str = ""       # Đặt mặc định là rỗng để không bị lỗi "Field required"
    context: str = ""        # Đặt mặc định là rỗng
    history: str = ""
    text: str = ""

# --- API 1: ĐỊNH GIÁ (ĐÃ SỬA LẠI LOGIC) ---
@app.post("/predict")
async def predict_price(data: RoomInput):
    print("👉 Nhận request định giá Ultimate...")
    try:
        # 1. Chuyển đổi dữ liệu từ Pydantic sang Dictionary
        input_dict = data.dict()
        
        # 2. Gọi Model ML trực tiếp (thay vì gọi qua backend_agent cũ)
        # Hàm predictor.predict cần nhận dict và trả về số
        raw_price = predictor.predict(input_dict)
        
        if raw_price == 0:
            return {"price_formatted": "Lỗi Model", "explanation": "Không thể dự đoán (Lỗi ML)."}

        price_str = f"{raw_price:,} VNĐ"
        
        return {
            "price_formatted": price_str,
            "explanation": f"Dự đoán dựa trên: {data.Loai_hinh}, {data.Noi_that} tại {data.Quan_huyen}."
        }
    except Exception as e:
        print(f"❌ Lỗi API Predict: {e}")
        return {"price_formatted": "Lỗi Server", "explanation": str(e)}

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


# Tìm endpoint /chat và thay toàn bộ bằng đoạn này:
@app.post("/chat")
async def chat_consultant(req: ChatRequest):
    if 'chat_model' not in globals():
        return {"reply": "Lỗi: Chat Model chưa khởi tạo."}

    try:
        # --- LOGIC THÔNG MINH: Tự động ghép nội dung ---
        # Nếu Frontend gửi 'text' (kiểu cũ), ta dùng nó làm câu hỏi
        # Nếu Frontend gửi 'question' (kiểu mới), ta dùng question
        
        user_input = req.question if req.question else req.text
        
        # Nếu cả 2 đều rỗng -> Báo lỗi nhẹ
        if not user_input.strip():
            return {"reply": "Bạn chưa nhập câu hỏi nào cả."}

        # Xây dựng Prompt cho AI
        prompt = f"""
        BẠN LÀ: Chuyên gia Bất động sản.
        
        --- DỮ LIỆU ĐẦU VÀO ---
        {req.context}
        
        --- CÂU HỎI / YÊU CẦU ---
        {user_input}
        
        --- LỊCH SỬ CHAT ---
        {req.history}
        
          --- YÊU CẦU TRẢ LỜI ---

        1. Trả lời ngắn gọn, đúng trọng tâm câu hỏi mới.

        2. Nếu khách hỏi "Cái đó", "Nó", "Phòng này"... hãy hiểu theo ngữ cảnh trong Lịch sử trò chuyện.

        3. Giọng điệu tư vấn chuyên nghiệp nhưng gần gũi.
        """
        
        response = chat_model.generate_content(prompt)
        return {"reply": response.text}

    except Exception as e:
        print(f"❌ Lỗi Chat: {e}")
        return {"reply": f"Xin lỗi, server đang bận. Lỗi: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)