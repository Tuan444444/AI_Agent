import os
import pandas as pd
import joblib
from dotenv import load_dotenv

# --- IMPORT CHUẨN (Tương thích LangChain cũ & mới) ---
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.tools import Tool, StructuredTool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional

# ==========================================
# 1. CẤU HÌNH & LOAD MODEL
# ==========================================
load_dotenv() 

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Kiểm tra Key ---
if not GOOGLE_API_KEY:
    print("❌ LỖI: Chưa có GOOGLE_API_KEY trong file .env")
    # Gán tạm để tránh crash, nhưng sẽ lỗi khi gọi lệnh
    os.environ["GOOGLE_API_KEY"] = "" 

# --- Tìm file Model (Dùng đường dẫn tuyệt đối) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(current_dir, "data/price_model.pkl") 

model = None
try:
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print(f"✅ (Backend) Đã load model: {MODEL_PATH}")
    else:
        print(f"❌ (Backend) Lỗi: Không tìm thấy file {MODEL_PATH}")
        print("👉 Hãy đảm bảo file 'price_model.pkl' nằm cùng thư mục với backend_agent.py")
except Exception as e:
    print(f"❌ (Backend) Lỗi load model: {e}")

# 1. Định nghĩa cấu trúc đầu vào MỚI (16 trường thông tin)
class HousePriceInput(BaseModel):
    # --- BẮT BUỘC PHẢI CÓ ---
    Quan_huyen: str = Field(..., description="Quận/Huyện (Ví dụ: 'Cầu Giấy', 'Đống Đa')")
    Dien_tich: float = Field(..., description="Diện tích phòng (m2)")
    
    # --- CÓ THỂ TỰ SUY LUẬN HOẶC ĐỂ MẶC ĐỊNH ---
    Loai_hinh: str = Field(default="Chung cư mini", description="Loại phòng: 'Chung cư mini', 'Trọ thường', 'Studio', '1N1K'")
    
    # Cấu trúc nhà
    Tong_so_tang: int = Field(default=7, description="Tổng số tầng của toà nhà (Mặc định 7)")
    Tang_phong: int = Field(default=3, description="Tầng của phòng (Mặc định tầng 3)")
    Thang_may: str = Field(default="Có", description="'Có' hoặc 'Không'")
    
    # Tiện nghi (Rất quan trọng)
    Noi_that: str = Field(default="Cơ bản (Giường, tủ, nóng lạnh, ĐH)", description="'Full đồ Luxury', 'Cơ bản', 'Đồ cũ/Thiếu đồ', 'Nhà trống'")
    Ban_cong_Cua_so: str = Field(default="Cửa sổ kính lớn (Big Window)", description="'Ban công rộng thoáng', 'Cửa sổ kính lớn', 'Cửa sổ giếng trời', 'Không cửa sổ'")
    Khu_bep: str = Field(default="Kệ bếp trong phòng", description="'Bếp tách biệt', 'Kệ bếp trong phòng', 'Nấu ăn chung khu'")
    Ve_sinh: str = Field(default="Khép kín (Cơ bản)", description="'Khép kín (Có vách kính tắm)', 'Khép kín (Cơ bản)', 'Vệ sinh chung'")
    May_giat: str = Field(default="Máy giặt chung (Sân thượng)", description="'Máy giặt riêng trong phòng', 'Máy giặt chung', 'Không có máy giặt'")
    
    # Môi trường
    Vi_tri_ngo: str = Field(default="Xe máy tránh nhau", description="'Mặt phố/Oto đỗ cửa', 'Ba gác tránh/Ngõ nông', 'Xe máy tránh nhau', 'Ngõ ngách sâu'")
    Cho_nuoi_pet: str = Field(default="Cấm nuôi Pet", description="'Cho nuôi Pet' hoặc 'Cấm nuôi Pet'")
    Gia_dien: str = Field(default="3500", description="Giá điện (VNĐ/số) hoặc 'Giá dân'")
    
    # Khoảng cách
    Khoang_cach_TT: float = Field(default=3000, description="Khoảng cách đến hồ Hoàn Kiếm (mét). Mặc định 3000m.")

# ==========================================
# 3. HÀM TÍNH TOÁN (Logic Core)
# ==========================================
def predict_house_price_core(
    Quan_huyen: str, Dien_tich: float, 
    Loai_hinh: str = "Chung cư mini",
    Tong_so_tang: int = 7, Tang_phong: int = 3, Thang_may: str = "Có",
    Noi_that: str = "Cơ bản (Giường, tủ, nóng lạnh, ĐH)",
    Ban_cong_Cua_so: str = "Cửa sổ kính lớn (Big Window)",
    Khu_bep: str = "Kệ bếp trong phòng",
    Ve_sinh: str = "Khép kín (Cơ bản)",
    May_giat: str = "Máy giặt chung (Sân thượng)",
    Vi_tri_ngo: str = "Xe máy tránh nhau",
    Cho_nuoi_pet: str = "Cấm nuôi Pet",
    Gia_dien: str = "3500",
    Khoang_cach_TT: float = 3000
) -> str:
    """
    Hàm lõi dự đoán giá nhà với đầy đủ 16 yếu tố.
    """
    try:
        # 1. Tạo DataFrame từ input (Phải đúng tên cột như lúc train)
        input_data = pd.DataFrame([{
            "Quan_huyen": Quan_huyen,
            "Loai_hinh": Loai_hinh,
            "Dien_tich": Dien_tich,
            "Tong_so_tang": Tong_so_tang,
            "Tang_phong": Tang_phong,
            "Thang_may": Thang_may,
            "Noi_that": Noi_that,
            "Ban_cong_Cua_so": Ban_cong_Cua_so,
            "Khu_bep": Khu_bep,
            "Ve_sinh": Ve_sinh,
            "May_giat": May_giat,
            "Vi_tri_ngo": Vi_tri_ngo,
            "Cho_nuoi_pet": Cho_nuoi_pet,
            "Gia_dien": str(Gia_dien), # Chuyển sang string cho chắc
            "Khoang_cach_TT": Khoang_cach_TT
        }])

        # 2. Dự đoán
        predicted_price = model.predict(input_data)[0]
        
        # 3. Format tiền đẹp (Ví dụ: 3,500,000)
        return f"{int(predicted_price):,} VNĐ"

    except Exception as e:
        return f"Lỗi tính toán: {str(e)}. Hãy kiểm tra lại dữ liệu đầu vào."
# ==========================================
# 4. TẠO AGENT & TOOLS
# ==========================================
price_tool = StructuredTool.from_function(
    func=predict_house_price_core,
    name="House_Price_Calculator",
    description="Công cụ tính giá phòng.",
    args_schema=HousePriceInput
)

search_tool = DuckDuckGoSearchRun()
search_tool_wrapper = Tool(
    name="Internet_Search",
    func=search_tool.run,
    description="Tìm thông tin bổ trợ."
)

tools = [price_tool, search_tool_wrapper]

# Khởi tạo LLM
llm = None
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=GOOGLE_API_KEY,
        temperature=0
    )
except Exception as e:
    print(f"⚠️ Cảnh báo LLM: {e}")

# --- SYSTEM PROMPT (QUAN TRỌNG: Phải có {tools} và {tool_names}) ---
system_prompt = """
Bạn là Chuyên gia Môi giới Bất động sản số 1 Hà Nội. Nhiệm vụ của bạn là định giá phòng trọ cực kỳ chi tiết và sát thực tế.

Bạn có một công cụ siêu việt là `House_Price_Calculator` có thể tính giá dựa trên 16 yếu tố.

CHIẾN THUẬT SUY LUẬN (MAPPING STRATEGY):
Khi người dùng mô tả, hãy cố gắng map từ khoá của họ vào các thông số kỹ thuật sau:

1. **Nội thất**:
   - "Full đồ", "Xách vali vào ở", "Sang trọng" -> Chọn `Noi_that="Full đồ Luxury..."`
   - "Đồ cơ bản", "Đủ đồ" -> Chọn `Noi_that="Cơ bản..."`
   - "Phòng trống", "Chưa có đồ" -> Chọn `Noi_that="Nhà trống"`

2. **Thoáng khí (Quan trọng)**:
   - "Có ban công", "Thoáng" -> Chọn `Ban_cong_Cua_so="Ban công rộng thoáng"`
   - "Cửa sổ to", "Sáng" -> Chọn `Ban_cong_Cua_so="Cửa sổ kính lớn..."`
   - "Kín", "Bí" -> Chọn `Ban_cong_Cua_so="Không cửa sổ..."`

3. **Tiện ích khác**:
   - "Nấu ăn riêng", "Không chung chủ" -> `Khu_bep="Bếp tách biệt"`
   - "Máy giặt riêng" -> `May_giat="Máy giặt riêng trong phòng"`
   - "Nuôi mèo", "Nuôi cún" -> `Cho_nuoi_pet="Cho nuôi Pet"`

4. **Vị trí/Ngõ**:
   - "Ô tô đỗ cửa" -> `Vi_tri_ngo="Mặt phố/Oto đỗ cửa"`
   - "Ngõ sâu", "Yên tĩnh" -> `Vi_tri_ngo="Ngõ ngách sâu..."`

⚠️ QUY TẮC VÀNG: 
- Nếu người dùng KHÔNG nhắc đến yếu tố nào, hãy ĐỂ MẶC ĐỊNH (Agent tự dùng giá trị default của hàm). Đừng hỏi lại khách quá nhiều gây khó chịu.
- Chỉ hỏi lại nếu thiếu thông tin cốt lõi là `Quan_huyen` và `Dien_tich`.

Ví dụ: Khách nói "Tìm phòng Cầu Giấy 25m2 có ban công nuôi được mèo".
-> Bạn gọi tool với: Quan_huyen="Cầu Giấy", Dien_tich=25, Ban_cong_Cua_so="Ban công rộng thoáng", Cho_nuoi_pet="Cho nuôi Pet". Các trường khác để tự động.
"""

prompt = ChatPromptTemplate.from_messages([ ("system", system_prompt), ("human", "{input}"), ("ai", "{agent_scratchpad}"), ])
# --- KHỞI TẠO AGENT ---
agent_executor = None
if llm:
    agent = create_structured_chat_agent(llm, tools,prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )

def run_agent_query(user_query: str, context: str = "") -> str:
    if not agent_executor:
        return "Lỗi: Hệ thống AI chưa sẵn sàng (Kiểm tra API Key hoặc kết nối mạng)."
    
    full_msg = f"Câu hỏi: {user_query}\nNgữ cảnh: {context}"
    try:
        res = agent_executor.invoke({"input": full_msg})
        return res["output"]
    except Exception as e:
        return f"Lỗi Agent: {e}"