import os
import pandas as pd
import joblib
from dotenv import load_dotenv
from database import save_message, get_chat_history

# --- IMPORT LANGCHAIN CHUẨN ---
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
# Dùng create_tool_calling_agent thay cho structured_chat_agent cũ
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool, StructuredTool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ==========================================
# 1. CẤU HÌNH & LOAD MODEL
# ==========================================
load_dotenv() 

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("❌ LỖI: Chưa có GOOGLE_API_KEY trong file .env")
    os.environ["GOOGLE_API_KEY"] = "" 

# --- Load Model ML ---
current_dir = os.path.dirname(os.path.abspath(__file__))
possible_paths = [
    os.path.join(current_dir, "data", "price_model.pkl"),
    os.path.join(current_dir, "price_model.pkl"),
    "data/price_model.pkl"
]

model = None
for path in possible_paths:
    if os.path.exists(path):
        try:
            model = joblib.load(path)
            print(f"✅ (Backend) Đã load model thành công: {path}")
            break
        except Exception as e:
            print(f"⚠️ Lỗi load file {path}: {e}")
            continue

if not model:
    print("❌ (Backend) CẢNH BÁO: Không tìm thấy file price_model.pkl!")

# ==========================================
# 2. ĐỊNH NGHĨA INPUT SCHEMA
# ==========================================
class HousePriceInput(BaseModel):
    Quan_huyen: str = Field(..., description="Quận/Huyện (Ví dụ: 'Cầu Giấy', 'Đống Đa')")
    Dien_tich: float = Field(..., description="Diện tích phòng (m2)")
    
    Loai_hinh: str = Field(default="Chung cư mini", description="Loại phòng")
    Tong_so_tang: int = Field(default=7, description="Tổng số tầng nhà")
    Tang_phong: int = Field(default=3, description="Tầng của phòng")
    Thang_may: str = Field(default="Có", description="'Có' hoặc 'Không'")
    Noi_that: str = Field(default="Cơ bản (Giường, tủ, nóng lạnh, ĐH)", description="Nội thất")
    Ban_cong_Cua_so: str = Field(default="Cửa sổ kính lớn (Big Window)", description="Ban công/Cửa sổ")
    Khu_bep: str = Field(default="Kệ bếp trong phòng", description="Khu bếp")
    Ve_sinh: str = Field(default="Khép kín (Cơ bản)", description="Vệ sinh")
    May_giat: str = Field(default="Máy giặt chung (Sân thượng)", description="Máy giặt")
    Vi_tri_ngo: str = Field(default="Xe máy tránh nhau", description="Vị trí ngõ")
    Cho_nuoi_pet: str = Field(default="Cấm nuôi Pet", description="Nuôi Pet")
    Gia_dien: str = Field(default="3500", description="Giá điện")
    
    # Quan trọng: Nhận diện khoảng cách
    Khoang_cach_TT: float = Field(default=0, description="Khoảng cách đến trung tâm (mét).")

# ==========================================
# 3. HÀM TÍNH TOÁN (CORE TOOL)
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
    Khoang_cach_TT: float = 0 
) -> str:
    if not model:
        return "Lỗi: Model chưa được load."

    try:
        # Logic ưu tiên thanh trượt
        final_distance = Khoang_cach_TT
        if final_distance <= 100:
            DISTRICT_MAPPING = {
                "Hoàn Kiếm": 1000, "Ba Đình": 2500, "Hai Bà Trưng": 3000,
                "Đống Đa": 3500, "Tây Hồ": 4000, "Cầu Giấy": 6000,
                "Thanh Xuân": 6500, "Hoàng Mai": 8000, "Nam Từ Liêm": 10000,
                "Bắc Từ Liêm": 11000, "Long Biên": 7000, "Hà Đông": 12000, 
                "Gia Lâm": 13000
            }
            final_distance = DISTRICT_MAPPING.get(Quan_huyen, 5000)
            print(f"ℹ️ (Auto) Hệ thống tự điền khoảng cách cho {Quan_huyen}: {final_distance}m")
        else:
            print(f"✅ (User) Sử dụng khoảng cách từ Thanh Trượt: {final_distance}m")

        # Tạo input cho model
        input_data = pd.DataFrame([{
            "Quan_huyen": Quan_huyen, "Loai_hinh": Loai_hinh, "Dien_tich": Dien_tich,
            "Tong_so_tang": Tong_so_tang, "Tang_phong": Tang_phong, "Thang_may": Thang_may,
            "Noi_that": Noi_that, "Ban_cong_Cua_so": Ban_cong_Cua_so, "Khu_bep": Khu_bep,
            "Ve_sinh": Ve_sinh, "May_giat": May_giat, "Vi_tri_ngo": Vi_tri_ngo,
            "Cho_nuoi_pet": Cho_nuoi_pet, "Gia_dien": str(Gia_dien), 
            "Khoang_cach_TT": final_distance
        }])

        predicted_price = model.predict(input_data)[0]
        min_price = int((predicted_price * 0.95 )/ 1000) * 1000 
        max_price = int((predicted_price * 1.05) / 1000) * 1000
        avg_price = int(predicted_price)
        return (
            f"Giá dự báo trung bình: {avg_price:,} VNĐ.\n"
            f"Khoảng giá khuyến nghị: Từ {min_price:,} VNĐ đến {max_price:,} VNĐ.\n"
            f"Phân tích chi tiết dựa trên các yếu tố đầu vào. "
            f"Tư vấn những ưu nhược điểm với tư cách khách hàng dễ đưa ra quyết định."
        )

    except Exception as e:
        return f"Lỗi tính toán: {str(e)}"

# ==========================================
# 4. TẠO AGENT (DÙNG TOOL CALLING)
# ==========================================

# Định nghĩa Tool
price_tool = StructuredTool.from_function(
    func=predict_house_price_core,
    name="House_Price_Calculator",
    description="Công cụ tính giá phòng CHÍNH XÁC.",
    args_schema=HousePriceInput
)

search_tool = DuckDuckGoSearchRun()
search_tool_wrapper = Tool(
    name="Internet_Search",
    func=search_tool.run,
    description="Tìm kiếm thông tin bổ trợ."
)

tools = [price_tool, search_tool_wrapper]

# Khởi tạo LLM
llm = None
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-flash-latest",
        google_api_key=GOOGLE_API_KEY,
        temperature=0 # Quan trọng: Để 0
    )
except Exception as e:
    print(f"⚠️ Cảnh báo LLM: {e}")

# --- SYSTEM PROMPT ---
# Với create_tool_calling_agent, prompt đơn giản hơn nhiều
system_prompt = """
Bạn là một Chuyên gia Tư vấn Bất động sản thân thiện, nhiệt tình và am hiểu thị trường Hà Nội.
Tên của bạn là "Trợ lý AI Nhà Đất".

NHIỆM VỤ:
Sử dụng công cụ `House_Price_Calculator` để định giá, sau đó tư vấn cho khách hàng.

PHONG CÁCH TRẢ LỜI:
1.  **Thân thiện & Tự nhiên:** Đừng trả lời như cái máy. Hãy dùng từ ngữ như: "Theo em thấy...", "Mức giá hợp lý cho căn này...", "Vị trí này khá đẹp...".
2.  **Luôn dùng KHOẢNG GIÁ:** Tool sẽ trả về khoảng giá (Ví dụ: 3tr5 - 3tr8). Hãy nhấn mạnh vào khoảng này để khách hàng dễ cân nhắc.
3.  **Phân tích thêm:** Dựa vào dữ liệu đầu vào (Thang máy, Nội thất, Ban công...), hãy thêm 1-2 câu nhận xét.
    * Ví dụ: "Vì phòng có ban công thoáng nên giá này là rất tốt", hoặc "Do thang bộ nên giá sẽ mềm hơn chút".
4.  **Trình bày đẹp:** Sử dụng Bullet point, in đậm các con số tiền để dễ nhìn.

VÍ DỤ TRẢ LỜI TỐT:
"Dựa trên thông tin bác cung cấp, em đã tính toán kỹ lưỡng. Với căn phòng full đồ ở Cầu Giấy này, mức giá thị trường đang dao động trong khoảng **3.500.000đ - 3.800.000đ**.
Mức giá này em thấy khá hợp lý vì nhà mình có thang máy và ban công thoáng, rất được khách thuê ưa chuộng ạ."
"""

# Prompt Template mới (Tương thích Tool Calling)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", """
    THÔNG TIN LỊCH SỬ CHAT:
    {chat_history}
    
    DỮ LIỆU ĐẦU VÀO (CONTEXT) TỪ NGƯỜI DÙNG:
    {context}
    
    YÊU CẦU/CÂU HỎI:
    {input}
    """),
    # Placeholder này cực kỳ quan trọng cho Tool Calling Agent
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent_executor = None
if llm:
    # --- DÙNG HÀM MỚI NÀY ĐỂ FIX LỖI ---
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True 
    )

# ==========================================
# ==========================================
# 5. HÀM GỌI TỪ MAIN (ĐÃ NÂNG CẤP MEMORY)
# ==========================================
def run_agent_query(user_query: str, session_id: str, context_data: str = "") -> str:
    """
    Xử lý câu hỏi với bộ nhớ dài hạn từ Database.
    """
    if not agent_executor:
        return "Lỗi: Hệ thống AI chưa sẵn sàng."

    try:
        # 1. Tự động lấy lịch sử từ DB dựa trên session_id
        history_str = get_chat_history(session_id)
        
        # 2. Gọi Agent
        result = agent_executor.invoke({
            "input": user_query,
            "context": context_data,
            "chat_history": history_str # Truyền lịch sử vào prompt
        })
        ai_response = result["output"]

        # 3. Lưu cuộc hội thoại mới vào DB
        # Lưu câu hỏi người dùng
        save_message(session_id, "user", f"Context: {context_data}\nCâu hỏi: {user_query}")
        # Lưu câu trả lời AI
        save_message(session_id, "ai", ai_response)

        return ai_response

    except Exception as e:
        print(f"❌ Lỗi Agent: {e}")
        return f"Xin lỗi, có lỗi khi xử lý: {str(e)}"