# import os
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.prompts import PromptTemplate

# # Load biến môi trường
# load_dotenv()
# api_key = os.getenv("GOOGLE_API_KEY")

# class ReasoningAgent:
#     def __init__(self):
#         self.llm = None
#         if not api_key:
#             print("⚠️ Cảnh báo: Chưa tìm thấy GOOGLE_API_KEY trong file .env")
#         else:
#             try:
#                 # --- CẤU HÌNH MODEL ---
#                 # Sử dụng 'gemini-1.5-flash' để phản hồi nhanh và thông minh hơn
#                 # temperature=0.6: Giữ cho AI sáng tạo vừa đủ nhưng vẫn bám sát thực tế
#                 self.llm = ChatGoogleGenerativeAI(
#                     model="gemini-flash-latest", 
#                     google_api_key=api_key, 
#                     temperature=0.4,
#                     convert_system_message_to_human=True
#                 )
#                 print("✅ Đã khởi tạo ReasoningAgent (Gemini) thành công!")
#             except Exception as e:
#                 print(f"❌ Lỗi khởi tạo Gemini: {str(e)}")

#     def explain(self, quan, loai_phong, dien_tich, tien_ich, price):
#         """
#         Phân tích giá phòng dựa trên dữ liệu đầu vào.
#         """
#         if not self.llm:
#             return "Lỗi: Hệ thống AI chưa được cấu hình (Thiếu API Key)."


#         # 1. Xử lý dữ liệu trước khi đưa vào Prompt
#         # Format giá tiền cho dễ đọc (ví dụ: 3500000 -> 3,500,000)
#         formatted_price = "{:,.0f}".format(price)
        
#         # Xử lý tiện ích nếu trống
#         feature_text = tien_ich if tien_ich and len(str(tien_ich)) > 2 else "Cơ bản, chưa rõ chi tiết"

#         template = """
# 🎯 VAI TRÒ (ROLE)
# Bạn là một AI Agent chuyên biệt trong lĩnh vực Phân tích Giá thuê Phòng trọ tại Hà Nội,
# đóng vai trò như một Chuyên gia Bất động sản cao cấp với hơn 10 năm kinh nghiệm thị trường.

# Bạn KHÔNG phải là mô hình dự đoán giá.
# Bạn là Agent GIẢI THÍCH & ĐÁNH GIÁ kết quả do hệ thống Machine Learning cung cấp.

# ---

# 🎯 MỤC TIÊU (GOAL)
# Giải thích một cách logic, dễ hiểu và chuyên nghiệp:
# - Vì sao căn phòng có mức giá thuê như vậy
# - Mức giá đó đang ở vị trí nào so với mặt bằng chung
# - Đối tượng thuê phù hợp nhất

# ---

# 📌 DỮ LIỆU ĐẦU VÀO (INPUT DATA)
# Thông tin căn phòng do hệ thống cung cấp:

# 📍 Quận/Khu vực: {quan}
# 🏠 Loại phòng: {loai_phong}
# 📐 Diện tích: {dien_tich} m²
# ✨ Tiện ích: {feature_text}
# 💰 Giá thuê dự đoán (CỐ ĐỊNH): {formatted_price} VNĐ/tháng

# ⚠️ Lưu ý: Giá thuê trên đã được dự đoán bởi mô hình Random Forest và KHÔNG ĐƯỢC THAY ĐỔI.

# ---

# 🧠 QUY TRÌNH SUY LUẬN (REASONING STEPS)
# Hãy phân tích theo các bước sau:
# 1. Đặt mức giá vào bối cảnh thị trường của quận {quan}
# 2. Phân tích giá trị trên mỗi m²
# 3. Đánh giá tác động của:
#    - Diện tích
#    - Loại phòng
#    - Các tiện ích ({feature_text})
# 4. Xác định nhóm người thuê phù hợp nhất

# ---

# 📝 ĐỊNH DẠNG CÂU TRẢ LỜI (OUTPUT FORMAT)
# Trả lời NGẮN GỌN (3–5 câu), súc tích, giọng điệu chuyên nghiệp.
# Không lan man, không giải thích kỹ thuật Machine Learning.

# Cấu trúc bắt buộc:

# 1️⃣ 📊 ĐÁNH GIÁ MỨC GIÁ  
# - Mức giá này được xem là **CAO / HỢP LÝ / THẤP** so với mặt bằng chung tại quận {quan}.  
# - Giá trung bình khoảng X VNĐ/m² (tính từ dữ liệu đã cho).

# 2️⃣ 💡 NGUYÊN NHÂN CHÍNH  
# - Phân tích các yếu tố chính ảnh hưởng đến giá: diện tích, loại phòng và tiện ích.
# - Giải thích vì sao các tiện ích như {feature_text} làm tăng hoặc giữ giá ở mức hiện tại.

# 3️⃣ 🎯 KHUYẾN NGHỊ  
# - Căn phòng phù hợp nhất với nhóm đối tượng nào.
# - Người thuê có nên chốt nhanh hay có thể cân nhắc thêm.

# ---

# 🚫 RÀNG BUỘC NGHIÊM NGẶT (CONSTRAINTS)
# - KHÔNG được tự suy đoán giá mới
# - KHÔNG được thay đổi mức giá đầu vào
# - KHÔNG nhắc đến mô hình huấn luyện, thuật toán, code
# - CHỈ đóng vai trò phân tích & giải thích kết quả

# 📌 Hãy tập trung vào GIÁ TRỊ THỰC TẾ cho người thuê.
# """


#         # 3. Khởi tạo Prompt Template
#         prompt = PromptTemplate.from_template(template)

#         # 4. Tạo Chain (Theo chuẩn LCEL - LangChain Expression Language)
#         chain = prompt | self.llm

#         try:
#             # 5. Thực thi và lấy kết quả
#             response = chain.invoke({
#                 "quan": quan,
#                 "loai_phong": loai_phong,
#                 "dien_tich": dien_tich,
#                 "feature_text": feature_text, # Dùng biến đã xử lý
#                 "formatted_price": formatted_price # Dùng biến đã xử lý
#             })
            
#             # Trả về nội dung text
#             return response.content.strip()

#         except Exception as e:
#             # Fallback an toàn nếu API lỗi
#             print(f"❌ Lỗi khi gọi Gemini: {e}")
#             return f"Giá dự đoán là {formatted_price} VNĐ. (Hiện tại AI đang bận nên chưa thể phân tích chi tiết)."




import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# =============================
# LOAD ENV
# =============================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")


class ReasoningAgent:
    """
    AI Agent chuyên GIẢI THÍCH & PHÂN TÍCH
    (KHÔNG dự đoán giá)
    """

    def __init__(self):
        self.llm = None

        if not API_KEY:
            print("⚠️ Chưa tìm thấy GOOGLE_API_KEY trong file .env")
            return

        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-flash-latest",
                google_api_key=API_KEY,
                temperature=0.4,
                convert_system_message_to_human=True
            )
            print("✅ ReasoningAgent khởi tạo thành công (Gemini)")
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Gemini: {e}")

    # =============================
    # MAIN FUNCTION
    # =============================
    def explain(self, quan, loai_phong, dien_tich, tien_ich, price):
        """
        Giải thích mức giá thuê phòng do ML dự đoán
        """

        if not self.llm:
            return "Hệ thống AI chưa sẵn sàng."

        # =============================
        # 1. TIỀN XỬ LÝ DỮ LIỆU (BẮT BUỘC)
        # =============================

        try:
            quan = str(quan)
            loai_phong = str(loai_phong)
            dien_tich = float(dien_tich)
            price = float(price)
        except Exception:
            return "Dữ liệu đầu vào không hợp lệ."

        formatted_price = "{:,.0f}".format(price)

        # Xử lý tiện ích (FIX LỖI LIST)
        if isinstance(tien_ich, list):
            feature_text = ", ".join(map(str, tien_ich))
        elif isinstance(tien_ich, str) and tien_ich.strip():
            feature_text = tien_ich.strip()
        else:
            feature_text = "Tiện ích cơ bản"

        # =============================
        # 2. PROMPT TEMPLATE (AI AGENT)
        # =============================
        template = """
🎯 VAI TRÒ
Bạn là một AI Agent chuyên phân tích giá thuê phòng trọ tại Hà Nội,
đóng vai Chuyên gia Bất động sản với hơn 10 năm kinh nghiệm.

Bạn KHÔNG dự đoán giá.
Bạn CHỈ giải thích mức giá do hệ thống Machine Learning cung cấp.

---

📌 THÔNG TIN CĂN PHÒNG
📍 Quận: {quan}
🏠 Loại phòng: {loai_phong}
📐 Diện tích: {dien_tich} m²
✨ Tiện ích: {feature_text}
💰 Giá thuê: {formatted_price} VNĐ/tháng

⚠️ Giá thuê trên là CỐ ĐỊNH và KHÔNG ĐƯỢC THAY ĐỔI.

---

🧠 YÊU CẦU PHÂN TÍCH
1. Đánh giá mức giá so với mặt bằng chung tại quận {quan}
- Khi đặt mức giá này trong bối cảnh thị trường phòng trọ tại quận {quan}
  và so sánh với các phòng có diện tích & tiện ích TƯƠNG ĐƯƠNG,
  mức giá này được xem là: CAO / HỢP LÝ / THẤP.

2. Ước tính giá trung bình trên mỗi m²
3. Phân tích tác động của diện tích, loại phòng và tiện ích
4. Xác định đối tượng thuê phù hợp

---

📝 ĐỊNH DẠNG TRẢ LỜI (3–5 CÂU)
1️⃣ 📊 ĐÁNH GIÁ MỨC GIÁ  
2️⃣ 💡 NGUYÊN NHÂN CHÍNH  
3️⃣ 🎯 KHUYẾN NGHỊ  

🚫 KHÔNG:
- Suy đoán giá mới
- Nói về thuật toán, mô hình ML, code
- Trả lời dài dòng
"""

        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm

        # =============================
        # 3. GỌI LLM + FIX OUTPUT
        # =============================
        try:
            response = chain.invoke({
                "quan": quan,
                "loai_phong": loai_phong,
                "dien_tich": dien_tich,
                "feature_text": feature_text,
                "formatted_price": formatted_price
            })

            # Gemini có thể trả list hoặc string
            if isinstance(response.content, list):
                text = ""
                for item in response.content:
                    if isinstance(item, dict) and "text" in item:
                        text += item["text"]
                return text.strip()

            if isinstance(response.content, str):
                return response.content.strip()

            return str(response.content)

        except Exception as e:
            print(f"❌ Lỗi khi gọi Gemini: {e}")
            return (
                f"Giá thuê dự đoán là {formatted_price} VNĐ/tháng. "
                "Hiện AI chưa thể phân tích chi tiết do quá tải."
            )
 
#chạy chương trình: 1.Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#                   2.\venv\Scripts\activate
#                   3.uvicorn main:app --reload
