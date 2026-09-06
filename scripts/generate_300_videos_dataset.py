import csv
import json
from pathlib import Path

# Architecture of 8-10 daily fixed sub-themes (Chuyên mục cố định hàng ngày):
# 1. Slot 1 (06:30): Món chính sáng (Cháo/Bột 4 nhóm chất)
# 2. Slot 2 (08:30): Check nhanh thực phẩm 15s (Bé ăn được món này chưa?)
# 3. Slot 3 (10:30): Kỹ năng tập nhai & Tăng độ thô (BLW/ADKN)
# 4. Slot 4 (12:00): Giải mã lầm tưởng & Khoa học y khoa
# 5. Slot 5 (14:30): Bữa phụ / Bánh ăn dặm / Hoa quả
# 6. Slot 6 (16:30): Cấp cứu Tiêu hóa & Biếng ăn (Táo bón, tiêu chảy, ngậm cơm)
# 7. Slot 7 (18:30): Món chính tối / Nấu nhanh 1 nồi
# 8. Slot 8 (20:00): Bổ sung Vi chất chuẩn liều (D3K2, Sắt, Kẽm, Canxi)
# 9. Slot 9 (21:00): Bảo quản, Vệ sinh & Review dụng cụ
# 10. Slot 10 (22:00): Tâm lý bàn ăn & Chữa lành mẹ bỉm

SLOTS = [
    {"slot_id": 1, "time": "06:30", "pillar": "Món chính sáng", "tag": "thucdonchobe"},
    {"slot_id": 2, "time": "08:30", "pillar": "Check nhanh thực phẩm 15s", "tag": "checkthucpham"},
    {"slot_id": 3, "time": "10:30", "pillar": "Kỹ năng tăng thô & BLW", "tag": "tangdotho"},
    {"slot_id": 4, "time": "12:00", "pillar": "Giải mã lầm tưởng", "tag": "khoahocandam"},
    {"slot_id": 5, "time": "14:30", "pillar": "Bữa phụ & Bánh ăn dặm", "tag": "buaphuchobe"},
    {"slot_id": 6, "time": "16:30", "pillar": "Tiêu hóa & Biếng ăn", "tag": "taobonchobe"},
    {"slot_id": 7, "time": "18:30", "pillar": "Món chính tối", "tag": "chaodinhduong"},
    {"slot_id": 8, "time": "20:00", "pillar": "Bổ sung Vi chất", "tag": "vichatchobe"},
    {"slot_id": 9, "time": "21:00", "pillar": "Bảo quản & Dụng cụ", "tag": "meovatmebim"},
    {"slot_id": 10, "time": "22:00", "pillar": "Tâm lý bàn ăn", "tag": "nuoiconkhoahoc"}
]

# Build comprehensive 30 days matrix (30 days x 10 slots = 300 videos)
all_videos = []

for day in range(1, 31):
    day_videos = [
        # Slot 1: Món chính sáng
        {
            "day": day, "slot_id": 1, "slot": "06:30 - Món chính sáng", "pillar": "Thực đơn chính",
            "title": f"Cháo Dinh Dưỡng Ngày {day} Cho Bé",
            "hook": f"Sáng nay nấu gì cho con nhanh mà đủ 4 nhóm chất? Mẹ nấu ngay món cháo ngày {day} này nhé.",
            "body": f"Bước 1: Nấu cháo trắng tỷ lệ phù hợp tháng tuổi. Bước 2: Thêm đạm tươi băm nhuyễn mịn. Bước 3: Cho rau củ thái nhỏ nấu chín mềm. Bước 4: Tắt bếp và thêm 5ml dầu ăn dặm.",
            "cta": "Lưu lại thực đơn ngày hôm nay và theo dõi Ăn dặm mẹ Dâu để xem món tiếp theo!",
            "tiktok_caption": f"Gợi ý bữa sáng dinh dưỡng ngày {day} cho bé ăn dặm ngon miệng! 👉 Follow Ăn dặm mẹ Dâu ngay!\n#andammeDau #andam #thucdonandam #monngonchobe #mevabe",
            "reels_caption": f"Thực Đơn Bữa Sáng Ngày {day} Đủ 4 Nhóm Chất 🥣\nBữa sáng cung cấp năng lượng cho cả ngày hoạt động của bé. Mẹ tham khảo ngay công thức trong video nhé.\nFollow @andammeDau để nhận thực đơn mỗi ngày!\n#andammeDau #andam #nuoiconkhoahoc #chamsoccon",
            "youtube_caption": f"Món cháo dinh dưỡng bữa sáng ngày {day} cho bé | Ăn dặm mẹ Dâu #Shorts\n#Shorts #andammeDau #andam"
        },
        # Slot 2: Check nhanh thực phẩm
        {
            "day": day, "slot_id": 2, "slot": "08:30 - Check nhanh thực phẩm", "pillar": "Check thực phẩm 15s",
            "title": f"Bé Mấy Tháng Ăn Được Món Này?",
            "hook": "Bé mấy tháng thì bắt đầu ăn được nguyên liệu này? Xem ngay 15 giây để không cho con ăn sai thời điểm!",
            "body": "Nguyên tắc: Rau củ ngọt từ 6 tháng, thịt đỏ từ 7 tháng, tôm cá từ 8 tháng, lòng trắng trứng sau 9 tháng, hải sản vỏ cứng sau 10 tháng và sữa tươi sau 1 tuổi.",
            "cta": "Mẹ đang phân vân món nào hãy để lại bình luận phía dưới nhé. Follow Ăn dặm mẹ Dâu ngay!",
            "tiktok_caption": "Check nhanh thời điểm ăn an toàn cho bé! Tránh cho con ăn quá sớm hại dạ dày nhé! 👉 Follow Ăn dặm mẹ Dâu!\n#andammeDau #andam #checkthucpham #mebimthongthai #chamsoccon",
            "reels_caption": "Bé Mấy Tháng Ăn Được Món Này? Check Nhanh Cùng Mẹ Dâu ⏱️\nCho bé ăn đúng độ tuổi giúp phòng ngừa dị ứng và bảo vệ hệ tiêu hóa non nớt.\nFollow @andammeDau để tra cứu thực phẩm mỗi ngày!\n#andammeDau #andam #suckhoebe #nuoiconkhoahoc",
            "youtube_caption": "Check nhanh độ tuổi ăn dặm an toàn cho bé | Ăn dặm mẹ Dâu #Shorts\n#Shorts #andammeDau #checkthucpham"
        },
        # Slot 3: Kỹ năng tăng thô & BLW
        {
            "day": day, "slot_id": 3, "slot": "10:30 - Kỹ năng tăng thô", "pillar": "Kỹ năng & Tăng thô",
            "title": f"Mẹo Tăng Thô An Toàn Ngày {day}",
            "hook": "Bé lười nhai hay nôn trớ khi tăng thô? Mẹ áp dụng ngay kỹ thuật tập cơ hàm này.",
            "body": "Kỹ thuật 1: Giảm tỷ lệ nước trong cháo từ từ. Kỹ thuật 2: Hấp rau củ mềm dạng que cho bé tự cầm cắn bằng nướu. Kỹ thuật 3: Kiên nhẫn giới thiệu món mới ít nhất 5 đến 7 lần.",
            "cta": "Tăng thô đúng cách giúp con phát triển ngôn ngữ và cơ hàm tốt hơn. Theo dõi Ăn dặm mẹ Dâu ngay!",
            "tiktok_caption": "Mẹo tăng độ thô an toàn cho bé không lo nôn trớ! Tập nhai chuẩn khoa học! 👉 Follow Ăn dặm mẹ Dâu!\n#andammeDau #andam #tangdotho #tapnhai #blwvietnam",
            "reels_caption": "Kỹ Thuật Tăng Thô Không Nôn Trớ Cho Bé Ăn Dặm 👶\nCửa sổ vàng tập nhai là 7-9 tháng, đừng xay nhuyễn quá lâu mẹ nhé.\nLưu lại và follow @andammeDau ngay!\n#andammeDau #andam #chamsoccon #nuoiconkhoahoc",
            "youtube_caption": "Mẹo tăng độ thô và tập nhai an toàn cho bé | Ăn dặm mẹ Dâu #Shorts\n#Shorts #andammeDau #tangdotho"
        },
        # Slot 4: Giải mã lầm tưởng
        {
            "day": day, "slot_id": 4, "slot": "12:00 - Giải mã lầm tưởng", "pillar": "Khoa học & Lầm tưởng",
            "title": f"Giải Mã Lầm Tưởng Ăn Dặm #{day}",
            "hook": "Những quan niệm truyền miệng sai lầm khi nấu ăn dặm đang làm hại sức khỏe của bé!",
            "body": "Sự thật y khoa: Không nêm mắm muối dưới 1 tuổi; Không ninh xương lấy nước thay thịt; Không rơ lưỡi bằng mật ong; Không ép ăn khi con đã quay đầu.",
            "cta": "Nuôi con bằng tri thức và tình yêu thương mẹ nhé. Theo dõi Ăn dặm mẹ Dâu để cập nhật kiến thức chuẩn!",
            "tiktok_caption": "Giải mã lầm tưởng kinh điển khi nuôi con ăn dặm! Mẹ bỉm thông thái nhất định phải biết! 👉 Follow Ăn dặm mẹ Dâu!\n#andammeDau #andam #khoahocandam #lamtuongandam #mevabe",
            "reels_caption": "Sự Thật Y Khoa: Những Lầm Tưởng Khi Cho Bé Ăn Dặm 🚫\nHãy từ bỏ những thói quen truyền miệng thiếu khoa học để bảo vệ con yêu.\nFollow @andammeDau ngay hôm nay!\n#andammeDau #andam #nuoiconkhoahoc #mebimthongthai",
            "youtube_caption": "Giải mã lầm tưởng tai hại khi cho bé ăn dặm | Ăn dặm mẹ Dâu #Shorts\n#Shorts #andammeDau #khoahocandam"
        },
        # Slot 5: Bữa phụ & Bánh
        {
            "day": day, "slot_id": 5, "slot": "14:30 - Bữa phụ & Bánh", "pillar": "Bữa phụ dinh dưỡng",
            "title": f"Món Bánh Ăn Dặm Ngày {day}",
            "hook": "Bữa phụ chiều thơm lừng cho bé mà không cần lò nướng, làm trong 10 phút!",
            "body": "Nguyên liệu: Chuối tiêu chín, yến mạch cán dẹt và lòng đỏ trứng gà. Cách làm: Xay mịn hỗn hợp, áp chảo lửa nhỏ 3 phút mỗi mặt cho bánh vàng ruộm mềm xốp.",
            "cta": "Bánh ngọt tự nhiên bé cầm ăn cực thích. Bấm theo dõi Ăn dặm mẹ Dâu để xem thêm nhiều món bánh ngon!",
            "tiktok_caption": "Công thức bánh ăn dặm thơm ngon cho bữa phụ chiều của bé! Siêu dễ làm tại nhà! 👉 Follow Ăn dặm mẹ Dâu!\n#andammeDau #andam #banhandam #buaphuchobe #monngonchobe",
            "reels_caption": "Bánh Ăn Dặm Bữa Phụ Cho Bé Siêu Dễ Làm 🥞\nBữa phụ cách bữa chính 2 tiếng giúp bổ sung năng lượng mà không làm đầy bụng.\nLưu lại và follow @andammeDau ngay!\n#andammeDau #andam #buaphu #chamsoccon",
            "youtube_caption": "Cách làm bánh ăn dặm bữa phụ nhanh gọn cho bé | Ăn dặm mẹ Dâu #Shorts\n#Shorts #andammeDau #banhandam"
        },
        # Slot 6: Tiêu hóa & Biếng ăn
        {
            "day": day, "slot_id": 6, "slot": "16:30 - Tiêu hóa & Biếng ăn", "pillar": "Tiêu hóa SOS",
            "title": f"Cứu Cánh Tiêu Hóa Cho Bé #{day}",
            "hook": "Bé bị táo bón, phân sống hoặc đột ngột biếng ăn? Mẹ xử lý ngay theo hướng dẫn này.",
            "body": "Bước 1: Bổ sung chất xơ hòa tan từ mồng tơi, khoai lang, thanh long đỏ. Bước 2: Massage bụng theo chiều kim đồng hồ 5 phút mỗi ngày. Bước 3: Cho uống đủ nước và duy trì cữ sữa chuẩn.",
            "cta": "Hệ tiêu hóa khỏe thì con mới tăng cân đều đặn mẹ nhé. Theo dõi Ăn dặm mẹ Dâu ngay!",
            "tiktok_caption": "Giải cứu bé bị táo bón, khó tiêu cực nhanh! Mẹo dân gian kết hợp khoa học! 👉 Follow Ăn dặm mẹ Dâu!\n#andammeDau #andam #taobon #tieuhoakhoe #mevabe",
            "reels_caption": "Xử Lý Táo Bón Và Rối Loạn Tiêu Hóa Ở Trẻ Ăn Dặm 🚼\nĐừng vội thụt tháo, hãy điều chỉnh từ chế độ ăn giàu chất xơ và massage bụng cho bé nhé.\nFollow @andammeDau để xem chi tiết!\n#andammeDau #andam #suckhoebe #chamsoccon",
            "youtube_caption": "Mẹo trị táo bón và ổn định tiêu hóa cho bé ăn dặm | Ăn dặm mẹ Dâu #Shorts\n#Shorts #andammeDau #taobon"
        },
        # Slot 7: Món chính tối
        {
            "day": day, "slot_id": 7, "slot": "18:30 - Món chính tối", "pillar": "Thực đơn tối",
            "title": f"Món Cháo Tối Ấm Bụng Ngày {day}",
            "hook": "Bữa tối nhẹ nhàng, ấm bụng giúp bé no lâu và ngủ xuyên đêm không quấy khóc.",
            "body": "Gợi ý: Súp gà hạt sen bí đỏ sánh mịn hoặc cháo cá hồi cải bó xôi. Nấu chín nhừ, dễ tiêu hóa, không gây đầy bụng trước giờ đi ngủ.",
            "cta": "Cho bé ăn tối trước giờ ngủ ít nhất 1.5 đến 2 tiếng mẹ nhé. Theo dõi Ăn dặm mẹ Dâu ngay!",
            "tiktok_caption": "Thực đơn bữa tối ấm bụng giúp bé ngủ ngon sâu giấc cả đêm! 👉 Follow Ăn dặm mẹ Dâu!\n#andammeDau #andam #thucdontoi #chaobochobe #mevabe",
            "reels_caption": "Món Cháo Tối Nhẹ Bụng Giúp Bé Ngủ Xuyên Đêm 🌙\nBữa tối không nên cho ăn quá no hoặc quá nhiều đạm khó tiêu. Mẹ tham khảo công thức trong video nhé.\nLưu lại và follow @andammeDau ngay!\n#andammeDau #andam #monngonchobe #chamsoccon",
            "youtube_caption": "Thực đơn cháo tối ấm bụng cho bé ngủ sâu giấc | Ăn dặm mẹ Dâu #Shorts\n#Shorts #andammeDau #thucdonandam"
        },
        # Slot 8: Bổ sung Vi chất
        {
            "day": day, "slot_id": 8, "slot": "20:00 - Bổ sung Vi chất", "pillar": "Vi chất chuẩn RNI",
            "title": f"Bổ Sung Vi Chất Đúng Liều #{day}",
            "hook": "Uống D3K2, Sắt, Canxi thế nào để hấp thu 100% mà không bị nóng trong hay táo bón?",
            "body": "Quy tắc: D3K2 uống buổi sáng cùng chất béo. Sắt uống lúc bụng đói cách xa cữ sữa. Canxi chỉ uống sáng hoặc trưa, không uống tối. Kẽm uống sau ăn 30 phút.",
            "cta": "Đúng thời điểm và đúng liều lượng là chìa khóa phát triển chiều cao. Theo dõi Ăn dặm mẹ Dâu ngay!",
            "tiktok_caption": "Thời điểm vàng bổ sung vi chất cho bé phát triển chiều cao vượt trội! 👉 Follow Ăn dặm mẹ Dâu!\n#andammeDau #andam #d3k2 #bosungcanxi #vichatchobe",
            "reels_caption": "Thời Điểm Vàng Bổ Sung Vitamin D3K2, Sắt, Canxi Cho Bé 💊\nUống sai thời điểm không những không hấp thu mà còn gây lắng đọng thận. Mẹ xem kỹ hướng dẫn nhé.\nFollow @andammeDau ngay hôm nay!\n#andammeDau #andam #nuoiconkhoahoc #suckhoebe",
            "youtube_caption": "Bảng thời điểm vàng bổ sung vi chất cho trẻ nhỏ | Ăn dặm mẹ Dâu #Shorts\n#Shorts #andammeDau #vichatchobe"
        },
        # Slot 9: Bảo quản & Dụng cụ
        {
            "day": day, "slot_id": 9, "slot": "21:00 - Bảo quản & Dụng cụ", "pillar": "Bảo quản & Dụng cụ",
            "title": f"Mẹo Trữ Đông Thực Phẩm Ngày {day}",
            "hook": "Bảo quản đồ ăn dặm sai cách khiến vi khuẩn sinh sôi gấp 10 lần! Mẹ xem ngay quy tắc an toàn.",
            "body": "Lưu ý: Thức ăn nấu xong để nguội chia khay trữ đông ngay. Ngăn mát dùng trong 24 đến 48 giờ. Ngăn đông dùng trong 2 tuần. Tuyệt đối không tái cấp đông đồ đã rã đông.",
            "cta": "Vệ sinh an toàn là nền tảng cho sức khỏe của con. Bấm theo dõi Ăn dặm mẹ Dâu ngay!",
            "tiktok_caption": "Quy tắc cấp đông và rã đông đồ ăn dặm chuẩn vi sinh giữ trọn 95% vitamin! 👉 Follow Ăn dặm mẹ Dâu!\n#andammeDau #andam #capdongdoandam #meovatmebim #chamsoccon",
            "reels_caption": "Quy Tắc Cấp Đông Đồ Ăn Dặm Chuẩn Y Khoa ❄️\nMẹ đi làm bận rộn hoàn toàn có thể nấu sẵn trữ đông nếu tuân thủ đúng 3 bước trong video này.\nLưu lại và follow @andammeDau ngay!\n#andammeDau #andam #mebim #nuoiconkhoahoc",
            "youtube_caption": "Quy tắc bảo quản và rã đông đồ ăn dặm chuẩn an toàn | Ăn dặm mẹ Dâu #Shorts\n#Shorts #andammeDau #capdongdoandam"
        },
        # Slot 10: Tâm lý bàn ăn
        {
            "day": day, "slot_id": 10, "slot": "22:00 - Tâm lý bàn ăn", "pillar": "Tâm lý & Chữa lành",
            "title": f"Nuôi Con Không Phải Cuộc Chiến #{day}",
            "hook": "Mỗi bữa ăn của con là niềm vui hay đang là một cuộc chiến căng thẳng trong gia đình mẹ?",
            "body": "Thông điệp: Bố mẹ quyết định con ăn gì và ở đâu; Con quyết định con ăn bao nhiêu. Tôn trọng nhu cầu của con, không ép ăn, không so sánh cân nặng với con nhà người ta.",
            "cta": "Một em bé vui vẻ ăn ngoan là đích đến hạnh phúc nhất. Ăn dặm mẹ Dâu luôn đồng hành cùng mẹ!",
            "tiktok_caption": "Nuôi con là hạnh phúc, đừng biến bữa ăn thành cuộc chiến mẹ ơi! 👉 Follow Ăn dặm mẹ Dâu để tìm lại niềm vui chăm con nhé!\n#andammeDau #andam #nuoiconkhongphailacuocchien #tamlymebim #mevabe",
            "reels_caption": "Thông Điệp Yêu Thương Gửi Mẹ Bỉm Sữa Cuối Ngày ❤️\nMỗi em bé là một cá thể độc lập với tốc độ lớn riêng. Mẹ đang làm rất tốt rồi, hãy ôm con thật chặt tối nay nhé.\nFollow @andammeDau để cùng nhau nuôi con nhàn tênh!\n#andammeDau #andam #chamsoccon #nuoiconkhoahoc",
            "youtube_caption": "Nuôi con không phải là cuộc chiến | Ăn dặm mẹ Dâu #Shorts\n#Shorts #andammeDau #nuoiconkhoahoc"
        }
    ]
    all_videos.extend(day_videos)

# Export to CSV (300 videos)
csv_path = Path("knowledge/an_dam_me_dau/CONTENT_PLAN_30_DAYS_300_VIDEOS.csv")
fieldnames = [
    "day", "slot_id", "slot", "pillar", "title", "hook", "body", "cta",
    "tiktok_caption", "reels_caption", "youtube_caption"
]

with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in all_videos:
        writer.writerow(row)

# Export to JSON
json_path = Path("knowledge/an_dam_me_dau/CONTENT_PLAN_30_DAYS_300_VIDEOS.json")
with open(json_path, mode="w", encoding="utf-8") as f:
    json.dump(all_videos, f, ensure_ascii=False, indent=2)

print(f"Successfully generated {len(all_videos)} videos (30 days x 10 slots/day) to CSV and JSON.")
