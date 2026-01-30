import streamlit as st
import requests
import pandas as pd
import os

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="Trợ Lý BĐS AI", layout="wide", page_icon="🏠")
API_URL = "http://127.0.0.1:8000"

st.markdown("""
<style>
    .stChatMessage {border-radius: 10px; padding: 10px;}
    .user-msg {background-color: #e6f3ff;}
    .ai-msg {background-color: #f0f2f6;}
    .stButton button {width: 100%;}
</style>
""", unsafe_allow_html=True)

# --- 2. HÀM LOGIC PHÂN LOẠI (DỰA TRÊN TỔNG HỢP NHIỀU ẢNH) ---
def auto_classify_utility(description):
    """
    Phân loại tiện ích dựa trên mô tả TỔNG HỢP từ nhiều ảnh.
    Logic: Đếm điểm 7 món (Giường, Tủ, AC, Nóng lạnh, Tủ lạnh, Bếp, Gác lửng)
    """
    desc = description.lower()
    
    # 1. Check từ khóa "Full option" (Ưu tiên cao nhất)
    if any(x in desc for x in ["đầy đủ", "full nội thất", "full option", "tiện nghi đầy đủ"]):
        return "Đầy đủ"

    # 2. Quét từng món
    # Gác lửng/Gác xép cũng tính là có chỗ ngủ (Giường)
    has_giuong = any(x in desc for x in ["giường", "bed", "nệm", "chỗ ngủ", "gác lửng", "gác xép"])
    # Tủ quần áo (tránh nhầm tủ lạnh)
    has_tu = any(x in desc for x in ["tủ quần áo", "wardrobe", "tủ đồ"]) or ("tủ" in desc and "tủ lạnh" not in desc)
    # Các món khác
    has_dieuhoa = any(x in desc for x in ["điều hòa", "máy lạnh", "ac", "air conditioner"])
    has_nonglanh = any(x in desc for x in ["nóng lạnh", "heater", "water heater"])
    has_tulanh = any(x in desc for x in ["tủ lạnh", "fridge"])
    has_bep = any(x in desc for x in ["bếp", "kệ bếp", "kitchen", "nấu ăn"])
    
    # Tính điểm (Max 6 nhóm chính, Gác lửng gộp vào Giường hoặc tính riêng tùy bạn, ở đây tôi tính điểm tổng món tìm thấy)
    # Tách Gác lửng ra check riêng để tăng cơ hội kiếm điểm nếu cần
    has_gac = any(x in desc for x in ["gác lửng", "gác xép", "mezzanine"])
    
    points = 0
    if has_giuong: points += 1
    if has_tu: points += 1
    if has_dieuhoa: points += 1
    if has_nonglanh: points += 1
    if has_tulanh: points += 1
    if has_bep: points += 1
    if has_gac and not has_giuong: points += 1 # Nếu có gác mà chưa tính giường thì cộng thêm
    
    # Logic quy đổi điểm
    if points >= 5: return "Đầy đủ"    # 5-6 món
    if points == 4: return "Có"        # 4 món
    if points >= 2: return "Cơ bản"    # 2-3 món (thường là Giường + Tủ + Bếp/Xe)
    if points >= 1: return "Thiếu"     # 1 món
    return "Không"

# --- 3. LOAD DATA ---
@st.cache_data
def load_options():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Tìm file ở nhiều vị trí để tránh lỗi
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
            
    default = {"quan": ["Quận 1"], "loai": ["Trọ thường"], "tien_ich": ["Cơ bản"], "xe": ["Yes"]}

    if not file_path:
        return default

    try:
        df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')
        return {
            "quan": sorted(df['Quan_huyen'].astype(str).unique().tolist()),
            "loai": sorted(df['Loai_phong'].astype(str).unique().tolist()),
            "tien_ich": sorted(df['Tien_ich_co_ban'].astype(str).unique().tolist()),
            "xe": sorted(df['Cho_de_xe'].astype(str).unique().tolist())
        }
    except:
        return default

options = load_options()

# --- 4. STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! Hãy upload 1 hoặc nhiều ảnh phòng để tôi định giá chính xác nhất nhé."}]
if "ai_data" not in st.session_state:
    st.session_state.ai_data = {} 
if "context" not in st.session_state:
    st.session_state.context = ""

# --- 5. SIDEBAR: UPLOAD NHIỀU ẢNH ---
with st.sidebar:
    st.title("🛠️ Nhập liệu thông minh")
    
    # A. UPLOAD NHIỀU ẢNH (accept_multiple_files=True)
    uploaded_files = st.file_uploader("📸 Chọn nhiều ảnh (Phòng, Bếp, WC...)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    
    if uploaded_files and st.button("🔍 Phân tích tất cả ảnh"):
        
        full_description = []
        total_area = 0.0
        found_loai_phong = None
        
        # Thanh tiến trình
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Đang soi ảnh {i+1}/{len(uploaded_files)}: {file.name}...")
            try:
                # Gửi từng ảnh lên API
                files = {"file": (file.name, file.getvalue(), file.type)}
                res = requests.post(f"{API_URL}/analyze-image", files=files)
                
                if res.status_code == 200:
                    data = res.json()
                    desc = data.get("description", "") or data.get("Mo_ta", "")
                    
                    # Cộng dồn mô tả
                    if desc:
                        full_description.append(f"- Ảnh {i+1}: {desc}")
                    
                    # Lấy diện tích lớn nhất tìm thấy (hoặc trung bình, ở đây lấy max cho an toàn)
                    area = float(data.get("Dien_tich", 0))
                    if area > total_area:
                        total_area = area
                        
                    # Lấy loại phòng (lấy cái đầu tiên tìm thấy khác null)
                    if not found_loai_phong and data.get("Loai_phong"):
                        found_loai_phong = data.get("Loai_phong")
                        
            except Exception as e:
                st.error(f"Lỗi ảnh {file.name}: {e}")
            
            # Cập nhật thanh tiến trình
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        status_text.text("✅ Đã xong!")
        progress_bar.empty()
        
        # --- TỔNG HỢP KẾT QUẢ ---
        combined_desc = " ".join(full_description)
        
        # Chạy logic phân loại trên TOÀN BỘ mô tả gộp
        final_tien_ich = auto_classify_utility(combined_desc)
        
        # Lưu vào Session
        st.session_state.ai_data = {
            "Mo_ta": combined_desc,
            "Tien_ich_co_ban": final_tien_ich,
            "Loai_phong": found_loai_phong if found_loai_phong else "Trọ thường",
            "Dien_tich": total_area if total_area > 0 else 25.0
        }
        
        st.success(f"Đã phân tích {len(uploaded_files)} ảnh!")
        with st.expander("👁️ Xem chi tiết AI thấy gì"):
            st.write(combined_desc)
            st.info(f"👉 Kết luận tiện ích: **{final_tien_ich}**")

    # B. FORM NHẬP (AUTO FILL)
    with st.form("input_form"):
        st.write("---")
        ai_data = st.session_state.ai_data
        
        # 1. Quận
        quan = st.selectbox("Quận/Huyện", options["quan"])
        
        # 2. Loại phòng
        idx_loai = 0
        cur_loai = ai_data.get("Loai_phong")
        if cur_loai in options["loai"]:
            idx_loai = options["loai"].index(cur_loai)
        loai = st.selectbox("Loại phòng", options["loai"], index=idx_loai)
        
        # 3. Diện tích
        val_dt = float(ai_data.get("Dien_tich", 25))
        dt = st.number_input("Diện tích (m2)", value=val_dt)
        
        # 4. Tiện ích (Logic tìm kiếm thông minh)
        suggested = ai_data.get("Tien_ich_co_ban", options["tien_ich"][0])
        idx_ti = 0
        
        # Map dữ liệu AI sang dữ liệu CSV
        if suggested in options["tien_ich"]:
            idx_ti = options["tien_ich"].index(suggested)
        else:
            # Map tương đối nếu không khớp 100%
            if suggested == "Đầy đủ" and "Full" in options["tien_ich"]: # VD CSV dùng từ Full
                 idx_ti = options["tien_ich"].index("Full")
            elif suggested == "Có" and "Cơ bản" in options["tien_ich"]:
                idx_ti = options["tien_ich"].index("Cơ bản")
        
        tien_ich = st.selectbox("Tiện ích", options["tien_ich"], index=idx_ti)
        
        # 5. Các thông số khác
        xe = st.selectbox("Chỗ để xe", options["xe"])
        kc_tt = st.slider("Cách trung tâm (m)", 0, 10000, 3000)
        kc_dh = st.slider("Cách trường ĐH (m)", 0, 5000, 1000)
        
        submitted = st.form_submit_button("💰 ĐỊNH GIÁ NGAY", type="primary")

# --- 6. XỬ LÝ KẾT QUẢ ---
if submitted:
    payload = {
        "Quan_huyen": quan, "Loai_phong": loai, "Dien_tich": dt,
        "Tien_ich_co_ban": tien_ich, "Cho_de_xe": xe,
        "Khoang_cach_TT": kc_tt, "Gan_truong_DH": kc_dh
    }
    
    with st.spinner("Đang định giá..."):
        try:
            res = requests.post(f"{API_URL}/predict", json=payload)
            if res.status_code == 200:
                data = res.json()
                price = data['price_formatted']
                explain = data['explanation']
                
                # Lưu context cho Chatbot
                st.session_state.context = (
                    f"Thông tin phòng: {quan}, {dt}m2, {loai}. "
                    f"Tiện ích: {tien_ich} (Xe: {xe}). "
                    f"Mô tả chi tiết từ ảnh: {st.session_state.ai_data.get('Mo_ta', 'N/A')}. "
                    f"Giá dự đoán: {price}"
                )
                
                msg = f"### 💵 Giá tham khảo: {price}\n\n{explain}"
                st.session_state.messages.append({"role": "assistant", "content": msg})
                st.rerun()
            else:
                st.error("Lỗi API định giá.")
        except Exception as e:
            st.error(f"Lỗi: {e}")

# Màn hình Chat
st.title("Chuyên gia tư vấn Phòng Trọ ")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Hỏi thêm về căn này..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    
    ctx = st.session_state.context if st.session_state.context else "Chưa có thông tin phòng."
    
    try:
        res = requests.post(f"{API_URL}/chat", json={"question": prompt, "context": ctx})
        if res.status_code == 200:
            reply = res.json()["reply"]
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").markdown(reply)
    except:
        pass