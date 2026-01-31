import streamlit as st
import requests
import pandas as pd
import os

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Trợ Lý BĐS AI", layout="wide", page_icon="🏠")
# API_URL = "http://127.0.0.1:8000" # Local
API_URL = "http://localhost:8000"   # Đổi port nếu cần

st.markdown("""
<style>
    .stChatMessage {border-radius: 10px; padding: 10px;}
    .user-msg {background-color: #e6f3ff;}
    .ai-msg {background-color: #f0f2f6;}
    .stButton button {width: 100%;}
    /* Làm đẹp các expander trong sidebar */
    .streamlit-expanderHeader {font-weight: bold; color: #333;}
</style>
""", unsafe_allow_html=True)

# --- 2. HÀM LOGIC PHÂN LOẠI ẢNH (GIỮ NGUYÊN NHƯ CŨ) ---
def auto_classify_utility(description):
    """
    Phân loại mức độ nội thất dựa trên mô tả từ ảnh.
    Map sang các key mới của hệ thống: Luxury, Cơ bản, Đồ cũ, Nhà trống.
    """
    desc = description.lower()
    
    # 1. Check từ khóa "Full option" 
    if any(x in desc for x in ["đầy đủ", "full nội thất", "full option", "sang trọng", "luxury"]):
        return "Full đồ Luxury (Smart TV, Sofa...)"

    # 2. Quét món đồ
    has_giuong = any(x in desc for x in ["giường", "bed", "nệm", "chỗ ngủ", "gác lửng"])
    has_tu = any(x in desc for x in ["tủ quần áo", "wardrobe", "tủ đồ"])
    has_dieuhoa = any(x in desc for x in ["điều hòa", "máy lạnh", "ac"])
    has_nonglanh = any(x in desc for x in ["nóng lạnh", "heater"])
    has_tulanh = any(x in desc for x in ["tủ lạnh", "fridge"])
    has_bep = any(x in desc for x in ["bếp", "kệ bếp", "kitchen"])
    
    points = 0
    if has_giuong: points += 1
    if has_tu: points += 1
    if has_dieuhoa: points += 1
    if has_nonglanh: points += 1
    if has_tulanh: points += 1
    if has_bep: points += 1
    
    # Logic quy đổi sang 4 mức độ mới
    if points >= 5: return "Full đồ Luxury (Smart TV, Sofa...)"
    if points >= 3: return "Cơ bản (Giường, tủ, nóng lạnh, ĐH)"
    if points >= 1: return "Đồ cũ/Thiếu đồ"
    return "Nhà trống"

# --- 3. LOAD DATA (CẬP NHẬT ĐỂ LOAD CÁC CỘT MỚI) ---
@st.cache_data
def load_options():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(current_dir, "data2_file.csv"),
        os.path.join(current_dir, "data", "data2_file.csv"),
        "data2_file.csv"
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
            
    # Giá trị mặc định (Fallback nếu không thấy file CSV)
    default = {
        "quan": ["Cầu Giấy", "Đống Đa", "Ba Đình", "Hoàn Kiếm", "Tây Hồ", "Thanh Xuân", "Hai Bà Trưng", "Hoàng Mai"],
        "loai": ["Chung cư mini", "Trọ thường", "Căn hộ dịch vụ (Studio)", "1N1K (1 Khách 1 Ngủ)", "Homestay (Sleepbox)"],
        "noi_that": ["Full đồ Luxury (Smart TV, Sofa...)", "Cơ bản (Giường, tủ, nóng lạnh, ĐH)", "Đồ cũ/Thiếu đồ", "Nhà trống"],
        "ban_cong": ["Ban công rộng thoáng", "Cửa sổ kính lớn (Big Window)", "Cửa sổ giếng trời (Nhìn tường)", "Không cửa sổ (Phòng hộp)"],
        "khu_bep": ["Bếp tách biệt (Ngăn mùi)", "Kệ bếp trong phòng", "Nấu ăn chung khu (Tầng 1)"],
        "ve_sinh": ["Khép kín (Có vách kính tắm)", "Khép kín (Cơ bản)", "Vệ sinh chung (Chung tầng)"],
        "may_giat": ["Máy giặt riêng trong phòng", "Máy giặt chung (Sân thượng)", "Không có máy giặt"],
        "ngo": ["Mặt phố/Oto đỗ cửa", "Ba gác tránh/Ngõ nông", "Xe máy tránh nhau", "Ngõ ngách sâu/Hẻm nhỏ"],
        "pet": ["Cho nuôi Pet", "Cấm nuôi Pet"]
    }

    if not file_path:
        return default

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig') # Thường csv tạo bằng pandas python mặc định là ,
        # Nếu lỗi separator thì thử lại engine python
        return {
            "quan": sorted(df['Quan_huyen'].astype(str).unique().tolist()),
            "loai": sorted(df['Loai_hinh'].astype(str).unique().tolist()),
            "noi_that": sorted(df['Noi_that'].astype(str).unique().tolist()),
            "ban_cong": sorted(df['Ban_cong_Cua_so'].astype(str).unique().tolist()),
            "khu_bep": sorted(df['Khu_bep'].astype(str).unique().tolist()),
            "ve_sinh": sorted(df['Ve_sinh'].astype(str).unique().tolist()),
            "may_giat": sorted(df['May_giat'].astype(str).unique().tolist()),
            "ngo": sorted(df['Vi_tri_ngo'].astype(str).unique().tolist()),
            "pet": sorted(df['Cho_nuoi_pet'].astype(str).unique().tolist())
        }
    except Exception as e:
        # st.error(f"Không load được data CSV chuẩn: {e}. Dùng mặc định.")
        return default

options = load_options()

# --- 4. STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! Hãy tải ảnh phòng hoặc nhập thông số chi tiết bên trái để tôi định giá chuẩn xác."}]
if "ai_data" not in st.session_state:
    st.session_state.ai_data = {} 
if "context" not in st.session_state:
    st.session_state.context = ""

# --- 5. SIDEBAR: NHẬP LIỆU (FORM MỚI CHI TIẾT) ---
with st.sidebar:
    st.title("🛠️ Nhập liệu thông minh")
    
    # A. UPLOAD ẢNH (Giữ nguyên logic cũ)
    uploaded_files = st.file_uploader("📸 Chọn ảnh phòng (AI sẽ tự điền Nội thất)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    
    if uploaded_files and st.button("🔍 Phân tích ảnh"):
        full_description = []
        total_area = 0.0
        
        progress_bar = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            try:
                files = {"file": (file.name, file.getvalue(), file.type)}
                res = requests.post(f"{API_URL}/analyze-image", files=files)
                if res.status_code == 200:
                    data = res.json()
                    desc = data.get("description", "") or data.get("Mo_ta", "")
                    if desc: full_description.append(desc)
                    # Lấy diện tích max tìm thấy
                    area = float(data.get("Dien_tich", 0))
                    if area > total_area: total_area = area
            except: pass
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        progress_bar.empty()
        
        combined_desc = " ".join(full_description)
        # Map sang hệ thống nội thất mới
        suggested_noi_that = auto_classify_utility(combined_desc)
        
        st.session_state.ai_data = {
            "Mo_ta": combined_desc,
            "Noi_that": suggested_noi_that,
            "Dien_tich": total_area if total_area > 0 else 25.0
        }
        st.success("Đã phân tích xong! Hãy kiểm tra các trường bên dưới.")

    # B. FORM NHẬP CHI TIẾT (CẬP NHẬT 16 TRƯỜNG)
    with st.form("input_form"):
        st.write("---")
        st.subheader("📍 1. Thông tin cơ bản")
        
        # Quận & Diện tích
        c1, c2 = st.columns(2)
        with c1:
            quan = st.selectbox("Quận/Huyện", options["quan"])
        with c2:
            val_dt = float(st.session_state.ai_data.get("Dien_tich", 25.0))
            dt = st.number_input("Diện tích (m2)", value=val_dt, min_value=5.0)

        loai = st.selectbox("Loại hình", options["loai"])
        kc_tt = st.slider("Cách Hồ Gươm (m)", 500, 15000, 3000, step=500)
        
        # Nhóm Cấu trúc
        with st.expander("🏢 2. Cấu trúc Toà nhà (Tầng/Thang máy)"):
            c3, c4 = st.columns(2)
            with c3:
                so_tang = st.number_input("Tổng số tầng", 1, 20, 7)
                thang_may = st.radio("Thang máy", ["Có", "Không"], horizontal=True, index=0)
            with c4:
                tang_phong = st.number_input("Phòng ở tầng?", 1, 20, 3)
                
        # Nhóm Tiện nghi (Quan trọng) - Auto fill từ AI
        with st.expander("🛋️ 3. Nội thất & Tiện nghi (Quan trọng)", expanded=True):
            # Tự động điền Nội thất từ kết quả phân tích ảnh
            ai_noi_that = st.session_state.ai_data.get("Noi_that", options["noi_that"][1]) # Default Cơ bản
            idx_nt = 0
            if ai_noi_that in options["noi_that"]:
                idx_nt = options["noi_that"].index(ai_noi_that)
            
            noi_that = st.selectbox("Chất lượng Nội thất", options["noi_that"], index=idx_nt)
            ban_cong = st.selectbox("Ban công / Cửa sổ", options["ban_cong"])
            khu_bep = st.selectbox("Khu vực bếp", options["khu_bep"])
            ve_sinh = st.selectbox("Nhà vệ sinh", options["ve_sinh"])
            may_giat = st.selectbox("Chỗ giặt đồ", options["may_giat"])

        # Nhóm Dịch vụ
        with st.expander("🛡️ 4. Dịch vụ & Môi trường"):
            vi_tri_ngo = st.selectbox("Vị trí ngõ", options["ngo"])
            c5, c6 = st.columns(2)
            with c5:
                nuoi_pet = st.radio("Nuôi thú cưng", options["pet"], horizontal=True)
            with c6:
                gia_dien = st.select_slider("Giá điện", options=["Giá dân", "3000", "3500", "3800", "4000"], value="3500")
        
        submitted = st.form_submit_button("💰 ĐỊNH GIÁ NGAY", type="primary")

# --- 6. XỬ LÝ KẾT QUẢ ---
if submitted:
    # Chuẩn bị payload khớp 100% với Backend mới
    payload = {
        "Quan_huyen": quan,
        "Dien_tich": dt,
        "Loai_hinh": loai,
        "Tong_so_tang": int(so_tang),
        "Tang_phong": int(tang_phong),
        "Thang_may": thang_may,
        "Noi_that": noi_that,
        "Ban_cong_Cua_so": ban_cong,
        "Khu_bep": khu_bep,
        "Ve_sinh": ve_sinh,
        "May_giat": may_giat,
        "Vi_tri_ngo": vi_tri_ngo,
        "Cho_nuoi_pet": nuoi_pet,
        "Gia_dien": str(gia_dien),
        "Khoang_cach_TT": float(kc_tt)
    }
    
    with st.spinner("🤖 AI đang tính toán 16 yếu tố..."):
        try:
            # Gọi API định giá (dùng tool predict_house_price_core gián tiếp hoặc trực tiếp)
            # Ở đây ta gọi endpoint chat để Agent tự xử lý format text
            # Hoặc nếu bạn có endpoint /predict riêng nhận JSON thì gọi vào đó.
            # Giả sử bạn vẫn dùng logic cũ là gọi Chat Agent để nó trả lời:
            
            summary_prompt = f"""
            Định giá chi tiết cho phòng này:
            - {loai}, {dt}m2 tại {quan} (Cách TT {kc_tt}m)
            - Tầng {tang_phong}/{so_tang}, Thang máy: {thang_may}
            - Nội thất: {noi_that}
            - Chi tiết: {ban_cong}, {khu_bep}, {ve_sinh}, {may_giat}
            - Môi trường: {vi_tri_ngo}, {nuoi_pet}, Điện {gia_dien}
            """
            
            # Update Context cho Chatbot
            st.session_state.context = summary_prompt
            
            # Gửi request
            res = requests.post(f"{API_URL}/chat", json={"text": summary_prompt})
            
            if res.status_code == 200:
                data = res.json()
                reply = data.get("reply", "")
                
                msg = f"{reply}"
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.rerun()
            else:
                st.error(f"Lỗi Server: {res.status_code}")
                
        except Exception as e:
            st.error(f"Lỗi kết nối: {e}")

# --- 7. MÀN HÌNH CHAT (GIỮ NGUYÊN) ---
st.title("Chuyên gia tư vấn Phòng Trọ")

# Header động
if submitted:
    st.info(f"✅ Đang xem xét căn: {loai} {dt}m2 tại {quan} - {noi_that}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- PHẦN CHAT UI (Thay thế đoạn cuối file cũ) ---
if prompt := st.chat_input("Hỏi thêm về căn này..."):
    # 1. Hiển thị câu hỏi người dùng ngay lập tức
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    # 2. Chuẩn bị Context (Thông tin phòng)
    # Nếu chưa định giá thì context để trống hoặc lấy thông tin từ form
    if "context" not in st.session_state:
        st.session_state.context = "Khách hàng đang hỏi chung chung, chưa nhập thông tin phòng cụ thể."
    
    ctx = st.session_state.context

    # 3. CHUẨN BỊ MEMORY (Gom lịch sử chat) -> ĐÂY LÀ PHẦN QUAN TRỌNG
    # Lấy 10 tin nhắn gần nhất để gửi đi (tránh gửi quá dài gây lỗi)
    recent_msgs = st.session_state.messages[-10:] 
    history_text = ""
    for msg in recent_msgs:
        role = "Khách" if msg["role"] == "user" else "AI"
        history_text += f"- {role}: {msg['content']}\n"

    # 4. Gửi Request xuống Backend
    payload = {
        "question": prompt,
        "context": ctx,
        "history": history_text  # <-- Gửi kèm lịch sử
    }
    
    try:
        res = requests.post(f"{API_URL}/chat", json=payload)
        if res.status_code == 200:
            reply = res.json().get("reply", "Lỗi phản hồi.")
            
            # Hiển thị câu trả lời của AI
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").markdown(reply)
        else:
            st.error(f"Lỗi Server: {res.text}")
    except Exception as e:
        st.error(f"Không kết nối được Server Chat: {e}")