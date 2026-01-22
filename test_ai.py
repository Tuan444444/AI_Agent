# import os
# import google.generativeai as genai
# from dotenv import load_dotenv

# load_dotenv()
# api_key = os.getenv("GOOGLE_API_KEY")

# if not api_key:
#     print("❌ Chưa có Key!")
# else:
#     genai.configure(api_key=api_key)
#     print("📋 Đang tải danh sách model khả dụng cho Key của bạn...")
#     try:
#         count = 0
#         for m in genai.list_models():
#             if 'generateContent' in m.supported_generation_methods:
#                 print(f"   ✅ {m.name}")
#                 count += 1
#         if count == 0:
#             print("❌ Không tìm thấy model nào. Có thể do Key hoặc Mạng.")
#     except Exception as e:
#         print(f"❌ Lỗi: {e}")

from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

try:
    res = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Test quota"
    )
    print("✅ KEY OK – QUOTA HOẠT ĐỘNG")
    print(res.text)
except Exception as e:
    print("❌ KEY CÓ VẤN ĐỀ:")
    print(e)
