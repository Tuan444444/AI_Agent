import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import os

# 1. Đọc dữ liệu
csv_path = 'data/data2_file.csv'
if not os.path.exists(csv_path):
    print(f" Lỗi: Không tìm thấy file {csv_path}")
    exit()

print("⏳ Đang đọc dữ liệu...")

# --- SỬA LỖI ĐỌC FILE ---
try:
    # Thử đọc với dấu phẩy trước, encoding utf-8-sig (để trị lỗi ký tự lạ đầu file của Excel)
    df = pd.read_csv(csv_path, encoding='utf-8-sig', skipinitialspace=True)
    
    # Nếu đọc xong mà chỉ thấy có 1 cột -> Khả năng cao là bị lỗi dấu chấm phẩy
    if len(df.columns) <= 1:
        print(" Phát hiện file dùng dấu chấm phẩy (;), đang đọc lại...")
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig', skipinitialspace=True)
except Exception as e:
    # Dự phòng encoding khác nếu utf-8 lỗi
    print(" Thử đọc bằng encoding latin-1...")
    df = pd.read_csv(csv_path, encoding='latin-1', skipinitialspace=True)

# Chuẩn hóa tên cột: Xóa khoảng trắng thừa ở đầu/cuối tên cột
df.columns = df.columns.str.strip()

print(f"📊 Các cột tìm thấy trong file: {list(df.columns)}")

# --- CẤU HÌNH CỘT ---
features = [
    'Quan_huyen', 'Loai_phong', 'Dien_tich', 
    'Tien_ich_co_ban', 'Cho_de_xe',
    'Khoang_cach_TT', 'Gan_truong_DH'
]
target = 'Gia_thue'

# Kiểm tra xem có cột nào bị thiếu không
missing_cols = [col for col in features + [target] if col not in df.columns]
if missing_cols:
    print(f" LỖI NGHIÊM TRỌNG: Không tìm thấy các cột sau trong file CSV: {missing_cols}")
    print(" Hãy mở file CSV ra kiểm tra xem tên cột có đúng chính xác từng chữ không.")
    exit()

# Xử lý dữ liệu: Xóa dòng thiếu
df = df.dropna(subset=features + [target])

# Chuyển đổi dữ liệu số (đôi khi Excel lưu số có dấu phẩy 100,000 làm Python tưởng là chữ)
def clean_currency(x):
    if isinstance(x, str):
        return float(x.replace(',', '').replace('.', '').replace('VND', '').strip())
    return x

# Áp dụng làm sạch cho cột Giá và Diện tích (đề phòng)
df[target] = df[target].apply(clean_currency)
df['Dien_tich'] = df['Dien_tich'].apply(clean_currency)

X = df[features]
y = df[target]

print(f" Dữ liệu sẵn sàng: {len(df)} dòng.")

# 2. Định nghĩa cột nào là chữ (cần mã hóa), cột nào là số (giữ nguyên)
categorical_features = ['Quan_huyen', 'Loai_phong', 'Tien_ich_co_ban', 'Cho_de_xe']

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ],
    remainder='passthrough' 
)

# 3. Tạo Pipeline
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=150, random_state=42))
])

# 4. Huấn luyện lại
print(" Đang huấn luyện mô hình...")
model.fit(X, y)

# 5. Lưu model
joblib.dump(model, 'data/price_model.pkl')
print(" XONG! Đã tạo file model thành công.")