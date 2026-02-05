import joblib
import pandas as pd
import os

# Đường dẫn model (Đảm bảo bạn đã train ra file mới này)
MODEL_PATH = "data/price_model.pkl"

class PricePredictor:
    def __init__(self):
        # Kiểm tra file model có tồn tại không
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                print(f"✅ Đã load thành công model từ: {MODEL_PATH}")
            except Exception as e:
                self.model = None
                print(f"❌ Lỗi khi load file .pkl: {e}")
        else:
            self.model = None
            print(f"⚠️ Cảnh báo: Không tìm thấy file {MODEL_PATH}")

    def predict(self, data_dict):
        """
        Hàm dự đoán MỚI:
        - Input: data_dict (Dictionary chứa toàn bộ 15-16 trường thông tin)
        - Output: Giá dự đoán (Int)
        """
        if not self.model:
            print("❌ Chưa có model để dự đoán.")
            return 0
        
        try:
            print("🔍 DEBUG INPUT:", data_dict)
            # 1. Chuyển đổi Dictionary thành DataFrame
            # (Pandas sẽ tự khớp tên cột với tên key trong dict)
            input_df = pd.DataFrame([data_dict])
            
            # 2. Thực hiện dự đoán
            # Model Pipeline đã có sẵn các bước xử lý (OneHotEncoder, StandardScaler) nên ta đưa data thô vào được luôn
            prediction = self.model.predict(input_df)[0]
            
            return int(prediction)

        except Exception as e:
            print(f"❌ Lỗi Logic Dự Đoán (ML): {e}")
            # In ra danh sách cột model mong muốn để debug nếu lệch tên
            if hasattr(self.model, "feature_names_in_"):
                print(f"ℹ️ Model mong đợi các cột: {self.model.feature_names_in_}")
            print(f"ℹ️ Dữ liệu nhận được: {data_dict}")
            return 0