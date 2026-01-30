import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

class ReasoningAgent:
    def __init__(self):
        self.llm = None
        if API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-flash-latest", # Dùng bản flash mới cho nhanh
                google_api_key=API_KEY,
                temperature=0.5
            )

    def explain(self, features_dict, price_str):
        """
        features_dict: Dictionary chứa toàn bộ 15 thông số
        price_str: Giá đã format
        """
        if not self.llm: return "Chưa cấu hình API Key."

        # Tạo mô tả từ dict
        desc = ", ".join([f"{k}: {v}" for k, v in features_dict.items()])

        template = f"""
        Bạn là Chuyên gia Môi giới Bất động sản Hà Nội có 10 năm kinh nghiệm (Am hiểu khu vực Cầu Giấy, Đống Đa...).
        
        DỮ LIỆU CĂN PHÒNG:
        {{info_text}}
        
        GIÁ AI DỰ ĐOÁN: {{price_str}}
        
        YÊU CẦU:
        Hãy viết một đoạn nhận xét ngắn (khoảng 3-4 câu) giải thích mức giá trên cho khách thuê.
        
        GỢI Ý LOGIC PHÂN TÍCH:
        1. Nếu có "Thang máy" và "Full đồ Luxury" -> Khen giá hợp lý vì tiện nghi cao.
        2. Nếu "Ngõ xe máy tránh" hoặc "Ngõ sâu" -> Giải thích giá rẻ hơn do vị trí không thuận tiện.
        3. Nếu "Diện tích" nhỏ (<20m2) mà giá cao -> Kiểm tra xem có phải khu trung tâm (Hoàn Kiếm/Ba Đình) không?
        4. "Cho nuôi Pet" là một điểm cộng lớn -> Nhắc khách hàng đây là lợi thế hiếm.
        
        VĂN PHONG:
        Thân thiện, khách quan, dùng từ ngữ chuyên ngành (full option, thoáng, khép kín).
        """
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        try:
            res = chain.invoke({"desc": desc, "price": price_str})
            return res.content
        except:
            return "AI đang bận, chưa thể giải thích chi tiết."