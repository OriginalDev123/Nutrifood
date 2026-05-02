"""
NutriAI - Food Seed Generator v2.1
Logic: Seed dữ liệu cho bảng 'foods' và 'food_servings'
"""

import sys
from pathlib import Path
from decimal import Decimal
from sqlalchemy import or_

# Thiết lập path để import module từ thư mục gốc
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.food import Food, FoodServing

db = SessionLocal()

# ==========================================
# CẤU HÌNH ĐỊNH LƯỢNG (SERVING SIZES)
# ==========================================
S_DEFAULT = [{"description": "100g", "size_g": 100, "is_default": True}]
S_BOWL    = [{"description": "1 bát (200g)", "size_g": 200, "is_default": True}]
S_PLATE   = [{"description": "1 đĩa (150g)", "size_g": 150, "is_default": True}]

# ==========================================
# HÀM HỖ TRỢ (HELPER)
# ==========================================
def F(vi, en, cat, cal, p, c, f, 
      desc=None, cuisine="global", fiber=0, sugar=0, sodium=0, 
      barcode=None, image=None, servings=None):
    """
    Đóng gói dữ liệu thực phẩm theo chuẩn cấu trúc bảng foods.
    Thứ tự tham số tối ưu: Tên -> Category -> Macro cơ bản -> Thông tin bổ sung.
    """
    return {
        "name_vi": vi, 
        "name_en": en, 
        "category": cat, 
        "description": desc or f"Dữ liệu dinh dưỡng cho {vi}",
        "cuisine_type": cuisine,
        "calories_per_100g": cal, 
        "protein_per_100g": p, 
        "carbs_per_100g": c, 
        "fat_per_100g": f,
        "fiber_per_100g": fiber, 
        "sugar_per_100g": sugar, 
        "sodium_per_100g": sodium,
        "barcode": barcode,
        "image_url": image,
        "servings": servings or S_DEFAULT
    }

# ==========================================
# DANH SÁCH DỮ LIỆU THỰC PHẨM
# ==========================================
FOODS_DATA = [
    
    # ===== Proteins - Meat =====
    
    # Thịt bò (Generic Beef for common searches)
    F("Thịt bò", "Beef", "protein", 250, 26.0, 0, 15.0, desc="Thịt bò tổng quát, giá trị trung bình cho tra cứu nhanh."),
    # Thịt bò - Specific cuts
    F("Thăn nội", "Beef Tenderloin", "protein", 255, 26.0, 0, 15.0, desc="Phần thịt mềm nhất của con bò, nằm ở phía trong xương sống."),
    F("Thăn ngoại", "Beef Sirloin", "protein", 244, 27.0, 0, 14.0, desc="Thịt thăn phía ngoài, có kết cấu chắc và thơm nhờ lớp mỡ mỏng."),
    F("Thăn lưng", "Beef Ribeye", "protein", 291, 24.0, 0, 22.0, desc="Phần thịt giữa xương sườn, có nhiều vân mỡ xen kẽ giúp thịt rất mềm."),
    F("Bắp bò", "Beef Shank", "protein", 201, 34.0, 0, 6.0, desc="Thịt cơ bắp ở chân, chứa nhiều collagen, phù hợp hầm hoặc ngâm mắm."),
    F("Nạm bò", "Beef Flank", "protein", 192, 28.0, 0, 8.0, desc="Phần thịt bụng, có thớ rõ rệt, thường dùng làm phở hoặc bò kho."),
    F("Gầu bò", "Beef Brisket", "protein", 248, 21.0, 0, 18.0, desc="Phần thịt gần ức, mỡ trắng, ăn giòn và rất thơm khi nấu chín."),
    F("Dẻ sườn", "Beef Rib Fingers", "protein", 310, 20.0, 0, 25.0, desc="Phần thịt nằm giữa các xương sườn, lý tưởng cho món nướng."),
    F("Lưỡi bò", "Beef Tongue", "protein", 224, 15.0, 0, 16.0, desc="Phần nội tạng sạch, giòn và béo, chứa nhiều vitamin B12."),
    F("Ba chỉ bò", "Beef Short Plate", "protein", 330, 14.0, 0, 30.0, desc="Phần bụng dưới, các dải thịt và mỡ xen kẽ nhau."),
    F("Đuôi bò", "Beef Tail", "protein", 262, 19.0, 0, 20.0, desc="Gồm xương và lớp thịt bao quanh, dùng để nấu các món súp bổ dưỡng."),

    # Thịt heo (Generic Pork for common searches)
    F("Thịt heo", "Pork", "protein", 242, 17.0, 0, 19.0, desc="Thịt heo tổng quát, giá trị trung bình cho tra cứu nhanh."),
    # Thịt heo - Specific cuts
    F("Thăn nội heo", "Pork Tenderloin", "protein", 143, 26.0, 0, 3.5, desc="Phần thịt nạc nhất của con heo, ít mỡ, mềm, phù hợp cho chế độ ăn kiêng."),
    F("Thăn ngoại heo", "Pork Loin", "protein", 190, 24.0, 0, 10.0, desc="Phần thịt lưng, thớ thịt dày, thường có một lớp mỡ mỏng bao quanh."),
    F("Thịt ba chỉ", "Pork Belly", "protein", 518, 9.0, 0, 53.0, desc="Phần thịt ở bụng heo với các lớp nạc và mỡ xen kẽ, rất béo và thơm."),
    F("Thịt vai heo", "Pork Shoulder", "protein", 232, 18.0, 0, 18.0, desc="Thịt có tỉ lệ nạc mỡ cân bằng, dai giòn, phù hợp làm món kho hoặc xay."),
    F("Chân giò heo", "Pork Knuckle", "protein", 220, 19.0, 0, 16.0, desc="Phần thịt ở cổ chân heo, chứa nhiều da và gân, thường dùng hầm canh."),
    F("Sườn non heo", "Pork Spare Ribs", "protein", 277, 17.0, 0, 23.0, desc="Phần xương sườn có nhiều thịt và mỡ, rất được ưa chuộng cho món nướng."),
    F("Thịt nạc dăm", "Pork Collar", "protein", 170, 19.0, 0, 10.0, desc="Thịt có các lớp mỡ mỏng xen kẽ bên trong, giúp thịt khi nấu không bị khô."),
    F("Móng giò", "Pork Trotter", "protein", 212, 19.0, 0, 15.0, desc="Phần bàn chân heo, giàu gelatin và collagen, tốt cho khớp."),
    F("Má heo", "Pork Jowl", "protein", 590, 7.0, 0, 63.0, desc="Phần thịt ở má, tỉ lệ mỡ rất cao nhưng kết cấu giòn, thường dùng làm giò thủ."),
    F("Thịt mông heo", "Pork Leg", "protein", 160, 21.0, 0, 8.0, desc="Phần thịt ở đùi sau, nạc dày, ít mỡ, thường dùng làm ruốc (chà bông) hoặc giò."),
    
    # Thịt trâu
    F("Thăn nội trâu", "Buffalo Tenderloin", "protein", 130, 26.8, 0, 1.8, desc="Phần thịt mềm nhất, gần như không có mỡ, màu đỏ sẫm đặc trưng."),
    F("Thăn ngoại trâu", "Buffalo Striploin", "protein", 155, 25.0, 0, 5.5, desc="Phần thịt nằm ở lưng, thớ thịt to, chắc và ít mỡ hơn so với thăn ngoại bò."),
    F("Bắp hoa trâu", "Buffalo Shin", "protein", 145, 27.5, 0, 3.2, desc="Phần bắp có nhiều gân xen kẽ, ăn giòn, ngọt thịt, rất giàu sắt."),
    F("Nạm trâu", "Buffalo Flank", "protein", 180, 24.0, 0, 8.5, desc="Phần thịt bụng có thớ dài, dai hơn nạc thăn, phù hợp làm món hầm hoặc thái mỏng nhúng giấm."),
    F("Thịt mông trâu", "Buffalo Topside", "protein", 140, 27.0, 0, 2.5, desc="Phần nạc mông dày, không mỡ, thường được dùng để làm thịt trâu gác bếp."),
    F("Thịt vai trâu", "Buffalo Blade", "protein", 165, 24.0, 0, 7.0, desc="Phần thịt từ bả vai, có tỷ lệ nạc mỡ vừa phải, thớ thịt dày."),
    F("Thịt cổ trâu", "Buffalo Chuck", "protein", 175, 23.0, 0, 8.5, desc="Thịt vùng cổ, có các mô liên kết xen kẽ, thường dùng cho các món hầm hoặc xay."),
    F("Đuôi trâu", "Buffalo Tail", "protein", 250, 18.0, 0, 19.0, desc="Gồm xương xương và thịt bao quanh, chứa nhiều collagen, rất bổ dưỡng khi hầm."),
    F("Gầu trâu", "Buffalo Brisket", "protein", 210, 21.0, 0, 13.5, desc="Phần thịt gần ức, mỡ trâu thường trắng và cứng hơn mỡ bò, ăn khá giòn."),
    F("Lưỡi trâu", "Buffalo Tongue", "protein", 215, 14.5, 0, 16.5, desc="Bộ phận giàu dinh dưỡng, kết cấu giòn mềm đặc biệt sau khi làm sạch và chế biến."),
    
    # Thịt cừu
    F("Sườn cừu", "Lamb Rack", "protein", 282, 17.0, 0, 23.0, desc="Phần sườn có xương, thịt cực kỳ mềm và thơm, thường dùng để nướng nguyên tảng."),
    F("Đùi cừu", "Lamb Leg", "protein", 234, 18.0, 0, 17.0, desc="Phần thịt đùi sau, ít mỡ hơn sườn, thường dùng làm món nướng đút lò (Roast)."),
    F("Thăn nội cừu", "Lamb Tenderloin", "protein", 120, 22.0, 0, 3.5, desc="Dải thịt nhỏ nằm dọc xương sống, cực kỳ ít mỡ và là phần mềm nhất của con cừu."),
    F("Thăn ngoại cừu", "Lamb Loin", "protein", 216, 20.0, 0, 14.5, desc="Phần thịt từ thắt lưng, nạc nhiều, thường được cắt thành các miếng bít tết nhỏ."),
    F("Thịt vai cừu", "Lamb Shoulder", "protein", 280, 16.5, 0, 23.5, desc="Có nhiều mỡ và cơ hơn đùi, rất ngọt thịt, phù hợp cho các món hầm hoặc nướng chậm."),
    F("Bắp cừu", "Lamb Shank", "protein", 186, 20.0, 0, 11.5, desc="Phần thịt dưới đùi, nhiều gân và cơ, khi hầm lâu thịt sẽ mềm tan và rất thơm."),
    F("Nạm cừu", "Lamb Breast", "protein", 360, 13.0, 0, 34.0, desc="Phần bụng cừu, chứa nhiều mỡ và sụn, thường được dùng để cuộn nướng hoặc nấu ragu."),
    F("Thịt cổ cừu", "Lamb Neck", "protein", 210, 18.5, 0, 15.0, desc="Phần thịt xương xen kẽ, rất ngọt, thường được thái khoanh để nấu súp hoặc hầm."),
    F("Thịt hông cừu", "Lamb Flank", "protein", 195, 21.0, 0, 12.0, desc="Dải thịt nạc ở vùng bụng dưới, thớ thịt rõ rệt, thường dùng để băm nhỏ hoặc làm xúc xích."),
    F("Thịt mông cừu", "Lamb Chump", "protein", 225, 19.5, 0, 16.0, desc="Phần giao giữa lưng và đùi sau, thịt nạc chắc, có lớp mỡ bao quanh rất thơm."),
    
    # Thịt dê
    F("Đùi dê", "Goat Leg", "protein", 143, 27.0, 0, 3.0, desc="Phần nạc dày nhất, ít mỡ, thớ thịt săn chắc, thường dùng làm món nướng hoặc hấp."),
    F("Sườn dê", "Goat Ribs", "protein", 220, 19.0, 0, 15.0, desc="Phần sườn có cả xương và thịt mỡ xen kẽ, lý tưởng cho món sườn dê nướng muối ớt."),
    F("Thăn dê", "Goat Loin", "protein", 125, 25.0, 0, 2.1, desc="Dải thịt nạc dọc xương sống, rất mềm và ít mùi nồng nhất trong các bộ phận."),
    F("Thịt vai dê", "Goat Shoulder", "protein", 160, 23.0, 0, 7.0, desc="Thịt có tỷ lệ mỡ nạc vừa phải, thớ thịt nhỏ hơn đùi, phù hợp làm món xào hoặc cà ri."),
    F("Chân giò dê", "Goat Shank", "protein", 155, 24.0, 0, 6.0, desc="Phần từ khớp gối trở xuống, nhiều mô liên kết, rất tốt khi hầm thuốc bắc hoặc nấu lẩu."),
    F("Cổ dê", "Goat Neck", "protein", 170, 21.0, 0, 9.0, desc="Có sự kết hợp giữa xương sụn và thịt, giúp nước dùng rất ngọt, thường dùng nấu lẩu."),
    F("Ba rọi dê", "Goat Belly", "protein", 285, 16.0, 0, 24.0, desc="Phần bụng có các lớp mỡ và nạc, thường dùng để nướng hoặc làm món giả cầy."),
    F("Vú dê", "Goat Udder", "protein", 250, 14.0, 0, 21.0, desc="Kết cấu giòn, béo đặc trưng, là món nướng khoái khẩu tại Việt Nam (thường được thay bằng nầm heo)."),
    F("Đuôi dê", "Goat Tail", "protein", 210, 17.0, 0, 15.0, desc="Chứa nhiều tủy và collagen, thường được hầm để bồi bổ sức khỏe."),
    F("Tai dê", "Goat Ears", "protein", 120, 20.0, 0, 4.0, desc="Chủ yếu là sụn và da, thường dùng làm các món nộm, gỏi hoặc nướng giòn."),
    
    # Thịt gà
    F("Ức gà (có da)", "Chicken Breast with skin", "protein", 172, 21.0, 0, 9.0, desc="Phần thịt trắng ở vùng bụng/ngực, giàu đạm nhất, phù hợp cho người tập gym."),
    F("Phi lê ức gà", "Chicken Breast Boneless Skinless", "protein", 120, 23.0, 0, 2.5, desc="Ức gà đã lọc bỏ da và xương, lượng chất béo cực thấp."),
    F("Đùi tỏi gà", "Chicken Drumstick", "protein", 161, 18.0, 0, 9.0, desc="Phần dưới của chân gà, thịt nâu, cử động nhiều nên thớ thịt chắc và ngọt."),
    F("Má đùi gà", "Chicken Thigh", "protein", 209, 17.0, 0, 15.0, desc="Phần thịt nằm trên đùi tỏi, có nhiều vân mỡ nên thịt rất mềm và không bị khô."),
    F("Cánh gà", "Chicken Wings", "protein", 203, 18.0, 0, 14.0, desc="Gồm ba phần: âu cánh, cánh giữa và đầu cánh; chứa nhiều collagen từ da."),
    F("Chân gà", "Chicken Feet", "protein", 215, 19.0, 0, 15.0, desc="Không có thịt, chủ yếu là da, gân và sụn; thường dùng làm món nhậu hoặc hầm lấy nước dùng."),
    F("Mề gà", "Chicken Gizzard", "protein", 94, 18.0, 0, 2.0, desc="Phần dạ dày cơ của gà, kết cấu giòn sần sật, rất ít béo nhưng giàu sắt."),
    F("Gan gà", "Chicken Liver", "protein", 116, 17.0, 0, 5.0, desc="Nội tạng giàu dinh dưỡng, mềm, béo, chứa lượng Vitamin B12 và folate rất cao."),
    F("Tim gà", "Chicken Heart", "protein", 153, 16.0, 0, 9.0, desc="Phần cơ tim, ăn dai giòn, giàu kẽm và các vitamin nhóm B."),
    F("Phao câu gà", "Chicken Tail", "protein", 380, 10.0, 0, 38.0, desc="Phần cuối cùng của thân gà, chứa tuyến nhờn, cực kỳ béo."),
    
    # Thịt vịt
    F("Ức vịt (có da)", "Duck Breast with skin", "protein", 337, 19.0, 0, 28.0, desc="Phần thịt nạc dày ở ngực, có lớp mỡ dưới da rất đặc trưng, thường dùng làm bít tết vịt."),
    F("Phi lê ức vịt", "Duck Breast Skinless", "protein", 140, 23.5, 0, 5.0, desc="Phần nạc ức đã lọc bỏ hoàn toàn da và mỡ, lượng protein rất cao và ít calo."),
    F("Đùi vịt (có da)", "Duck Leg with skin", "protein", 217, 17.0, 0, 15.0, desc="Thịt đùi vịt dai hơn gà, vị đậm, rất hợp với các món hầm hoặc nướng chậm (Confit)."),
    F("Cánh vịt", "Duck Wings", "protein", 220, 16.0, 0, 17.0, desc="Ít thịt, chủ yếu là da và gân, thường dùng để nấu cháo hoặc làm món nhắm."),
    F("Đùi tỏi vịt", "Duck Drumstick", "protein", 180, 18.5, 0, 11.0, desc="Phần dưới của chân vịt, thớ thịt đỏ sẫm, ngọt và chắc."),
    F("Lòng vịt", "Duck Giblets", "protein", 124, 17.5, 0, 5.5, desc="Hỗn hợp nội tạng sạch của vịt, thường dùng xào dứa hoặc nấu miến."),
    F("Gan vịt (thường)", "Duck Liver", "protein", 136, 18.0, 0, 4.5, desc="Giàu sắt và Vitamin A. Lưu ý: Gan béo (Foie Gras) sẽ có lượng béo lên tới 40-50g."),
    F("Chân vịt", "Duck Feet", "protein", 160, 19.0, 0, 9.0, desc="Cấu tạo chủ yếu là da và các khớp sụn, thường dùng làm món chân vịt rút xương."),
    F("Lưỡi vịt", "Duck Tongue", "protein", 270, 12.0, 0, 24.0, desc="Phần thịt rất nhỏ nhưng cực kỳ béo và giòn sụn ở giữa, món ăn khoái khẩu trong các bữa tiệc."),
    F("Cổ vịt", "Duck Neck", "protein", 250, 14.0, 0, 21.0, desc="Chứa nhiều xương sống và lớp da bọc ngoài dày mỡ, thường dùng nấu nước dùng hoặc làm cổ vịt cay."),
    
    # Thịt ngan
    F("Ức ngan (có da)", "Muscovy Duck Breast with skin", "protein", 220, 19.5, 0, 15.5, desc="Phần nạc ức rất dày, chắc thịt, lớp mỡ mỏng hơn so với vịt cỏ hay vịt bầu."),
    F("Phi lê ức ngan", "Muscovy Duck Breast Skinless", "protein", 135, 22.0, 0, 4.5, desc="Thịt nạc đỏ, giàu sắt, kết cấu gần giống với thịt thăn bò nếu chế biến đúng cách."),
    F("Đùi ngan", "Muscovy Duck Leg", "protein", 190, 18.0, 0, 12.5, desc="Do ngan di chuyển và vận động nhiều, phần đùi rất chắc, ngọt, phù hợp làm món giả cầy."),
    F("Cánh ngan", "Muscovy Duck Wings", "protein", 210, 17.5, 0, 15.0, desc="Cánh ngan khá lớn, có nhiều thịt ở phần âu cánh, thường dùng nấu măng."),
    F("Đầu cổ ngan", "Muscovy Duck Head & Neck", "protein", 185, 15.0, 0, 13.5, desc="Thường dùng để ninh lấy nước dùng nhờ vị ngọt thanh từ xương ngan."),
    F("Lòng ngan", "Muscovy Duck Giblets", "protein", 130, 18.0, 0, 6.0, desc="Bao gồm tim, gan, mề sạch; mề ngan thường rất to và giòn."),
    F("Chân ngan", "Muscovy Duck Feet", "protein", 155, 19.5, 0, 8.0, desc="Chứa nhiều collagen, da dày, thường dùng cho các món canh măng hoặc ngâm sả tắc."),
    F("Tiết ngan", "Muscovy Duck Blood", "protein", 75, 12.0, 0.5, 0.2, desc="Giàu sắt và protein, thường dùng để đánh tiết canh hoặc luộc chín ăn kèm bún."),
    F("Phao câu ngan", "Muscovy Duck Tail", "protein", 395, 9.0, 0, 40.0, desc="Cực kỳ béo, chứa tuyến nhờn lớn, calo rất cao."),
    F("Xương khung ngan", "Muscovy Duck Carcass", "protein", 140, 16.0, 0, 8.0, desc="Phần khung xương sau khi đã lọc thịt, dùng để hầm nước dùng rất ngọt."),
    
    # Thịt ngỗng
    F("Ức ngỗng (có da)", "Goat Breast with skin", "protein", 371, 16.0, 0, 33.0, desc="Phần thịt đỏ đậm, rất thơm, lớp mỡ dưới da dày giúp thịt không bị khô khi áp chảo."),
    F("Phi lê ức ngỗng", "Goose Breast Skinless", "protein", 161, 22.8, 0, 7.1, desc="Phần nạc ức đỏ sẫm như bít tết bò, giàu sắt và protein chất lượng cao."),
    F("Đùi ngỗng", "Goose Leg", "protein", 230, 18.5, 0, 17.5, desc="Thịt đùi dai chắc, đậm vị, thường được dùng để nướng hoặc làm món ngỗng hầm rượu vang."),
    F("Cánh ngỗng", "Goose Wings", "protein", 250, 17.0, 0, 20.0, desc="Cánh ngỗng rất lớn, chứa nhiều collagen, phù hợp cho các món canh hoặc nướng muối ớt."),
    F("Gan ngỗng béo", "Foie Gras", "protein", 462, 11.4, 0, 44.0, desc="Loại gan đặc biệt từ ngỗng được vỗ béo, cực kỳ ngậy, tan trong miệng như bơ."),
    F("Mỡ ngỗng", "Goose Fat", "protein", 900, 0, 0, 99.8, desc="Được dùng như dầu ăn cao cấp, chứa nhiều chất béo không bão hòa đơn có lợi cho tim mạch."),
    F("Gan ngỗng (thường)", "Goose Liver", "protein", 133, 16.5, 0, 4.3, desc="Gan từ ngỗng nuôi tự nhiên, giàu Vitamin A, sắt và hậu vị đắng nhẹ, béo."),
    F("Mề ngỗng", "Goose Gizzard", "protein", 110, 20.0, 0, 3.5, desc="Dày và giòn hơn mề vịt, rất ít béo, thường được thái mỏng xào lăn."),
    F("Chân ngỗng", "Goose Feet", "protein", 170, 21.0, 0, 9.5, desc="Kích thước lớn, nhiều da sụn, thường dùng làm các món hầm bồi bổ sức khỏe."),
    F("Cổ ngỗng", "Goose Neck", "protein", 240, 15.0, 0, 20.0, desc="Lớp da cổ rất rộng và dai, thường được người Việt dùng để nhồi tiết, đậu xanh và thịt heo."),
    
    # Thịt gà tây
    F("Ức gà tây (có da)", "Turkey Breast with skin", "protein", 157, 22.0, 0, 7.0, desc="Phần nạc lớn nhất, rất ít béo. Là nguồn protein tinh khiết cho người xây dựng cơ bắp."),
    F("Phi lê ức gà tây", "Turkey Breast Skinless", "protein", 104, 24.0, 0, 1.5, desc="Cực kỳ ít calo, gần như không có chất béo, vị thanh nhẹ."),
    F("Đùi tỏi gà tây", "Turkey Drumstick", "protein", 143, 20.0, 0, 6.5, desc="Phần thịt sẫm màu, chứa nhiều cơ và gân, vị đậm đà hơn phần ức."),
    F("Má đùi gà tây", "Turkey Thigh", "protein", 159, 18.5, 0, 9.0, desc="Phần thịt đỏ của gà tây, chứa nhiều sắt và kẽm hơn phần thịt trắng."),
    F("Cánh gà tây", "Turkey Wings", "protein", 192, 18.0, 0, 13.0, desc="Chứa nhiều da và sụn, khi nướng lớp da sẽ rất giòn và thơm."),
    F("Thăn gà tây", "Turkey Tenderloin", "protein", 115, 24.5, 0, 1.2, desc="Dải nạc nhỏ nằm phía sau ức, là phần mềm nhất của con gà tây."),
    F("Cổ gà tây", "Turkey Neck", "protein", 160, 17.0, 0, 10.0, desc="Chứa nhiều thịt vụn bám quanh xương, tạo vị ngọt sâu cho các món súp."),
    F("Gan gà tây", "Turkey Liver", "protein", 128, 17.5, 0, 4.8, desc="Kích thước lớn, rất giàu folate và vitamin B12."),
    F("Tim gà tây", "Turkey Heart", "protein", 140, 16.5, 0, 7.5, desc="Thớ thịt cơ chắc chắn, dai giòn, giàu khoáng chất."),
    F("Mề gà tây", "Turkey Gizzard", "protein", 115, 19.0, 0, 3.5, desc="Rất to và dày, sau khi hầm lâu sẽ có độ giòn sần sật đặc trưng."),
    
    # Thịt bồ câu
    F("Ức bồ câu", "Pigeon Breast", "protein", 142, 23.0, 0, 4.5, desc="Phần thịt dày, đỏ sẫm như thịt bò, cực kỳ nạc và giàu sắt, thường được áp chảo tái vừa."),
    F("Đùi bồ câu", "Pigeon Leg", "protein", 158, 20.5, 0, 7.5, desc="Thịt đùi chắc, thơm, chứa nhiều mô liên kết, rất tốt khi hầm hoặc quay."),
    F("Thân chim bồ câu (nguyên con)", "Whole Pigeon Body", "protein", 213, 18.5, 0, 14.5, desc="Dữ liệu tính cả da cho chim nguyên con, thường dùng để hầm thuốc bắc hoặc nấu cháo."),
    F("Gan bồ câu", "Pigeon Liver", "protein", 130, 17.0, 0, 5.0, desc="Kích thước nhỏ nhưng cực kỳ giàu vitamin A và các khoáng chất bồi bổ máu."),
    F("Tim bồ câu", "Pigeon Heart", "protein", 145, 16.0, 0, 8.5, desc="Phần cơ nhỏ, dai giòn, thường được giữ lại khi hầm nguyên con để giữ chất."),
    F("Mề bồ câu", "Pigeon Gizzard", "protein", 105, 19.0, 0, 2.5, desc="Rất nhỏ, giòn sần sật, ít béo, thường dùng xào cùng lòng mề."),
    F("Đầu bồ câu", "Pigeon Head", "protein", 110, 14.0, 0, 5.5, desc="Thường được ninh cùng cháo cho trẻ nhỏ hoặc người già để bổ sung trí não."),
    F("Xương bồ câu", "Pigeon Bones", "protein", 95, 12.0, 0, 4.0, desc="Xương bồ câu khá mềm, khi hầm lâu chất ngọt tiết ra rất thanh, dùng làm nước cốt súp."),
    F("Tiết bồ câu", "Pigeon Blood", "protein", 70, 13.0, 0.4, 0.1, desc="Giàu sắt, thường được cho trực tiếp vào cháo để tăng độ bổ dưỡng."),
    F("Trứng chim bồ câu", "Pigeon Egg", "protein", 160, 14.0, 1.5, 11.0, desc="Nhỏ, lòng trắng trong suốt khi luộc, chứa hàm lượng dinh dưỡng cao hơn trứng gà."),
    
    # Thịt chim cút
    F("Chim cút nguyên con", "Whole Quail", "protein", 192, 20.0, 0, 12.0, desc="Dữ liệu tính cả da và xương, thường dùng để chiên bơ hoặc nướng."),
    F("Ức chim cút", "Quail Breast", "protein", 119, 22.5, 0, 2.3, desc="Phần thịt nạc trắng, cực kỳ ít béo, thớ thịt mịn và nhanh chín."),
    F("Đùi chim cút", "Quail Leg", "protein", 145, 19.5, 0, 6.8, desc="Nhỏ nhưng chắc thịt, vị đậm đà hơn phần ức."),
    F("Trứng chim cút", "Quail Egg", "protein", 158, 13.0, 0.4, 11.0, desc="Chứa nhiều choline và lecithin, tốt cho sự phát triển trí não."),
    F("Gan chim cút", "Quail Liver", "protein", 125, 17.0, 0, 4.2, desc="Nhỏ và mềm, rất giàu vitamin nhóm B và sắt."),
    F("Mề chim cút", "Quail Gizzard", "protein", 98, 18.5, 0, 1.8, desc="Rất nhỏ, giòn, thường được giữ lại khi chế biến chim nguyên con."),
    F("Xương chim cút", "Quail Bones", "protein", 85, 10.0, 0, 3.5, desc="Xương chim cút rất nhỏ và giòn, khi chiên kỹ có thể ăn được cả xương để bổ sung canxi."),
    F("Đầu chim cút", "Quail Head", "protein", 105, 13.0, 0, 4.5, desc="Thường dùng trong các món hầm hoặc nướng giòn."),
    F("Tiết chim cút", "Quail Blood", "protein", 68, 12.5, 0.3, 0.1, desc="Hàm lượng sắt cao, thường dùng trong y học cổ truyền để bồi bổ."),
    F("Chim cút làm sạch", "Dressed Quail", "protein", 134, 21.8, 0, 4.5, desc="Chim đã bỏ đầu, chân và nội tạng, chỉ còn phần thân thịt."),
    
    # Thịt thỏ
    F("Thăn thỏ", "Rabbit Loin", "protein", 135, 24.5, 0, 3.5, desc="Dải thịt dọc xương sống, cực kỳ nạc và mềm, không có mỡ."),
    F("Đùi sau thỏ", "Rabbit Hind Legs", "protein", 150, 23.0, 0, 6.0, desc="Phần tập trung nhiều thịt nhất của con thỏ, chắc thịt, thường dùng làm món nướng hoặc roti."),
    F("Đùi trước thỏ", "Rabbit Forelegs", "protein", 140, 22.0, 0, 5.5, desc="Nhỏ hơn đùi sau, thớ thịt ngắn, phù hợp cho các món hầm hoặc xào."),
    F("Thịt vai thỏ", "Rabbit Shoulder", "protein", 145, 21.5, 0, 6.5, desc="Thịt vùng vai có độ dai vừa phải, vị ngọt đậm đà."),
    F("Sườn thỏ", "Rabbit Ribs", "protein", 160, 20.0, 0, 8.5, desc="Phần xương sườn mỏng, thịt xen kẽ xương, thường dùng để nấu các món canh."),
    F("Gan thỏ", "Rabbit Liver", "protein", 125, 18.0, 0, 4.5, desc="Giàu sắt và Vitamin A, kết cấu mịn màng, là nguyên liệu tuyệt vời làm pate."),
    F("Tim thỏ", "Rabbit Heart", "protein", 130, 16.5, 0, 6.5, desc="Phần cơ nhỏ, chắc, giàu khoáng chất."),
    F("Cật thỏ", "Rabbit Kidneys", "protein", 100, 16.0, 0, 3.0, desc="Nhỏ và sạch, thường được chế biến cùng lòng mề thỏ."),
    F("Thịt bụng thỏ", "Rabbit Belly", "protein", 180, 19.0, 0, 11.0, desc="Phần thịt mỏng ở bụng, có chứa một chút mỡ (loại mỡ này rất lành tính)."),
    F("Đầu thỏ", "Rabbit Head", "protein", 120, 15.0, 0, 6.0, desc="Chủ yếu dùng trong các món hầm hoặc món cay đặc sản (phổ biến trong ẩm thực Tứ Xuyên)."),
    
    # Thịt ngựa
    F("Thăn nội ngựa", "Horse Tenderloin", "protein", 121, 22.5, 0, 3.0, desc="Phần thịt mềm nhất của ngựa, hầu như không có mỡ, vị ngọt thanh đặc trưng."),
    F("Thăn ngoại ngựa", "Horse Sirloin", "protein", 155, 21.0, 0, 7.5, desc="Phần thịt lưng chắc, thớ thịt rõ rệt, thường dùng cho món bít tết hoặc xào."),
    F("Bắp ngựa", "Horse Shank", "protein", 145, 24.0, 0, 5.0, desc="Chứa nhiều gân xen kẽ, ăn rất giòn và ngọt, là phần thịt có hàm lượng sắt cao nhất."),
    F("Thịt vai ngựa", "Horse Shoulder", "protein", 160, 20.0, 0, 8.5, desc="Thớ thịt to, chắc, phù hợp cho các món hầm hoặc nấu thắng cố."),
    F("Thịt mông ngựa", "Horse Rump", "protein", 130, 23.0, 0, 3.5, desc="Phần nạc dày, ít mỡ, thường được dùng để sấy khô (thịt ngựa gác bếp)."),
    F("Nạm ngựa", "Horse Flank", "protein", 185, 19.0, 0, 11.5, desc="Phần thịt bụng, có tỷ lệ mỡ nạc đan xen, thớ thịt dài."),
    F("Sườn ngựa", "Horse Ribs", "protein", 210, 18.0, 0, 15.0, desc="Xương sườn ngựa rất lớn, thịt bám xương ngọt, thường dùng để ninh nước dùng."),
    F("Tim ngựa", "Horse Heart", "protein", 140, 17.5, 0, 7.0, desc="Kích thước tim lớn, rất giàu phospho và vitamin nhóm B."),
    F("Gan ngựa", "Horse Liver", "protein", 135, 19.0, 0, 4.0, desc="Chứa lượng Vitamin A và sắt cực lớn, vị hơi đắng nhưng béo."),
    F("Đuôi ngựa", "Horse Tail", "protein", 240, 16.0, 0, 19.0, desc="Phần xương đuôi giàu collagen, dùng để hầm thuốc bắc hoặc nấu lẩu."),
    
    # Thịt lạc đà
    F("Bướu lạc đà", "Camel Hump", "protein", 630, 1.2, 0, 70.0, desc="Cấu tạo chủ yếu là mô mỡ dự trữ, có kết cấu mịn, thường dùng để thắng mỡ hoặc nướng."),
    F("Thăn nội lạc đà", "Camel Tenderloin", "protein", 110, 23.5, 0, 1.8, desc="Phần nạc mềm nhất, nằm sâu trong khoang bụng, cực kỳ ít béo và giàu protein."),
    F("Thăn ngoại lạc đà", "Camel Striploin", "protein", 125, 22.0, 0, 4.0, desc="Thớ thịt to, chắc, thường được thái mỏng để làm món bít tết hoặc xào nhanh."),
    F("Đùi lạc đà", "Camel Leg", "protein", 115, 23.0, 0, 2.5, desc="Thịt đùi rất nạc, chắc, thớ thịt hơi thô, thường được hầm lâu để làm mềm."),
    F("Vai lạc đà", "Camel Shoulder", "protein", 130, 21.5, 0, 4.8, desc="Phần thịt từ bả vai, có hương vị đậm đà, phù hợp cho các món cà ri hoặc hầm."),
    F("Sườn lạc đà", "Camel Ribs", "protein", 160, 19.5, 0, 9.0, desc="Thịt bám xương sườn, có độ ngọt cao, thường được nướng nguyên tảng trong các lễ hội."),
    F("Bắp lạc đà", "Camel Shank", "protein", 120, 24.5, 0, 2.2, desc="Phần cơ chân, nhiều mô liên kết, sau khi hầm sẽ rất ngọt và có độ giòn của gân."),
    F("Gan lạc đà", "Camel Liver", "protein", 138, 19.0, 0, 4.5, desc="Nguồn cung cấp sắt và Vitamin A dồi dào, vị đậm đà đặc trưng."),
    F("Lưỡi lạc đà", "Camel Tongue", "protein", 195, 14.5, 0, 15.0, desc="Phần thịt cơ dày, giòn và béo hơn các phần thịt khác, thường được luộc hoặc nướng."),
    F("Cổ lạc đà", "Camel Neck", "protein", 150, 20.0, 0, 7.5, desc="Phần xương cổ dài, thịt ngọt, chuyên dùng để ninh lấy nước cốt súp."),
    
    # Thịt đà điểu
    F("Phi lê đà điểu", "Ostrich Fillet", "protein", 115, 25.5, 0, 1.4, desc="Phần thịt mềm nhất, nằm sâu bên trong, hầu như không có mỡ và gân."),
    F("Thăn đà điểu", "Ostrich Steak", "protein", 123, 24.0, 0, 2.9, desc="Phần nạc đùi dày, thớ thịt mịn, rất phù hợp cho món bít tết hoặc nướng."),
    F("Thịt đùi đà điểu", "Ostrich Fan", "protein", 118, 23.5, 0, 2.1, desc="Phần thịt có thớ lớn nhất, màu đỏ sẫm, rất giàu sắt và kẽm."),
    F("Bắp đà điểu", "Ostrich Drum", "protein", 130, 26.0, 0, 3.0, desc="Phần cơ chân hoạt động nhiều, có nhiều gân xen kẽ, ăn giòn và ngọt thịt."),
    F("Cổ đà điểu", "Ostrich Neck", "protein", 155, 18.0, 0, 9.2, desc="Xương cổ lớn, thịt bám quanh rất ngọt, thường dùng nấu lẩu hoặc hầm thuốc bắc."),
    F("Cánh đà điểu", "Ostrich Wings", "protein", 180, 17.5, 0, 12.0, desc="Rất ít thịt, chủ yếu là da dày và xương sụn, giàu collagen."),
    F("Gan đà điểu", "Ostrich Liver", "protein", 140, 19.5, 0, 5.5, desc="Kích thước lớn, chứa hàm lượng Vitamin A và Folate cực cao."),
    F("Tim đà điểu", "Ostrich Heart", "protein", 145, 17.0, 0, 8.5, desc="Phần cơ rất chắc, dai giòn, giàu khoáng chất bồi bổ cơ thể."),
    F("Gân đà điểu", "Ostrich Tendon", "protein", 150, 35.0, 0, 0.5, desc="Chứa hàm lượng protein tinh khiết và collagen cao, không béo, ăn giòn sần sật."),
    F("Mỡ đà điểu", "Ostrich Fat", "protein", 880, 0, 0, 98.0, desc="Chứa nhiều axit béo Omega-3, 6, 9, thường được thắng lấy tinh dầu dưỡng da."),
    
    # Thịt chuột đồng
    F("Thịt chuột đồng (nguyên con làm sạch)", "Whole Field Mouse Meat", "protein", 105, 23.0, 0, 1.5, desc="Phần nạc thân sau khi bỏ đầu, đuôi và nội tạng. Cực kỳ nạc và giàu đạm."),
    F("Đùi chuột đồng", "Field Mouse Legs", "protein", 110, 22.0, 0, 2.5, desc="Phần tập trung nhiều cơ nhất, thịt chắc, dai và ngọt nhất trên con chuột."),
    F("Gan chuột", "Field Mouse Liver", "protein", 120, 18.0, 0, 4.0, desc="Nhỏ nhưng béo, chứa nhiều vitamin A và sắt, thường được giữ lại khi chế biến."),
    F("Mỡ chuột", "Field Mouse Fat", "protein", 750, 2.0, 0, 80.0, desc="Dải mỡ nhỏ thường nằm ở vùng bụng hoặc bẹn, mỡ chuột đồng thơm, không bị hôi."),
    F("Tim chuột", "Field Mouse Heart", "protein", 130, 16.0, 0, 7.0, desc="Kích thước rất nhỏ, giàu khoáng chất, thường được nấu cùng thân chim."),
    F("Da chuột", "Field Mouse Skin", "protein", 150, 14.0, 0, 10.0, desc="Nếu không lột da, khi thui vàng da chuột sẽ rất giòn và chứa nhiều collagen."),

    # Thịt chó
    F("Ba chỉ chó", "Dog Belly", "protein", 320, 16.5, 0, 28.0, desc="Phần thịt bụng có các lớp mỡ và nạc xen kẽ, da mỏng, thường dùng làm món hấp."),
    F("Đùi chó", "Dog Leg", "protein", 185, 20.0, 0, 11.5, desc="Phần thịt nạc nhất, thớ thịt săn chắc, phù hợp làm món nướng hoặc xào lăn."),
    F("Thịt vai chó", "Dog Shoulder", "protein", 210, 18.0, 0, 15.5, desc="Có sự cân bằng giữa nạc, mỡ và gân, thường được thái miếng vuông để nấu nhựa mận."),
    F("Sườn chó", "Dog Ribs", "protein", 245, 17.0, 0, 19.5, desc="Thịt bám xương sườn, vị ngọt, thường dùng để nướng hoặc nấu canh măng."),
    F("Dồi chó (nguyên liệu)", "Dog Blood Sausage Components", "protein", 160, 14.0, 2.0, 11.0, desc="Hỗn hợp gồm tiết, mỡ chày, đỗ xanh và rau thơm; giàu sắt và vitamin."),
    F("Đầu chó", "Dog Head", "protein", 140, 15.0, 0, 8.5, desc="Gồm xương sụn, da và óc, thường dùng để ninh lấy nước dùng ngọt."),
    F("Gan chó", "Dog Liver", "protein", 132, 18.5, 0, 4.8, desc="Rất giàu Vitamin A và sắt, kết cấu mềm và béo."),
    F("Tim chó", "Dog Heart", "protein", 125, 16.5, 0, 6.0, desc="Phần cơ chắc, dai giòn, giàu khoáng chất."),
    F("Đuôi chó", "Dog Tail", "protein", 230, 15.5, 0, 18.5, desc="Chủ yếu là da và xương sụn, thường dùng để hầm thuốc bắc hoặc nấu lẩu."),
    F("Chân giò chó", "Dog Shank", "protein", 175, 19.0, 0, 10.5, desc="Phần khuỷu chân, nhiều da và gân, khi nấu chín có độ giòn đặc trưng."),
    
    # Thịt nai
    F("Thăn nội nai", "Venison Tenderloin", "protein", 120, 24.0, 0, 2.4, desc="Phần thịt mềm nhất, không có mỡ, thường được dùng để áp chảo hoặc làm bít tết tái."),
    F("Thăn ngoại nai", "Venison Striploin", "protein", 135, 23.0, 0, 4.2, desc="Thớ thịt mịn, chắc, hương vị đậm đà hơn thăn nội, rất phù hợp để nướng."),
    F("Thịt mông/đùi nai", "Venison Haunch", "protein", 115, 25.0, 0, 1.8, desc="Phần thịt nạc nhất, thớ lớn, thường dùng để thái mỏng nhúng giấm hoặc làm khô nai."),
    F("Thịt vai nai", "Venison Shoulder", "protein", 145, 21.0, 0, 6.5, desc="Thịt có độ dai vừa phải, giàu hương vị, phù hợp cho các món sốt vang hoặc cà ri."),
    F("Bắp nai", "Venison Shank", "protein", 125, 26.5, 0, 2.0, desc="Chứa nhiều mô liên kết, khi hầm lâu thịt sẽ rất ngọt và có độ giòn sần sật của gân."),
    F("Sườn nai", "Venison Ribs", "protein", 195, 19.0, 0, 13.0, desc="Xương sườn mỏng, thịt bám xương rất ngọt, thường dùng để nướng hoặc ninh nước dùng."),
    F("Nạm nai", "Venison Flank", "protein", 160, 20.0, 0, 8.5, desc="Phần thịt bụng mỏng, thớ dài, thường dùng để băm nhỏ hoặc làm thịt viên."),
    F("Tim nai", "Venison Heart", "protein", 140, 17.5, 0, 7.2, desc="Rất giàu sắt và khoáng chất, thớ thịt cơ chắc chắn, dai giòn."),
    F("Gan nai", "Venison Liver", "protein", 138, 20.0, 0, 4.0, desc="Nguồn cung cấp Vitamin A dồi dào, vị đậm đà, ít tanh hơn gan bò hay heo."),
    F("Đuôi nai", "Venison Tail", "protein", 220, 16.0, 0, 17.0, desc="Trong y học cổ truyền, đuôi nai (lộc vĩ) được dùng làm thuốc bổ thận, tráng dương."),

    # Thịt heo rừng
    F("Thăn nội heo rừng", "Wild Boar Tenderloin", "protein", 115, 24.0, 0, 2.1, desc="Phần thịt mềm nhất, thớ thịt mịn, không có mỡ bám, vị ngọt thanh."),
    F("Thăn ngoại heo rừng", "Wild Boar Loin", "protein", 150, 22.0, 0, 6.5, desc="Phần nạc lưng chắc, thường đi kèm với lớp da dày và giòn đặc trưng."),
    F("Ba chỉ heo rừng", "Wild Boar Belly", "protein", 280, 17.0, 0, 23.5, desc="Khác với heo nhà, ba chỉ heo rừng mỡ rất ít, da dày, khi nướng mỡ chảy ra rất thơm."),
    F("Thịt vai heo rừng", "Wild Boar Shoulder", "protein", 165, 20.5, 0, 9.0, desc="Thịt chắc, có tỷ lệ nạc mỡ cân bằng, phù hợp nhất cho các món xào lăn hoặc kho giả cầy."),
    F("Thịt mông/đùi heo rừng", "Wild Boar Leg", "protein", 140, 23.0, 0, 5.0, desc="Phần thịt nạc dày, thớ thịt đỏ đậm, thường dùng làm bít tết hoặc nướng tảng."),
    F("Sườn heo rừng", "Wild Boar Ribs", "protein", 210, 18.5, 0, 15.0, desc="Xương sườn nhỏ, thịt bám xương chắc và ngọt, thường được nướng muối ớt."),
    F("Chân giò heo rừng", "Wild Boar Shank", "protein", 170, 21.0, 0, 9.5, desc="Phần khuỷu chân nhiều gân và da dày, khi hầm chín da sẽ giòn sần sật rất hấp dẫn."),
    F("Mũi/Tai heo rừng", "Wild Boar Snout/Ears", "protein", 130, 16.0, 0, 7.0, desc="Cấu tạo chủ yếu là sụn và da dày, món khai vị khoái khẩu khi nướng hoặc làm gỏi."),
    F("Gan heo rừng", "Wild Boar Liver", "protein", 135, 19.5, 0, 4.5, desc="Giàu sắt và vitamin, vị đậm đà hơn gan heo nhà."),
    F("Đuôi heo rừng", "Wild Boar Tail", "protein", 245, 15.0, 0, 20.0, desc="Chủ yếu là xương và da, thường dùng ninh nước dùng để lấy vị ngọt thanh tự nhiên."),
    
    # Thịt kangaroo
    F("Thăn nội Kangaroo", "Kangaroo Fillet", "protein", 98, 22.5, 0, 1.0, desc="Phần thịt nạc nhất và mềm nhất, không có mỡ, vị thanh nhẹ."),
    F("Thăn ngoại Kangaroo", "Kangaroo Striploin", "protein", 102, 23.0, 0, 1.2, desc="Thớ thịt chắc, mịn, thường được thái miếng dày để áp chảo."),
    F("Thịt mông/đùi Kangaroo", "Kangaroo Rump", "protein", 110, 24.0, 0, 1.5, desc="Phần nạc dày, thớ thịt đỏ đậm, giàu sắt và kẽm."),
    F("Đuôi Kangaroo", "Kangaroo Tail", "protein", 185, 18.0, 0, 12.0, desc="Chứa nhiều xương sụn và collagen, mỡ tập trung nhiều hơn ở đây, rất tốt khi hầm."),
    F("Thịt vai Kangaroo", "Kangaroo Shoulder", "protein", 115, 21.0, 0, 3.2, desc="Thịt chắc, có nhiều mô liên kết, phù hợp cho các món hầm hoặc nấu cà ri."),
    F("Bắp Kangaroo", "Kangaroo Shank", "protein", 105, 25.0, 0, 1.2, desc="Cực kỳ nạc, giàu gân, sau khi hầm lâu sẽ rất ngọt và mềm."),
    F("Thịt Kangaroo xay", "Kangaroo Mince", "protein", 120, 21.5, 0, 4.0, desc="Hỗn hợp nạc vụn, được dùng làm nhân bánh hoặc sốt mỳ Ý cho người ăn kiêng."),
    F("Gan Kangaroo", "Kangaroo Liver", "protein", 135, 19.0, 0, 4.5, desc="Nguồn cung cấp Vitamin A và sắt dồi dào, vị đậm đà đặc trưng."),
    F("Tim Kangaroo", "Kangaroo Heart", "protein", 140, 17.0, 0, 8.0, desc="Phần cơ chắc chắn, giàu khoáng chất bồi bổ cơ thể."),
    F("Sườn Kangaroo", "Kangaroo Ribs", "protein", 165, 19.0, 0, 10.0, desc="Xương nhỏ, thịt bám sườn ngọt, thường dùng để nướng tảng."),
    
    # Thịt cá sấu
    F("Thịt đuôi cá sấu", "Crocodile Tail Fillet", "protein", 105, 22.5, 0, 1.5, desc="Phần nạc nhất và mềm nhất, thớ thịt mịn, thường dùng làm bít tết hoặc xào."),
    F("Thịt lườn cá sấu", "Crocodile Flank", "protein", 115, 21.0, 0, 3.0, desc="Phần thịt từ thân, có kết cấu chắc chắn, phù hợp cho các món nướng hoặc kho."),
    F("Bàn chân cá sấu", "Crocodile Paws", "protein", 130, 19.5, 0, 5.5, desc="Chứa nhiều da và mô liên kết, sau khi hầm sẽ rất mềm và giòn, tốt cho xương khớp."),
    F("Sườn cá sấu", "Crocodile Ribs", "protein", 145, 18.0, 0, 7.5, desc="Xương sườn nhỏ, thịt bám xương ngọt, thường được nướng muối ớt hoặc nướng bơ tỏi."),
    F("Da cá sấu (ăn được)", "Crocodile Skin", "protein", 95, 12.0, 0, 5.0, desc="Lớp da sau khi xử lý sạch, giàu collagen, thường dùng làm gỏi hoặc chiên giòn."),
    F("Tim cá sấu", "Crocodile Heart", "protein", 110, 17.0, 0, 4.5, desc="Phần cơ chắc, ít béo, giàu khoáng chất, thường được hầm thuốc bắc."),
    F("Gan cá sấu", "Crocodile Liver", "protein", 125, 18.5, 0, 4.0, desc="Chứa nhiều sắt và Vitamin A, vị đậm đà và béo nhẹ."),
    F("Thịt cổ cá sấu", "Crocodile Neck", "protein", 140, 19.0, 0, 7.0, desc="Nhiều xương và thịt vụn, vị rất ngọt, chuyên dùng để nấu lẩu hoặc súp."),
    F("Phi lê cổ cá sấu", "Crocodile Neck Fillet", "protein", 120, 22.0, 0, 3.5, desc="Phần nạc lọc từ cổ, thớ thịt ngắn, dai giòn, phù hợp làm món nhúng giấm."),
    F("Mỡ cá sấu", "Crocodile Fat", "protein", 850, 0, 0, 95.0, desc="Chứa nhiều axit béo không bão hòa, thường dùng để trị bỏng hoặc bệnh ngoài da."),
    
    # Thịt ếch
    F("Đùi ếch", "Frog Legs", "protein", 73, 16.5, 0, 0.3, desc="Phần tập trung nhiều thịt nhất, thớ thịt chắc, giàu protein và rất ít béo."),
    F("Thân ếch", "Frog Body", "protein", 68, 15.0, 0, 0.2, desc="Phần thịt ở sống lưng và bụng, thịt mỏng hơn đùi nhưng rất ngọt và mềm."),
    F("Da ếch", "Frog Skin", "protein", 90, 12.0, 0, 4.5, desc="Chứa nhiều collagen, khi chiên giòn hoặc xào sả ớt có độ giòn đặc trưng."),
    F("Gan ếch", "Frog Liver", "protein", 115, 14.0, 0, 5.0, desc="Nhỏ và béo, chứa nhiều vitamin A, thường được giữ lại khi chế biến ếch nguyên con."),
    F("Bao tử ếch", "Frog Stomach", "protein", 85, 13.5, 0, 2.0, desc="Một trong những bộ phận quý của ếch, kết cấu giòn, thường dùng làm món xào."),
    F("Trứng ếch", "Frog Eggs", "protein", 130, 11.0, 1.5, 8.5, desc="Thường có vào mùa sinh sản, vị béo ngậy, giàu dinh dưỡng nhưng cần làm sạch kỹ."),
    F("Xương ếch", "Frog Bones", "protein", 60, 8.0, 0, 1.5, desc="Xương ếch khá mềm, khi băm nhỏ làm chả hoặc chiên kỹ có thể ăn được cả xương."),
    F("Ếch làm sạch (còn da)", "Whole Dressed Frog with skin", "protein", 82, 16.0, 0, 1.2, desc="Ếch đã bỏ đầu và nội tạng, giữ lại da, dùng cho các món nướng hoặc lẩu."),
    
    # Thịt ba ba
    F("Thịt nạc ba ba", "Turtle Flesh", "protein", 89, 17.5, 0, 1.6, desc="Phần nạc từ 4 đùi và thân, thịt trắng hồng, vị ngọt, rất giàu kẽm và đồng."),
    F("Rìa mai ba ba", "Turtle Calipee", "protein", 120, 19.0, 0, 4.5, desc="Phần sụn mềm bao quanh mai, cực kỳ giàu collagen và gelatin, ăn giòn sần sật."),
    F("Chân ba ba", "Turtle Paws", "protein", 110, 18.0, 0, 3.5, desc="Nhiều da và gân, thớ thịt chắc, thường dùng trong các món hầm."),
    F("Gan ba ba", "Turtle Liver", "protein", 125, 16.0, 0, 5.5, desc="Vị béo, giàu sắt và Vitamin A, thường được giữ lại để xào hoặc hầm."),
    F("Tim ba ba", "Turtle Heart", "protein", 105, 15.0, 0, 3.0, desc="Kích thước nhỏ, được coi là phần bổ nhất cho hệ tim mạch theo dân gian."),
    F("Trứng ba ba", "Turtle Eggs", "protein", 155, 12.5, 1.2, 11.0, desc="Vỏ mềm hoặc dai, lòng đỏ rất lớn và béo, chứa hàm lượng lecithin cao."),
    F("Tiết ba ba", "Turtle Blood", "protein", 65, 12.0, 0.5, 0.1, desc="Thường được pha với rượu để uống, được cho là có tác dụng bồi bổ sinh lực."),
    F("Mỡ ba ba", "Turtle Fat", "protein", 780, 0, 0, 85.0, desc="Thường có màu vàng sẫm, đông đặc ở nhiệt độ thường, vị rất ngậy."),
    F("Mai ba ba (Mi biệt)", "Trionycis Carapax", "protein", 45, 8.0, 0, 0.5, desc="Thành phần chủ yếu là canxi và keratin, thường dùng để ninh nước dùng hoặc làm thuốc."),
    
    # Thịt rắn
    F("Thịt nạc rắn", "Snake Meat", "protein", 93, 21.0, 0, 0.9, desc="Phần nạc dọc xương sống, cực kỳ ít mỡ, thớ thịt dai và săn chắc."),
    F("Da rắn", "Snake Skin", "protein", 110, 14.5, 0, 5.5, desc="Chứa nhiều collagen, khi chiên giòn hoặc xào sả ớt có độ dai giòn rất lạ miệng."),
    F("Gan rắn", "Snake Liver", "protein", 125, 17.5, 0, 5.0, desc="Giàu vitamin A và sắt, vị béo bùi, thường được dùng để xào lăn."),
    F("Tim rắn", "Snake Heart", "protein", 115, 16.0, 0, 4.5, desc="Kích thước nhỏ bằng hạt ngô, thường được pha với rượu hoặc nuốt sống theo dân gian."),
    F("Mỡ rắn", "Snake Fat", "protein", 800, 0, 0, 88.0, desc="Thường dùng để thắng lấy tinh dầu mỡ rắn, có tác dụng trị bỏng và nứt nẻ da rất tốt."),
    F("Mật rắn", "Snake Gall", "protein", 60, 5.0, 1.5, 0.5, desc="Vị đắng, tính hàn, thường pha với rượu để chữa các chứng đau nhức xương khớp."),
    F("Tiết rắn", "Snake Blood", "protein", 72, 13.0, 0.4, 0.1, desc="Giàu sắt, thường pha với rượu mạnh để dùng ngay sau khi lấy."),
    F("Xương rắn", "Snake Bones", "protein", 85, 12.0, 0, 3.5, desc="Gồm xương sống và nhiều xương sườn nhỏ, thường được băm nhuyễn để làm chả hoặc chiên giòn."),
    
    # ===== Proteins - Seafood =====
    
    # Cá Hồi (Salmon) - Giàu Omega-3 nhất
    F("Cá Hồi", "Salmon", "protein", 208, 20.0, 0, 13.0, desc="Thịt đỏ cam, béo ngậy, cung cấp lượng lớn Vitamin D và Astaxanthin."),
    # Cá Ngừ (Tuna) - "Bít tết" của đại dương
    F("Cá Ngừ", "Tuna", "protein", 132, 28.0, 0, 0.6, desc="Thịt đỏ thẫm, hàm lượng protein cực cao, rất ít béo, phù hợp để ăn Sashimi."),
    # Cá Thu (Mackerel) - Hương vị đậm đà
    F("Cá Thu", "Mackerel", "protein", 205, 18.6, 0, 13.9, desc="Thịt chắc, giàu dầu cá, là nguồn cung cấp Vitamin B12 tuyệt vời."),
    # Cá Trích (Herring) - Nhỏ nhưng giàu dinh dưỡng
    F("Cá Trích", "Herring", "protein", 158, 18.0, 0, 9.0, desc="Thịt thơm, béo, chứa nhiều canxi và thường được dùng làm gỏi hoặc đóng hộp."),
    # Cá Mú (Grouper) - Đặc sản thịt trắng cao cấp
    F("Cá Mú", "Grouper", "protein", 92, 19.4, 0, 1.0, desc="Thịt trắng, dai giòn, vị ngọt thanh, cực kỳ ít béo và lành tính."),
    # Cá Chẽm (Barramundi) - Cá chẽm biển/nước lợ
    F("Cá Chẽm", "Barramundi", "protein", 108, 20.1, 0, 2.5, desc="Thịt nạc, thớ lớn, da dày và béo, rất giàu Omega-3 so với các loại cá thịt trắng khác."),
    # Cá Tuyết (Cod) - Nguồn Protein tinh khiết
    F("Cá Tuyết", "Cod", "protein", 82, 17.8, 0, 0.7, desc="Thịt trắng tinh, dễ tiêu hóa, hương vị nhẹ nhàng, rất ít calo."),
    # Cá Kiếm (Swordfish) - Thịt chắc như thịt gia súc
    F("Cá Kiếm", "Swordfish", "protein", 144, 20.0, 0, 6.7, desc="Kết cấu thịt rất chắc và đặc, thường được cắt thành khoanh bít tết để nướng."),   
    # Cá Lóc/Cá Quả (Snakehead Fish) - Vua cá nước ngọt về dinh dưỡng
    F("Cá Lóc", "Snakehead Fish", "protein", 97, 18.2, 0, 2.7, desc="Thịt chắc, trắng, vị ngọt thanh. Chứa hàm lượng albumin cao giúp vết thương mau lành."),
    # Cá Rô Phi (Tilapia) - Phổ biến và cân bằng
    F("Cá Rô Phi", "Tilapia", "protein", 128, 20.1, 0, 1.7, desc="Thịt trắng, hương vị nhẹ nhàng, rất giàu selen và phosphor."),
    # Cá Diêu Hồng (Red Tilapia) - Thịt thơm và béo vừa phải
    F("Cá Diêu Hồng", "Red Tilapia", "protein", 120, 19.5, 0, 4.6, desc="Một dòng cá rô phi nhưng thịt có độ béo cao hơn, thơm và mềm hơn."),
    # Cá Tra (Pangasius) - Nhiều nạc, thớ thịt dày
    F("Cá Tra", "Pangasius", "protein", 125, 15.0, 0, 7.2, desc="Thịt màu hơi sẫm hoặc trắng tùy loại, thớ thịt dày, nạc chắc."),
    # Cá Basa (Basa Fish) - Nổi tiếng với mỡ cá giàu Omega
    F("Cá Basa", "Basa Fish", "protein", 158, 13.5, 0, 11.5, desc="Thịt rất mềm, màu trắng tinh. Lớp mỡ cá basa chứa nhiều axit béo không no có lợi."),
    # Cá Trê (Catfish) - Giàu Vitamin D
    F("Cá Trê", "Catfish", "protein", 119, 15.0, 0, 6.0, desc="Thịt sẫm màu, béo và ngọt. Cung cấp lượng Vitamin D tự nhiên rất cao."),
    # Cá Chép (Carp) - Thực phẩm bổ dưỡng cho bà bầu
    F("Cá Chép", "Carp", "protein", 127, 17.8, 0, 5.6, desc="Thịt dày, vị đậm đà. Theo Đông y, cá chép có tác dụng an thai và lợi sữa."),
    # Cá Mè (Silver Carp) - Chứa nhiều dầu cá
    F("Cá Mè", "Silver Carp", "protein", 115, 15.5, 0, 5.9, desc="Thịt mịn, nhiều mỡ, nhưng có khá nhiều xương dăm. Đầu cá mè được coi là phần quý nhất."),
    
    # Tôm Sú (Black Tiger Prawn) - Thịt chắc, kích thước lớn
    F("Tôm Sú", "Black Tiger Prawn", "protein", 95, 21.0, 0.5, 0.9, desc="Thịt rất chắc, dai, vị ngọt đậm đà. Thích hợp cho các món nướng hoặc hấp."),
    # Tôm Thẻ Chân Trắng (Whiteleg Shrimp) - Phổ biến nhất
    F("Tôm Thẻ Chân Trắng", "Whiteleg Shrimp", "protein", 91, 19.8, 0.4, 0.8, desc="Thịt mềm và ngọt hơn tôm sú, vỏ mỏng, phù hợp cho hầu hết các cách chế biến."),
    # Tôm Hùm (Lobster) - Hải sản thượng hạng
    F("Tôm Hùm", "Lobster", "protein", 89, 19.0, 0.1, 0.9, desc="Thớ thịt dày, trắng tinh, vị ngọt sang trọng. Cực kỳ ít chất béo và giàu đồng, selen."),
    # Tôm Càng Xanh (Giant Freshwater Prawn) - Đặc sản nước ngọt
    F("Tôm Càng Xanh", "Giant Freshwater Prawn", "protein", 92, 18.5, 0.6, 1.2, desc="Thịt ngọt, có độ dai vừa phải. Đặc biệt phần gạch ở đầu tôm rất béo và thơm."),
    # Tôm Tích / Bề Bề (Mantis Shrimp) - Vị ngọt độc đáo
    F("Tôm Tích (Bề Bề)", "Mantis Shrimp", "protein", 102, 17.5, 1.2, 2.8, desc="Thịt có vị trung hòa giữa tôm và cua, rất ngọt. Lưu ý vỏ tôm tích rất sắc nhọn."),

    # Cua Hoàng Đế (King Crab) - Đẳng cấp hải sản
    F("Cua Hoàng Đế", "King Crab", "protein", 84, 18.3, 0, 0.6, desc="Thớ thịt to, trắng, vị ngọt thanh và hơi mặn đặc trưng của biển sâu. Rất ít béo."),
    # Cua Gạch (Mud Crab with Roe) - Siêu bổ dưỡng
    F("Cua Gạch", "Mud Crab with Roe", "protein", 135, 17.5, 0.5, 7.0, desc="Thịt cua ngọt chắc kết hợp với phần gạch (trứng) béo ngậy, giàu Vitamin A và Omega-3."),
    # Cua Thịt (Mud Crab - Male) - Chuyên về đạm
    F("Cua Thịt", "Mud Crab", "protein", 98, 20.0, 0, 1.2, desc="Phần thịt từ cua đực, thớ thịt săn chắc, đầy đặn, hàm lượng protein cao và ít mỡ."),
    # Ghẹ Xanh (Blue Swimmer Crab) - Vị ngọt thanh
    F("Ghẹ Xanh", "Blue Swimmer Crab", "protein", 93, 19.0, 0, 1.1, desc="Loại ghẹ ngon nhất, thịt trắng mịn, ngọt và thơm hơn cua, vỏ mỏng dễ tách."),
    # Ghẹ Hoa (Flower Crab) - Phổ biến và kinh tế
    F("Ghẹ Hoa", "Flower Crab", "protein", 88, 18.1, 0, 0.9, desc="Thịt ghẹ hoa mềm, thanh, ít calo, là lựa chọn tuyệt vời cho các món hấp hoặc nấu súp."),
    
    # Mực Ống - Thân mỏng, giòn, phù hợp nhồi thịt hoặc cắt khoanh
    F("Mực ống", "Squid", "protein", 92, 15.6, 3.1, 1.3, desc="Giàu Riboflavin và Selen. Có chứa một lượng nhỏ carbohydrate tự nhiên."),
    # Mực Lá - Thịt dày, ngọt nhất trong các loại mực
    F("Mực lá", "Bigfin Reef Squid", "protein", 110, 18.5, 2.5, 1.5, desc="Thịt dày, vị ngọt đậm, thường được dùng cho các món sashimi hoặc nướng."),
    # Mực Nang - Thịt rất dày, chắc, trắng tinh
    F("Mực nang", "Cuttlefish", "protein", 79, 16.0, 0.8, 0.7, desc="Chứa hàm lượng sắt và đồng cao. Phần mai mực còn được dùng làm dược liệu."),
    # Bạch Tuộc - Thịt dai chắc, giàu Vitamin B12
    F("Bạch tuộc", "Octopus", "protein", 82, 15.0, 2.2, 1.0, desc="Cung cấp lượng lớn Selenium và Vitamin B12, giúp hỗ trợ hệ thần kinh."),
    # Mực Ghim - Nhỏ, thân dài, thường ăn nguyên con
    F("Mực ghim", "Mitre Squid", "protein", 85, 16.2, 1.5, 1.0, desc="Thường được hấp gừng hoặc xào, thịt ngọt thanh và giòn nhẹ."),
    
    # Nghêu (Ngao) - Rất giàu sắt
    F("Nghêu (Ngao)", "Clam", "protein", 74, 12.8, 2.6, 1.2, desc="Nguồn cung cấp Vitamin B12 và Sắt tuyệt vời, giúp bổ máu."),
    # Sò Huyết - "Thứ phẩm" bổ máu nhất
    F("Sò huyết", "Blood Cockle", "protein", 71, 11.7, 3.2, 0.7, desc="Đặc trưng bởi huyết cá sắc đỏ giàu hemoglobin, cực kỳ bổ dưỡng cho người thiếu sắt."),
    # Sò Điệp - Chỉ ăn phần cồi thịt trắng
    F("Sò điệp (Cồi)", "Scallops", "protein", 69, 12.1, 2.4, 0.5, desc="Thịt mềm, ngọt thanh, chứa nhiều Magie và Kali, rất tốt cho tim mạch."),
    # Hàu - Vua Kẽm
    F("Hàu", "Oyster", "protein", 68, 7.0, 3.9, 2.5, desc="Chứa hàm lượng kẽm cao nhất trong tự nhiên, hỗ trợ sinh lý và miễn dịch."),
    # Vẹm Xanh - Tốt cho xương khớp
    F("Vẹm xanh", "Green Mussels", "protein", 86, 11.9, 3.7, 2.2, desc="Chứa nhiều glucosamine tự nhiên và omega-3, hỗ trợ giảm viêm khớp."),
    # Tu Hài (Ốc vòi voi nhỏ)
    F("Tu hài", "Elephant Trunk Clam", "protein", 82, 14.5, 2.0, 0.8, desc="Thịt chắc, giòn sần sật, vị ngọt rất đặc trưng và thanh."),
    # Ốc Móng Tay
    F("Ốc móng tay", "Razor Clam", "protein", 78, 15.0, 1.5, 0.5, desc="Thịt trắng, dai giòn, giàu đạm và canxi."),
    # Ốc Hương - "Nữ hoàng" loài ốc
    F("Ốc hương", "Sweet Snail", "protein", 90, 18.0, 2.0, 0.5, desc="Thịt giòn, thơm mùi lá dứa tự nhiên, giàu dinh dưỡng và không bị ngấy."),
    # Ốc Bươu / Ốc Nhồi - Dân dã, lành tính
    F("Ốc bươu/nhồi", "Apple Snail", "protein", 84, 11.1, 3.9, 0.7, desc="Giàu canxi và vitamin B, thường dùng trong các món canh, bún ốc."),
    # Ốc Len - Béo ngậy với nước cốt dừa
    F("Ốc len", "Cerithidea obtusa", "protein", 95, 13.0, 5.0, 1.5, desc="Thịt nhỏ nhưng đậm đà, chứa nhiều khoáng chất từ vùng ngập mặn."),
    # Bào Ngư - Thượng phẩm đại dương
    F("Bào ngư", "Abalone", "protein", 105, 17.1, 6.0, 0.8, desc="Chứa hợp chất paolin giúp kháng khuẩn. Cực kỳ bổ dưỡng cho sức khỏe tổng thể."),

    # Nhím biển (Uni/Sea Urchin) - Trứng nhím biển
    F("Trứng Nhím biển (Uni)", "Sea Urchin Roe", "protein", 172, 13.3, 4.8, 11.5, desc="Thực chất là tuyến sinh dục. Vị béo ngậy như kem, giàu Omega-3 và Vitamin A."),
    # Hải sâm (Sea Cucumber) - Nhân sâm từ biển
    F("Hải sâm", "Sea Cucumber", "protein", 56, 13.0, 0, 0.4, desc="Cực kỳ ít calo, không cholesterol. 70% protein là collagen giúp tái tạo mô và da."),

    # Rong mứt (Nori) - Thường dùng làm kim báp
    F("Rong mứt (tươi)", "Nori (Fresh)", "protein", 35, 5.8, 5.1, 0.3, desc="Giàu Vitamin A, C và Vitamin B12 (hiếm gặp ở thực vật)."),
    # Rong biển phổ tai (Kombu) - Nguồn vị ngọt Umami tự nhiên
    F("Rong biển Kombu", "Kombu", "protein", 43, 1.7, 9.6, 0.1, desc="Chứa hàm lượng I-ốt cao nhất. Dùng để nấu nước dùng dashi."),
    # Rong nho (Sea Grapes) - Trứng cá hồi xanh
    F("Rong nho", "Sea Grapes", "protein", 4, 0.5, 0.8, 0.0, desc="Thấp calo, giàu khoáng chất và chất xơ, ăn giòn tan như trứng cá."),
    # Tảo xoắn Spirulina (Dạng khô) - Siêu thực phẩm
    F("Tảo xoắn Spirulina (Khô)", "Spirulina (Dried)", "protein", 290, 57.5, 23.9, 7.7, desc="Tỷ lệ protein lên tới gần 60%, chứa đầy đủ các axit amin thiết yếu."),
    
    # ===== Carbs - Grains =====
    
    # Gạo Trắng (White Rice/Jasmine)
    F("Gạo trắng (Jasmine)", "White Rice", "carbs", 365, 7.1, 80.0, 0.6, desc="Đã xay xát bỏ lớp cám, dễ tiêu hóa, chỉ số GI cao, cung cấp năng lượng nhanh."),
    # Cơm (Cooked Rice) - Món ăn chính tại Việt Nam
    F("Cơm trắng", "Cooked White Rice", "carbs", 130, 2.7, 28.2, 0.3, desc="Cơm trắng nấu chín từ gạo Jasmine, món chính của người Việt.", servings=S_BOWL),
    F("Cơm lứt", "Cooked Brown Rice", "carbs", 112, 2.3, 23.5, 0.9, desc="Cơm lứt nấu chín, giữ nguyên lớp cám, giàu chất xơ.", servings=S_BOWL),
    F("Cơm gạo nếp", "Cooked Sticky Rice", "carbs", 116, 2.0, 25.8, 0.2, desc="Cơm nếp nấu chín, dẻo và no lâu.", servings=S_BOWL),
    # Gạo Lứt (Brown Rice) - Gạo nguyên cám
    F("Gạo lứt", "Brown Rice", "carbs", 360, 7.5, 76.0, 2.7, desc="Giữ nguyên lớp cám và mầm, giàu chất xơ, Magie và Vitamin B1. Chỉ số GI trung bình."),
    # Gạo Nếp (Sticky Rice)
    F("Gạo nếp", "Glutinous Rice", "carbs", 348, 6.5, 77.5, 0.7, desc="Chứa hàm lượng amylopectin cao tạo độ dẻo dính, năng lượng đậm đặc, no lâu."),
    # Gạo Huyết Rồng / Gạo đỏ (Red Rice)
    F("Gạo huyết rồng", "Red Rice", "carbs", 355, 7.0, 75.0, 2.5, desc="Vỏ màu đỏ sẫm, chứa nhiều chất chống oxy hóa anthocyanin và sắt."),
    # Gạo Basmati (Ấn Độ)
    F("Gạo Basmati", "Basmati Rice", "carbs", 350, 8.5, 78.0, 0.5, desc="Hạt dài, mùi thơm thảo mộc, chỉ số GI thấp hơn gạo trắng thông thường."),
    # Lúa mì nguyên cám (Whole Wheat)
    F("Lúa mì nguyên cám", "Whole Wheat", "carbs", 339, 13.2, 72.0, 2.5, desc="Hàm lượng protein và chất xơ cao, là nguyên liệu cho bánh mì đen và pasta nguyên cám."),
    # Yến mạch (Oats) - Siêu thực phẩm cho tim mạch
    F("Yến mạch", "Oats", "carbs", 389, 16.9, 66.0, 6.9, desc="Giàu Beta-glucan giúp giảm cholesterol, hàm lượng protein cao nhất trong nhóm ngũ cốc."),
    # Lúa mạch (Barley)
    F("Lúa mạch", "Barley", "carbs", 354, 12.5, 73.5, 2.3, desc="Chất xơ rất cao, thường dùng nấu súp hoặc làm trà, bia."),
    # Hắc mạch (Rye)
    F("Hắc mạch / Lúa mạch đen", "Rye", "carbs", 338, 10.3, 76.0, 1.6, desc="Hương vị đậm, thường làm bánh mì đen đặc, chỉ số GI thấp, hỗ trợ kiểm soát đường huyết."),
    # Ngô tẻ / Ngô vàng (Flint Corn)
    F("Ngô vàng (khô)", "Yellow Corn", "carbs", 365, 9.4, 74.0, 4.7, desc="Giàu Zeaxanthin và Lutein, thường dùng làm bột ngô hoặc thức ăn chăn nuôi."),
    # Ngô ngọt / Bắp Mỹ (Sweet Corn)
    F("Bắp Mỹ (tươi)", "Sweet Corn", "carbs", 86, 3.2, 19.0, 1.2, desc="Tính trên bắp tươi. Chứa nhiều đường tự nhiên hơn, vị ngọt, dùng làm món ăn kèm."),
    # Ngô nếp (Waxy Corn)
    F("Bắp nếp (tươi)", "Waxy Corn", "carbs", 165, 4.1, 35.0, 0.8, desc="Độ dẻo cao nhờ 100% tinh bột amylopectin, năng lượng cao hơn bắp Mỹ."),
    
    # Diêm mạch (Quinoa) - Protein hoàn chỉnh
    F("Hạt Diêm mạch", "Quinoa", "carbs", 368, 14.1, 64.0, 6.1, desc="Chứa tất cả 9 axit amin thiết yếu, giàu Magie và sắt. Có 3 loại trắng, đỏ, đen với vị đậm tăng dần."),
    # Kiều mạch (Buckwheat) - Tốt cho tim mạch
    F("Hạt Kiều mạch", "Buckwheat", "carbs", 343, 13.2, 71.5, 3.4, desc="Chứa Rutin giúp bền thành mạch máu. Là nguyên liệu chính làm mì Soba Nhật Bản."),
    # Hạt dền (Amaranth) - Siêu thực phẩm cổ đại
    F("Hạt dền", "Amaranth", "carbs", 371, 13.6, 65.0, 7.0, desc="Hàm lượng Canxi cao gấp đôi sữa và gấp 3 lần lúa mì. Thớ hạt rất nhỏ, vị hơi nồng của đất."),
    # Hạt kê (Millet) - Lành tính và kiềm hóa
    F("Hạt kê", "Millet", "carbs", 378, 11.0, 72.8, 4.2, desc="Dễ tiêu hóa, có tính kiềm (tốt cho dạ dày). Giàu chất chống oxy hóa và lecithin cho não bộ."),
    
    # Khoai tây (Potatoes) - Nguồn Kali dồi dào
    F("Khoai tây", "Potato", "carbs", 77, 2.0, 17.5, 0.1, desc="Giàu Kali và Vitamin C. Chỉ số GI thay đổi mạnh tùy theo cách chế biến (luộc thấp hơn nướng/chiên)."),
    # Khoai lang (Sweet Potatoes) - Thực phẩm vàng cho giảm cân
    F("Khoai lang", "Sweet Potato", "carbs", 86, 1.6, 20.1, 0.1, desc="Khoai vàng giàu Beta-carotene, khoai tím giàu Anthocyanin. Chỉ số GI thấp, giàu chất xơ hòa tan."),
    # Sắn / Khoai mì (Cassava) - Năng lượng đậm đặc
    F("Sắn (Khoai mì)", "Cassava", "carbs", 160, 1.4, 38.0, 0.3, desc="Năng lượng cao gấp đôi khoai tây. Lưu ý cần sơ chế kỹ (ngâm nước/luộc kỹ) để loại bỏ nhựa độc."),
    # Khoai môn (Taro)
    F("Khoai môn", "Taro", "carbs", 112, 1.5, 26.5, 0.2, desc="Chứa nhiều chất xơ và tinh bột kháng, rất tốt cho hệ tiêu hóa và đường huyết."),
    # Khoai sọ (Eddoe)
    F("Khoai sọ", "Eddoe", "carbs", 116, 1.5, 25.0, 0.1, desc="Kích thước nhỏ, thịt nhớt hơn khoai môn, giàu Kali giúp kiểm soát huyết áp."),
    # Khoai mỡ (Purple Yam)
    F("Khoai mỡ", "Purple Yam", "carbs", 118, 1.5, 27.5, 0.1, desc="Màu tím đặc trưng từ chất chống oxy hóa, thường dùng nấu canh để tạo độ sánh và bổ dưỡng."),
    # Củ từ (Arrowroot/Yam)
    F("Củ từ", "Wild Yam", "carbs", 118, 1.5, 27.0, 0.1, desc="Vị ngọt, tính bình, thường dùng cho người có hệ tiêu hóa kém."),
    # Củ mài / Hoài sơn (Mountain Yam)
    F("Củ mài (Hoài sơn)", "Mountain Yam", "carbs", 118, 2.0, 26.0, 0.2, desc="Vị thuốc quý trong Đông y, giúp bồi bổ tỳ vị và tăng cường sức khỏe."),
    # Củ năng (Water Chestnut)
    F("Củ năng", "Water Chestnut", "carbs", 97, 1.4, 23.9, 0.1, desc="Thực chất là thân củ của cây thủy sinh, vị ngọt thanh, giòn, giàu chất chống oxy hóa."),
    # Củ sen (Lotus Root)
    F("Củ sen", "Lotus Root", "carbs", 74, 2.6, 17.2, 0.1, desc="Thực phẩm dưỡng sinh quý, giàu sắt, Vitamin C và chất xơ. Có tác dụng an thần, bổ máu."),
    
    # Đậu Xanh (Mung Bean) - Thanh nhiệt, giải độc
    F("Đậu xanh", "Mung Bean", "carbs", 341, 23.8, 62.6, 1.2, desc="Giàu chất chống oxy hóa (vitexin và isovitexin). Phù hợp làm ngũ cốc giải nhiệt."),
    # Đậu Đỏ (Adzuki Bean) - Tốt cho thận và tim mạch
    F("Đậu đỏ", "Adzuki Bean", "carbs", 329, 19.9, 62.9, 0.5, desc="Chứa hàm lượng chất xơ hòa tan cực cao và kali, hỗ trợ kiểm soát huyết áp."),
    # Đậu Đen (Black Bean) - Giàu Anthocyanin
    F("Đậu đen", "Black Bean", "carbs", 341, 21.6, 62.4, 1.4, desc="Lớp vỏ màu đen chứa anthocyanin (chống lão hóa) mạnh mẽ. Rất giàu sắt và folate."),
    # Đậu Trắng (White Kidney Bean) - Hỗ trợ giảm cân
    F("Đậu trắng", "White Kidney Bean", "carbs", 333, 23.4, 60.0, 0.8, desc="Chứa hoạt chất ức chế enzyme alpha-amylase, giúp giảm hấp thụ tinh bột vào cơ thể."),
    # Đậu Hà Lan (Green Peas)
    F("Đậu hà lan (khô)", "Green Peas", "carbs", 341, 24.5, 60.0, 1.2, desc="Nguồn cung cấp Vitamin K và Mangan dồi dào, hỗ trợ sức khỏe xương khớp."),
    # Đậu Nành (Soybean) - "Thịt thực vật"
    F("Đậu nành", "Soybean", "carbs", 446, 36.5, 30.2, 19.9, desc="Đặc biệt nhất nhóm: Protein cực cao và hoàn chỉnh, giàu béo tốt (Omega-6), tinh bột vừa phải."),
    # Đậu Lăng (Lentils) - Nhanh chín và giàu sắt
    F("Đậu lăng", "Lentils", "carbs", 352, 24.6, 63.0, 1.1, desc="Không cần ngâm lâu như các loại đậu khác. Cực kỳ giàu folate và sắt cho phụ nữ."),
    # Đậu Gà (Chickpeas/Garbanzo) - Nền tảng của món Hummus
    F("Đậu gà", "Chickpeas", "carbs", 364, 19.3, 60.6, 6.0, desc="Vị bùi như hạt dẻ, giàu chất xơ hòa tan giúp giảm cholesterol và hỗ trợ tiêu hóa."),
    
    # ===== Vegetables =====    
    
    # 1. Xà lách Mỡ (Butterhead/Boston Lettuce) - Mềm mại và béo nhẹ
    F("Xà lách mỡ", "Butterhead Lettuce", "fiber", 13, 1.5, 2.2, 0.2, desc="Lá mềm, vị ngọt thanh và có độ béo nhẹ đặc trưng. Giàu sắt và folate."),
    # 2. Xà lách Romaine (Xà lách Lô-ma) - Linh hồn của Salad Caesar
    F("Xà lách Romaine", "Romaine Lettuce", "fiber", 17, 1.2, 3.3, 0.3, desc="Cấu trúc lá dài, giòn, sống lá cứng. Chứa hàm lượng Vitamin A và K cao nhất trong họ xà lách."),
    # 3. Xà lách Mỹ / Xà lách Cuộn (Iceberg Lettuce) - Giòn nhất
    F("Xà lách Mỹ (Iceberg)", "Iceberg Lettuce", "fiber", 14, 0.9, 3.0, 0.1, desc="Cuộn tròn như bắp cải, chứa nhiều nước, cực kỳ giòn nhưng giá trị dinh dưỡng thấp hơn các loại lá xanh đậm."),
    # 4. Xà lách Lô-lô Xanh/Tím (Lollo Rossa/Bionda) - Lá xoăn đẹp mắt
    F("Xà lách Lô-lô", "Lollo Lettuce", "fiber", 16, 1.3, 2.5, 0.2, desc="Lá xoăn mềm, màu tím chứa nhiều anthocyanin giúp chống lão hóa và bảo vệ mạch máu."),
    # 5. Xà lách Lá Sồi (Oakleaf Lettuce)
    F("Xà lách Lá Sồi", "Oakleaf Lettuce", "fiber", 15, 1.4, 2.1, 0.2, desc="Lá có hình dạng giống lá cây sồi, vị ngọt và bùi. Rất nhạy cảm với nhiệt độ."),
    # 6. Xà lách Diếp Quăn (Endive/Curly Escarole) - Vị đắng nhẹ
    F("Xà lách Diếp quăn", "Endive", "fiber", 17, 1.3, 3.4, 0.2, desc="Cánh lá nhỏ, xoăn tít, vị hơi đắng giúp kích thích tiêu hóa và làm sạch gan."),
    
    # 1. Rau Muống (Water Spinach) - Rau quốc hồn quốc túy
    F("Rau muống", "Water Spinach", "fiber", 19, 3.0, 3.1, 0.3, desc="Giàu sắt và Vitamin A. Có tính thanh nhiệt, giải độc và nhuận tràng rất tốt."),
    # 2. Rau Ngót (Katuk / Star Gooseberry) - Siêu thực phẩm cho phụ nữ
    F("Rau ngót", "Katuk", "fiber", 59, 5.3, 11.0, 0.4, desc="Hàm lượng đạm thực vật và Canxi cực cao. Giúp làm sạch sản dịch và bổ máu sau sinh."),
    # 3. Rau Dền (Amaranth Leaves) - Vua Canxi của nhóm rau
    F("Rau dền", "Amaranth Leaves", "fiber", 23, 2.4, 4.0, 0.3, desc="Chứa lượng Canxi cao vượt trội (gần gấp đôi sữa) và giàu sắt. Giúp bổ máu và chắc xương."),
    # 4. Rau Mồng Tơi (Malabar Spinach) - Giàu chất nhầy pectin
    F("Rau mồng tơi", "Malabar Spinach", "fiber", 19, 2.0, 3.4, 0.3, desc="Chất nhầy giúp nhuận tràng, thải cholesterol và làm mát cơ thể trong mùa hè."),
    # 5. Rau Lang (Sweet Potato Leaves) - Rau trường thọ
    F("Rau lang", "Sweet Potato Leaves", "fiber", 35, 2.5, 5.0, 0.5, desc="Chứa nhiều chất chống oxy hóa (Polyphenols) giúp bảo vệ thị lực và tim mạch."),
    # 6. Rau Đay (Jute Leaves) - Cặp bài trùng với mồng tơi
    F("Rau đay", "Jute Leaves", "fiber", 43, 2.8, 6.0, 0.5, desc="Đứng đầu về hàm lượng Canxi (khoảng 400-500mg/100g) và Sắt trong các loại rau lá."),
    # 7. Rau Bí (Pumpkin Leaves/Stems)
    F("Rau bí", "Pumpkin Leaves", "fiber", 28, 3.3, 4.0, 0.4, desc="Giàu Kali và Vitamin C, giúp ổn định huyết áp và tăng cường miễn dịch."),
    
    # 1. Hành lá (Scallion/Green Onion) - Kháng viêm và bổ mắt
    F("Hành lá", "Scallion", "fiber", 32, 1.8, 7.3, 0.2, desc="Giàu Vitamin K và Allicin giúp kháng khuẩn. Thành phần không thể thiếu trong hầu hết món nước."),
    # 2. Ngò rí (Cilantro/Coriander) - Giải độc kim loại nặng
    F("Ngò rí", "Cilantro", "fiber", 23, 2.1, 3.7, 0.5, desc="Chứa nhiều Linalool giúp hỗ trợ tiêu hóa và các hợp chất hỗ trợ đào thải chì, thủy ngân."),
    # 3. Húng quế (Thai Basil) - Chống oxy hóa và kháng khuẩn
    F("Húng quế", "Thai Basil", "fiber", 23, 3.2, 2.7, 0.6, desc="Giàu Eugenol giúp giảm viêm khớp. Mùi thơm đặc trưng rất hợp với phở và các món bò."),
    # 4. Tía tô (Perilla) - Kháng Histamine tự nhiên
    F("Tía tô", "Perilla", "fiber", 37, 2.8, 7.0, 0.5, desc="Chứa axit rosmarinic giúp giảm triệu chứng dị ứng, cảm cúm. Giàu sắt và canxi."),
    # 5. Kinh giới (Vietnamese Balm) - Làm mát và trị mụn
    F("Kinh giới", "Vietnamese Balm", "fiber", 22, 2.5, 3.5, 0.4, desc="Chứa nhiều tinh dầu có tính sát khuẩn cao, hỗ trợ điều trị các bệnh ngoài da và cảm mạo."),
    # 6. Bạc hà (Peppermint/Spearmint) - Thông mũi, mát họng
    F("Bạc hà", "Peppermint", "fiber", 44, 3.8, 8.4, 0.7, desc="Hàm lượng Menthol cao giúp giãn cơ trơn đường tiêu hóa và giảm đầy hơi, khó tiêu."),
    # 7. Thì là (Dill) - Cặp bài trùng của các món cá
    F("Thì là", "Dill", "fiber", 43, 3.5, 7.0, 1.1, desc="Giàu hợp chất monoterpene giúp bảo vệ tế bào và kích thích tiết sữa cho phụ nữ sau sinh."),
    # 8. Diếp cá (Fish Mint) - Thanh nhiệt, kháng sinh
    F("Diếp cá", "Fish Mint", "fiber", 18, 2.1, 2.5, 0.2, desc="Mùi tanh đặc trưng nhưng là vị thuốc quý giúp kháng viêm, lợi tiểu và trị táo bón."),
    
    # 1. Cải Bắp (Cabbage) - Loại rau quốc dân
    F("Cải bắp", "Cabbage", "fiber", 25, 1.3, 5.8, 0.1, desc="Giàu Vitamin K và Vitamin C. Chứa hợp chất lưu huỳnh hỗ trợ sức khỏe dạ dày."),
    # 2. Cải Thảo (Napa Cabbage) - Linh hồn của Kimchi
    F("Cải thảo", "Napa Cabbage", "fiber", 13, 1.1, 2.2, 0.1, desc="Lượng calo cực thấp, vị ngọt thanh, rất giàu folate và canxi."),
    # 3. Cải Thìa / Cải Chíp (Bok Choy)
    F("Cải thìa", "Bok Choy", "fiber", 13, 1.5, 2.2, 0.2, desc="Nguồn cung cấp Quercetin chống viêm hiệu quả. Một trong những loại rau giàu Canxi nhất."),
    # 4. Cải Ngọt (Choy Sum) - Phổ biến trong món xào
    F("Cải ngọt", "Choy Sum", "fiber", 16, 1.5, 3.0, 0.2, desc="Chứa nhiều chất xơ giúp nhuận tràng, giàu Kali và Vitamin B nhóm."),
    # 5. Cải Bẹ Xanh (Mustard Greens) - Vị cay nồng đặc trưng
    F("Cải bẹ xanh", "Mustard Greens", "fiber", 27, 2.9, 4.7, 0.4, desc="Giàu Myrosinase - một loại enzyme giúp kích hoạt các chất chống ung thư."),
    # 6. Cải Xoăn (Kale) - Siêu thực phẩm (Superfood)
    F("Cải xoăn (Kale)", "Kale", "fiber", 49, 4.3, 8.8, 0.9, desc="Mật độ dinh dưỡng cực cao. Hàm lượng Vitamin A, K, C vượt trội so với tất cả các loại cải khác."),
    
    # 1. Bông cải xanh (Broccoli) - Siêu thực phẩm giải độc
    F("Bông cải xanh", "Broccoli", "fiber", 34, 2.8, 6.6, 0.4, desc="Giàu Sulforaphane giúp chống ung thư, chứa nhiều Vitamin C và K."),
    # 2. Súp lơ trắng (Cauliflower) - Thay thế tinh bột tuyệt vời
    F("Súp lơ trắng", "Cauliflower", "fiber", 25, 1.9, 5.0, 0.3, desc="Hàm lượng Choline cao tốt cho trí não. Thường dùng làm giả cơm hoặc đế bánh pizza."),
    # 3. Bông Bí (Pumpkin Flowers) - Giàu Vitamin A
    F("Bông bí", "Pumpkin Flowers", "fiber", 15, 1.0, 3.3, 0.1, desc="Chứa nhiều Beta-carotene tốt cho mắt và da. Vị ngọt, bùi, giòn nhẹ."),
    # 4. Bông So Đũa (Sesbania Grandiflora) - Đặc sản miền Tây
    F("Bông so đũa", "Sesbania Flower", "fiber", 27, 1.3, 5.5, 0.2, desc="Vị nhẫn nhẹ, hậu ngọt. Giàu Vitamin B và sắt, có tác dụng trị cảm và nhuận tràng."),
    # 5. Bông Điên Điển (Sesbania Sesban) - Linh hồn mùa nước nổi
    F("Bông điên điển", "Sesbania Sesban Flower", "fiber", 20, 1.5, 3.0, 0.1, desc="Giàu chất xơ và vitamin, thường dùng nấu canh chua hoặc làm gỏi."),
    # 6. Atiso (Artichoke) - Thần dược cho gan
    F("Atiso (Phần nạc hoa)", "Artichoke", "fiber", 47, 3.3, 10.5, 0.2, desc="Chứa Cynarin và Silymarin cực tốt cho gan. Hàm lượng chất xơ thuộc hàng cao nhất trong các loại rau."),
    
    # 1. Bầu (Bottle Gourd) - Thanh nhiệt, giải độc
    F("Bầu", "Bottle Gourd", "fiber", 14, 0.6, 3.4, 0.1, desc="Chứa tới 95% nước, vị ngọt tính hàn. Giàu Vitamin C và các hợp chất ngăn ngừa lão hóa."),
    # 2. Bí Đao (Wax Gourd) - Khắc tinh của mỡ thừa
    F("Bí đao", "Wax Gourd", "fiber", 13, 0.4, 3.0, 0.1, desc="Chứa axit propanedioic giúp ức chế sự chuyển hóa đường thành mỡ, hỗ trợ giảm cân."),
    # 3. Bí Đỏ / Bí Ngô (Pumpkin) - Nguồn Vitamin A khổng lồ
    F("Bí đỏ", "Pumpkin", "fiber", 26, 1.0, 6.5, 0.1, desc="Giàu Beta-carotene và Lutein tốt cho mắt. Lượng tinh bột cao hơn các loại bầu bí khác."),
    # 4. Mướp Hương (Luffa) - Thơm tho và nhuận tràng
    F("Mướp hương", "Luffa", "fiber", 20, 0.9, 4.3, 0.2, desc="Chứa nhiều chất nhầy pectin và Vitamin B, giúp làm đẹp da và hỗ trợ tiêu hóa."),
    # 5. Khổ Qua (Bitter Melon) - Kháng sinh tự nhiên cho đường huyết
    F("Khổ qua", "Bitter Melon", "fiber", 17, 1.0, 3.7, 0.2, desc="Chứa Charantin và Polypeptide-p giúp hạ đường huyết tự nhiên. Vị đắng đặc trưng giúp giải độc gan."),
    # 6. Dưa Leo (Cucumber) - Cấp ẩm và làm mát
    F("Dưa leo", "Cucumber", "fiber", 15, 0.7, 3.6, 0.1, desc="Nguồn cung cấp Silica giúp tóc và móng chắc khỏe. Vỏ dưa leo chứa nhiều chất xơ và Vitamin K."),

    # 1. Cà chua (Tomato) - Nguồn Lycopene dồi dào
    F("Cà chua", "Tomato", "fiber", 18, 0.9, 3.9, 0.2, desc="Giàu Lycopene giúp bảo vệ tim mạch và làn da. Hàm lượng Vitamin C cao."),
    # 2. Cà tím (Eggplant) - Chất chống oxy hóa từ lớp vỏ
    F("Cà tím", "Eggplant", "fiber", 25, 1.0, 5.9, 0.2, desc="Vỏ chứa Nasunin giúp bảo vệ tế bào não. Thớ thịt xốp, giàu chất xơ hòa tan."),
    # 3. Ớt chuông Đỏ (Red Bell Pepper) - Vua Vitamin C
    F("Ớt chuông đỏ", "Red Bell Pepper", "fiber", 31, 1.0, 6.0, 0.3, desc="Chứa lượng Vitamin C gấp 3 lần cam. Giàu Beta-carotene và Quercetin."),
    # 4. Ớt chuông Xanh (Green Bell Pepper)
    F("Ớt chuông xanh", "Green Bell Pepper", "fiber", 20, 0.9, 4.6, 0.2, desc="Là ớt chuông chưa chín hẳn, vị hơi hăng đắng nhẹ, ít đường hơn ớt đỏ."),
    # 5. Ớt chuông Vàng (Yellow Bell Pepper)
    F("Ớt chuông vàng", "Yellow Bell Pepper", "fiber", 27, 1.0, 6.3, 0.2, desc="Vị ngọt thanh, giàu Lutein và Zeaxanthin rất tốt cho sức khỏe thị lực."),
    # 6. Ớt cay (Chili Pepper) - Tăng cường trao đổi chất
    F("Ớt cay", "Chili Pepper", "fiber", 40, 1.9, 8.8, 0.4, desc="Chứa Capsaicin giúp giảm đau, đốt cháy mỡ thừa và thông đường hô hấp."),
    
    # 1. Đậu bắp (Okra) - "Vua" chất nhầy hữu ích
    F("Đậu bắp", "Okra", "fiber", 33, 1.9, 7.5, 0.2, desc="Giàu chất xơ hòa tan (mucilage) giúp kiểm soát đường huyết và bảo vệ niêm mạc dạ dày."),
    # 2. Bắp non / Ngô bao tử (Baby Corn)
    F("Bắp non", "Baby Corn", "fiber", 26, 2.3, 5.2, 0.2, desc="Là ngô thu hoạch sớm. Ít tinh bột và calo hơn ngô già, giàu chất xơ và Vitamin B."),
    # 3. Măng tây (Asparagus) - Rau cao cấp giàu Folate
    F("Măng tây", "Asparagus", "fiber", 20, 2.2, 3.9, 0.1, desc="Chứa axit amin asparagine giúp lợi tiểu và prebiotic tốt cho vi khuẩn đường ruột."),
    # 4. Giá đỗ (Bean Sprouts) - Năng lượng nảy mầm
    F("Giá đỗ (Đậu xanh)", "Mung Bean Sprouts", "fiber", 30, 3.0, 5.9, 0.2, desc="Rất giàu Vitamin C và enzyme tiêu hóa. Calo thấp nhưng mật độ dinh dưỡng cao."),
    # 5. Hoa chuối (Banana Blossom) - Giàu chất xơ và sắt
    F("Hoa chuối", "Banana Blossom", "fiber", 51, 1.6, 9.9, 0.6, desc="Nguồn cung cấp chất xơ tuyệt vời, giúp hạ đường huyết và giảm tình trạng thiếu máu."),
    
    # 1. Cà rốt (Carrot) - "Vua" Vitamin A
    F("Cà rốt", "Carrot", "fiber", 41, 0.9, 9.6, 0.2, desc="Chứa hàm lượng Beta-carotene cực cao, tốt cho mắt và miễn dịch. Chất xơ hòa tan giúp giảm cholesterol."),
    # 2. Củ cải trắng (White Radish/Daikon) - "Nhân sâm trắng"
    F("Củ cải trắng", "White Radish", "fiber", 18, 0.6, 4.1, 0.1, desc="Giàu enzyme tiêu hóa (diastase) giúp chuyển hóa tinh bột. Vị cay nhẹ có tác dụng long đờm."),
    # 3. Củ cải đỏ (Radish)
    F("Củ cải đỏ", "Radish", "fiber", 16, 0.7, 3.4, 0.1, desc="Chứa nhiều anthocyanin và catechin, hỗ trợ bảo vệ tim mạch và chống viêm."),
    # 4. Củ dền (Beetroot) - Tăng cường lưu thông máu
    F("Củ dền", "Beetroot", "fiber", 43, 1.6, 9.6, 0.2, desc="Giàu Nitrate tự nhiên giúp giãn mạch máu, hạ huyết áp và tăng sức bền thể lực."),
    # 5. Su hào (Kohlrabi) - Rau họ Cải dạng củ
    F("Su hào", "Kohlrabi", "fiber", 27, 1.7, 6.2, 0.1, desc="Thực chất là phần thân phình to. Cực kỳ giàu Vitamin C (gần bằng cam) và chất xơ."),
    # 6. Hành tây (Onion) - Bảo vệ tim mạch
    F("Hành tây", "Onion", "fiber", 40, 1.1, 9.3, 0.1, desc="Giàu Quercetin chống oxy hóa. Giúp loãng máu và giảm nguy cơ xơ vữa động mạch."),
    # 7. Tỏi (Garlic) - Kháng sinh Allicin
    F("Tỏi", "Garlic", "fiber", 149, 6.4, 33.1, 0.5, desc="Mật độ dinh dưỡng cực cao. Chứa Allicin giúp diệt khuẩn, hạ mỡ máu và tăng đề kháng."),
    # 8. Gừng (Ginger) - Chống nôn và ấm bụng
    F("Gừng", "Ginger", "fiber", 80, 1.8, 17.8, 0.8, desc="Chứa Gingerol giúp giảm đau cơ, kháng viêm và kích thích hệ tiêu hóa."),
    # 9. Nghệ (Turmeric) - Hoạt chất Curcumin
    F("Nghệ", "Turmeric", "fiber", 312, 7.8, 67.1, 3.3, desc="Nổi tiếng với Curcumin giúp chữa lành vết loét dạ dày và chống oxy hóa tế bào."),
    # 10. Riềng (Galangal)
    F("Riềng", "Galangal", "fiber", 71, 1.0, 15.0, 1.0, desc="Họ gừng nhưng vị cay nồng hơn. Giúp giảm đầy hơi và ngăn ngừa nhiễm trùng."),
    
    # 1. Măng tây (Asparagus) - Rau cao cấp giàu Folate
    F("Măng tây", "Asparagus", "fiber", 20, 2.2, 3.9, 0.1, desc="Chứa axit amin asparagine giúp lợi tiểu tự nhiên và giàu chất xơ prebiotic tốt cho hệ vi sinh đường ruột."),
    # 2. Măng tươi (Bamboo Shoots) - Giòn ngọt và giàu Kali
    F("Măng tươi", "Bamboo Shoots", "fiber", 27, 2.6, 5.2, 0.3, desc="Hàm lượng chất xơ cực cao giúp nhuận tràng. Giàu Kali tốt cho huyết áp."),
    # 3. Dọc mùng / Bạc hà (Taro Stems) - Cấu trúc xốp đặc biệt
    F("Dọc mùng", "Taro Stems", "fiber", 5, 0.3, 1.0, 0.0, desc="Calo cực thấp (gần như bằng 0). Cấu trúc xốp giúp thấm hút nước dùng, rất giàu phosphor và kali."),
    # 4. Cần tây (Celery) - Thực phẩm "Calo âm"
    F("Cần tây", "Celery", "fiber", 16, 0.7, 3.0, 0.2, desc="Chứa Apigenin và Luteolin giúp hạ huyết áp và kháng viêm. Đứng đầu về khả năng cấp nước và thanh lọc."),
    # 5. Ngó sen (Lotus Stem) - Thanh mát và sạch ruột
    F("Ngó sen", "Lotus Stem", "fiber", 74, 2.6, 17.0, 0.1, desc="Cung cấp nhiều Vitamin C và sắt. Có tác dụng an thần, giúp ngủ ngon và cầm máu nhẹ."),
    
    # 1. Nấm Rơm - Đặc sản nhiệt đới
    F("Nấm rơm", "Straw Mushroom", "protein", 32, 3.8, 4.6, 0.7, desc="Giàu Vitamin C và các axit amin thiết yếu. Có tính hàn, giúp thanh nhiệt."),
    # 2. Nấm Kim Châm - Giòn và tốt cho trí não
    F("Nấm kim châm", "Enoki Mushroom", "protein", 37, 2.7, 7.8, 0.3, desc="Giàu Lysine giúp phát triển trí tuệ trẻ em và Ergothioneine chống oxy hóa."),
    # 3. Nấm Hương / Đông Cô - "Hoàng hậu" của các loại nấm
    F("Nấm hương", "Shiitake Mushroom", "protein", 34, 2.2, 6.8, 0.5, desc="Chứa Lentinan giúp tăng cường miễn dịch và Eritadenine giúp hạ cholesterol."),
    # 4. Nấm Đùi Gà - Kết cấu như thịt
    F("Nấm đùi gà", "King Oyster Mushroom", "protein", 35, 3.3, 6.0, 0.4, desc="Thân chắc, vị bùi. Giàu chất xơ và Kali, giúp ổn định huyết áp."),
    # 5. Nấm Bào Ngư / Nấm Sò
    F("Nấm bào ngư", "Oyster Mushroom", "protein", 33, 3.3, 6.0, 0.4, desc="Chứa Lovastatin tự nhiên tốt cho tim mạch. Nguồn cung cấp kẽm và sắt dồi dào."),
    # 6. Nấm Mỡ (Trắng/Nâu)
    F("Nấm mỡ", "Button Mushroom", "protein", 22, 3.1, 3.3, 0.3, desc="Nguồn Vitamin D thực vật duy nhất (khi tiếp xúc ánh sáng mặt trời) và giàu Selen."),
    # 7. Mộc Nhĩ / Nấm Mèo - Giòn và bổ máu
    F("Mộc nhĩ (tươi)", "Wood Ear Mushroom", "protein", 25, 1.0, 6.0, 0.2, desc="Hàm lượng sắt cực cao. Có tác dụng chống đông máu và làm sạch mạch máu."),
    # 8. Nấm Tuyết / Ngân Nhĩ - "Yến sào" của người nghèo
    F("Nấm tuyết (tươi)", "Snow Fungus", "protein", 22, 0.5, 5.0, 0.1, desc="Giàu Polysaccharide giúp dưỡng ẩm da và tốt cho hệ hô hấp."),
    
    # ===== Fruits =====
    
    # 1. Cam (Orange) - Phổ biến và cân bằng
    F("Cam (Navel/Cao Phong)", "Orange", "fruit", 47, 0.9, 11.8, 0.1, desc="Giàu Vitamin C và Hesperidin giúp bền thành mạch. Cam sành thường nhiều nước và chua hơn."),
    # 2. Quýt (Mandarin/Tangerine) - Ngọt và dễ bóc vỏ
    F("Quýt", "Mandarin", "fruit", 53, 0.8, 13.3, 0.3, desc="Hàm lượng đường cao hơn cam, giàu Vitamin A dưới dạng Beta-carotene."),
    # 3. Tắc / Quất (Kumquat) - Ăn được cả vỏ
    F("Tắc (Quất)", "Kumquat", "fruit", 71, 1.9, 15.9, 0.9, desc="Đặc biệt vì tinh dầu ở vỏ chứa nhiều chất kháng viêm, thường dùng trị ho."),
    # 4. Bưởi (Pomelo/Grapefruit) - Thực phẩm hỗ trợ giảm cân
    F("Bưởi (Năm Roi/Da Xanh)", "Pomelo", "fruit", 38, 0.8, 9.6, 0.0, desc="Chỉ số GI cực thấp. Chứa Lycopene (ở bưởi hồng) và giúp đốt cháy mỡ thừa hiệu quả."),
    # 5. Chanh xanh (Lime) - Độ chua cao, giàu axit citric
    F("Chanh xanh", "Lime", "fruit", 30, 0.7, 10.5, 0.2, desc="Nguồn cung cấp axit citric dồi dào, giúp tăng cường hấp thụ sắt từ thực vật."),
    # 6. Chanh vàng (Lemon) - Hương thơm thanh khiết
    F("Chanh vàng", "Lemon", "fruit", 29, 1.1, 9.3, 0.3, desc="Vỏ dày, mùi thơm dịu, thường dùng trong các công thức detox và làm bánh."),
    
    # 1. Táo (Apple) - "Mỗi ngày một quả táo, bác sĩ không đến nhà"
    F("Táo", "Apple", "fruit", 52, 0.3, 13.8, 0.2, desc="Giàu Pectin giúp hạ cholesterol và Quercetin chống viêm. Nên ăn cả vỏ để lấy chất xơ."),
    # 2. Lê (Pear) - Cực kỳ giàu chất xơ
    F("Lê", "Pear", "fruit", 57, 0.4, 15.2, 0.1, desc="Chất xơ rất cao giúp nhuận tràng. Vị ngọt thanh, tính mát, hỗ trợ giảm ho và thanh phế."),
    # 3. Đào (Peach) - Thơm ngọt và bổ da
    F("Đào", "Peach", "fruit", 39, 0.9, 9.5, 0.3, desc="Giàu Kali và Vitamin C. Chứa các hợp chất phenolic giúp chống lão hóa da."),
    # 4. Mận (Plum) - Hỗ trợ tiêu hóa tuyệt vời
    F("Mận", "Plum", "fruit", 46, 0.7, 11.4, 0.3, desc="Chứa Sorbitol tự nhiên giúp nhuận tràng hiệu quả. Mận đỏ chứa nhiều Anthocyanin."),
    # 5. Mơ (Apricot) - "Kho" Vitamin A
    F("Mơ", "Apricot", "fruit", 48, 1.4, 11.1, 0.4, desc="Hàm lượng Beta-carotene cực cao, cực tốt cho thị lực và hệ miễn dịch."),
    # 6. Anh đào (Cherry) - Chống viêm và cải thiện giấc ngủ
    F("Anh đào", "Cherry", "fruit", 50, 1.0, 12.0, 0.3, desc="Giàu Melatonin tự nhiên giúp ngủ ngon và các chất chống oxy hóa giúp giảm đau cơ."),
    
    # 1. Chuối (Banana) - Nguồn Kali và năng lượng tức thì
    F("Chuối", "Banana", "fruit", 89, 1.1, 22.8, 0.3, desc="Giàu Kali tốt cho tim mạch. Chuối chín chứa nhiều đường, chuối xanh chứa nhiều tinh bột kháng."),
    # 2. Xoài (Mango) - Vua của các loại quả nhiệt đới
    F("Xoài chín", "Mango", "fruit", 60, 0.8, 15.0, 0.4, desc="Cực kỳ giàu Vitamin A và Vitamin C. Chứa các enzyme hỗ trợ tiêu hóa protein."),
    # 3. Đu đủ (Papaya) - Siêu thực phẩm cho hệ tiêu hóa
    F("Đu đủ", "Papaya", "fruit", 43, 0.5, 10.8, 0.3, desc="Chứa enzyme papain giúp phân giải protein dạ dày. Giàu Beta-carotene và Lycopene."),
    # 4. Dứa / Thơm (Pineapple) - Kháng viêm tự nhiên
    F("Dứa (Thơm)", "Pineapple", "fruit", 50, 0.5, 13.1, 0.1, desc="Chứa Bromelain có tác dụng kháng viêm và hỗ trợ tiêu hóa mạnh mẽ."),
    # 5. Thanh long (Dragon Fruit) - Giàu chất xơ và hạt bổ não
    F("Thanh long", "Dragon Fruit", "fruit", 60, 1.2, 13.0, 1.5, desc="Hạt nhỏ chứa Omega-3, Omega-9 tốt cho tim. Thanh long ruột đỏ giàu Anthocyanin hơn."),
    # 6. Vú sữa (Star Apple)
    F("Vú sữa", "Star Apple", "fruit", 64, 1.0, 14.5, 0.4, desc="Vị ngọt dịu, chứa nhiều Canxi và sắt, tốt cho phụ nữ mang thai."),
    # 7. Sabôchê / Hồng xiêm (Sapodilla)
    F("Sabôchê", "Sapodilla", "fruit", 83, 0.4, 20.0, 1.1, desc="Rất giàu chất xơ (5.3g/100g) và tannin giúp kháng viêm đường ruột."),
    # 8. Sầu riêng (Durian) - Vua của các loại quả
    F("Sầu riêng", "Durian", "fruit", 147, 1.5, 27.1, 5.3, desc="Năng lượng cực cao. Giàu chất béo không bão hòa và các hợp chất lưu huỳnh tốt cho sức khỏe."),
    # 9. Mít (Jackfruit)
    F("Mít chín", "Jackfruit", "fruit", 95, 1.7, 23.2, 0.6, desc="Giàu Vitamin B6 và Magie. Xơ mít cũng chứa nhiều dinh dưỡng và chất xơ."),
    # 10. Vải (Lychee)
    F("Vải thiều", "Lychee", "fruit", 66, 0.8, 16.5, 0.4, desc="Hàm lượng Vitamin C cực cao, giàu polyphenol giúp bảo vệ mạch máu."),
    # 11. Nhãn (Longan)
    F("Nhãn", "Longan", "fruit", 60, 1.3, 15.1, 0.1, desc="Vị ngọt đậm, theo Đông y có tác dụng an thần, bồi bổ tâm tỳ."),
    # 12. Măng cụt (Mangosteen) - "Nữ hoàng" trái cây
    F("Măng cụt", "Mangosteen", "fruit", 73, 0.4, 18.0, 0.6, desc="Vỏ chứa Xanthones - chất chống oxy hóa cực mạnh giúp kháng viêm và diệt khuẩn."),
    
    # 1. Dâu tây (Strawberry) - Vua Vitamin C trong nhóm mọng
    F("Dâu tây", "Strawberry", "fruit", 32, 0.7, 7.7, 0.3, desc="Giàu Vitamin C và Folate. Chứa Pelargonidin giúp kiểm soát đường huyết hiệu quả."),
    # 2. Việt quất (Blueberry) - Siêu thực phẩm cho não bộ
    F("Việt quất", "Blueberry", "fruit", 57, 0.7, 14.5, 0.3, desc="Hàm lượng Anthocyanin cực cao, giúp cải thiện trí nhớ và ngăn ngừa suy giảm nhận thức."),
    # 3. Mâm xôi (Raspberry) - Nhà vô địch về chất xơ
    F("Mâm xôi", "Raspberry", "fruit", 52, 1.2, 11.9, 0.7, desc="Chứa tới 6.5g chất xơ/100g. Giàu Ellagitannins giúp kháng viêm và chống ung thư."),
    # 4. Nho Đỏ/Đen (Red/Black Grapes) - Tốt cho tim mạch
    F("Nho đỏ/đen", "Grapes", "fruit", 69, 0.7, 18.1, 0.2, desc="Vỏ và hạt chứa Resveratrol - hoạt chất vàng giúp bảo vệ tim và chống lão hóa."),
    # 5. Dâu tằm (Mulberry) - Vị thuốc dân dã
    F("Dâu tằm", "Mulberry", "fruit", 43, 1.4, 9.8, 0.4, desc="Giàu sắt và Vitamin C. Giúp bổ máu, đen tóc và hỗ trợ giấc ngủ theo Đông y."),
    
    # 1. Dưa hấu (Watermelon) - Cấp nước và phục hồi cơ bắp
    F("Dưa hấu", "Watermelon", "fruit", 30, 0.6, 7.6, 0.2, desc="Chứa 92% nước. Giàu Lycopene (nhiều hơn cả cà chua) và Citrulline giúp giảm đau nhức cơ bắp."),
    # 2. Dưa lưới (Cantaloupe) - "Kho" Vitamin A
    F("Dưa lưới (vàng)", "Cantaloupe", "fruit", 34, 0.8, 8.2, 0.2, desc="Màu cam đặc trưng cho thấy hàm lượng Beta-carotene cực cao. Giàu Vitamin C và Kali."),
    # 3. Dưa lê (Honeydew) - Ngọt thanh và giàu khoáng chất
    F("Dưa lê", "Honeydew Melon", "fruit", 36, 0.5, 9.1, 0.1, desc="Chứa nhiều Vitamin C, B6 và Folate. Lớp vỏ sát thịt quả chứa nhiều khoáng chất nhất."),
    # 4. Dưa gang (Oriental Pickling Melon) - Thanh nhiệt bậc nhất
    F("Dưa gang", "Oriental Melon", "fruit", 26, 0.6, 6.0, 0.1, desc="Vị nhạt, tính hàn. Thường dùng dầm đường hoặc đá để giải nhiệt mùa hè, rất lợi tiểu."),
    
    # 1. Bơ (Avocado) - "Bơ sáp" / Bơ Hass
    F("Trái Bơ", "Avocado", "fat", 160, 2.0, 8.5, 14.7, desc="Giàu axit oleic (chất béo đơn không bão hòa) giúp giảm viêm và tốt cho tim. Cực kỳ ít đường, giàu Kali và chất xơ."),
    # 2. Cơm dừa / Thịt dừa già (Coconut Meat)
    F("Cơm dừa (Già)", "Coconut Meat", "fat", 354, 3.3, 15.2, 33.5, desc="Chứa chất béo trung tính chuỗi trung bình (MCTs) giúp cung cấp năng lượng nhanh. Giàu mangan và đồng."),
    # 3. Cơm dừa non (Young Coconut Meat)
    F("Cơm dừa non", "Young Coconut Meat", "fat", 110, 1.5, 10.0, 7.0, desc="Mềm mỏng, lượng béo và calo thấp hơn nhiều so với dừa già, vị ngọt thanh."),
    
    # ===== Dairy =====
    
    # 1. Sữa bò nguyên kem (Whole Milk)
    F("Sữa bò nguyên kem", "Whole Milk", "protein", 61, 3.2, 4.8, 3.3, desc="Giữ nguyên lớp béo tự nhiên, giàu Vitamin A và D tan trong dầu. Tốt cho trẻ em đang lớn."),
    # 2. Sữa bò ít béo (Low-fat 1-2%)
    F("Sữa bò ít béo", "Low-fat Milk", "protein", 43, 3.4, 5.0, 1.0, desc="Cân bằng giữa calo và dinh dưỡng, thường được bổ sung thêm Vitamin D."),
    # 3. Sữa bò tách béo (Skim Milk)
    F("Sữa bò tách béo", "Skim Milk", "protein", 35, 3.4, 5.1, 0.1, desc="Gần như không chứa béo, calo thấp nhất. Phù hợp cho người giảm cân hoặc mỡ máu cao."),
    # 4. Sữa dê (Goat Milk)
    F("Sữa dê", "Goat Milk", "protein", 69, 3.6, 4.5, 4.1, desc="Chứa nhiều acid béo chuỗi ngắn dễ tiêu hóa hơn sữa bò. Ít gây dị ứng hơn với một số người."),
    # 5. Sữa bột nguyên kem
    F("Sữa bột nguyên kem", "Whole Milk Powder", "protein", 496, 26.3, 38.4, 26.7, desc="Dạng khô cô đặc, giàu năng lượng. Tiện lợi cho việc lưu trữ và pha chế."),
    # 6. Sữa đặc có đường (Sweetened Condensed Milk)
    F("Sữa đặc có đường", "Condensed Milk", "carbs", 322, 7.9, 54.4, 8.7, desc="Lượng đường cực cao (thường chiếm >40%). Chủ yếu dùng để pha cà phê hoặc làm bánh."),
    # 7. Sữa đặc không đường (Evaporated Milk)
    F("Sữa cô đặc (Không đường)", "Evaporated Milk", "protein", 134, 6.8, 10.0, 7.6, desc="Sữa tươi được đun nóng để bay hơi 60% nước. Có vị béo ngậy và màu hơi kem, không ngọt sắc."),
    
    # 1. Sữa chua Hy Lạp (Greek Yogurt) - "Siêu thực phẩm" giàu đạm
    F("Sữa chua Hy Lạp (Nguyên bản)", "Greek Yogurt", "protein", 97, 9.0, 4.0, 5.0, desc="Đã được tách nước sữa (whey), làm tăng gấp đôi lượng đạm so với sữa chua thường. Kết cấu đặc mịn, ít đường."),
    # 2. Sữa chua thường (Nguyên chất/Không đường)
    F("Sữa chua không đường", "Plain Yogurt", "protein", 63, 3.5, 5.0, 3.3, desc="Giàu Canxi và lợi khuẩn Lactobacillus. Phù hợp để ăn hàng ngày hỗ trợ tiêu hóa."),
    # 3. Nấm sữa Kefir - Thức uống lên men quyền năng
    F("Kefir", "Kefir", "protein", 55, 3.3, 4.0, 3.0, desc="Chứa tới 30-50 chủng lợi khuẩn và nấm men khác nhau, đa dạng hơn hẳn sữa chua thường."),
    # 4. Váng sữa (Milk Skin/Creamer) - Năng lượng cho trẻ nhỏ
    F("Váng sữa", "Milk Skin", "fat", 180, 2.5, 12.0, 13.5, desc="Thành phần chủ yếu là chất béo và protein sữa, cung cấp nhiều năng lượng và Canxi."),
    # 5. Sữa chua uống (Probiotic Drink)
    F("Sữa chua uống", "Drinking Yogurt", "carbs", 70, 1.2, 15.0, 0.8, desc="Thường được bổ sung thêm nhiều đường để cân bằng vị chua. Tập trung vào các chủng lợi khuẩn cụ thể."),
    
    # 1. Phô mai tươi (Fresh) - Mozzarella
    F("Mozzarella tươi", "Fresh Mozzarella", "protein", 280, 22.2, 2.2, 20.0, desc="Độ ẩm cao, vị nhẹ. Giàu lợi khuẩn Lactobacillus fermentum tốt cho miễn dịch."),
    # 2. Phô mai cứng (Hard) - Parmesan
    F("Parmesan (Reggiano)", "Parmesan Cheese", "protein", 431, 38.5, 4.1, 28.5, desc="Vua của các loại phô mai về Canxi và Protein. Rất ít lactose do quá trình ủ lâu (12-36 tháng)."),
    # 3. Phô mai bán cứng (Semi-hard) - Cheddar
    F("Cheddar", "Cheddar Cheese", "protein", 403, 24.9, 1.3, 33.3, desc="Phổ biến nhất thế giới. Nguồn cung cấp Vitamin K2 tuyệt vời cho sức khỏe xương và tim."),
    # 4. Phô mai mềm (Soft) - Brie/Camembert
    F("Phô mai Brie", "Brie Cheese", "fat", 334, 20.8, 0.5, 27.7, desc="Vỏ mốc trắng đặc trưng, béo ngậy. Giàu Vitamin B12 và Riboflavin."),
    # 5. Phô mai xanh (Blue) - Gorgonzola
    F("Phô mai xanh", "Blue Cheese", "protein", 353, 21.4, 2.3, 28.7, desc="Chứa nấm men Penicillium, có đặc tính kháng viêm mạnh và hương vị cực kỳ nồng đậm."),
    # 6. Phô mai chế biến (Processed) - Phô mai miếng
    F("Phô mai lát (Chế biến)", "Processed Cheese", "fat", 327, 18.0, 5.0, 25.0, desc="Được trộn thêm muối nhũ hóa. Tiện lợi, giàu canxi nhưng thường chứa nhiều natri hơn phô mai tự nhiên."),
    
    # 1. Bơ lạt (Unsalted Butter) - Chuẩn mực trong làm bánh
    F("Bơ lạt", "Unsalted Butter", "fat", 717, 0.9, 0.1, 81.1, desc="Chứa tối thiểu 80% béo sữa. Giàu Vitamin A và axit butyric tốt cho sức khỏe đường ruột."),
    # 2. Bơ mặn (Salted Butter)
    F("Bơ mặn", "Salted Butter", "fat", 713, 0.9, 0.1, 80.6, desc="Tương tự bơ lạt nhưng được thêm khoảng 1.5-2% muối để bảo quản và tăng hương vị."),
    # 3. Heavy Cream - Đậm đặc chất béo
    F("Heavy Cream", "Heavy Cream", "fat", 340, 2.8, 2.6, 36.0, desc="Chứa hàm lượng béo cao nhất trong các loại kem lỏng, dễ đánh bông và giữ form tốt."),
    # 4. Whipping Cream - Phổ biến nhất
    F("Whipping Cream", "Whipping Cream", "fat", 292, 2.2, 3.0, 30.0, desc="Độ béo vừa phải để tạo bọt khí, là nền tảng cho các loại kem trang trí và súp Âu."),
    # 5. Kem chua (Sour Cream) - Lên men béo sữa
    F("Kem chua", "Sour Cream", "fat", 193, 2.1, 4.6, 18.0, desc="Kem tươi được lên men bởi vi khuẩn lactic, có vị chua nhẹ, kết cấu đặc, giàu lợi khuẩn."),
    
    # ===== Eggs & Nuts =====
    
    # 1. Trứng gà - Cân bằng nhất
    F("Trứng gà", "Chicken Egg", "protein", 143, 12.6, 0.7, 9.5, desc="Chứa Choline cực tốt cho não bộ và Lutein/Zeaxanthin tốt cho mắt. Trứng gà ta thường có tỷ lệ lòng đỏ cao hơn."),
    # 2. Trứng vịt - Béo và đậm đà hơn
    F("Trứng vịt", "Duck Egg", "protein", 185, 12.8, 1.5, 13.8, desc="Lượng calo và chất béo cao hơn trứng gà. Lòng đỏ lớn, giàu Vitamin B12 và Omega-3."),
    # 3. Trứng cút - Nhỏ nhưng có võ
    F("Trứng cút", "Quail Egg", "protein", 158, 13.0, 0.4, 11.1, desc="Mật độ dinh dưỡng cao. Chứa nhiều sắt và Vitamin B2 hơn trứng gà nếu tính theo cùng trọng lượng."),
    # 4. Trứng ngỗng - Năng lượng khổng lồ
    F("Trứng ngỗng", "Goose Egg", "protein", 185, 13.9, 1.3, 13.3, desc="Kích thước lớn gấp 3-4 lần trứng gà. Rất giàu Folate và khoáng chất, vị béo ngậy."),
    # 5. Lòng trắng trứng - Đạm tinh khiết
    F("Lòng trắng trứng", "Egg White", "protein", 52, 10.9, 0.7, 0.2, desc="Gần như không chứa chất béo và cholesterol. Là nguồn đạm lý tưởng để xây dựng cơ bắp."),
    # 6. Lòng đỏ trứng - Kho báu dinh dưỡng
    F("Lòng đỏ trứng", "Egg Yolk", "fat", 322, 15.9, 3.6, 26.5, desc="Nơi tập trung toàn bộ vitamin (A, D, E, K), khoáng chất và chất béo. Chứa hàm lượng Cholesterol cao."),
    # 7. Trứng muối - Đậm đà, giàu canxi
    F("Trứng vịt muối", "Salted Duck Egg", "protein", 182, 13.0, 1.5, 13.5, desc="Quá trình muối làm tăng hàm lượng canxi nhưng cũng làm tăng vọt lượng Natri (muối)."),
    # 8. Trứng Bắc thảo - Hương vị độc đáo
    F("Trứng Bắc thảo", "Century Egg", "protein", 160, 13.1, 1.0, 10.7, desc="Trứng được ủ trong hỗn hợp kiềm. Protein được phân giải một phần nên dễ hấp thụ hơn, có mùi ammoniac đặc trưng."),

    # 1. Hạnh nhân (Almond) - Vua Vitamin E
    F("Hạnh nhân", "Almond", "fat", 579, 21.2, 21.6, 49.9, desc="Giàu chất xơ và Vitamin E nhất trong nhóm. Giúp bảo vệ tế bào khỏi stress oxy hóa."),
    # 2. Hạt điều (Cashew) - Giàu sắt và magie
    F("Hạt điều", "Cashew", "fat", 553, 18.2, 30.2, 43.8, desc="Chứa nhiều tinh bột hơn các loại hạt khác. Giàu Sắt, Magie và Kẽm giúp tăng cường miễn dịch."),
    # 3. Óc chó (Walnut) - Thực phẩm cho não bộ
    F("Hạt óc chó", "Walnut", "fat", 654, 15.2, 13.7, 65.2, desc="Nguồn thực vật dẫn đầu về Omega-3 (ALA), giúp giảm viêm và hỗ trợ chức năng não."),
    # 4. Dẻ cười (Pistachio) - Ít calo nhất
    F("Hạt dẻ cười", "Pistachio", "fat", 562, 20.2, 27.5, 45.3, desc="Chứa nhiều Lutein và Zeaxanthin tốt cho mắt. Lượng calo thấp nhất trong nhóm hạt vỏ cứng."),
    # 5. Đậu phộng (Lạc) - Đạm thực vật giá rẻ
    F("Đậu phộng", "Peanut", "fat", 567, 25.8, 16.1, 49.2, desc="Về mặt sinh học là họ Đậu. Giàu Biotin và Resveratrol (giống trong nho đỏ) tốt cho tim."),
    # 6. Hạt mắc ca (Macadamia) - Đỉnh cao chất béo tốt
    F("Hạt mắc ca", "Macadamia", "fat", 718, 7.9, 13.8, 75.8, desc="Chứa lượng béo cao nhất, chủ yếu là chất béo đơn không bão hòa (tương tự dầu olive)."),
    # 7. Hồ đào (Pecan) - Chất chống oxy hóa mạnh
    F("Hạt hồ đào", "Pecan", "fat", 691, 9.2, 13.9, 72.0, desc="Xếp hạng rất cao về khả năng chống oxy hóa trong các loại thực phẩm khô."),
    # 8. Hạt phỉ (Hazelnut) - Tốt cho tim mạch
    F("Hạt phỉ", "Hazelnut", "fat", 628, 15.0, 16.7, 60.8, desc="Giàu Folate và Mangan. Thường được kết hợp với chocolate để tạo hương vị bùi béo."),
    # 9. Hạt thông (Pine nut)
    F("Hạt thông", "Pine nut", "fat", 673, 13.7, 13.1, 68.4, desc="Chứa axit pinolenic giúp kiềm chế cơn đói. Giàu Vitamin K và Magie."),
    
    # 1. Hạt Chia - Nhà vô địch chất xơ và Omega-3
    F("Hạt Chia", "Chia Seeds", "fiber", 486, 16.5, 42.1, 30.7, desc="Chứa lượng Omega-3 thực vật và chất xơ cực cao. Khi ngâm nước tạo lớp gel tốt cho hệ tiêu hóa."),
    # 2. Hạt Lanh (Flaxseed) - Giàu Lignans
    F("Hạt Lanh", "Flaxseed", "fat", 534, 18.3, 28.9, 42.2, desc="Nguồn cung cấp Lignans dồi dào nhất (chất chống oxy hóa giúp cân bằng nội tiết tố). Nên xay nhỏ để hấp thụ tốt nhất."),
    # 3. Hạt Vừng / Mè (Trắng/Đen) - Kho canxi thực vật
    F("Hạt Vừng (Mè)", "Sesame Seeds", "fat", 573, 17.7, 23.5, 49.7, desc="Cực kỳ giàu Canxi và Magie. Vừng đen chứa nhiều chất chống oxy hóa anthocyanin hơn."),
    # 4. Hạt Bí Xanh - "Vua" Kẽm và Magie
    F("Hạt Bí Xanh", "Pumpkin Seeds", "protein", 559, 30.2, 10.7, 49.1, desc="Hàm lượng đạm thực vật rất cao. Giàu Kẽm giúp hỗ trợ tuyến tiền liệt và hệ miễn dịch."),
    # 5. Hạt Hướng Dương - Giàu Vitamin E và Selen
    F("Hạt Hướng Dương", "Sunflower Seeds", "fat", 584, 20.8, 20.0, 51.5, desc="Nguồn cung cấp Vitamin E tuyệt vời bảo vệ màng tế bào. Giàu Selen hỗ trợ chức năng tuyến giáp."),
    # 6. Hạt Gai Dầu (Hemp Seed) - Protein hoàn chỉnh
    F("Hạt Gai Dầu", "Hemp Seeds", "protein", 553, 31.6, 8.7, 48.8, desc="Chứa tỷ lệ Omega-6 và Omega-3 lý tưởng (3:1). Cung cấp protein hoàn chỉnh với đầy đủ 9 axit amin thiết yếu."),
    # 7. Hạt Dưa - Đặc sản ngày Tết
    F("Hạt Dưa", "Watermelon Seeds", "protein", 557, 28.3, 15.3, 47.4, desc="Giàu Magie, Sắt và Kẽm. Là món ăn vặt lành mạnh nếu không tẩm màu hóa học."),
    
    # ===== Fats & Condiments =====
    
    # 1. Dầu Olive Extra Virgin - "Vàng lỏng" của Địa Trung Hải
    F("Dầu Olive (EVOO)", "Extra Virgin Olive Oil", "fat", 884, 0.0, 0.0, 100.0, desc="Ép lạnh cơ học, giữ trọn Polyphenol. Điểm khói thấp (~160-190°C), tốt nhất là ăn trực tiếp hoặc trộn salad."),
    # 2. Dầu Đậu Nành - Phổ biến nhất
    F("Dầu Đậu Nành", "Soybean Oil", "fat", 884, 0.0, 0.0, 100.0, desc="Giàu chất béo đa không bão hòa và Vitamin K. Điểm khói trung bình (~230°C), phù hợp xào nấu hằng ngày."),
    # 3. Dầu Hạt Cải (Canola) - Ít béo bão hòa nhất
    F("Dầu Hạt Cải", "Canola Oil", "fat", 884, 0.0, 0.0, 100.0, desc="Tỷ lệ Omega-6/Omega-3 rất tốt. Điểm khói cao (~200-240°C), đa năng cho nhiều cách chế biến."),
    # 4. Dầu Mè (Vừng) - Hương vị đậm đà
    F("Dầu Mè", "Sesame Oil", "fat", 884, 0.0, 0.0, 100.0, desc="Chứa Sesamol giúp chống oxy hóa mạnh. Thường dùng ướp thực phẩm hoặc thêm vào sau khi nấu để giữ mùi thơm."),
    # 5. Dầu Đậu Phộng (Lạc) - Chuyên gia chiên rán
    F("Dầu Đậu Phộng", "Peanut Oil", "fat", 884, 0.0, 0.0, 100.0, desc="Điểm khói rất cao (~230°C) và không bị lẫn mùi thực phẩm cũ. Lý tưởng cho các món chiên ngập dầu."),
    # 6. Dầu Bơ (Avocado Oil) - Đỉnh cao chịu nhiệt
    F("Dầu Bơ", "Avocado Oil", "fat", 884, 0.0, 0.0, 100.0, desc="Điểm khói cao nhất (~270°C). Giàu chất béo đơn không bão hòa như dầu olive nhưng bền vững với nhiệt hơn."),
    
    # 1. Mỡ lợn (Heo) - "Vàng trắng" trong bếp Việt
    F("Mỡ lợn (Lard)", "Lard", "fat", 900, 0.0, 0.0, 100.0, desc="Giàu Vitamin D và axit oleic. Điểm khói cao (~190°C), tạo độ giòn và hương vị thơm ngon đặc trưng cho món chiên xào."),
    # 2. Mỡ bò (Tallow) - Bí quyết của món bít tết và phở
    F("Mỡ bò", "Beef Tallow", "fat", 902, 0.0, 0.0, 100.0, desc="Rất giàu axit béo bão hòa, cực kỳ bền với nhiệt (điểm khói ~250°C). Chứa CLA giúp hỗ trợ trao đổi chất."),
    # 3. Mỡ gia cầm (Gà/Vịt) - Hương vị tinh tế
    F("Mỡ gà/vịt", "Poultry Fat", "fat", 898, 0.0, 0.0, 99.8, desc="Chứa nhiều chất béo không bão hòa hơn mỡ bò/lợn. Điểm khói trung bình (~175°C), lý tưởng để quay, nướng hoặc làm cơm gà."),
    # 4. Dầu cá (Fish Oil) - Nguồn Omega-3 quý giá
    F("Dầu cá", "Fish Oil", "fat", 902, 0.0, 0.0, 100.0, desc="Cực kỳ giàu EPA và DHA. Không dùng để nấu nướng vì rất dễ bị oxy hóa. Chủ yếu dùng làm thực phẩm bổ sung."),
    
    # 1. Muối - Natri nguyên chất
    F("Muối (Biển/Hồng)", "Salt", "sodium", 0, 0.0, 0.0, 0.0, desc="Chứa khoảng 38,000 - 40,000mg Natri. Muối hồng chứa thêm một ít khoáng chất vi lượng như sắt và magie."),
    # 2. Nước mắm truyền thống - Đạm từ cá
    F("Nước mắm (40 độ đạm)", "Fish Sauce", "sodium", 60, 10.0, 5.0, 0.0, desc="Chứa 7,000 - 9,000mg Natri. Độ đạm càng cao thì hàm lượng axit amin tự nhiên càng phong phú."),
    # 3. Nước tương (Xì dầu) - Gia vị từ đậu nành
    F("Nước tương", "Soy Sauce", "sodium", 53, 8.0, 4.9, 0.1, desc="Chứa khoảng 5,500mg Natri. Tamari là loại nước tương lên men tự nhiên, thường không chứa gluten."),
    # 4. Mắm tôm / Mắm ruốc - Đậm đặc vi chất
    F("Mắm tôm", "Shrimp Paste", "sodium", 101, 14.8, 4.2, 2.8, desc="Rất giàu canxi và protein đã được thủy phân. Chứa khoảng 7,000mg Natri."),
    # 5. Hạt nêm / Bột canh - Gia vị tổng hợp
    F("Bột canh", "Seasoning Powder", "sodium", 150, 2.0, 30.0, 0.5, desc="Hỗn hợp muối, đường, bột ngọt và hương liệu. Lượng Natri chiếm khoảng 30-40% trọng lượng."),
    
    # 1. Đường cát trắng (Refined Sugar) - Tinh khiết 99.9%
    F("Đường cát trắng", "White Sugar", "carbs", 387, 0.0, 100.0, 0.0, desc="Chỉ cung cấp calo rỗng, không có vitamin hay khoáng chất. Làm tăng đường huyết cực nhanh."),
    # 2. Đường thốt nốt / Đường nâu - Giữ lại một ít khoáng chất
    F("Đường thốt nốt", "Palm Sugar", "carbs", 383, 0.0, 95.0, 0.0, desc="Chứa một lượng nhỏ Kali, Sắt và Vitamin nhóm B. Chỉ số GI thấp hơn đường trắng một chút."),
    # 3. Mật ong - "Kháng sinh" tự nhiên
    F("Mật ong", "Honey", "carbs", 304, 0.3, 82.4, 0.0, desc="Chứa các enzyme, chất chống oxy hóa và hydrogen peroxide giúp kháng khuẩn. Vị ngọt đậm hơn đường."),
    # 4. Siro Phong (Maple Syrup)
    F("Siro Phong", "Maple Syrup", "carbs", 260, 0.0, 67.0, 0.1, desc="Giàu Mangan và Kẽm. Chứa các hợp chất chống viêm tự nhiên."),
    # 5. Siro Bắp (Corn Syrup)
    F("Siro Bắp", "Corn Syrup", "carbs", 286, 0.0, 77.0, 0.0, desc="Chủ yếu là Glucose. Thường được dùng trong làm bánh để ngăn chặn sự kết tinh của đường."),
    
    # 1. Giấm táo (Apple Cider Vinegar) - "Ngôi sao" của sức khỏe
    F("Giấm táo", "Apple Cider Vinegar", "carbs", 21, 0.0, 0.9, 0.0, desc="Chứa 'con giấm' (Mother) giàu lợi khuẩn. Giúp ổn định đường huyết và hỗ trợ giảm cân."),
    # 2. Giấm Balsamic - Sang trọng và đậm đà
    F("Giấm Balsamic", "Balsamic Vinegar", "carbs", 88, 0.5, 17.0, 0.0, desc="Lên men từ nho, ủ lâu năm. Lượng đường và calo cao hơn giấm thường nhưng giàu chất chống oxy hóa."),
    # 3. Giấm gạo / Giấm trắng
    F("Giấm gạo", "Rice Vinegar", "carbs", 18, 0.0, 0.1, 0.0, desc="Vị chua thanh, ít gắt hơn giấm trắng tinh luyện. Phổ biến trong ẩm thực Á Đông."),
    # 4. Tương cà (Ketchup)
    F("Tương cà", "Ketchup", "carbs", 101, 1.0, 26.0, 0.1, desc="Chứa Lycopene từ cà chua nhưng cũng chứa rất nhiều đường và muối."),
    # 5. Tương ớt (Chili Sauce)
    F("Tương ớt", "Chili Sauce", "carbs", 95, 1.2, 23.0, 0.2, desc="Kích thích vị giác, chứa capsaicin. Cần kiểm soát lượng đường bổ sung trong các loại tương đóng chai."),
    # 6. Mù tạt (Mustard) - Gia vị "siêu thực phẩm"
    F("Mù tạt (Vàng)", "Mustard", "fat", 66, 4.4, 5.8, 4.0, desc="Calo cực thấp, giàu Isothiocyanate giúp kháng viêm và bảo vệ tế bào."),
    # 7. Tương đen (Hoisin Sauce)
    F("Tương đen", "Hoisin Sauce", "carbs", 220, 1.5, 48.0, 1.2, desc="Vị mặn ngọt đậm đà từ đậu nành lên men, tỏi và đường. Hàm lượng đường khá cao."),
    # 8. Mayonnaise - Đậm đặc chất béo
    F("Mayonnaise", "Mayonnaise", "fat", 680, 1.0, 0.6, 75.0, desc="Hỗn hợp nhũ tương giữa dầu và lòng đỏ trứng. Mật độ năng lượng rất cao."),
    # 9. Sốt mè rang (Roasted Sesame Dressing)
    F("Sốt mè rang", "Sesame Dressing", "fat", 380, 2.5, 15.0, 35.0, desc="Thơm bùi từ vừng nhưng chứa nhiều dầu và đường để tạo độ dẻo mịn."),
    
    # 1. Bột Nghệ - "Vàng ròng" kháng viêm
    F("Bột Nghệ", "Turmeric Powder", "antioxidant", 312, 7.8, 67.0, 3.2, desc="Chứa Curcumin giúp chống oxy hóa mạnh, hỗ trợ gan và tiêu hóa. Nên dùng kèm tiêu đen để tăng hấp thụ."),
    # 2. Bột Quế - Ổn định đường huyết
    F("Bột Quế", "Cinnamon Powder", "fiber", 247, 4.0, 80.6, 1.2, desc="Giúp tăng nhạy cảm insulin, hỗ trợ kiểm soát đường huyết. Rất giàu chất xơ hòa tan."),
    # 3. Tiêu đen - Chất dẫn sinh học
    F("Bột Tiêu đen", "Black Pepper", "antioxidant", 251, 10.4, 64.0, 3.3, desc="Chứa Piperine giúp cơ thể hấp thụ các dưỡng chất khác tốt hơn (đặc biệt là nghệ)."),
    # 4. Ngũ vị hương / Bột Cà ri - Hỗn hợp thảo mộc
    F("Bột Cà ri", "Curry Powder", "antioxidant", 325, 14.3, 58.0, 14.0, desc="Sự kết hợp của nghệ, ngò, thì là, tiêu... tạo nên phổ dinh dưỡng và hương vị đa dạng."),
    # 5. Hoa hồi (Star Anise) - Kháng virus tự nhiên
    F("Hoa hồi", "Star Anise", "antioxidant", 337, 17.6, 50.0, 15.9, desc="Chứa Axit Shikimic (nguyên liệu sản xuất thuốc Tamiflu). Giúp hỗ trợ hệ hô hấp và tiêu hóa."),
    # 6. Thảo quả (Black Cardamom)
    F("Thảo quả", "Black Cardamom", "antioxidant", 311, 11.0, 68.0, 6.7, desc="Nổi tiếng là 'nữ hoàng gia vị' trong nước Phở. Có tác dụng ấm bụng, giải độc."),
    # 7. Đinh hương (Cloves) - Vô địch chất chống oxy hóa
    F("Đinh hương", "Cloves", "antioxidant", 274, 6.0, 65.5, 13.0, desc="Có chỉ số ORAC (khả năng hấp thụ gốc tự do) cao hàng đầu thế giới. Chứa Eugenol giúp giảm đau răng và sát trùng."),

    # ===== Beverages =====
    
    # 1. Nước tinh khiết (Purified Water)
    F("Nước tinh khiết", "Purified Water", "hydration", 0, 0.0, 0.0, 0.0, desc="Đã loại bỏ tạp chất và vi khuẩn qua màng RO. pH trung tính (~7.0). Thích hợp uống hằng ngày."),
    # 2. Nước khoáng (Mineral Water)
    F("Nước khoáng", "Mineral Water", "minerals", 0, 0.0, 0.0, 0.0, desc="Chứa Canxi, Magie, Natri tự nhiên. Giúp bổ sung điện giải, hỗ trợ xương và tim mạch."),
    # 3. Nước suối (Spring Water)
    F("Nước suối", "Spring Water", "hydration", 0, 0.0, 0.0, 0.0, desc="Nước chảy từ các tầng địa chất ngầm, giữ được độ tinh khiết tự nhiên và một lượng khoáng nhẹ."),
    # 4. Nước ion kiềm (Alkaline Water)
    F("Nước ion kiềm", "Alkaline Water", "pH", 0, 0.0, 0.0, 0.0, desc="Có pH cao (8.5 - 9.5) và giàu Hydro (H2) chống oxy hóa. Giúp trung hòa axit dư thừa trong cơ thể."),
    
    # 1. Cà phê đen (Espresso/Americano) - Tăng cường trao đổi chất
    F("Cà phê đen", "Black Coffee", "antioxidant", 2, 0.1, 0.0, 0.0, desc="Chứa Axit Chlorogenic giúp đốt cháy mỡ thừa. Caffeine giúp tăng sự tập trung và sức bền."),
    # 2. Trà xanh (Green Tea) - Bậc thầy chống lão hóa
    F("Trà xanh", "Green Tea", "antioxidant", 1, 0.2, 0.0, 0.0, desc="Giàu EGCG giúp ngăn ngừa ung thư và bảo vệ tim mạch. Chứa L-theanine giúp thư giãn thần kinh."),
    # 3. Trà Ô long (Oolong Tea)
    F("Trà Ô long", "Oolong Tea", "antioxidant", 1, 0.0, 0.1, 0.0, desc="Trà lên men bán phần, hỗ trợ tiêu hóa chất béo và làm sạch vòm họng sau bữa ăn."),
    # 4. Trà đen (Black Tea)
    F("Trà đen", "Black Tea", "antioxidant", 1, 0.0, 0.3, 0.0, desc="Lên men toàn phần, chứa Theaflavins tốt cho sức khỏe mạch máu. Caffeine cao hơn trà xanh."),
    # 5. Trà thảo mộc (Hoa cúc/Atiso) - Thanh nhiệt, an thần
    F("Trà thảo mộc", "Herbal Tea", "wellness", 0, 0.0, 0.2, 0.0, desc="Không chứa caffeine. Giúp giải độc gan (Atiso) hoặc hỗ trợ giấc ngủ (Hoa cúc)."),
    # 6. Trà gạo lứt / Đậu đen rang
    F("Trà ngũ cốc", "Roasted Grain Tea", "hydration", 5, 0.2, 1.0, 0.0, desc="Hương vị thơm bùi, giàu khoáng chất từ lớp vỏ hạt. Rất tốt cho người tiểu đường và giảm cân."),
    
    # 1. Nước Cam ép - Cú hích Vitamin C
    F("Nước cam ép", "Orange Juice", "vitamin", 45, 0.7, 10.4, 0.2, desc="Giàu Vitamin C và Kali. Lưu ý: 100ml nước cam cô đặc lượng đường của gần 1 quả cam nhưng không có chất xơ."),
    # 2. Nước ép Táo - Ngọt thanh, giàu polyphenol
    F("Nước táo ép", "Apple Juice", "antioxidant", 46, 0.1, 11.3, 0.1, desc="Chứa nhiều đường fructose tự nhiên. Giúp bù nước và cung cấp năng lượng nhanh."),
    # 3. Nước dừa tươi - "Lotion" cho tế bào
    F("Nước dừa tươi", "Coconut Water", "electrolytes", 19, 0.7, 3.7, 0.2, desc="Chứa các chất điện giải (Kali, Natri, Magie) tương đương dịch cơ thể. Là nước uống phục hồi tốt nhất sau vận động."),
    # 4. Nước ép Cần tây - Xu hướng thanh lọc (Detox)
    F("Nước cần tây", "Celery Juice", "minerals", 14, 0.7, 3.0, 0.2, desc="Calo cực thấp, giàu Natri và Kali tự nhiên. Giúp giảm sưng viêm và hỗ trợ tiêu hóa."),
    # 5. Nước ép Cà rốt - Bổ mắt và da
    F("Nước cà rốt", "Carrot Juice", "vitamin", 40, 1.0, 9.3, 0.2, desc="Đặc biệt giàu Beta-carotene. Ép nước giúp cơ thể hấp thụ lượng carotenoid này dễ dàng hơn ăn sống."),
    # 6. Nước Rau má - Giải nhiệt truyền thống
    F("Nước rau má", "Pennywort Juice", "wellness", 20, 1.0, 4.0, 0.1, desc="Vị đắng nhẹ, tính mát. Chứa triterpenoids giúp lành vết thương và thanh nhiệt gan."),
    
    # 1. Nước ngọt có gas (Cola/Soda)
    F("Nước ngọt có gas", "Carbonated Soft Drink", "sugar", 42, 0.0, 10.6, 0.0, desc="Thành phần chính là nước bão hòa CO2, chất tạo ngọt và axit thực phẩm. Gây mòn men răng và tăng đường huyết nhanh."),
    # 2. Nước tăng lực (Energy Drink)
    F("Nước tăng lực", "Energy Drink", "sugar", 60, 0.0, 15.0, 0.0, desc="Hàm lượng đường cực cao kèm theo Caffeine và Taurine. Giúp tỉnh táo tức thì nhưng dễ gây hiện tượng 'crash' sau đó."),
    # 3. Trà chanh/Trà đào đóng chai
    F("Trà đóng chai", "Bottled Tea", "sugar", 45, 0.1, 11.0, 0.0, desc="Lượng đường tương đương nước ngọt có gas. Hàm lượng trà thật thường rất thấp so với hương liệu và đường."),
    # 4. Trà sữa (Milk Tea) - "Bom" calo
    F("Trà sữa (Truyền thống)", "Bubble Milk Tea", "mixed", 80, 1.2, 12.0, 3.5, desc="Sự kết hợp của trà, bột kem béo, đường và trân dẻo. Một ly 500ml có thể chứa tới 400-500 kcal."),
    # 5. Siro pha chế (Strawberry/Pineapple Syrup)
    F("Siro pha chế", "Beverage Syrup", "sugar", 250, 0.0, 62.0, 0.0, desc="Dạng đường cô đặc. Thường dùng một lượng nhỏ (20-30ml) để pha chế đồ uống."),
    
    # 1. Sữa Đậu nành (Soy Milk) - Đối trọng của sữa bò
    F("Sữa Đậu nành", "Soy Milk", "protein", 43, 3.3, 2.0, 1.8, desc="Cung cấp Protein hoàn chỉnh tương đương sữa bò. Chứa Isoflavones tốt cho tim mạch và nội tiết."),
    # 2. Sữa Hạnh nhân (Almond Milk) - Calo thấp nhất
    F("Sữa Hạnh nhân", "Almond Milk", "fat", 15, 0.5, 0.3, 1.1, desc="Lượng calo rất thấp, phù hợp cho người giảm cân. Giàu Vitamin E tự nhiên nhưng ít đạm."),
    # 3. Sữa Yến mạch (Oat Milk) - Thơm ngon, giàu xơ
    F("Sữa Yến mạch", "Oat Milk", "carbs", 50, 1.0, 7.0, 2.0, desc="Chứa Beta-glucan giúp giảm cholesterol. Vị ngọt tự nhiên và kết cấu béo mịn, rất hợp pha cà phê."),
    # 4. Sữa Hạt điều (Cashew Milk) - Béo ngậy nhất
    F("Sữa Hạt điều", "Cashew Milk", "fat", 25, 1.0, 1.5, 2.0, desc="Kết cấu kem mịn nhất trong các loại sữa hạt. Giàu Magie và chất béo đơn không bão hòa."),
    # 5. Sữa Gạo (Rice Milk) - Dịu nhẹ cho tiêu hóa
    F("Sữa Gạo", "Rice Milk", "carbs", 47, 0.3, 9.0, 1.0, desc="Ít gây dị ứng nhất. Hàm lượng Carbs cao, cung cấp năng lượng nhanh nhưng ít protein."),
    
    # 1. Bia (Beer) - "Bánh mì lỏng"
    F("Bia (Lon/Hơi)", "Beer", "alcohol", 43, 0.5, 3.6, 0.0, desc="Chứa khoảng 4-5% độ cồn. Calo đến từ cả cồn và carbohydrate từ lúa mạch."),
    # 2. Bia thủ công (Craft Beer)
    F("Bia thủ công", "Craft Beer", "alcohol", 60, 1.0, 5.0, 0.0, desc="Thường có độ cồn cao hơn (6-9%) và đậm đặc mạch nha hơn, dẫn đến lượng calo cao hơn bia thường."),
    # 3. Rượu Vang (Vang đỏ/trắng)
    F("Rượu Vang", "Wine", "alcohol", 85, 0.1, 2.6, 0.0, desc="Độ cồn ~12-14%. Vang đỏ chứa Resveratrol - một chất chống oxy hóa tốt cho tim mạch nếu uống điều độ."),
    # 4. Rượu mạnh (40% Vol) - Vodka/Whiskey/Rượu đế
    F("Rượu mạnh", "Distilled Spirits", "alcohol", 231, 0.0, 0.0, 0.0, desc="Gần như toàn bộ calo đến từ cồn. Không chứa carbs hay protein. Độ cồn càng cao, calo càng lớn."),
    
    # Bổ sung ingredients
    
    # Thêm vào nhóm Fruits
    F("Chanh dây (Cốt)", "Passion Fruit (Juice)", "fruit", 60, 1.2, 13.0, 0.2, desc="Nước cốt chanh dây nguyên chất, giàu Vitamin C và mùi thơm nồng nàn."),

    # Thêm vào nhóm Fats & Condiments (Sweeteners)
    F("Đường ăn kiêng (Stevia)", "Stevia Sweetener", "carbs", 0, 0, 100.0, 0, desc="Chất tạo ngọt không calo, chiết xuất từ cỏ ngọt, phù hợp cho người tiểu đường và giảm cân."),

    # Thêm vào nhóm Herbs/Spices
    F("Lá hương thảo (Tươi)", "Fresh Rosemary", "antioxidant", 131, 3.3, 20.7, 5.9, desc="Thảo mộc có mùi thơm nồng, đặc trưng của ẩm thực phương Tây, giàu chất chống oxy hóa."),
    
    # Thêm vào nhóm Carbs - Grains (hoặc nhóm bột)
    F("Bột bắp", "Corn Starch", "carbs", 381, 0.3, 91.0, 0.1, desc="Bột tinh bột từ bắp, dùng làm chất kết dính hoặc làm sệt nước sốt."),
    
    # Thêm vào nhóm Herbs/Spices
    F("Ngò tây (Parsley)", "Parsley", "antioxidant", 36, 3.0, 6.3, 0.8, desc="Thảo mộc phổ biến trong món Âu, giàu Vitamin K và chất chống oxy hóa."),
    
    # Thêm vào nhóm Gia vị thảo mộc
    F("Hạt Mắc khén", "Mac Khen Seeds", "antioxidant", 260, 8.0, 45.0, 10.0, desc="Gia vị đặc trưng vùng Tây Bắc, có mùi thơm nồng và vị tê nhẹ."),
    F("Hạt Dỗi", "Hat Doi Seeds", "antioxidant", 320, 12.0, 35.0, 15.0, desc="Được mệnh danh là vàng đen Tây Bắc, mùi thơm rất đặc biệt khi rang chín."),
    F("Lá Kinh giới tây (Oregano)", "Dried Oregano", "antioxidant", 265, 9.0, 68.9, 4.3, desc="Lá thơm khô phổ biến trong ẩm thực Ý, rất hợp với cà chua và phô mai."),
    
    # Thêm vào nhóm Fats & Condiments (Condiments)
    F("Nước tương Tamari", "Tamari Soy Sauce", "sodium", 60, 10.0, 5.5, 0.1, desc="Nước tương lên men tự nhiên không chứa lúa mì, vị đậm đà và ít mặn hơn nước tương thường."),
    
    # Thêm vào nhóm Vegetables (Gourd & Squash)
    F("Bí ngòi", "Zucchini", "fiber", 17, 1.2, 3.1, 0.3, desc="Họ bầu bí, chứa nhiều nước và vitamin C. Khi bào sợi có thể thay thế mì/phở (Zoodles)."),

    # Thêm vào nhóm Proteins - Poultry
    F("Xương khung gà", "Chicken Carcass", "protein", 130, 15.0, 0, 8.0, desc="Phần xương sau khi lọc thịt, dùng ninh nước dùng để lấy vị ngọt tự nhiên và collagen."),
    
    # Thêm vào nhóm Herbs/Spices/Antioxidants
    F("Táo đỏ (Khô)", "Dried Red Dates", "antioxidant", 280, 1.2, 73.0, 0.5, desc="Vị thuốc bổ máu, giàu polyphenol và chất xơ, tạo vị ngọt tự nhiên cho món hầm."),
    F("Kỷ tử (Khô)", "Goji Berries", "antioxidant", 349, 14.3, 77.0, 0.4, desc="Siêu thực phẩm giàu Zeaxanthin tốt cho mắt và hỗ trợ phục hồi hệ miễn dịch."),
       
    # Thêm vào nhóm Ground Spices (Antioxidant)
    F("Ớt bột Paprika", "Paprika Powder", "antioxidant", 282, 14.1, 54.0, 12.8, desc="Ớt bột ngọt không cay, giàu Vitamin A và tạo màu đỏ đẹp mắt cho món nướng."),
       
   # Thêm vào nhóm Mushrooms/Antioxidants
    F("Nấm linh chi (Tươi/Nâu)", "Brown Shimeji Mushroom", "antioxidant", 35, 3.1, 5.2, 0.5, desc="Loại nấm nhỏ mọc thành chùm, vị bùi, giàu chất xơ và hoạt chất hỗ trợ miễn dịch."),    
       
    # Thêm vào nhóm Proteins - Seafood
    F("Cá Cam", "Amberjack", "protein", 146, 23.0, 0, 5.2, desc="Cá biển thịt chắc, ngọt, giàu Omega-3 và Vitamin D, thớ thịt dày phù hợp cho món nướng."),    
       
    # Thêm vào nhóm Proteins - Seafood
    F("Cồi sò điệp", "Scallops", "protein", 111, 20.5, 5.4, 0.8, desc="Nguồn đạm tinh khiết, giàu Magie và Vitamin B12, kết cấu mềm mọng."),

    # Thêm vào nhóm Fats & Condiments (Fats)
    F("Quả Ô liu (Đen/Xanh)", "Olives", "fat", 115, 0.8, 6.3, 10.7, desc="Giàu axit oleic (Omega-9) và chất chống oxy hóa, đặc trưng của ẩm thực Địa Trung Hải."), 
       
    # Thêm/Cập nhật vào nhóm Proteins - Meat
    F("Thịt bò (Thăn nội)", "Beef Tenderloin", "protein", 180, 24.0, 0, 9.0, desc="Phần thịt bò mềm nhất, ít mỡ, giàu sắt và kẽm, phù hợp cho chế độ ăn tăng cơ."),
       
    # Thêm vào nhóm Herbs/Vegetables
    F("Lá lốt", "Wild Betel Leaf", "antioxidant", 39, 4.3, 5.2, 1.0, desc="Thảo mộc có mùi thơm đặc trưng, giúp giảm đau nhức xương khớp và hỗ trợ tiêu hóa."),

    # Thêm/Cập nhật vào nhóm Proteins - Meat
    F("Thịt heo (Thăn nội)", "Pork Tenderloin", "protein", 143, 26.0, 0, 3.5, desc="Phần thịt nạc nhất của heo, hầu như không có mỡ giắt, giàu Vitamin B1."),
       
    # Thêm vào nhóm Proteins - Meat
    F("Bắp bò", "Beef Shank", "protein", 201, 21.0, 0, 12.0, desc="Phần thịt từ chân bò, chứa nhiều gân và mô liên kết, giàu collagen tốt cho khớp và da."),

    # Thêm vào nhóm Ground Spices (Antioxidant)
    F("Bột Ngũ vị hương", "Five Spice Powder", "antioxidant", 320, 7.0, 58.0, 7.0, desc="Hỗn hợp gia vị gồm quế, hồi, đinh hương, tiêu, hạt thì là; giúp tăng hương vị mà không thêm calo đáng kể."),
       
    # Thêm vào nhóm Vegetables
    F("Bông thiên lý", "Tonkin Jasmine Flowers", "fiber", 24, 2.9, 3.0, 0.2, desc="Loại hoa giàu chất xơ, Vitamin C và Beta-carotene, có tác dụng an thần và giải nhiệt."),

    # Cập nhật/Thêm vào nhóm Fruits
    F("Táo tây (Apple)", "Apple", "fruit", 52, 0.3, 13.8, 0.2, desc="Chứa pectin và enzyme tự nhiên giúp làm mềm thịt và tạo vị ngọt thanh cho nước sốt."), 
        
    # Thêm vào nhóm Carbs - Grains
    F("Bún gạo lứt (Khô)", "Dried Brown Rice Vermicelli", "carbs", 350, 7.5, 77.0, 1.5, desc="Sản phẩm từ gạo lứt nguyên cám, giàu chất xơ và có chỉ số đường huyết (GI) thấp hơn bún trắng."),

    # Thêm vào nhóm Herbs/Spices
    F("Tiêu xanh", "Green Peppercorns", "antioxidant", 40, 2.0, 8.0, 0.5, desc="Tiêu chưa chín hẳn, chứa nhiều tinh dầu piperine giúp kích thích tiêu hóa và kháng viêm."),
        
    # Thêm vào nhóm Fruits
    F("Dứa (Thơm)", "Pineapple", "fruit", 50, 0.5, 13.1, 0.1, desc="Chứa enzyme Bromelain giúp làm mềm thịt và hỗ trợ tiêu hóa protein."),

    # Thêm vào nhóm Vegetables
    F("Đậu que", "Green Beans", "fiber", 31, 1.8, 7.0, 0.2, desc="Nguồn chất xơ dồi dào, giàu Vitamin K và Manganese tốt cho xương."),
        
    # Thêm vào nhóm Herbs/Antioxidants
    F("Củ Riềng", "Galangal", "antioxidant", 71, 1.2, 15.0, 1.0, desc="Thảo mộc cùng họ gừng, có mùi thơm cay nhẹ đặc trưng, hỗ trợ tiêu hóa và kháng viêm."),

    # Thêm vào nhóm Fermented Foods
    F("Mẻ (Cơm chua)", "Fermented Rice", "antioxidant", 50, 1.5, 10.0, 0.5, desc="Cơm lên men tự nhiên giàu lợi khuẩn (Lactic acid bacteria) giúp tạo độ chua thanh và làm mềm thịt."),

    # Thêm vào nhóm Condiments
    F("Mắm tôm", "Shrimp Paste", "sodium", 73, 14.8, 1.5, 0.8, desc="Gia vị lên men truyền thống, giàu đạm và canxi, tạo hương vị đậm đà đặc trưng."),
        
    # Thêm vào nhóm Vegetables
    F("Đậu bắp", "Okra", "fiber", 33, 1.9, 7.5, 0.2, desc="Giàu chất xơ hòa tan và chất nhầy mucilage giúp bảo vệ niêm mạc dạ dày và hỗ trợ tiêu hóa."),

    # Thêm vào nhóm Seafood/Superfoods
    F("Rong biển khô", "Dried Seaweed", "antioxidant", 45, 3.0, 9.0, 0.5, desc="Nguồn cung cấp I-ốt, Magie và Canxi dồi dào, hỗ trợ tuyến giáp và hồi phục cơ thể."),    
        
    # Cập nhật vào nhóm Proteins - Plant-based
    F("Đậu hũ trắng (Cứng)", "Firm Tofu", "protein", 83, 10.0, 2.0, 4.8, desc="Đạm thực vật hoàn chỉnh từ đậu nành, ít calo và không chứa cholesterol."),   
        
    # Thêm vào nhóm Fats & Fruits
    F("Bơ quả (Avocado)", "Avocado", "fat", 160, 2.0, 8.5, 14.7, desc="Nguồn cung cấp axit béo đơn không bão hòa (Omega-9) và Kali tuyệt vời cho tim mạch."),

    # Thêm vào nhóm Proteins - Plant-based
    F("Đậu hũ non (Silken Tofu)", "Silken Tofu", "protein", 55, 5.0, 2.0, 3.0, desc="Kết cấu mềm mượt như thạch, hàm lượng nước cao, cực kỳ dễ tiêu hóa."),
        
    # Thêm vào nhóm Vegetables/Fungi
    F("Nấm mèo (Mộc nhĩ)", "Wood Ear Mushroom", "fiber", 25, 0.5, 7.0, 0.1, desc="Giàu chất xơ và sắt, giúp cải thiện lưu thông máu và tạo độ giòn tự nhiên."),

    # Thêm vào nhóm Carbs
    F("Bún tàu (Miến dong)", "Glass Noodles", "carbs", 330, 0.5, 82.0, 0.1, desc="Làm từ tinh bột dong riềng, không chứa gluten, kết cấu dai mềm hấp dẫn."),
            
    # Thêm vào nhóm Fats & Nuts
    F("Hạt điều (Rang)", "Roasted Cashews", "fat", 553, 18.2, 30.2, 43.8, desc="Giàu Magie, Kẽm và chất béo không bão hòa đơn, hỗ trợ trí não và sức khỏe tim mạch."),

    # Thêm vào nhóm Condiments
    F("Nước tương đậu nành", "Soy Sauce", "sodium", 53, 8.0, 5.0, 0.1, desc="Gia vị lên men truyền thống từ đậu nành, giàu vị Umami tự nhiên."),
        
    # Thêm vào nhóm Carbs & Plant-proteins
    F("Đậu xanh (Cà vỏ/Khô)", "Peeled Mung Beans", "protein", 347, 23.0, 62.0, 1.2, desc="Nguồn đạm thực vật dồi dào, giàu chất xơ hòa tan và tinh bột chậm (Slow-carb)."),

    # Thêm vào nhóm Vegetables/Carbs
    F("Ngô ngọt (Bắp Mỹ)", "Sweet Corn", "carbs", 86, 3.2, 19.0, 1.2, desc="Cung cấp chất xơ và lutein tốt cho mắt, tạo độ ngọt tự nhiên cho món ăn."),   
        
    # Thêm vào nhóm Vegetables/Fungi
    F("Nấm đùi gà", "King Oyster Mushroom", "protein", 35, 3.4, 6.1, 0.1, desc="Loại nấm có kết cấu chắc, dai như thịt, giàu protein thực vật, Kali và chất xơ hòa tan."), 
        
    # Thêm vào nhóm Proteins - Plant-based
    F("Đậu nành Nhật (Edamame)", "Edamame", "protein", 121, 11.9, 8.9, 5.2, desc="Đậu nành non nguyên quả, chứa hàm lượng protein và chất xơ cực cao, giàu khoáng chất."),
        
    # Thêm vào nhóm Vegetables/Fungi
    F("Nấm rơm", "Straw Mushrooms", "protein", 32, 3.8, 4.6, 0.5, desc="Loại nấm phổ biến trong món kho, giàu Protein, Vitamin D và các axit amin thiết yếu."),

    # Thêm vào nhóm Herbs/Vegetables
    F("Hành Boa-rô", "Leek", "antioxidant", 61, 1.5, 14.2, 0.3, desc="Hành tỏi tây, tạo mùi thơm đặc trưng cho các món chay/healthy mà không nồng như hành tím."), 
        
    # Thêm vào nhóm Herbs/Vegetables
    F("Lá Hẹ", "Chives", "antioxidant", 30, 3.3, 4.4, 0.7, desc="Giàu chất xơ, vitamin A, C và hợp chất allicin giúp kháng khuẩn, hỗ trợ tiêu hóa."),

    # Thêm vào nhóm Seafood/Antioxidants
    F("Rong biển Nori", "Nori Seaweed", "antioxidant", 35, 5.8, 5.0, 0.3, desc="Dạng lá khô cán mỏng, chứa mật độ khoáng chất cực cao, đặc biệt là I-ốt và Vitamin B12."),  
        
    # Thêm vào nhóm Carbs & Plant-proteins
    F("Đậu lăng (Khô)", "Dried Lentils", "protein", 353, 25.0, 60.0, 1.1, desc="Siêu thực phẩm giàu sắt, folate và chất xơ hòa tan, chỉ số GI cực thấp."),

    # Thêm vào nhóm Vegetables
    F("Cải bẹ xanh", "Mustard Greens", "fiber", 27, 2.7, 4.7, 0.4, desc="Loại rau có vị cay đắng nhẹ, giàu Vitamin A, K và có tính kiềm giúp giải nhiệt cơ thể."),
        
    # Thêm vào nhóm Vegetables
    F("Bí ngòi", "Zucchini", "fiber", 17, 1.2, 3.1, 0.3, desc="Loại quả họ bầu bí, cực thấp calo, giàu Kali, rất dễ tạo hình thành sợi mì (Zoodles)."),

    # Thêm vào nhóm Healthy Fats/Sauces
    F("Sốt Pesto (Hạt điều/Basil)", "Cashew Basil Pesto", "fat", 450, 5.0, 10.0, 42.0, desc="Sốt đậm đà từ húng tây, dầu olive và hạt điều, cung cấp Omega-9 và chất chống oxy hóa."),   
        
    # Cập nhật/Thêm vào nhóm Proteins
    F("Tôm (Sú/Thẻ) luộc", "Boiled Shrimp", "protein", 99, 24.0, 0.2, 0.3, desc="Nguồn đạm tinh khiết, giàu Astaxanthin chống oxy hóa và Selen."),

    # Bông cải xanh và Cải bẹ xanh đã có trong dữ liệu trước đó, tôi sẽ sử dụng lại. 
        
    # Thêm vào nhóm Dairy & Fats
    F("Phô mai Mozzarella", "Mozzarella Cheese", "fat", 280, 22.0, 2.0, 20.0, desc="Phô mai có độ tan chảy tốt, cung cấp Canxi và Protein hỗ trợ cấu trúc đế bánh súp lơ."),

    # Thêm vào nhóm Herbs/Spices
    F("Thảo mộc Ý (Khô)", "Dried Italian Herbs", "antioxidant", 250, 10.0, 45.0, 10.0, desc="Hỗn hợp húng tây, kinh giới, xạ hương giúp tạo hương vị Pizza đặc trưng mà không thêm calo."),

    # Thêm vào nhóm Vegetables/Fruits
    F("Đu đủ xanh", "Green Papaya", "fiber", 43, 0.5, 10.8, 0.1, desc="Chứa enzyme Papain giúp làm mềm thịt và hỗ trợ tiêu hóa, giàu Vitamin C và chất xơ."),

    # Thêm vào nhóm Sauces/Antioxidants
    F("Sốt Salsa tươi", "Fresh Salsa", "antioxidant", 36, 1.5, 7.0, 0.2, desc="Hỗn hợp cà chua, hành tây, chanh và ngò rí; giàu Lycopene và không chứa chất béo."),

    # Thêm vào nhóm Dairy & Fats
    F("Cream Cheese", "Cream Cheese", "fat", 342, 6.0, 4.0, 34.0, desc="Phô mai kem mềm, giàu béo và ít carb, tạo cấu trúc béo ngậy cho bánh mì Keto."),

    # Thêm vào nhóm Nuts/Flours
    F("Bột Hạnh nhân", "Almond Flour", "protein", 581, 21.0, 20.0, 50.0, desc="Hạt hạnh nhân nghiền mịn, thay thế bột mì hoàn hảo trong chế độ Keto và Gluten-free."),

    # Thêm vào nhóm Pantry
    F("Cream of Tartar", "Cream of Tartar", "pantry", 258, 0, 61.0, 0, desc="Muối axit giúp ổn định cấu trúc bọt khí của lòng trắng trứng khi đánh bông."),

    # Thêm vào nhóm Vegetables
    F("Cà tím", "Eggplant", "fiber", 25, 1.0, 6.0, 0.2, desc="Giàu chất xơ và Nasunin (chống oxy hóa), cấu trúc xốp giúp thay thế lá mì hiệu quả."),

    # Thêm vào nhóm Dairy & Fats
    F("Phô mai Ricotta", "Ricotta Cheese", "protein", 174, 11.0, 3.0, 13.0, desc="Phô mai mềm, ít béo hơn Mozzarella, giàu Canxi và Whey protein."),

    # Thêm vào nhóm Smart Carbs (Zero-carb)
    F("Mì Shirataki (Mì nưa)", "Shirataki Noodles", "fiber", 10, 0.5, 2.0, 0, desc="Làm từ bột củ nưa, chứa chất xơ hòa tan Glucomannan, gần như không calo và không tinh bột."),

    # Thêm vào nhóm Vegetables
    F("Giá đỗ", "Mung Bean Sprouts", "fiber", 30, 3.0, 6.0, 0.2, desc="Giàu Vitamin C, khoáng chất và enzyme hỗ trợ tiêu hóa, cực thấp calo."),

    # Thêm vào nhóm Vegetables/Fungi
    F("Nấm Portobello", "Portobello Mushroom", "protein", 22, 2.1, 3.9, 0.3, desc="Mũ nấm lớn, thịt dày và dai, giàu Kali và Vitamin nhóm B, thay thế hoàn hảo cho vỏ bánh burger."),

    # Thêm vào nhóm Smart Carbs (Zero-calorie)
    F("Cơm hạt Konjac", "Konjac Rice", "fiber", 10, 0, 2.3, 0, desc="Làm từ củ nưa, chứa Glucomannan giúp giảm hấp thụ chất béo và tinh bột, hỗ trợ giảm cân tối đa."),

    # Thêm vào nhóm Vegetables
    F("Cải Kale", "Curly Kale", "fiber", 49, 4.3, 8.8, 0.9, desc="Siêu thực phẩm giàu Vitamin K, Canxi và chất chống oxy hóa; kết cấu lá xoăn dễ trở nên giòn khi nướng."),

    # Thêm vào nhóm Smart Carbs (Natural)
    F("Bí đỏ sợi", "Spaghetti Squash", "carbs", 31, 0.6, 7.0, 0.6, desc="Loại bí đặc biệt có thịt tự tách thành sợi như mì sau khi nấu chín, giàu chất xơ và Vitamin A."),

    # Thêm vào nhóm Carbs - Grains
    F("Yến mạch nguyên cám", "Rolled Oats", "carbs", 389, 16.9, 66.0, 6.9, desc="Ngũ cốc nguyên cám giàu Beta-glucan, giúp giảm cholesterol và ổn định đường huyết."),

    # Cập nhật nhóm Proteins
    F("Lòng trắng trứng", "Egg White", "protein", 52, 11.0, 0.7, 0.2, desc="Nguồn đạm tinh khiết, không béo, không cholesterol, dễ đông tụ để tạo màng thực phẩm."),

    # Thêm vào nhóm Proteins - Seafood
    F("Cá chép", "Carp", "protein", 127, 18.0, 0, 5.6, desc="Thịt cá trắng, lành tính, giàu axit amin thiết yếu và tốt cho hệ tiêu hóa."),

    # Thêm vào nhóm Proteins - Meat
    F("Móng giò heo (Nạc)", "Lean Pork Knuckle", "collagen", 210, 21.0, 0, 14.0, desc="Nguồn cung cấp Collagen dồi dào cho da và xương, giúp phục hồi mô mềm và hỗ trợ lợi sữa."),

    # Thêm vào nhóm Healthy Fats & Nuts
    F("Hạt óc chó", "Walnuts", "fat", 654, 15.2, 13.7, 65.2, desc="Vua của các loại hạt cho trí não, cung cấp Omega-3 (ALA) và chất chống oxy hóa Polyphenol."),

    # Thêm vào nhóm Dairy & Proteins
    F("Sữa chua Hy Lạp (Không đường)", "Greek Yogurt Plain", "protein", 59, 10.0, 3.6, 0.4, desc="Sữa chua đã tách nước, hàm lượng protein cao gấp đôi sữa chua thường và giàu lợi khuẩn."),

    # Thêm vào nhóm Herbs/Medicinal
    F("Táo đỏ (Khô)", "Dried Red Dates", "carbs", 287, 1.2, 73.0, 0.5, desc="Giàu Vitamin C và chất chống oxy hóa, hỗ trợ an thần và bồi bổ khí huyết."),
    F("Kỷ tử", "Goji Berries", "antioxidant", 349, 14.0, 77.0, 0.4, desc="Siêu thực phẩm cho mắt và hệ miễn dịch, giàu Zeaxanthin và Polysaccharides."),
    F("Nghệ tươi", "Fresh Turmeric", "anti-inflammatory", 52, 1.3, 10.0, 0.1, desc="Chứa Curcumin giúp kháng viêm mạnh mẽ, hỗ trợ nhanh lành vết thương và tốt cho tiêu hóa."),

    # Thêm vào nhóm Herbs & Vegetables
    F("Lá ngải cứu", "Mugwort Leaves", "herb", 45, 3.5, 8.5, 0.4, desc="Vị thuốc đông y giúp điều hòa khí huyết, giảm đau và an thai."),

    # Thêm vào nhóm Smart Carbs - Seeds & Beans
    F("Hạt sen tươi", "Fresh Lotus Seeds", "carbs", 89, 4.1, 17.0, 0.5, desc="Giàu Magie, Phospho và Vitamin B1, giúp an thần và hỗ trợ giấc ngủ."),
    F("Đậu đen", "Black Beans", "protein", 341, 21.6, 62.4, 1.4, desc="Nguồn cung cấp Axit Folic (B9), Sắt và Anthocyanin dồi dào cho máu huyết."),

    # Cập nhật nhóm Proteins - Seafood
    F("Cá hồi phi lê", "Salmon Fillet", "protein", 208, 20.0, 0, 13.0, desc="Nguồn cung cấp Omega-3 (DHA & EPA) hàng đầu, hỗ trợ phát triển trí não và thị lực."),

    # Thêm vào nhóm Pantry/Natural Sweetener
    F("Đường thốt nốt", "Palm Sugar", "carbs", 383, 0, 95.0, 0, desc="Chứa nhiều khoáng chất hơn đường tinh luyện, chỉ số đường huyết (GI) thấp hơn, vị ngọt thanh."),

    # Thêm vào nhóm Vegetables
    F("Bí đỏ", "Pumpkin", "vitamin-a", 26, 1.0, 6.5, 0.1, desc="Nguồn tiền Vitamin A (Beta-carotene) cực cao, hỗ trợ võng mạc và hệ miễn dịch."),
    F("Măng tây", "Asparagus", "folate", 20, 2.2, 3.9, 0.1, desc="Giàu Axit Folic (B9), chất xơ và Vitamin K, hỗ trợ phát triển hệ thần kinh thai nhi."),

    # Thêm vào nhóm Dairy/Fats
    F("Kem tươi (Whipping Cream)", "Whipping Cream", "fat", 345, 2.1, 2.8, 37.0, desc="Chất béo sữa giúp hòa tan Vitamin A, tạo độ ngậy và cung cấp năng lượng nhanh."),

    # Thêm vào nhóm Proteins - Poultry
    F("Thịt bồ câu", "Pigeon Meat", "protein", 142, 21.3, 0, 6.2, desc="Thịt gia cầm giàu dinh dưỡng, hàm lượng sắt cao và rất dễ tiêu hóa."),

    # Thêm vào nhóm Vegetables - Leafy Greens
    F("Rau bina (Chân vịt)", "Spinach", "folate", 23, 2.9, 3.6, 0.4, desc="Loại rau lá xanh đậm giàu Axit Folic (B9), Sắt và Vitamin K hàng đầu."),

    # Thêm vào nhóm Vegetables
    F("Rau ngót", "Katuk Leaves", "detox", 35, 5.3, 3.4, 0.4, desc="Giàu Vitamin C, Canxi và Papaverin giúp hỗ trợ co bóp tử cung và thải độc sau sinh."),
    F("Giá đỗ (Đậu xanh)", "Mung Bean Sprouts", "hormone", 30, 3.0, 6.0, 0.2, desc="Nguồn cung cấp Vitamin E dồi dào, hỗ trợ nội tiết tố và làm chậm quá trình oxy hóa."),

    # Thêm vào nhóm Proteins - Seafood
    F("Cá thu", "Mackerel", "protein", 205, 18.6, 0, 13.9, desc="Cá béo giàu Omega-3, Vitamin D và B12, rất tốt cho hệ thần kinh và tim mạch."),

    # Thêm vào nhóm Smart Carbs - Beans
    F("Đậu đỏ (Khô)", "Dried Red Beans", "fiber", 329, 22.0, 60.0, 0.8, desc="Chứa Saponin hỗ trợ lợi tiểu, giảm phù nề và giàu chất sắt tái tạo máu."),

    # Thêm vào nhóm Premium Proteins & Recovery
    F("Tổ yến (Tinh chế)", "Bird's Nest", "protein", 345, 55.0, 30.0, 0.5, desc="Siêu thực phẩm giàu axit amin (Lysine, Threonine), giúp tái tạo mô và tăng cường miễn dịch."),

    # Cập nhật nhóm Smart Carbs - Beans (Dùng cho nước uống)
    F("Đậu đen xanh lòng", "Green Kernel Black Bean", "detox", 341, 21.0, 62.0, 1.4, desc="Giàu Molybdenum giúp giải độc Sulfites và Anthocyanin chống lão hóa."),

    # Thêm vào nhóm Vegetables
    F("Khổ qua", "Bitter Melon", "metabolism", 17, 1.0, 3.7, 0.2, desc="Chứa Charantin và Polypeptide-p giúp hạ đường huyết và cải thiện độ nhạy insulin."),

    # Thêm vào nhóm Fruits/Sauce Base
    F("Nước cam tươi", "Fresh Orange Juice", "vitamin", 45, 0.7, 10.4, 0.2, desc="Cung cấp vị ngọt tự nhiên, axit hữu cơ và Vitamin C giúp tăng cường hấp thụ sắt."),

    # Thêm vào nhóm Smart Carbs - Beans
    F("Đậu xanh nguyên vỏ", "Whole Mung Beans", "fiber", 347, 23.8, 62.6, 1.2, desc="Giàu chất xơ hòa tan và protein thực vật, có chỉ số GI thấp giúp ổn định đường huyết."),

    # Thêm vào nhóm Pantry/Natural Sweetener
    F("Đường cỏ ngọt (Stevia)", "Stevia Sweetener", "pantry", 0, 0, 0, 0, desc="Chất tạo ngọt tự nhiên chiết xuất từ lá cỏ ngọt, không chứa calo và không làm tăng chỉ số đường huyết."),

    # Thêm vào nhóm Smart Carbs - Legumes
    F("Đậu lăng (Luộc)", "Lentils Boiled", "fiber", 116, 9.0, 20.0, 0.4, desc="Siêu thực phẩm Low-GI, chứa nhiều Folate, Sắt và lượng chất xơ hòa tan cực cao."),

    # Thêm vào nhóm Vegetables
    F("Ớt chuông", "Bell Pepper", "vitamin", 20, 0.9, 4.6, 0.2, desc="Nguồn Vitamin C dồi dào gấp 3 lần cam, chứa nhiều Carotenoid bảo vệ thị lực và mạch máu."),

    # Thêm vào nhóm Vegetables
    F("Hoa thiên lý", "Tonkin Jasmine", "fiber", 24, 2.5, 4.0, 0.2, desc="Giàu chất xơ và các khoáng chất giúp an thần, làm mát cơ thể và ổn định đường huyết."),
    F("Lá hẹ", "Chives", "heart-health", 30, 2.5, 4.4, 0.7, desc="Chứa Allicin giúp hạ huyết áp, giảm mỡ máu và có tính kháng khuẩn tự nhiên."),

    # Thêm vào nhóm Smart Carbs - Legumes & Nuts
    F("Đậu nành Nhật (Edamame)", "Edamame", "protein", 122, 11.0, 10.0, 5.0, desc="Đạm thực vật hoàn chỉnh, giàu Isoflavones và chất xơ, hỗ trợ tim mạch và nội tiết."),

    # Thêm vào nhóm Vegetables
    F("Nấm hương", "Shiitake Mushroom", "antioxidant", 34, 2.2, 7.0, 0.5, desc="Giàu Polysaccharides và Vitamin D, giúp tăng cường miễn dịch và tạo vị Umami tự nhiên."),

    # Thêm vào nhóm Vegetables & Herbs
    F("Lá giang", "River Leaf (La Giang)", "digestive", 25, 1.5, 4.0, 0.2, desc="Giàu Saponin tạo vị chua thanh đặc trưng, giúp kháng khuẩn và hỗ trợ tiêu hóa cực tốt."),

    # Thêm vào nhóm Herbs/Spices
    F("Lá mùi tây (Parsley)", "Parsley", "antioxidant", 36, 3.0, 6.0, 0.8, desc="Chứa nhiều Vitamin K và chất chống oxy hóa, giúp giảm đầy hơi và làm đẹp da."),

    # Thêm vào nhóm Vegetables & Fungi
    F("Nấm đùi gà", "King Oyster Mushroom", "umami", 35, 3.3, 6.0, 0.4, desc="Giàu Ergothioneine (chống oxy hóa) và vị Umami đậm đà, kết cấu dai giòn thay thế thịt tốt."),

    # Thêm vào nhóm Seeds & Healthy Fats
    F("Hạt bí ngô", "Pumpkin Seeds", "magnesium", 559, 30.0, 10.0, 49.0, desc="Nguồn cung cấp Magie, Kẽm và Omega-3 thực vật tuyệt vời, hỗ trợ chuyển hóa đường."),

    # Thêm vào nhóm Healthy Fats & Nuts
    F("Hạnh nhân sống", "Raw Almonds", "fat", 579, 21.2, 21.6, 49.9, desc="Giàu Vitamin E và Magie, giúp ổn định đường huyết và giảm áp lực oxy hóa."),

    # Thêm vào nhóm Herbs & Spices
    F("Lá húng quế/quế tây", "Basil Leaves", "metabolism", 23, 3.1, 2.7, 0.6, desc="Chứa tinh dầu giúp cải thiện độ nhạy insulin và có đặc tính kháng khuẩn mạnh."),

    # Thêm vào nhóm Vegetables
    F("Bí xanh (Bí đao)", "Winter Melon", "detox", 12, 0.6, 3.0, 0.1, desc="Hàm lượng nước cực cao, chứa Axit Propanedioic giúp ngăn chặn đường chuyển hóa thành chất béo."),

    # Thêm vào nhóm Sauces/Metabolic Boosters
    F("Mù tạt (Wasabi/Vàng)", "Mustard", "metabolism", 66, 3.7, 4.8, 3.4, desc="Chứa Isothiocyanates giúp kích thích tiêu hóa và tăng nhẹ tốc độ trao đổi chất cơ bản."),

    # Thêm vào nhóm Fruits
    F("Táo xanh", "Green Apple", "carbs", 52, 0.3, 13.8, 0.2, desc="Chứa Pectin (chất xơ hòa tan) giúp ổn định đường huyết, vị chua nhẹ từ Acid Malic hỗ trợ tiêu hóa."),

    # Thêm vào nhóm Vegetables & Fungi
    F("Nấm hương (khô)", "Dried Shiitake Mushroom", "antioxidant", 296, 9.6, 75.0, 1.0, desc="Nguồn polysaccharides dồi dào giúp tăng cường miễn dịch, cung cấp vị Umami tự nhiên đậm đà."),

    # Thêm vào nhóm Dairy & Fats
    F("Bơ lạt (Unsalted Butter)", "Unsalted Butter", "fat", 717, 0.9, 0.1, 81.0, desc="Nguồn chất béo bão hòa tự nhiên, giàu Vitamin A, D, E tan trong dầu."),

    # Thêm vào nhóm Proteins - Meat
    F("Thịt ba chỉ heo", "Pork Belly", "protein-fat", 518, 9.0, 0, 53.0, desc="Phần thịt lý tưởng cho Keto với hàm lượng mỡ cao, cung cấp năng lượng bền bỉ và độ ẩm cho món nướng."),

    # Thêm vào nhóm Dairy & Fats
    F("Phô mai Cheddar", "Cheddar Cheese", "fat-protein", 403, 25.0, 1.3, 33.0, desc="Nguồn cung cấp chất béo và Canxi dồi dào, hầu như không chứa Carbs."),
    F("Kem tươi (Heavy Cream)", "Heavy Cream", "fat", 340, 2.8, 2.6, 36.0, desc="Thành phần quan trọng để tăng độ béo cho các món trứng và sốt Keto."),

    # Thêm vào nhóm Proteins - Poultry
    F("Cánh gà (có da)", "Chicken Wing with Skin", "protein-fat", 203, 18.0, 0, 14.5, desc="Nguồn cung cấp chất béo và đạm cân bằng, lớp da chứa nhiều collagen và béo tốt cho Keto."),

    # Thêm vào nhóm Sauces & Fats
    F("Sốt Mayonnaise (Keto)", "Keto Mayonnaise", "fat", 680, 1.0, 1.0, 75.0, desc="Được làm từ dầu quả bơ hoặc dầu olive, không chứa đường, là nguồn cung cấp chất béo tập trung."),

    # Thêm vào nhóm Healthy Fats & Fruits
    F("Bơ sáp", "Avocado", "fat", 160, 2.0, 8.5, 14.7, desc="Siêu thực phẩm Keto giàu Kali và Acid Oleic, hỗ trợ tim mạch và cung cấp năng lượng sạch."),

    # Cập nhật nhóm Proteins - Meat (cho tỉ lệ mỡ cao hơn)
    F("Thịt ba chỉ (nhiều mỡ)", "Fatty Pork Belly", "fat-protein", 518, 9.0, 0, 53.0, desc="Phần thịt lý tưởng cho Keto, mỡ heo chứa Vitamin D và giúp hấp thụ các vitamin tan trong dầu từ rau củ."),

    # Thêm vào nhóm Healthy Fats & Plant Milks
    F("Nước cốt dừa đặc", "Coconut Cream Thick", "fat-mcts", 197, 2.0, 2.8, 21.3, desc="Giàu MCTs hỗ trợ đốt mỡ và cung cấp năng lượng nhanh cho não bộ."),

    # Thêm vào nhóm Vegetables
    F("Măng tây", "Asparagus", "vitamin-fiber", 20, 2.2, 3.9, 0.1, desc="Chứa Asparagine hỗ trợ lợi tiểu và làm sạch hệ thống, cực ít carbs."),

    # Cập nhật nhóm Healthy Fats & Nuts
    F("Hạt óc chó", "Walnuts", "fat", 654, 15.2, 13.7, 65.2, desc="Nguồn Omega-3 (ALA) thực vật dồi dào, hỗ trợ chức năng não và giảm viêm."),

    # Thêm vào nhóm Proteins - Meat
    F("Thịt heo vai sấn", "Fatty Pork Shoulder", "fat-protein", 320, 16.0, 0, 28.0, desc="Phần thịt có dải mỡ dày, lý tưởng để làm nhân nhồi giúp món hấp không bị khô và giàu năng lượng."),

    # Thêm vào nhóm Sauces & Fats
    F("Mỡ lợn (Lard)", "Lard", "fat", 902, 0, 0, 100.0, desc="Chất béo động vật chịu nhiệt tốt, chứa khoảng 40% chất béo bão hòa và giàu Vitamin D."),

    # Cập nhật nhóm Vegetables
    F("Súp lơ trắng", "Cauliflower", "low-carb-sub", 25, 1.9, 5.0, 0.3, desc="Nguyên liệu thay thế tinh bột hoàn hảo, giàu Vitamin C và hợp chất Sulforaphane."),

    # Thêm vào nhóm Vegetables
    F("Cà tím", "Eggplant", "fiber", 25, 1.0, 6.0, 0.2, desc="Giàu chất xơ và nước, cấu trúc mô xốp giúp hấp thụ chất béo và gia vị rất hiệu quả."),

    # Thêm vào nhóm Healthy Fats & Nuts
    F("Lạc (Đậu phộng) rang", "Roasted Peanuts", "fat-protein", 567, 25.8, 16.1, 49.2, desc="Nguồn cung cấp chất béo đơn không bão hòa (MUFA) và Protein thực vật dồi dào."),

    # Thêm vào nhóm Proteins - Seafood
    F("Cá ngừ ngâm dầu", "Canned Tuna in Oil", "protein-fat", 198, 26.0, 0, 10.0, desc="Nguồn đạm tiện lợi, giàu Omega-3; phần dầu giúp tăng mật độ năng lượng cho Keto."),

    # Thêm vào nhóm Proteins - Meat
    F("Sườn bẹ heo", "Pork Spareribs", "fat-protein", 395, 15.0, 0, 37.0, desc="Phần thịt có dải mỡ dày và lớp màng collagen, cung cấp lượng chất béo bão hòa lớn."),

    # Thêm vào nhóm Healthy Fats & Oils
    F("Dầu MCT", "MCT Oil", "fat", 834, 0, 0, 100.0, desc="Chất béo chuỗi trung bình chiết xuất từ dừa, hấp thụ trực tiếp qua gan để tạo năng lượng nhanh."),

    # Cập nhật nhóm Proteins - Meat
    F("Thịt thăn nội bò", "Beef Tenderloin", "protein", 250, 26.0, 0, 15.0, desc="Phần thịt bò nạc nhất, giàu sắt và kẽm, kết cấu mềm mịn phù hợp cho các món cuộn."),

    # Thêm vào nhóm Vegetables (Root & Cruciferous)
    F("Củ dền", "Beetroot", "detox", 43, 1.6, 9.6, 0.2, desc="Giàu Betalain và Nitrates tự nhiên, hỗ trợ giải độc gan và hạ huyết áp."),
    F("Bắp cải tím", "Purple Cabbage", "antioxidant", 31, 1.4, 7.4, 0.2, desc="Chứa Anthocyanin mạnh mẽ giúp chống viêm và bảo vệ sức khỏe tim mạch."),

    # Thêm vào nhóm Vegetables (Leafy & High-water)
    F("Cải bó xôi (Spinach)", "Spinach", "alkalizing", 23, 2.9, 3.6, 0.4, desc="Siêu thực phẩm giàu Sắt, Magie và Chlorophyll, hỗ trợ kiềm hóa máu mạnh mẽ."),
    F("Dưa chuột", "Cucumber", "hydration", 15, 0.7, 3.6, 0.1, desc="Chứa 95% là nước cùng các hợp chất silica giúp nuôi dưỡng làn da và hỗ trợ bài tiết."),

    # Thêm vào nhóm Vegetables & Seaweed
    F("Rong biển khô", "Dried Seaweed", "detox", 45, 3.0, 9.0, 0.5, desc="Nguồn I-ốt tự nhiên dồi dào, chứa Alginate giúp ngăn hấp thụ chất béo và đào thải kim loại nặng."),

    # Thêm vào nhóm Fruits/Sauce Base
    F("Chanh leo", "Passion Fruit", "vitamin", 97, 2.2, 23.0, 0.7, desc="Giàu Vitamin C và các hợp chất chống oxy hóa, giúp tăng cường miễn dịch và làm sạch mạch máu."),

    # Thêm vào nhóm Healthy Fats & Seeds
    F("Hạt lanh", "Flaxseed", "fat-fiber", 534, 18.3, 28.9, 42.2, desc="Giàu Omega-3 (ALA) và lignans, hỗ trợ tiêu hóa và cân bằng nội tiết tố."),

    # Thêm vào nhóm Spices & Herbs
    F("Nghệ tươi", "Fresh Turmeric", "anti-inflammatory", 52, 1.3, 10.0, 0.1, desc="Chứa Curcumin mạnh mẽ giúp kháng viêm, cần dùng kèm tiêu đen để tối ưu hấp thụ."),

    # Thêm vào nhóm Vegetables & Herbal
    F("Cần tây", "Celery", "alkalizing", 16, 0.7, 3.0, 0.2, desc="Chứa apigenin và các muối cụm khoáng giúp kháng viêm và trung hòa axit dạ dày."),

    # Thêm vào nhóm Healthy Dessert Materials
    F("Nhựa đào", "Peach Gum", "collagen", 35, 1.2, 8.5, 0.1, desc="Chứa hàm lượng lớn Galactose và axit uronic, hỗ trợ nhuận tràng và dưỡng ẩm cho da."),
    F("Tuyết yến", "Pith of Sterculia", "hydration", 25, 0.5, 6.0, 0, desc="Thực vật tiết ra nhựa giàu chất xơ hòa tan, giúp giữ nước cho tế bào và thải độc đường ruột."),

    # Thêm vào nhóm Smart Carbs - Rice products
    F("Bánh tráng gạo lứt", "Brown Rice Paper", "smart-carbs", 330, 4.0, 75.0, 1.5, desc="Sản phẩm gạo lứt giữ nguyên cám, cung cấp chất xơ và vitamin nhóm B."),

    # Thêm vào nhóm Vegetables
    F("Bí ngòi", "Zucchini", "hydration", 17, 1.2, 3.1, 0.3, desc="Thành phần chứa hơn 90% nước, giàu Kali giúp cân bằng điện giải và hỗ trợ hạ huyết áp."),

    # Thêm vào nhóm Smart Carbs - Grains
    F("Yến mạch cán dẹt", "Rolled Oats", "fiber", 389, 16.9, 66.3, 6.9, desc="Giàu Beta-glucan giúp hạ cholesterol và ổn định đường huyết."),

    # Thêm vào nhóm Seeds & Superfoods
    F("Hạt chia", "Chia Seeds", "superfood", 486, 16.5, 42.1, 30.7, desc="Cung cấp Omega-3 và chất xơ hòa tan cực cao, tạo độ kết dính tự nhiên cho món ăn."),

    # Thêm vào nhóm Smart Carbs - Legumes
    F("Đậu đen xanh lòng", "Green Kernel Black Beans", "detox", 341, 24.4, 63.3, 1.4, desc="Giàu Molybdenum và Anthocyanin giúp hỗ trợ giải độc sulfites và bảo vệ gan."),

    # Cập nhật nhóm Vegetables
    F("Súp lơ trắng", "Cauliflower", "low-carb-sub", 25, 1.9, 5.0, 0.3, desc="Thay thế tinh bột hoàn hảo, chứa hàm lượng Choline cao hỗ trợ chức năng não và chuyển hóa mỡ."),

    # Thêm vào nhóm Vegetables
    F("Cà chua bi", "Cherry Tomato", "antioxidant", 18, 0.9, 3.9, 0.2, desc="Nguồn Lycopene dồi dào, giúp chống lão hóa và bảo vệ da khỏi tác hại của tia UV."),

    # Thêm vào nhóm Pantry/Acidifiers
    F("Giấm táo hữu cơ", "Organic Apple Cider Vinegar", "digestive", 22, 0, 0.9, 0, desc="Chứa acid axetic và lợi khuẩn, giúp cân bằng pH dạ dày và hỗ trợ giảm cân."),

    # Thêm vào nhóm Beverages/Fermented
    F("Trà Kombucha", "Kombucha Tea", "probiotics", 20, 0, 5.0, 0, desc="Thức uống lên men từ trà và SCOBY, giàu lợi khuẩn, acid hữu cơ và enzyme hỗ trợ tiêu hóa."),

    # Thêm vào nhóm Vegetables
    F("Mướp hương", "Luffa", "hydration", 20, 0.9, 4.0, 0.2, desc="Chứa nhiều nước, chất nhầy tự nhiên và vitamin C, có tác dụng thanh nhiệt và làm đẹp da."),

    # Thêm vào nhóm Vegetables & Medicinal Herbs
    F("Ngải cứu", "Mugwort", "medicinal-herb", 40, 3.5, 6.0, 0.5, desc="Dược liệu có tính ấm, giúp hoạt huyết, điều kinh và giảm đau tự nhiên."),

    # Cập nhật nhóm Proteins - Plant-based
    F("Đậu hũ", "Tofu", "plant-protein", 76, 8.0, 1.9, 4.8, desc="Nguồn đạm đậu nành lành mạnh, chứa đầy đủ 9 axit béo thiết yếu và không có cholesterol."),

    # Thêm vào nhóm Vegetables - Green Leafy
    F("Rau muống", "Morning Glory", "iron-fiber", 19, 3.2, 3.1, 0.4, desc="Giàu sắt, canxi và chất xơ, giúp hỗ trợ hệ tiêu hóa và phòng ngừa thiếu máu."),

    # Cập nhật nhóm Healthy Fats & Nuts
    F("Lạc nhân (Đậu phộng)", "Peanuts Raw", "fat-protein", 567, 25.8, 16.1, 49.2, desc="Cung cấp Protein thực vật và MUFA, hỗ trợ sức khỏe tim mạch và cung cấp năng lượng lâu dài."),

]

def seed_foods():
    print("=" * 70)
    print("🚀 BẮT ĐẦU NẠP DỮ LIỆU THỰC PHẨM v2.1")
    print("-" * 70)
    
    count_success = 0
    count_skip = 0
    count_error = 0

    for data in FOODS_DATA:
        try:
            # 1. Kiểm tra trùng lặp
            existing = db.query(Food).filter(
                or_(
                    Food.name_vi == data["name_vi"],
                    Food.name_en == data["name_en"]
                )
            ).first()

            if existing:
                print(f"⏭️  Bỏ qua: {data['name_vi']} (Đã tồn tại)")
                count_skip += 1
                continue

            # 2. Tách dữ liệu servings
            servings_list = data.get("servings", [])
            
            # 3. Khởi tạo đối tượng Food
            new_food = Food(
                name_vi=data["name_vi"],
                name_en=data.get("name_en"),
                description=data.get("description"),
                category=data["category"],
                cuisine_type=data.get("cuisine_type"),
                calories_per_100g=Decimal(str(data["calories_per_100g"])),
                protein_per_100g=Decimal(str(data.get("protein_per_100g", 0))),
                carbs_per_100g=Decimal(str(data.get("carbs_per_100g", 0))),
                fat_per_100g=Decimal(str(data.get("fat_per_100g", 0))),
                fiber_per_100g=Decimal(str(data.get("fiber_per_100g", 0))),
                sugar_per_100g=Decimal(str(data.get("sugar_per_100g", 0))),
                sodium_per_100g=Decimal(str(data.get("sodium_per_100g", 0))),
                barcode=data.get("barcode"),
                image_url=data.get("image_url"),
                source="admin",
                is_verified=True,
                is_deleted=False
            )
            
            db.add(new_food)
            db.flush()  # Để lấy được new_food.food_id

            # 4. Tạo các bản ghi FoodServing liên quan
            for s in servings_list:
                new_serving = FoodServing(
                    food_id=new_food.food_id,
                    serving_unit=s["description"],  # Trường bắt buộc trong DB
                    description=s["description"],  # Trường tùy chọn (nullable)
                    serving_size_g=Decimal(str(s["size_g"])),
                    is_default=s.get("is_default", False)
                )
                db.add(new_serving)

            db.commit()
            count_success += 1
            print(f"✅ Đã nạp thành công: {data['name_vi']}")

        except Exception as e:
            db.rollback()
            print(f"❌ Lỗi tại món {data.get('name_vi', 'Unknown')}: {str(e)}")
            count_error += 1

    print("-" * 70)
    print(f"📊 TỔNG KẾT: Thành công: {count_success} | Bỏ qua: {count_skip} | Lỗi: {count_error}")
    print("=" * 70)

if __name__ == "__main__":
    if not FOODS_DATA:
        print("⚠️ Danh sách FOODS_DATA đang trống.")
    else:
        seed_foods()
    db.close()
    
    
    