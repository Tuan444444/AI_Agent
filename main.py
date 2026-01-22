from fastapi import FastAPI
from pydantic import BaseModel
from core.ml_model import PricePredictor
from core.genai_chat import ReasoningAgent

app = FastAPI()
predictor = PricePredictor()
reasoner = ReasoningAgent()

# --- CẬP NHẬT INPUT ---
class RoomInput(BaseModel):
    Quan_huyen: str
    Loai_phong: str
    Dien_tich: float
    Tien_ich_co_ban: str
    Cho_de_xe: str
    Khoang_cach_TT: float   # <-- Nhập khoảng cách (mét)
    Gan_truong_DH: float    # <-- Nhập khoảng cách (mét)

@app.post("/predict")
async def predict_price(data: RoomInput):
    # 1. Tính giá (Truyền đủ 7 tham số)
    price = predictor.predict(
        data.Quan_huyen, 
        data.Loai_phong, 
        data.Dien_tich, 
        data.Tien_ich_co_ban, 
        data.Cho_de_xe,
        data.Khoang_cach_TT,
        data.Gan_truong_DH
    )
    
    # 2. Giải thích (Update thêm thông tin cho Gemini chém gió hay hơn)
    explanation = reasoner.explain(
        data.Quan_huyen, 
        data.Loai_phong, 
        data.Dien_tich, 
        data.Tien_ich_co_ban, 
        price
    )
    
    return {
        "price": price,
        "price_formatted": "{:,.0f} VND".format(price),
        "explanation": explanation
    }