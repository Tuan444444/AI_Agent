import streamlit as st
import requests
import pandas as pd
import os
import json
import uuid
# Đảm bảo file database.py nằm cùng thư mục
# Tìm dòng import và thêm check_session_exists
from database import get_history_for_frontend, check_session_exists

# --- 1. CẤU HÌNH TRANG & CSS ---
st.set_page_config(page_title="Trợ Lý BĐS AI", layout="wide", page_icon="🏠")

API_URL = "http://localhost:8000"

st.markdown("""
<style>
    .stChatMessage {border-radius: 10px; padding: 10px;}
    .user-msg {background-color: #e6f3ff;}
    .ai-msg {background-color: #f0f2f6;}
    .stButton button {width: 100%; border-radius: 8px;}
    .stExpander {border: 1px solid #ddd; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# --- 2. HÀM TIỆN ÍCH ---
def auto_classify_utility(description):
    """Phân loại mức độ nội thất dựa trên mô tả."""
    desc = description.lower()
    if any(x in desc for x in ["đầy đủ", "full nội thất", "full option", "sang trọng", "luxury"]):
        return "Full đồ Luxury (Smart TV, Sofa...)"
    
    points = 0
    checks = ["giường", "tủ", "điều hòa", "nóng lạnh", "tủ lạnh", "bếp"]
    for item in checks:
        if item in desc: points += 1
        
    if points >= 5: return "Full đồ Luxury (Smart TV, Sofa...)"
    if points >= 3: return "Cơ bản (Giường, tủ, nóng lạnh, ĐH)"
    if points >= 1: return "Đồ cũ/Thiếu đồ"
    return "Nhà trống"

@st.cache_data
def load_options():
    """Load dữ liệu dropdown từ CSV."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(current_dir, "data2_file.csv"),
        "data2_file.csv"
    ]
    file_path = next((p for p in possible_paths if os.path.exists(p)), None)
    
    default = {
        "quan": ["Cầu Giấy", "Đống Đa", "Ba Đình", "Hoàn Kiếm", "Tây Hồ", "Thanh Xuân", "Hai Bà Trưng", "Hoàng Mai"],
        "loai": ["Chung cư mini", "Trọ thường", "Căn hộ dịch vụ (Studio)", "1N1K"],
        "noi_that": ["Full đồ Luxury (Smart TV, Sofa...)", "Cơ bản (Giường, tủ, nóng lạnh, ĐH)", "Đồ cũ/Thiếu đồ", "Nhà trống"],
        "ban_cong": ["Ban công rộng thoáng", "Cửa sổ kính lớn", "Cửa sổ giếng trời", "Không cửa sổ"],
        "khu_bep": ["Bếp tách biệt", "Kệ bếp trong phòng", "Nấu ăn chung"],
        "ve_sinh": ["Khép kín (Có vách kính)", "Khép kín (Cơ bản)", "Vệ sinh chung"],
        "may_giat": ["Máy giặt riêng", "Máy giặt chung", "Không có"],
        "ngo": ["Mặt phố", "Ba gác tránh", "Xe máy tránh nhau", "Ngõ nhỏ"],
        "pet": ["Cho nuôi Pet", "Cấm nuôi Pet"]
    }

    if not file_path: return default

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        return {k: sorted(df[col].astype(str).unique().tolist()) for k, col in [
            ("quan", "Quan_huyen"), ("loai", "Loai_hinh"), ("noi_that", "Noi_that"),
            ("ban_cong", "Ban_cong_Cua_so"), ("khu_bep", "Khu_bep"), ("ve_sinh", "Ve_sinh"),
            ("may_giat", "May_giat"), ("ngo", "Vi_tri_ngo"), ("pet", "Cho_nuoi_pet")
        ]}
    except: return default

options = load_options()

# --- 3. QUẢN LÝ STATE & SESSION ---

# A. Khởi tạo Session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    print(f"🆕 New Session: {st.session_state.session_id}")

# B. Khởi tạo biến môi trường
if "ai_data" not in st.session_state: st.session_state.ai_data = {}
if "context" not in st.session_state: st.session_state.context = ""

# C. Load lịch sử chat từ Database (Chỉ chạy 1 lần khi messages rỗng)
if "messages" not in st.session_state:
    # Thử lấy từ DB
    db_history = get_history_for_frontend(st.session_state.session_id)
    if db_history:
        st.session_state.messages = db_history
    else:
        st.session_state.messages = [
            {"role": "assistant", "content": "Chào bạn! Tôi là AI định giá. Hãy nhập thông tin phòng để bắt đầu."}
        ]

# --- FILE: frontend.py ---
# Tìm đến phần Sidebar và thay thế bằng đoạn này:

with st.sidebar:
    st.title("🗂️ Quản lý Hội thoại")
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:6].upper()

    # Ô nhập ID
    input_id = st.text_input(
        "Mã/Tên phiên làm việc", 
        value=st.session_state.session_id
    )

    # Kiểm tra tồn tại để hiện thông báo (Code check cũ của bạn)
    is_exist = check_session_exists(input_id)
    if is_exist:
        st.warning(f"⚠️ ID '{input_id}' đã tồn tại! Đang hiển thị lại lịch sử.")
    else:
        st.success(f"✅ ID '{input_id}' là mới.")

    # --- ĐOẠN SỬA LOGIC QUAN TRỌNG NHẤT ---
    if input_id != st.session_state.session_id:
        # 1. Cập nhật ID mới
        st.session_state.session_id = input_id
        
        # 2. GỌI DB LOAD LỊCH SỬ NGAY TẠI ĐÂY (Thay vì chỉ xóa rỗng)
        print(f"🔄 Đang load lại lịch sử cho ID: {input_id}")
        history_from_db = get_history_for_frontend(input_id)
        
        if history_from_db:
            st.session_state.messages = history_from_db
            # (Tùy chọn) Hiện thông báo nhỏ góc màn hình
            st.toast(f"Đã khôi phục {len(history_from_db)} tin nhắn!", icon="🎉")
        else:
            # Nếu ID mới tinh chưa có gì -> Reset về rỗng hoặc câu chào
            st.session_state.messages = [
                {"role": "assistant", "content": "Chào bạn! Phiên chat mới đã sẵn sàng."}
            ]
            
        # 3. Load lại trang để hiển thị
        st.rerun()

    st.divider()
    if st.button("➕ Tạo phiên mới"):
        st.session_state.session_id = str(uuid.uuid4())[:6].upper()
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # --- Upload Ảnh ---
    uploaded_files = st.file_uploader("📸 Phân tích ảnh phòng", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    if uploaded_files and st.button("🔍 Phân tích ngay"):
        full_desc, total_area = [], 0.0
        p_bar = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            try:
                files = {"file": (file.name, file.getvalue(), file.type)}
                res = requests.post(f"{API_URL}/analyze-image", files=files)
                if res.status_code == 200:
                    d = res.json()
                    desc = d.get("description") or d.get("Mo_ta")
                    if desc: full_desc.append(desc)
                    area = float(d.get("Dien_tich", 0))
                    if area > total_area: total_area = area
            except Exception as e:
                st.error(f"Lỗi ảnh {file.name}: {e}")
            p_bar.progress((i + 1) / len(uploaded_files))
        
        p_bar.empty()
        
        # Lưu kết quả vào State
        combined_desc = " ".join(full_desc)
        st.session_state.ai_data = {
            "Mo_ta_full": combined_desc,
            "Noi_that": auto_classify_utility(combined_desc),
            "Dien_tich": total_area if total_area > 0 else 25.0
        }
        st.success("✅ Đã phân tích xong! Dữ liệu đã điền vào form.")
        st.rerun()

    # --- Form Nhập Liệu ---
    with st.form("input_form"):
        st.subheader("📝 Thông tin chi tiết")
        
        # Lấy dữ liệu mặc định từ AI nếu có
        ai = st.session_state.ai_data
        
        c1, c2 = st.columns(2)
        quan = c1.selectbox("Quận/Huyện", options["quan"])
        dt = c2.number_input("Diện tích (m2)", value=float(ai.get("Dien_tich", 25.0)), min_value=5.0)
        
        loai = st.selectbox("Loại hình", options["loai"])
        kc_tt = st.number_input("Cách Hồ Gươm (m)", value=0, step=100, help="0 = Tự tính theo Quận")
        
        with st.expander("Cấu trúc & Tiện nghi", expanded=True):
            c3, c4 = st.columns(2)
            so_tang = c3.number_input("Số tầng nhà", 1, 30, 7)
            thang_may = c3.radio("Thang máy", ["Có", "Không"], horizontal=True)
            tang_phong = c4.number_input("Tầng của phòng", 1, 30, 3)
            
            # Auto select nội thất
            def_nt = ai.get("Noi_that", options["noi_that"][1])
            idx_nt = options["noi_that"].index(def_nt) if def_nt in options["noi_that"] else 1
            
            noi_that = st.selectbox("Nội thất", options["noi_that"], index=idx_nt)
            ban_cong = st.selectbox("Ban công", options["ban_cong"])
            khu_bep = st.selectbox("Bếp", options["khu_bep"])
            ve_sinh = st.selectbox("Vệ sinh", options["ve_sinh"])
            may_giat = st.selectbox("Máy giặt", options["may_giat"])
            vi_tri_ngo = st.selectbox("Ngõ", options["ngo"])
            nuoi_pet = st.radio("Pet", options["pet"], horizontal=True)
            gia_dien = st.select_slider("Giá điện", ["3000", "3500", "3800", "4000", "Giá dân"], value="3500")

        submitted = st.form_submit_button("💰 ĐỊNH GIÁ NGAY", type="primary")

# --- 5. XỬ LÝ FORM SUBMIT (GỌI AGENT) ---
if submitted:
    # 1. Tạo Context JSON
    info_data = {
        "Quan_huyen": quan, "Dien_tich": dt, "Loai_hinh": loai,
        "Tong_so_tang": so_tang, "Tang_phong": tang_phong, "Thang_may": thang_may,
        "Noi_that": noi_that, "Ban_cong_Cua_so": ban_cong, "Khu_bep": khu_bep,
        "Ve_sinh": ve_sinh, "May_giat": may_giat, "Vi_tri_ngo": vi_tri_ngo,
        "Cho_nuoi_pet": nuoi_pet, "Gia_dien": str(gia_dien), "Khoang_cach_TT": kc_tt
    }
    context_str = json.dumps(info_data, ensure_ascii=False)
    st.session_state.context = context_str # Lưu context để chat tiếp
    
    # 2. Gọi Agent Định Giá
    # Tạo câu prompt giả lập người dùng hỏi định giá
    first_query = f"Tôi có căn phòng {dt}m2 ở {quan}. Hãy định giá giúp tôi dựa trên thông số trong context."
    
    # Hiển thị câu hỏi của user (ẩn danh nghĩa là form submit)
    st.session_state.messages.append({"role": "user", "content": f"Yêu cầu định giá: {loai} {dt}m2 tại {quan}"})
    
    with st.spinner("🤖 Đang tính toán giá thị trường..."):
        try:
            payload = {
                "question": first_query,
                "context": context_str,
                "session_id": st.session_state.session_id # <--- Gửi ID để lưu lịch sử
            }
            res = requests.post(f"{API_URL}/chat", json=payload)
            if res.status_code == 200:
                reply = res.json().get("reply", "Lỗi server")
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
            else:
                st.error(f"Lỗi API: {res.text}")
        except Exception as e:
            st.error(f"Không kết nối được Server: {e}")

# --- 6. GIAO DIỆN CHAT CHÍNH ---
st.title("💬 Chuyên gia Bất Động Sản")

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    avatar = "🤖" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- 7. INPUT CHAT (HỎI ĐÁP TIẾP THEO) ---
if prompt := st.chat_input("Hỏi thêm (VD: Khu này có tắc đường không?)..."):
    # 1. Hiện câu hỏi user
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user", avatar="👤").markdown(prompt)
    
    # 2. Lấy context đã lưu (nếu có)
    ctx = st.session_state.context if st.session_state.context else "Chưa có thông tin phòng."
    
    # 3. Gửi sang API
    try:
        payload = {
            "question": prompt,
            "context": ctx,
            "session_id": st.session_state.session_id # <--- Quan trọng
        }
        res = requests.post(f"{API_URL}/chat", json=payload)
        
        if res.status_code == 200:
            reply = res.json().get("reply", "Lỗi phản hồi")
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.chat_message("assistant", avatar="🤖").markdown(reply)
        else:
            st.error(f"Lỗi: {res.text}")
            
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")