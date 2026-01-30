import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# =============================
# LOAD ENV
# =============================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")


class ReasoningAgent:
    """
    AI Reasoning Agent
    - KHÔNG dự đoán giá
    - Phân tích, đánh giá và tư vấn dựa trên giá ML cung cấp
    """

    def __init__(self):
        if not API_KEY:
            raise ValueError("Chưa cấu hình GOOGLE_API_KEY trong file .env")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            google_api_key=API_KEY,
            temperature=0.4,
            convert_system_message_to_human=True
        )

        self.output_parser = StrOutputParser()
        self.chain = self._build_chain()

        print("✅ ReasoningAgent sẵn sàng hoạt động")

    # =============================
    # BUILD PROMPT + CHAIN
    # =============================
    def _build_chain(self):
        template = """
VAI TRÒ
Bạn là AI Reasoning Agent chuyên phân tích giá thuê phòng trọ tại Hà Nội và thành phố Hồ Chí Minh,
đóng vai một chuyên gia bất động sản với hơn 10 năm kinh nghiệm thực tế
trong lĩnh vực cho thuê phòng trọ và căn hộ nhỏ.

Nhiệm vụ của bạn là phân tích đặc điểm căn phòng,
lập luận về các yếu tố ảnh hưởng đến giá thuê,
sau đó trình bày kết luận về mức giá thuê đã được hệ thống xác định.

---

QUY TẮC BẮT BUỘC
- KHÔNG tự dự đoán hoặc thay đổi giá thuê
- Mức giá thuê được cung cấp là KẾT QUẢ CUỐI CÙNG và CỐ ĐỊNH
- KHÔNG nhắc đến AI, mô hình, thuật toán, học máy hay code
- KHÔNG sử dụng ký hiệu markdown (*, -, #) hoặc trình bày dạng gạch đầu dòng
- Trả lời ngắn gọn, rõ ràng, đúng vai trò chuyên gia tư vấn

---

THÔNG TIN CĂN PHÒNG
Quận: {quan}
Loại phòng: {loai_phong}
Diện tích: {dien_tich} m²
Tiện ích: {feature_text}

---

KẾT QUẢ PHÂN TÍCH GIÁ
Sau khi phân tích dữ liệu thị trường và các phòng tương đương,
hệ thống đã xác định mức giá thuê phù hợp cho căn phòng này là:
{formatted_price} VNĐ/tháng

---

YÊU CẦU PHÂN TÍCH
1. Phân tích các yếu tố chính ảnh hưởng đến giá thuê như vị trí, diện tích,
   loại phòng và tiện ích, đặt trong bối cảnh thị trường tại quận {quan}.
2. Từ các phân tích trên, đánh giá mức giá thuê này so với các phòng tương đương
   là CAO, HỢP LÝ hay THẤP.
3. Xác định nhóm người thuê phù hợp nhất với mức giá và đặc điểm căn phòng.
4. Đưa ra khuyến nghị thực tế cho người thuê hoặc chủ phòng.

---

ĐỊNH DẠNG TRẢ LỜI
Viết thành 3 đoạn văn ngắn:

Đoạn 1: Phân tích các yếu tố ảnh hưởng đến giá thuê và bối cảnh thị trường.
Đoạn 2: Kết luận mức giá thuê {formatted_price} VNĐ/tháng và đánh giá cao/thấp/hợp lý.
Đoạn 3: Khuyến nghị và tư vấn phù hợp cho người thuê.

"""

        prompt = PromptTemplate.from_template(template)
        return prompt | self.llm | self.output_parser

    # =============================
    # MAIN API
    # =============================
    def explain(self, quan, loai_phong, dien_tich, tien_ich, price):
        try:
            formatted_price = "{:,.0f}".format(float(price))

            if isinstance(tien_ich, list):
                feature_text = ", ".join(map(str, tien_ich))
            elif isinstance(tien_ich, str) and tien_ich.strip():
                feature_text = tien_ich.strip()
            else:
                feature_text = "Basic amenities"

            return self.chain.invoke({
                "quan": str(quan),
                "loai_phong": str(loai_phong),
                "dien_tich": float(dien_tich),
                "feature_text": feature_text,
                "formatted_price": formatted_price
            })

        except Exception as e:
            print(f"❌ ReasoningAgent error: {e}")
            return (
                f"Giá thuê là {formatted_price} VNĐ/tháng. "
                "Hiện hệ thống AI chưa thể phân tích chi tiết."
            )

 
 #chạy chương trình: 1.Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
 #                   2  .\venv\Scripts\activate
 #                   3.uvicorn main:app --reload
