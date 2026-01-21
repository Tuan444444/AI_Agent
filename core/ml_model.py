import joblib
import pandas as pd
import os

MODEL_PATH = "data/price_model.pkl"

class PricePredictor:
    def __init__(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
        else:
            self.model = None

    # --- CẬP NHẬT: Thêm tham số kc_trung_tam, kc_truong_dh ---
    def predict(self, quan, loai_phong, dien_tich, tien_ich, cho_de_xe, kc_trung_tam, kc_truong_dh):
        if not self.model: return 0
        
        input_data = pd.DataFrame([{
            'Quan_huyen': quan,
            'Loai_phong': loai_phong,
            'Dien_tich': dien_tich,
            'Tien_ich_co_ban': tien_ich,
            'Cho_de_xe': cho_de_xe,
            'Khoang_cach_TT': kc_trung_tam,   # <-- Thêm
            'Gan_truong_DH': kc_truong_dh     # <-- Thêm
        }])
        
        try:
            prediction = self.model.predict(input_data)[0]
            return int(prediction)
        except Exception as e:
            print(f"Lỗi dự đoán: {e}")
            return 0