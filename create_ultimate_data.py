import pandas as pd
import numpy as np
import random

# ==============================================================================
# 1. CẤU HÌNH HỆ SỐ GIÁ (PRICE FACTORS)
# ==============================================================================

# Hệ số Quận (Dựa trên giá đất thực tế 2024)
DISTRICT_FACTOR = {
    "Hoàn Kiếm": 1.6, "Ba Đình": 1.4, "Tây Hồ": 1.4, "Đống Đa": 1.35,
    "Hai Bà Trưng": 1.3, "Cầu Giấy": 1.25, "Thanh Xuân": 1.2, 
    "Nam Từ Liêm": 1.1, "Hoàng Mai": 1.0, "Bắc Từ Liêm": 0.95,
    "Hà Đông": 0.9, "Long Biên": 0.95, "Gia Lâm": 0.8
}

# Giá nền theo loại hình
BASE_PRICE_MAP = {
    "Chung cư mini": 2_800_000, 
    "Căn hộ dịch vụ (Studio)": 3_500_000, # Studio xịn hơn CCMN
    "1N1K (1 Khách 1 Ngủ)": 4_000_000,    # Đang hot trend
    "Trọ thường": 1_500_000,
    "Homestay (Sleepbox)": 1_200_000      # Giá rẻ nhưng tính theo đầu người
}

# Nội thất
INTERIOR_FACTOR = {
    "Full đồ Luxury (Smart TV, Sofa...)": 1.4,
    "Cơ bản (Giường, tủ, nóng lạnh, ĐH)": 1.15,
    "Đồ cũ/Thiếu đồ": 1.0,
    "Nhà trống": 0.9
}

# Ánh sáng & Thoáng khí (Yếu tố cực quan trọng với người ở)
VIEW_FACTOR = {
    "Ban công rộng thoáng": 1.2,      # Rất đắt giá
    "Cửa sổ kính lớn (Big Window)": 1.1,
    "Cửa sổ giếng trời (Nhìn tường)": 0.95,
    "Không cửa sổ (Phòng hộp)": 0.8   # Rất rẻ
}

# Bếp & Nấu ăn
KITCHEN_FACTOR = {
    "Bếp tách biệt (Ngăn mùi)": 1.15,
    "Kệ bếp trong phòng": 1.0,
    "Nấu ăn chung khu (Tầng 1)": 0.9
}

# Vệ sinh (WC)
WC_FACTOR = {
    "Khép kín (Có vách kính tắm)": 1.1, # Sang chảnh
    "Khép kín (Cơ bản)": 1.0,
    "Vệ sinh chung (Chung tầng)": 0.8   # Rất bất tiện -> Rẻ
}

# Tiện ích giặt là
LAUNDRY_FACTOR = {
    "Máy giặt riêng trong phòng": 1.15, # Cộng thêm khoảng 300-500k
    "Máy giặt chung (Sân thượng)": 1.0,
    "Không có máy giặt": 0.95
}

# Ngõ & Vị trí
ALLEY_FACTOR = {
    "Mặt phố/Oto đỗ cửa": 1.25,
    "Ba gác tránh/Ngõ nông": 1.1,
    "Xe máy tránh nhau": 1.0,
    "Ngõ ngách sâu/Hẻm nhỏ": 0.9
}

# Chính sách đặc biệt
PET_POLICY = {"Cho nuôi Pet": 1.05, "Cấm nuôi Pet": 1.0} # Cho nuôi pet thường đắt hơn chút hoặc cọc cao

# ==============================================================================
# 2. HÀM SINH DỮ LIỆU LOGIC
# ==============================================================================

def create_ultimate_dataset(num_samples=5000):
    data = []
    print(f"🚀 Đang khởi tạo {num_samples} bản ghi dữ liệu Full-Option...")

    for _ in range(num_samples):
        # --- A. CÁC THÔNG SỐ CƠ BẢN ---
        quan = random.choice(list(DISTRICT_FACTOR.keys()))
        loai = random.choice(list(BASE_PRICE_MAP.keys()))
        
        # Diện tích logic theo loại
        if "1N1K" in loai: dt = random.randint(35, 60)
        elif "Studio" in loai: dt = random.randint(25, 45)
        elif "Homestay" in loai: dt = random.randint(5, 10) # Diện tích giường/box
        else: dt = random.randint(15, 35)

        # --- B. CÁC THÔNG SỐ CHI TIẾT ---
        noi_that = random.choice(list(INTERIOR_FACTOR.keys()))
        view = random.choice(list(VIEW_FACTOR.keys()))
        bep = random.choice(list(KITCHEN_FACTOR.keys()))
        wc = random.choice(list(WC_FACTOR.keys()))
        giat = random.choice(list(LAUNDRY_FACTOR.keys()))
        ngo = random.choice(list(ALLEY_FACTOR.keys()))
        pet = random.choice(list(PET_POLICY.keys()))
        
        # Thang máy & Tầng
        so_tang_nha = random.randint(3, 9)
        tang_phong = random.randint(1, so_tang_nha)
        
        # Logic thang máy: Nhà > 5 tầng thường có, nhà < 5 tầng thường không
        if so_tang_nha >= 6:
            thang_may = random.choice(["Có", "Có", "Có", "Không"]) # 75% có
        else:
            thang_may = "Không"

        # --- C. TÍNH TOÁN GIÁ (PRICING ENGINE) ---
        # 1. Giá sàn diện tích
        unit_price = 100_000 # 100k/m2 trung bình
        if "Homestay" in loai: unit_price = 0 # Homestay tính theo slot, không tính theo m2 quá gắt
        
        base_val = BASE_PRICE_MAP[loai] + (dt * unit_price)
        
        # 2. Hệ số nhân (Multipliers)
        # Tầng: Thang bộ thì tầng cao rẻ. Thang máy thì tầng cao đắt (view đẹp).
        f_tang = 1.0
        if thang_may == "Không":
            if tang_phong == 1: f_tang = 1.1  # Tiện kinh doanh/đi lại
            elif tang_phong >= 4: f_tang = 0.85 # Leo mệt
        else:
            if tang_phong >= 6: f_tang = 1.05 # View thoáng
            
        # Tổng hợp hệ số
        total_factor = (
            DISTRICT_FACTOR[quan] * INTERIOR_FACTOR[noi_that] * VIEW_FACTOR[view] * KITCHEN_FACTOR[bep] * WC_FACTOR[wc] * LAUNDRY_FACTOR[giat] * ALLEY_FACTOR[ngo] *
            PET_POLICY[pet] *
            f_tang
        )
        
        final_price = base_val * total_factor
        
        # 3. Trừ khấu hao khoảng cách trung tâm
        kc_tt = random.randint(500, 12000) # mét
        final_price -= (kc_tt / 1000) * 60_000 
        
        # 4. Phụ phí dịch vụ (Service fees influence choices)
        # Giả lập giá điện nước để AI học (thường điện kinh doanh 4k thì giá phòng hay rẻ hơn xíu để bù)
        gia_dien = random.choice([3500, 3800, 4000, "Giá dân"])
        
        # 5. Noise & Finalize
        noise = random.uniform(0.95, 1.05)
        final_price = int(final_price * noise)
        if final_price < 1_000_000: final_price = 1_000_000 # Giá sàn

        # Lưu dữ liệu
        data.append([
            quan, loai, dt, so_tang_nha, tang_phong, thang_may, # Nhóm 1: Cấu trúc
            noi_that, view, bep, wc, giat,                      # Nhóm 2: Tiện nghi
            ngo, pet, gia_dien, kc_tt,                          # Nhóm 3: Môi trường
            final_price                                         # Label
        ])

    # Tạo DataFrame chuẩn
    columns = [
        'Quan_huyen', 'Loai_hinh', 'Dien_tich', 'Tong_so_tang', 'Tang_phong', 'Thang_may',
        'Noi_that', 'Ban_cong_Cua_so', 'Khu_bep', 'Ve_sinh', 'May_giat',
        'Vi_tri_ngo', 'Cho_nuoi_pet', 'Gia_dien', 'Khoang_cach_TT',
        'Gia_phong'
    ]
    
    df = pd.DataFrame(data, columns=columns)
    
    import os
    if not os.path.exists('data'): os.makedirs('data')
    df.to_csv("data/data2_file.csv", index=False)
    print("✅ ĐÃ TẠO XONG DATASET BẤT BẠI (ULTIMATE DATASET).")
    print(f"👉 File saved: data/data2_file.csv | Size: {len(df)} rows")

if __name__ == "__main__":
    create_ultimate_dataset()