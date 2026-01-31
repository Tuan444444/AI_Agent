import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# 1. Load Data
df = pd.read_csv("data/data2_file.csv")

# 2. KHAI BÁO FEATURE (Phải khớp 100% với file tạo data)
numeric_features = [
    'Dien_tich', 'Tong_so_tang', 'Tang_phong', 'Khoang_cach_TT'
]

categorical_features = [
    'Quan_huyen', 'Loai_hinh', 'Thang_may',
    'Noi_that', 'Ban_cong_Cua_so', 'Khu_bep', 'Ve_sinh', 'May_giat',
    'Vi_tri_ngo', 'Cho_nuoi_pet', 'Gia_dien'
]

# Chuyển đổi cột 'Gia_dien' sang string để tránh lỗi nếu nó lẫn lộn số và chữ
df['Gia_dien'] = df['Gia_dien'].astype(str)

X = df[numeric_features + categorical_features]
y = df['Gia_phong']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Pipeline xử lý
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# Model mạnh mẽ
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', GradientBoostingRegressor(n_estimators=300, max_depth=7, random_state=42))
])

print("⏳ Đang huấn luyện AI với 15 yếu tố chi tiết nhất...")
model.fit(X_train, y_train)

joblib.dump(model, "price_model.pkl")
print("💾 Đã lưu model (price_model.pkl)")