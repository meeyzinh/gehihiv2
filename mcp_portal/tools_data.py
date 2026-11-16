"""
Kho dữ liệu phong phú phục vụ 78 Công cụ MCP Portal
Không sử dụng mock/TODO - Toàn bộ dữ liệu thực tế, chuẩn tiếng Việt
"""

# ==============================================================================
# 1. 63 TỈNH THÀNH VIỆT NAM (TỌA ĐỘ DỰ BÁO THỜI TIẾT + MÃ BIỂN SỐ XE)
# ==============================================================================
PROVINCES_63 = {
    "hà nội": {"name": "Hà Nội", "lat": 21.0285, "lon": 105.8542, "plates": ["29", "30", "31", "32", "33", "40"]},
    "hồ chí minh": {"name": "TP. Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297, "plates": ["41", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59"]},
    "tp hcm": {"name": "TP. Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297, "plates": ["41", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59"]},
    "sài gòn": {"name": "TP. Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297, "plates": ["41", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59"]},
    "hải phòng": {"name": "Hải Phòng", "lat": 20.8449, "lon": 106.6881, "plates": ["15", "16"]},
    "đà nẵng": {"name": "Đà Nẵng", "lat": 16.0544, "lon": 108.2022, "plates": ["43"]},
    "cần thơ": {"name": "Cần Thơ", "lat": 10.0452, "lon": 105.7469, "plates": ["65"]},
    "an giang": {"name": "An Giang", "lat": 10.5216, "lon": 105.1259, "plates": ["67"]},
    "bà rịa - vũng tàu": {"name": "Bà Rịa - Vũng Tàu", "lat": 10.5417, "lon": 107.2429, "plates": ["72"]},
    "vũng tàu": {"name": "Bà Rịa - Vũng Tàu", "lat": 10.5417, "lon": 107.2429, "plates": ["72"]},
    "bắc giang": {"name": "Bắc Giang", "lat": 21.2731, "lon": 106.1946, "plates": ["98"]},
    "bắc kạn": {"name": "Bắc Kạn", "lat": 22.1470, "lon": 105.8348, "plates": ["97"]},
    "bạc liêu": {"name": "Bạc Liêu", "lat": 9.2941, "lon": 105.7278, "plates": ["94"]},
    "bắc ninh": {"name": "Bắc Ninh", "lat": 21.1861, "lon": 106.0763, "plates": ["99"]},
    "bến tre": {"name": "Bến Tre", "lat": 10.2415, "lon": 106.3759, "plates": ["71"]},
    "bình định": {"name": "Bình Định", "lat": 14.1667, "lon": 108.9000, "plates": ["77"]},
    "bình dương": {"name": "Bình Dương", "lat": 11.1603, "lon": 106.6575, "plates": ["61"]},
    "bình phước": {"name": "Bình Phước", "lat": 11.7511, "lon": 106.9048, "plates": ["93"]},
    "bình thuận": {"name": "Bình Thuận", "lat": 11.0903, "lon": 108.0722, "plates": ["86"]},
    "cà mau": {"name": "Cà Mau", "lat": 9.1769, "lon": 105.1524, "plates": ["69"]},
    "cao bằng": {"name": "Cao Bằng", "lat": 22.6667, "lon": 106.2500, "plates": ["11"]},
    "đắk lắk": {"name": "Đắk Lắk", "lat": 12.6667, "lon": 108.0500, "plates": ["47"]},
    "đắk nông": {"name": "Đắk Nông", "lat": 12.0040, "lon": 107.6875, "plates": ["48"]},
    "điện biên": {"name": "Điện Biên", "lat": 21.3833, "lon": 103.0167, "plates": ["27"]},
    "đồng nai": {"name": "Đồng Nai", "lat": 11.0500, "lon": 107.0167, "plates": ["39", "60"]},
    "đồng tháp": {"name": "Đồng Tháp", "lat": 10.4500, "lon": 105.6333, "plates": ["66"]},
    "gia lai": {"name": "Gia Lai", "lat": 13.9833, "lon": 108.0000, "plates": ["81"]},
    "hà giang": {"name": "Hà Giang", "lat": 22.8233, "lon": 104.9839, "plates": ["23"]},
    "hà nam": {"name": "Hà Nam", "lat": 20.5833, "lon": 105.9167, "plates": ["90"]},
    "hà tĩnh": {"name": "Hà Tĩnh", "lat": 18.3333, "lon": 105.9000, "plates": ["38"]},
    "hải dương": {"name": "Hải Dương", "lat": 20.9333, "lon": 106.3167, "plates": ["34"]},
    "hậu giang": {"name": "Hậu Giang", "lat": 9.7833, "lon": 105.4667, "plates": ["95"]},
    "hòa bình": {"name": "Hòa Bình", "lat": 20.8167, "lon": 105.3333, "plates": ["28"]},
    "hưng yên": {"name": "Hưng Yên", "lat": 20.6500, "lon": 106.0500, "plates": ["89"]},
    "khánh hòa": {"name": "Khánh Hòa", "lat": 12.2500, "lon": 109.1833, "plates": ["79"]},
    "nha trang": {"name": "Khánh Hòa", "lat": 12.2500, "lon": 109.1833, "plates": ["79"]},
    "kiên giang": {"name": "Kiên Giang", "lat": 10.0167, "lon": 105.0833, "plates": ["68"]},
    "phú quốc": {"name": "Kiên Giang (Phú Quốc)", "lat": 10.2289, "lon": 103.9572, "plates": ["68"]},
    "kon tum": {"name": "Kon Tum", "lat": 14.3500, "lon": 108.0000, "plates": ["82"]},
    "lai châu": {"name": "Lai Châu", "lat": 22.4000, "lon": 103.4667, "plates": ["25"]},
    "lâm đồng": {"name": "Lâm Đồng", "lat": 11.9404, "lon": 108.4583, "plates": ["49"]},
    "đà lạt": {"name": "Lâm Đồng (Đà Lạt)", "lat": 11.9404, "lon": 108.4583, "plates": ["49"]},
    "lạng sơn": {"name": "Lạng Sơn", "lat": 21.8500, "lon": 106.7500, "plates": ["12"]},
    "lào cai": {"name": "Lào Cai", "lat": 22.4833, "lon": 103.9667, "plates": ["24"]},
    "sa pa": {"name": "Lào Cai (Sa Pa)", "lat": 22.3364, "lon": 103.8438, "plates": ["24"]},
    "long an": {"name": "Long An", "lat": 10.5333, "lon": 106.4000, "plates": ["62"]},
    "nam định": {"name": "Nam Định", "lat": 20.4167, "lon": 106.1667, "plates": ["18"]},
    "nghệ an": {"name": "Nghệ An", "lat": 18.6667, "lon": 105.6667, "plates": ["37"]},
    "ninh bình": {"name": "Ninh Bình", "lat": 20.2500, "lon": 105.9667, "plates": ["35"]},
    "ninh thuận": {"name": "Ninh Thuận", "lat": 11.5667, "lon": 108.9833, "plates": ["85"]},
    "phú thọ": {"name": "Phú Thọ", "lat": 21.3167, "lon": 105.2167, "plates": ["19"]},
    "phú yên": {"name": "Phú Yên", "lat": 13.0833, "lon": 109.3000, "plates": ["78"]},
    "quảng bình": {"name": "Quảng Bình", "lat": 17.4833, "lon": 106.6000, "plates": ["73"]},
    "quảng nam": {"name": "Quảng Nam", "lat": 15.5667, "lon": 108.4833, "plates": ["92"]},
    "quảng ngãi": {"name": "Quảng Ngãi", "lat": 15.1167, "lon": 108.8000, "plates": ["76"]},
    "quảng ninh": {"name": "Quảng Ninh", "lat": 21.0067, "lon": 107.2925, "plates": ["14"]},
    "hạ long": {"name": "Quảng Ninh (Hạ Long)", "lat": 20.9500, "lon": 107.0833, "plates": ["14"]},
    "quảng trị": {"name": "Quảng Trị", "lat": 16.7500, "lon": 107.1833, "plates": ["74"]},
    "sóc trăng": {"name": "Sóc Trăng", "lat": 9.6000, "lon": 105.9667, "plates": ["83"]},
    "sơn la": {"name": "Sơn La", "lat": 21.3167, "lon": 103.9000, "plates": ["26"]},
    "tây ninh": {"name": "Tây Ninh", "lat": 11.3000, "lon": 106.1000, "plates": ["70"]},
    "thái bình": {"name": "Thái Bình", "lat": 20.4500, "lon": 106.3333, "plates": ["17"]},
    "thái nguyên": {"name": "Thái Nguyên", "lat": 21.5833, "lon": 105.8333, "plates": ["20"]},
    "thanh hóa": {"name": "Thanh Hóa", "lat": 19.8000, "lon": 105.7667, "plates": ["36"]},
    "thừa thiên huế": {"name": "Thừa Thiên Huế", "lat": 16.4667, "lon": 107.6000, "plates": ["75"]},
    "huế": {"name": "Thừa Thiên Huế", "lat": 16.4667, "lon": 107.6000, "plates": ["75"]},
    "tiền giang": {"name": "Tiền Giang", "lat": 10.3500, "lon": 106.3500, "plates": ["63"]},
    "trà vinh": {"name": "Trà Vinh", "lat": 9.9333, "lon": 106.3333, "plates": ["84"]},
    "tuyên quang": {"name": "Tuyên Quang", "lat": 21.8167, "lon": 105.2167, "plates": ["22"]},
    "vĩnh long": {"name": "Vĩnh Long", "lat": 10.2500, "lon": 105.9667, "plates": ["64"]},
    "vĩnh phúc": {"name": "Vĩnh Phúc", "lat": 21.3000, "lon": 105.6000, "plates": ["88"]},
    "yên bái": {"name": "Yên Bái", "lat": 21.7000, "lon": 104.8667, "plates": ["21"]}
}

PLATE_TO_PROVINCE = {}
for p_info in PROVINCES_63.values():
    p_name = p_info["name"]
    for plate in p_info["plates"]:
        PLATE_TO_PROVINCE[plate] = p_name

# Biển số xe đặc biệt
SPECIAL_PLATES = {
    "80": "Cục Cảnh sát Giao thông, cơ quan thuộc khối Trung ương Đảng, Nhà nước",
    "AA": "Quân đội - Quân đoàn 1",
    "BB": "Quân đội - Quân đoàn 2",
    "CC": "Quân đội - Quân đoàn 3",
    "DD": "Quân đội - Quân đoàn 4",
    "BK": "Quân đội - Binh chủng Đặc công",
    "BP": "Bộ đội Biên phòng",
    "TC": "Tổng cục Hậu cần",
    "TM": "Bộ Tổng tham mưu"
}

# ==============================================================================
# 2. TỪ ĐIỂN TIẾNG LÓNG GEN Z
# ==============================================================================
GENZ_SLANG = {
    "chầm kẽm": {"nghia": "Trầm cảm, mệt mỏi, áp lực tinh thần hoặc bực bội nhẹ nhàng.", "vidu": "Hôm nay deadline dí muốn chầm kẽm luôn á."},
    "gét gô": {"nghia": "Let's go, biểu thị quyết tâm làm một việc gì đó bất chấp khó khăn.", "vidu": "Thử thách ôn thi 1 đêm 5 môn, gét gô!"},
    "xu cà na": {"nghia": "Xui xẻo, gặp vận đen, chuyện không may xảy ra.", "vidu": "Sáng đi thi quên mang bút, đúng là xu cà na."},
    "u là trời": {"nghia": "Biến âm của 'Úi trời ơi', thốt lên khi bất ngờ hoặc ngỡ ngàng.", "vidu": "U là trời, sao cái áo này đẹp dữ vậy nè!"},
    "mlem mlem": {"nghia": "Khen món ăn ngon hoặc người nào đó quyến rũ, ưa nhìn.", "vidu": "Đĩa sườn nướng này trông mlem mlem quá."},
    "cột sống": {"nghia": "Chơi chữ từ 'cuộc sống', than thở về đau lưng hoặc gánh nặng người lớn.", "vidu": "Mới 20 tuổi mà cột sống này bất ổn quá."},
    "ô dề": {"nghia": "Làm quá lố, làm quá mức cần thiết dẫn đến hài hước hoặc lố lăng.", "vidu": "Trang điểm sương sương thôi chứ đừng làm ô dề quá nha."},
    "bão táp": {"nghia": "Ngầu, cuốn hút, đỉnh cao.", "vidu": "Quả visual hôm nay hơi bị bão táp luôn."},
    "flex": {"nghia": "Khoe khoang thành tích, của cải hay điểm mạnh một cách tự hào.", "vidu": "Anh ấy vừa flex học bổng toàn phần du học Mỹ."},
    "check var": {"nghia": "Kiểm tra tính xác thực, đối chứng lời nói xem có bốc phét không.", "vidu": "Để tôi check var xem ông này nói thật hay chém gió."},
    "phong sát": {"nghia": "Tẩy chay triệt để, cấm sóng hoàn toàn một nhân vật.", "vidu": "Nghệ sĩ vướng scandal lớn bị cộng đồng mạng phong sát."},
    "mai đẹt-ti-ni": {"nghia": "My destiny - định mệnh đời tôi, người yêu định mệnh.", "vidu": "Gặp được em đúng là mai đẹt ti ni của đời anh."},
    "luvyu": {"nghia": "Love you (yêu bạn, thương bạn).", "vidu": "Cảm ơn mày đã mua trà sữa cho tao, luvyuuu."},
    "cà khịa": {"nghia": "Chọc ghẹo, nói móc một cách hài hước, giải trí.", "vidu": "Thích đi cà khịa bạn bè cho vui cửa vui nhà."},
    "simp": {"nghia": "Mê muội, chiều chuộng người mình thích một cách mù quáng vô điều kiện.", "vidu": "Thằng bạn tôi đúng là chúa simp, bồ nói gì cũng nghe."},
    "red flag": {"nghia": "Dấu hiệu cảnh báo nguy hiểm trong mối quan hệ (người độc hại, thiếu tin cậy).", "vidu": "Mới quen mà kiểm soát tin nhắn là red flag to đùng."},
    "green flag": {"nghia": "Tín hiệu an toàn, người tử tế, biết lắng nghe và tôn trọng bạn.", "vidu": "Anh ấy luôn nhớ sở thích của bạn gái, chuẩn green flag."},
    "overthinking": {"nghia": "Suy nghĩ quá nhiều, tự vẽ ra kịch bản tiêu cực trong đầu.", "vidu": "Nửa đêm hay nằm overthinking về tương lai."},
    "healing": {"nghia": "Chữa lành tâm hồn, nghỉ ngơi, đi du lịch để giải tỏa stress.", "vidu": "Cuối tuần đi Đà Lạt một chuyến để healing thôi."},
    "slay": {"nghia": "Làm cực kỳ tốt, xuất sắc, đỉnh cao, tỏa sáng rực rỡ.", "vidu": "Bộ outfit hôm nay slay hết phần thiên hạ luôn chị ơi."},
    "rizz": {"nghia": "Sức hút cá nhân, tài ăn nói tán tỉnh khiến người khác rung động.", "vidu": "Anh chàng có charisma cực đỉnh, chuẩn rizz god."},
    "xịt keo": {"nghia": "Đứng hình, sững sờ không nói nên lời trước một tình huống bất ngờ.", "vidu": "Nghe tin người yêu cũ đi lấy chồng mà tôi xịt keo cứng ngắc."},
    "đúng nhận sai cãi": {"nghia": "Câu nói bắt trend xem bói bổ cau, ý bảo phải thừa nhận không được cãi.", "vidu": "Mày lười học nhất nhà đúng nhận sai cãi cho tao!"},
    "tinh hoa hội tụ": {"nghia": "Gom hết những thứ tinh túy, hoặc mỉa mai những điều lố bịch.", "vidu": "Bức ảnh này tinh hoa hội tụ cả hội bạn thân."},
    "ngon từ thịt ngọt từ xương": {"nghia": "Chất lượng cao, rất hài lòng, chuẩn không cần chỉnh.", "vidu": "Chiếc xe này chạy êm ru, ngon từ thịt ngọt từ xương."},
    "nói chung là": {"nghia": "Tóm lại, chốt hạ câu chuyện.", "vidu": "Nói chung là kèo này quá thơm rồi."},
    "lowkey": {"nghia": "Kín tiếng, khiêm tốn, không thích khoe khoang lên mạng xã hội.", "vidu": "Họ yêu nhau kiểu lowkey nhưng rất bền chặt."},
    "highkey": {"nghia": "Công khai, phô trương, muốn cả thế giới biết.", "vidu": "Tôi highkey ủng hộ dự án này của bạn."},
    "toxic": {"nghia": "Độc hại, tiêu cực, gây ảnh hưởng xấu đến tâm lý người khác.", "vidu": "Môi trường làm việc toxic quá nên mình đã xin nghỉ."},
    "cực mượt": {"nghia": "Trơn tru, không có bất kỳ trở ngại hay vấp váp nào.", "vidu": "Con robot xử lý giọng nói cực mượt luôn anh em."}
}

# ==============================================================================
# 3. GIẢI MÃ GIẤC MƠ
# ==============================================================================
DREAM_INTERPRETATIONS = {
    "rắn": {"ynghia": "Biểu tượng của sự biến chuyển, tài lộc hoặc cảnh báo sự ghen ghét xung quanh.", "tamly": "Rắn thể hiện nỗi sợ thầm kín hoặc năng lượng sáng tạo đang bị dồn nén.", "loikhuyen": "Hãy bình tĩnh xem xét các mối quan hệ đồng nghiệp và giữ vững lập trường."},
    "nước": {"ynghia": "Nước trong biểu thị sự thanh thản, tiền tài hanh thông; nước đục biểu thị bất an.", "tamly": "Biểu tượng cho trạng thái cảm xúc hiện tại của bạn.", "loikhuyen": "Dành thời gian tĩnh tâm, tránh để cảm xúc lấn át lý trí khi ra quyết định lớn."},
    "rụng răng": {"ynghia": "Dấu hiệu của sự tự ti về ngoại hình hoặc lo sợ mất đi quyền lực, lời nói mất trọng lượng.", "tamly": "Thường xảy ra khi bạn đang chịu áp lực lớn trong công việc hoặc sức khỏe giảm sút.", "loikhuyen": "Kiểm tra sức khỏe tổng quát và tự tin hơn vào năng lực bản thân."},
    "bay": {"ynghia": "Khao khát tự do, vượt qua rào cản và chuẩn bị đón nhận bước ngoặt mới.", "tamly": "Tâm trí đang tràn đầy hy vọng và muốn bứt phá khỏi những ràng buộc thường nhật.", "loikhuyen": "Hãy mạnh dạn bắt đầu kế hoạch mà bạn ấp ủ bấy lâu."},
    "chó": {"ynghia": "Chó thân thiện là điềm lành có quý nhân giúp đỡ; chó cắn cảnh báo bất hòa bạn bè.", "tamly": "Biểu thị lòng trung thành, tình bạn và bản năng bảo vệ bản thân.", "loikhuyen": "Trân trọng những người bạn chân thành kề vai sát cánh."},
    "lửa": {"ynghia": "Lửa sáng bùng cháy là điềm thịnh vượng, công danh phát đạt; lửa thiêu rụi là nóng vội.", "tamly": "Sự đam mê, nhiệt huyết hoặc cơn giận dữ đang chực chờ bùng nổ.", "loikhuyen": "Giữ nhiệt huyết nhưng cần kiềm chế tính nóng nảy trong giao tiếp."},
    "tiền": {"ynghia": "Nhặt được tiền biểu thị cơ hội may mắn; mất tiền phản ánh nỗi lo tài chính.", "tamly": "Khao khát thành công và sự công nhận giá trị của xã hội.", "loikhuyen": "Lập kế hoạch quản lý chi tiêu chặt chẽ và nắm bắt cơ hội nâng cao thu nhập."},
    "người yêu cũ": {"ynghia": "Chưa hẳn là muốn quay lại, mà là ký ức về một bài học cảm xúc trong quá khứ.", "tamly": "Bạn đang so sánh hiện tại với quá khứ hoặc có khúc mắc chưa được giải tỏa.", "loikhuyen": "Khép lại quá khứ để toàn tâm toàn ý xây dựng tương lai tốt đẹp hơn."},
    "người chết": {"ynghia": "Nói chuyện với người đã khuất thường là điềm lành báo trước vận may hoặc sự che chở.", "tamly": "Nỗi nhớ nhung hoặc cảm giác áy náy chưa hoàn thành tâm nguyện với người đó.", "loikhuyen": "Làm việc thiện, thắp hương tưởng nhớ và an tâm vững bước."},
    "đi thi": {"ynghia": "Mơ thấy đi thi muộn hoặc không làm được bài phản ánh áp lực bị đánh giá.", "tamly": "Hội chứng sợ thất bại khi sắp đối mặt với thử thách mới ngoài đời thực.", "loikhuyen": "Chuẩn bị kỹ lưỡng thì không có gì phải lo sợ, bạn giỏi hơn bạn nghĩ!"},
    "bị rượt đuổi": {"ynghia": "Đang trốn tránh trách nhiệm hoặc né tránh đối mặt với một sự thật khó khăn.", "tamly": "Tâm lý dồn nén lo âu cần lối thoát.", "loikhuyen": "Hãy dũng cảm đối diện, xử lý dứt điểm từng vấn đề nhỏ một."},
    "tai nạn": {"ynghia": "Cảnh báo cần cẩn trọng trong đi lại và lời ăn tiếng nói hàng ngày.", "tamly": "Cảm giác mất kiểm soát đối với một khía cạnh trong cuộc sống.", "loikhuyen": "Chậm lại một nhịp, quan sát kỹ trước khi hành động."},
    "đám cưới": {"ynghia": "Mơ thấy đám cưới biểu thị sự gắn kết, khởi đầu một dự án mới hoặc hợp tác làm ăn.", "tamly": "Mong muốn sự ổn định và cam kết lâu dài.", "loikhuyen": "Tập trung xây dựng các mối quan hệ đối tác tin cậy."},
    "trẻ em": {"ynghia": "Em bé cười là điềm may mắn tài lộc; em bé khóc phản ánh rắc rối nhỏ cần kiên nhẫn.", "tamly": "Sự ngây thơ, tính sáng tạo và khởi đầu mới non trẻ.", "loikhuyen": "Hãy nuôi dưỡng những ý tưởng mới với sự chăm chút và tình yêu thương."},
    "cá": {"ynghia": "Cá bơi lội tung tăng là điềm đại cát, tiền bạc dồi dào, thăng quan tiến chức.", "tamly": "Biểu tượng của sự giàu có, tự do và thịnh vượng.", "loikhuyen": "Thời cơ thuận lợi đang đến, hãy chủ động nắm bắt."}
}

# ==============================================================================
# 4. ĐỊA DANH LỊCH SỬ & DANH NHÂN VIỆT NAM
# ==============================================================================
HISTORICAL_PLACES_VN = {
    "hồ gươm": {"ten": "Hồ Hoàn Kiếm (Hồ Gươm)", "vitri": "Trung tâm Hà Nội", "nhanvat": "Vua Lê Lợi, Rùa Vàng", "sukien": "Nơi vua Lê Thái Tổ trả gươm báu Thuận Thiên cho Rùa Vàng sau khi đánh tan giặc Minh xâm lược vào thế kỷ 15, biểu tượng khát vọng hòa bình của dân tộc Việt Nam."},
    "văn miếu": {"ten": "Văn Miếu - Quốc Tử Giám", "vitri": "Hà Nội", "nhanvat": "Vua Lý Thánh Tông, Chu Văn An", "sukien": "Được xây dựng năm 1070 dưới thời Lý, là trường đại học đầu tiên của Việt Nam, nơi lưu giữ 82 bia tiến sĩ vinh danh truyền thống hiếu học."},
    "hoàng thành thăng long": {"ten": "Hoàng thành Thăng Long", "vitri": "Hà Nội", "nhanvat": "Lý Thái Tổ, các triều đại Lý, Trần, Lê, Nguyễn", "sukien": "Di sản văn hóa thế giới UNESCO, trung tâm quyền lực chính trị trải dài suốt 13 thế kỷ từ năm 1010 khi vua Lý Thái Tổ dời đô về Thăng Long."},
    "cố đô huế": {"ten": "Quần thể di tích Cố đô Huế", "vitri": "Thừa Thiên Huế", "nhanvat": "Các vị vua triều Nguyễn (1802 - 1945)", "sukien": "Kinh đô của Việt Nam dưới triều Nguyễn, di sản văn hóa thế giới đầu tiên của Việt Nam được UNESCO công nhận năm 1993 với Kinh thành, Hoàng thành, Tử Cấm Thành và các lăng tẩm uy nghiêm."},
    "địa đạo củ chi": {"ten": "Địa đạo Củ Chi", "vitri": "TP. Hồ Chí Minh", "nhanvat": "Quân và dân Củ Chi đất thép thành đồng", "sukien": "Hệ thống đường hầm ngầm dài hơn 250km được đào trong kháng chiến chống Pháp và chống Mỹ, kỳ tích quân sự độc nhất vô nhị thể hiện ý chí quật cường của nhân dân."},
    "dinh độc lập": {"ten": "Dinh Độc Lập (Dinh Thống Nhất)", "vitri": "Quận 1, TP. Hồ Chí Minh", "nhanvat": "Đại đội xe tăng 390 và lực lượng Quân Giải phóng", "sukien": "Nơi chứng kiến khoảnh khắc lịch sử trưa ngày 30/4/1975 khi xe tăng húc đổ cổng chính, kết thúc thắng lợi cuộc kháng chiến chống Mỹ cứu nước, non sông thu về một mối."},
    "chiến trường điện biên phủ": {"ten": "Quần thể di tích Chiến trường Điện Biên Phủ", "vitri": "Tỉnh Điện Biên", "nhanvat": "Đại tướng Võ Nguyên Giáp, các anh hùng Tô Vĩnh Diện, Bế Văn Đàn, Phan Đình Giót", "sukien": "Chiến thắng 'lừng lẫy năm châu, chấn động địa cầu' ngày 7/5/1954 tiêu diệt tập đoàn cứ điểm của thực dân Pháp, buộc Pháp ký Hiệp định Genève lập lại hòa bình ở Đông Dương."},
    "ngã ba đồng lộc": {"ten": "Khu di tích Ngã ba Đồng Lộc", "vitri": "Can Lộc, Hà Tĩnh", "nhanvat": "10 cô gái thanh niên xung phong anh dũng", "sukien": "Yết hầu giao thông huyết mạch trên đường Trường Sơn, nơi 10 nữ thanh niên xung phong hy sinh ngày 24/7/1968 khi tuổi đời mới mười tám đôi mươi để giữ mạch máu giao thông chi viện cho tiền tuyến."},
    "bạch đằng": {"ten": "Sông Bạch Đằng lịch sử", "vitri": "Quảng Ninh - Hải Phòng", "nhanvat": "Ngô Quyền (938), Lê Hoàn (981), Trần Hưng Đạo (1288)", "sukien": "Nơi diễn ra 3 trận thủy chiến cắm cọc gỗ chấn động lịch sử đánh tan quân Nam Hán, quân Tống và quân Nguyên Mông, khẳng định chủ quyền độc lập muôn đời của nước Đại Việt."},
    "côn đảo": {"ten": "Nhà tù Côn Đảo - Nghĩa trang Hàng Dương", "vitri": "Bà Rịa - Vũng Tàu", "nhanvat": "Nữ anh hùng Võ Thị Sáu, Tổng Bí thư Lê Duẩn, Nguyễn An Ninh", "sukien": "'Địa ngục trần gian' với hệ thống Chuồng Cọp khét tiếng do thực dân Pháp và đế quốc Mỹ xây dựng để giam giữ các chiến sĩ cách mạng kiên trung."},
    "phố cổ hội an": {"ten": "Đô thị cổ Hội An", "vitri": "Quảng Nam", "nhanvat": "Các thương nhân Việt, Hoa, Nhật thế kỷ 16-17", "sukien": "Thương cảng quốc tế sầm uất bậc nhất Đông Nam Á thời Trịnh - Nguyễn phân tranh, bảo tồn nguyên vẹn kiến trúc truyền thống Đông Á độc đáo."},
    "đền hùng": {"ten": "Khu di tích Lịch sử Đền Hùng", "vitri": "Núi Nghĩa Lĩnh, Việt Trì, Phú Thọ", "nhanvat": "18 đời Vua Hùng dựng nước Văn Lang", "sukien": "Cội nguồn của dân tộc Việt Nam, nơi tổ chức Giỗ Tổ Hùng Vương mùng 10 tháng 3 âm lịch: 'Dù ai đi ngược về xuôi / Nhớ ngày Giỗ Tổ mùng mười tháng ba'."}
}

# ==============================================================================
# 5. GỢI Ý MÓN ĂN VIỆT NAM (THEO BỮA & THỜI TIẾT)
# ==============================================================================
MEAL_SUGGESTIONS = {
    "sang": [
        {"mon": "Phở bò sốt vang Hà Nội", "mota": "Nước dùng thơm lừng quế hồi, thịt bò mềm nhừ, ăn kèm quẩy giòn và chút dấm tỏi cay cay."},
        {"mon": "Bánh mì kẹp thịt xíu mại pate", "mota": "Vỏ bánh giòn rụm, pate béo ngậy, thịt xíu mại đậm đà cùng dưa leo, ngò rí và sốt ớt cay nồng."},
        {"mon": "Bún chả Hà Nội", "mota": "Chả nướng than hoa thơm phức, nước mắm dưa góp chua ngọt thanh tao, bún tươi và rau sống."},
        {"mon": "Bánh cuốn Thanh Trì nóng hổi", "mota": "Bánh mỏng mịn tráng tay, nhân thịt băm mộc nhĩ giòn sần sật, rắc hành phi vàng ruộm chấm nước mắm cà cuống."},
        {"mon": "Cơm tấm sườn bì chả Sài Gòn", "mota": "Sườn nướng mật ong thơm phức, bì trộn thính, chả trứng béo mềm, chan mỡ hành và nước mắm kẹo ớt."},
        {"mon": "Xôi xéo đậu xanh mỡ hành", "mota": "Nếp dẻo thơm hạt vàng óng, đậu xanh bào mỏng bùi béo, ruốc thịt và hành phi thơm lừng."}
    ],
    "trua": [
        {"mon": "Cơm gia đình: Cá lóc kho tộ + Canh chua bông điên điển", "mota": "Vị mặn ngọt đậm đà của cá kho niêu đất kết hợp canh chua thanh mát giải nhiệt tuyệt đối."},
        {"mon": "Bún đậu mắm tôm thập cẩm", "mota": "Đậu hũ rán giòn ngoài mềm trong, chả cốm béo bùi, thịt bắp giò luộc, chấm mắm tôm đánh sủi bọt quất ớt."},
        {"mon": "Cơm gà xối mỡ Nha Trang", "mota": "Cơm nấu nước luộc gà vàng ươm, đùi gà chiên da giòn tan, ăn kèm đồ chua và nước sốt gừng đặc biệt."},
        {"mon": "Bún bò Huế đầy đủ", "mota": "Nước dùng cay nồng mùi sả và mắm ruốc, bắp bò hoa, chả cua, tiết luộc và rau chuối bào."},
        {"mon": "Cơm sườn xào chua ngọt + Canh rau ngót nấu thịt băm", "mota": "Món ăn thanh đạm đưa cơm, vị chua ngọt kích thích vị giác cho buổi trưa nhiều năng lượng."}
    ],
    "toi": [
        {"mon": "Lẩu gà lá é Phú Yên", "mota": "Nước lẩu thơm lừng sả ớt, thịt gà ta chắc ngọt, lá é the mát chống cảm lạnh cực kỳ thích hợp cho buổi tối sum vầy."},
        {"mon": "Bò nhúng dấm cuốn bánh tráng", "mota": "Thịt bắp bò thái mỏng nhúng nước dấm dừa chua thanh, cuộn bánh tráng cùng chuối chát, khế chua, chấm mắm nêm đậm đà."},
        {"mon": "Lẩu riêu cua bắp bò sườn sụn", "mota": "Gạch cua béo ngậy, nước dùng thanh chua vị giấm bỗng, bắp bò hoa tươi rói, sườn sụn giòn sần sật."},
        {"mon": "Cơm niêu: Thịt kho quẹt + Rau củ luộc thập cẩm", "mota": "Lớp cơm cháy giòn rụm đáy niêu quẹt nước mắm tóp mỡ tôm khô keo đặc, ăn cùng đĩa bông cải, đậu bắp xanh mướt."},
        {"mon": "Bánh xèo miền Tây giòn tan", "mota": "Vỏ bánh vàng ươm nghệ nước cốt dừa, nhân tôm sông, thịt ba chỉ, giá đỗ, cuộn rau rừng chấm mắm chua ngọt."}
    ],
    "chay": [
        {"mon": "Đậu hũ non sốt nấm đông cô", "mota": "Đậu hũ trắng mịn thanh khiết quyện cùng nước sốt nấm đậm đà thơm ngát mùi tiêu."},
        {"mon": "Canh chua nấm đậu bắp", "mota": "Vị chua thanh tự nhiên từ me và dứa, đậu bắp giòn ngọt, nấm bào ngư dai ngon bồi bổ sức khỏe."},
        {"mon": "Nem nấm chay rán giòn", "mota": "Vỏ bánh đa nem giòn rụm bọc nhân nấm đùi gà, mộc nhĩ, miến dong, khoai môn bùi bùi."}
    ]
}

# ==============================================================================
# 6. AI LÀ TRIỆU PHÚ - BỘ 15 CÂU HỎI TRẮC NGHIỆM
# ==============================================================================
MILLIONAIRE_QUESTIONS = [
    {
        "cau": 1,
        "hoi": "Thủ đô của nước Cộng hòa Xã hội Chủ nghĩa Việt Nam là thành phố nào?",
        "options": ["A. TP. Hồ Chí Minh", "B. Hà Nội", "C. Đà Nẵng", "D. Hải Phòng"],
        "dapan": "B",
        "giaithich": "Hà Nội là thủ đô của Việt Nam từ năm 1945 và tiếp tục là thủ đô sau khi thống nhất đất nước."
    },
    {
        "cau": 2,
        "hoi": "Loại cây nào xuất hiện trong câu tục ngữ 'Lạt mềm buộc chặt'?",
        "options": ["A. Cây tre", "B. Cây mía", "C. Cây bàng", "D. Cây chuối"],
        "dapan": "A",
        "giaithich": "Lạt được chẻ từ thân cây tre, nứa; câu tục ngữ khuyên nên dùng sự khéo léo, mềm mỏng để xử thế."
    },
    {
        "cau": 3,
        "hoi": "Trận Điện Biên Phủ trên không diễn ra trên bầu trời Hà Nội vào năm nào?",
        "options": ["A. 1954", "B. 1968", "C. 1972", "D. 1975"],
        "dapan": "C",
        "giaithich": "Trận Điện Biên Phủ trên không kéo dài 12 ngày đêm cuối tháng 12 năm 1972, bắn rơi nhiều pháo đài bay B-52."
    },
    {
        "cau": 4,
        "hoi": "Kim loại nào dẫn điện tốt nhất ở điều kiện tiêu chuẩn?",
        "options": ["A. Vàng (Au)", "B. Đồng (Cu)", "C. Nhôm (Al)", "D. Bạc (Ag)"],
        "dapan": "D",
        "giaithich": "Bạc (Ag) có độ dẫn điện cao nhất trong các kim loại, tiếp theo là Đồng, Vàng và Nhôm."
    },
    {
        "cau": 5,
        "hoi": "Ai là tác giả của bài hát 'Tiến quân ca' - Quốc ca của Việt Nam?",
        "options": ["A. Nhạc sĩ Văn Cao", "B. Nhạc sĩ Trịnh Công Sơn", "C. Nhạc sĩ Phạm Tuyên", "D. Nhạc sĩ Hoàng Vân"],
        "dapan": "A",
        "giaithich": "Nhạc sĩ Văn Cao sáng tác ca khúc Tiến quân ca vào mùa đông năm 1944."
    },
    {
        "cau": 6,
        "hoi": "Hành tinh nào gần Mặt Trời nhất trong Hệ Mặt Trời?",
        "options": ["A. Sao Kim", "B. Sao Thủy", "C. Sao Hỏa", "D. Trái Đất"],
        "dapan": "B",
        "giaithich": "Sao Thủy (Mercury) là hành tinh nằm gần Mặt Trời nhất với khoảng cách trung bình khoảng 58 triệu km."
    },
    {
        "cau": 7,
        "hoi": "Vịnh Hạ Long thuộc địa phận tỉnh/thành nào của Việt Nam?",
        "options": ["A. Hải Phòng", "B. Nam Định", "C. Quảng Ninh", "D. Thái Bình"],
        "dapan": "C",
        "giaithich": "Vịnh Hạ Long là di sản thiên nhiên thế giới thuộc tỉnh Quảng Ninh."
    },
    {
        "cau": 8,
        "hoi": "Hệ tuần hoàn của con người có mấy vòng tuần hoàn chính?",
        "options": ["A. 1 vòng", "B. 2 vòng", "C. 3 vòng", "D. 4 vòng"],
        "dapan": "B",
        "giaithich": "Hệ tuần hoàn người gồm 2 vòng: Vòng tuần hoàn lớn (nuôi cơ thể) và Vòng tuần hoàn nhỏ (phổi trao đổi khí)."
    },
    {
        "cau": 9,
        "hoi": "Vua nào đã dời đô từ Hoa Lư về Thăng Long vào mùa thu năm 1010?",
        "options": ["A. Lý Thái Tổ", "B. Đinh Tiên Hoàng", "C. Lê Đại Hành", "D. Trần Thái Tông"],
        "dapan": "A",
        "giaithich": "Vua Lý Thái Tổ (Lý Công Uẩn) viết Chiếu dời đô chuyển kinh đô về Thăng Long năm 1010."
    },
    {
        "cau": 10,
        "hoi": "Hợp chất khí nào chiếm tỉ lệ thể tích lớn nhất trong bầu khí quyển Trái Đất?",
        "options": ["A. Khí Oxy (O2)", "B. Khí Nitơ (N2)", "C. Khí Carbonic (CO2)", "D. Khí Argon (Ar)"],
        "dapan": "B",
        "giaithich": "Khí Nitơ (N2) chiếm khoảng 78% thể tích khí quyển, trong khi Oxy chiếm khoảng 21%."
    },
    {
        "cau": 11,
        "hoi": "Bán đảo Sơn Trà thuộc tỉnh/thành phố nào ở miền Trung?",
        "options": ["A. Quảng Nam", "B. Đà Nẵng", "C. Thừa Thiên Huế", "D. Quảng Ngãi"],
        "dapan": "B",
        "giaithich": "Bán đảo Sơn Trà được mệnh danh là 'viên ngọc quý' che chắn gió bão cho thành phố Đà Nẵng."
    },
    {
        "cau": 12,
        "hoi": "Tác phẩm văn học 'Chí Phèo' của Nam Cao lúc đầu có tên gọi là gì?",
        "options": ["A. Đôi lứa xứng đôi", "B. Cái lò gạch cũ", "C. Làng Vũ Đại ngày ấy", "D. Người cùng khổ"],
        "dapan": "B",
        "giaithich": "Tác phẩm ra đời năm 1941 với tên đầu tiên là 'Cái lò gạch cũ', nhà xuất bản đổi thành 'Đôi lứa xứng đôi', sau này tác giả đặt lại là 'Chí Phèo'."
    },
    {
        "cau": 13,
        "hoi": "Trong vật lý, định luật vạn vật hấp dẫn được tìm ra bởi nhà khoa học nào?",
        "options": ["A. Albert Einstein", "B. Isaac Newton", "C. Galileo Galilei", "D. Stephen Hawking"],
        "dapan": "B",
        "giaithich": "Sir Isaac Newton công bố định luật vạn vật hấp dẫn trong tác phẩm Principia Mathematica năm 1687."
    },
    {
        "cau": 14,
        "hoi": "Sông Mê Kông chảy qua bao nhiêu quốc gia trước khi đổ ra Biển Đông?",
        "options": ["A. 4 quốc gia", "B. 5 quốc gia", "C. 6 quốc gia", "D. 7 quốc gia"],
        "dapan": "C",
        "giaithich": "Sông Mê Kông chảy qua 6 quốc gia: Trung Quốc, Myanmar, Lào, Thái Lan, Campuchia và Việt Nam."
    },
    {
        "cau": 15,
        "hoi": "Hồ nước ngọt tự nhiên lớn nhất thế giới tính theo thể tích nước là hồ nào?",
        "options": ["A. Hồ Baikal", "B. Hồ Superior (Thượng)", "C. Hồ Victoria", "D. Biển Caspi"],
        "dapan": "A",
        "giaithich": "Hồ Baikal (Nga) chứa khoảng 20% lượng nước ngọt không đóng băng trên bề mặt Trái Đất, sâu nhất và có thể tích lớn nhất thế giới."
    }
]

# ==============================================================================
# 7. SÁT HẠCH LÝ THUYẾT LÁI XE MÁY A1 (KÈM CÂU ĐIỂM LIỆT)
# ==============================================================================
A1_THEORY_QUESTIONS = [
    {
        "id": 1,
        "cau_hoi": "Hành vi điều khiển xe cơ giới chạy quá tốc độ quy định, giành đường, vượt ẩu có bị nghiêm cấm hay không? (CÂU ĐIỂM LIỆT)",
        "dap_an_dung": "Bị nghiêm cấm.",
        "giai_thich": "Đây là hành vi vi phạm an toàn giao thông nghiêm trọng bị pháp luật nghiêm cấm triệt để."
    },
    {
        "id": 2,
        "cau_hoi": "Người điều khiển phương tiện tham gia giao thông đường bộ mà trong cơ thể có chất ma túy có bị nghiêm cấm không? (CÂU ĐIỂM LIỆT)",
        "dap_an_dung": "Bị nghiêm cấm hoàn toàn.",
        "giai_thich": "Sử dụng ma túy khi lái xe gây nguy hiểm tột cùng cho xã hội, bị cấm tuyệt đối theo Luật Giao thông đường bộ."
    },
    {
        "id": 3,
        "cau_hoi": "Người đủ bao nhiêu tuổi trở lên thì được điều khiển xe mô tô hai bánh có dung tích xi lanh từ 50 cm3 đến dưới 175 cm3 (Hạng A1)?",
        "dap_an_dung": "Đủ 18 tuổi trở lên.",
        "giai_thich": "Người từ đủ 16 tuổi chỉ được lái xe gắn máy dưới 50cm3; đủ 18 tuổi mới được thi bằng A1 và B1/B2."
    },
    {
        "id": 4,
        "cau_hoi": "Khi điều khiển xe mô tô hai bánh, người lái xe có được sử dụng ô (dù), điện thoại di động, thiết bị âm thanh (trừ thiết bị trợ thính) không? (CÂU ĐIỂM LIỆT)",
        "dap_an_dung": "Không được phép.",
        "giai_thich": "Sử dụng điện thoại, ô dù gây mất tập trung và giảm khả năng điều khiển phương tiện, bị phạt tiền nghiêm khắc."
    },
    {
        "id": 5,
        "cau_hoi": "Biển báo hiệu hình tròn, viền đỏ, nền trắng, trên nền có hình vẽ hoặc chữ số màu đen là loại biển báo gì?",
        "dap_an_dung": "Biển báo cấm.",
        "giai_thich": "Biển báo cấm biểu thị các điều cấm mà người tham gia giao thông không được vi phạm."
    },
    {
        "id": 6,
        "cau_hoi": "Biển báo hình tam giác đều, viền đỏ, nền vàng, hình vẽ màu đen bên trong là loại biển báo gì?",
        "dap_an_dung": "Biển báo nguy hiểm.",
        "giai_thich": "Biển nguy hiểm cảnh báo trước các tình huống nguy hiểm có thể xảy ra trên đoạn đường phía trước."
    },
    {
        "id": 7,
        "cau_hoi": "Tại nơi đường giao nhau không có báo hiệu đi theo vòng xuyến, người điều khiển phương tiện phải nhường đường như thế nào?",
        "dap_an_dung": "Nhường đường cho xe đi đến từ bên phải.",
        "giai_thich": "Quy tắc: Không có vòng xuyến thì nhường bên phải; Có báo hiệu vòng xuyến thì nhường xe đi từ bên trái."
    },
    {
        "id": 8,
        "cau_hoi": "Người ngồi trên xe mô tô hai bánh, xe gắn máy phải đội mũ bảo hiểm có cài quai đúng quy cách khi nào?",
        "dap_an_dung": "Khi tham gia giao thông đường bộ.",
        "giai_thich": "Bắt buộc đội mũ bảo hiểm đạt chuẩn và cài quai đúng quy cách trên mọi tuyến đường bộ."
    }
]

# ==============================================================================
# 8. ĐỐ VUI DÂN GIAN & CA DAO TỤC NGỮ
# ==============================================================================
FOLK_RIDDLES = [
    {
        "cau_do": "Thân em xưa ở bụi tre / Mùa đông xếp lại, mùa hè mở ra - Là cái gì?",
        "dap_an": "Cái quạt nan / quạt giấy",
        "giai_thich": "Quạt nan làm từ nan tre dán giấy hoặc đan lá, mùa hè nóng nực xòe ra quạt mát, mùa đông cất đi."
    },
    {
        "cau_do": "Cây chi nho nhỏ / Hạt nó đo đỏ / Tỉa đỗ nấu chè / Ăn vào cay xè - Là cây gì?",
        "dap_an": "Cây ớt",
        "giai_thich": "Quả ớt khi chín có màu đỏ tươi, hạt nhỏ, có vị cay nồng đặc trưng."
    },
    {
        "cau_do": "Vừa bằng một thước / Mà bước không qua - Là cái gì?",
        "dap_an": "Cái bóng của chính mình",
        "giai_thich": "Bóng đổ theo người, khi ta bước lên thì bóng cũng tiến tới nên không bao giờ bước qua được."
    },
    {
        "cau_do": "Đầu rồng đuôi phụng cánh tiên / Ngày thì xuống biển tối liền lên non - Là con gì?",
        "dap_an": "Con gà trống",
        "giai_thich": "Mào như đầu rồng, đuôi cong như phụng, sáng xuống đất bới giun (xuống biển), tối leo lên chuồng ngủ (lên non)."
    },
    {
        "cau_do": "Mẹ con nhà nọ kéo cày / Kẻ trước người sau suốt cả ngày / Mẹ đi trước bước thong dong / Con chạy theo sau khóc ròng ròng - Là cái gì?",
        "dap_an": "Kim và chỉ khâu vá",
        "giai_thich": "Kim nhọn đi trước dẫn đường, sợi chỉ dài xâu qua đuôi kim chạy theo sau."
    },
    {
        "cau_do": "Không miệng mà biết nói năng / Không chân không cẳng tưng bừng khắp nơi - Là cái gì?",
        "dap_an": "Cái radio / Đài phát thanh",
        "giai_thich": "Thiết bị truyền phát âm thanh tin tức và âm nhạc đến mọi miền đất nước."
    },
    {
        "cau_do": "Trắng phau như tuyết, mát lạnh như sương / Ai muốn ngọt ngào, xin mời nếm thử - Là gì?",
        "dap_an": "Hạt đường cát",
        "giai_thich": "Đường tinh luyện có màu trắng tinh và vị ngọt sắc."
    }
]

# ==============================================================================
# 9. 78 LÁ BÀI TAROT (BỘ RIDER-WAITE CHUẨN)
# ==============================================================================
TAROT_CARDS = {
    # 22 Lá Major Arcana (Ẩn chính)
    "0_The_Fool": {"ten": "0 - The Fool (Kẻ Khờ)", "nghia_xuoi": "Khởi đầu mới, tự do, phiêu lưu, niềm tin ngây thơ, tiềm năng vô hạn.", "nghia_nguoc": "Liều lĩnh, thiếu chín chắn, sợ hãi không dám bước tiếp, hành động nông nổi.", "tinh_duyen": "Mối tình mới mẻ đầy bất ngờ, dám yêu hết mình.", "cong_viec": "Thời điểm thích hợp để bắt đầu dự án mới độc đáo."},
    "1_The_Magician": {"ten": "I - The Magician (Phù Thủy)", "nghia_xuoi": "Ý chí mạnh mẽ, tài năng xuất chúng, kỹ năng biến ước mơ thành hiện thực.", "nghia_nguoc": "Thao túng, ảo tưởng, tài năng không được tận dụng, lừa dối.", "tinh_duyen": "Chủ động, có sức hút quyến rũ đối phương mãnh liệt.", "cong_viec": "Đang nắm giữ mọi công cụ và nguồn lực để thành công."},
    "2_The_High_Priestess": {"ten": "II - The High Priestess (Nữ Giáo Hoàng)", "nghia_xuoi": "Trực giác nhạy bén, sự thông thái tiềm ẩn, bí ẩn, bình thản.", "nghia_nguoc": "Bỏ qua trực giác, sống hời hợt, bí mật bị chôn vùi làm tổn thương.", "tinh_duyen": "Kết nối tâm linh sâu sắc, tình cảm kín đáo e ấp.", "cong_viec": "Nên lắng nghe giác quan thứ sáu hơn là quá vội vàng."},
    "3_The_Empress": {"ten": "III - The Empress (Hoàng Hậu)", "nghia_xuoi": "Sinh sôi nảy nở, tình mẫu tử, thịnh vượng, nghệ thuật, chăm sóc dịu dàng.", "nghia_nguoc": "Phụ thuộc cảm xúc, bế tắc sáng tạo, bỏ bê bản thân.", "tinh_duyen": "Mối quan hệ đơm hoa kết trái, hạnh phúc viên mãn.", "cong_viec": "Dự án phát triển mạnh mẽ, thu về lợi nhuận dồi dào."},
    "4_The_Emperor": {"ten": "IV - The Emperor (Hoàng Đế)", "nghia_xuoi": "Kỷ luật, quyền lực, cấu trúc vững vàng, bảo vệ, khả năng lãnh đạo.", "nghia_nguoc": "Độc đoán, kiểm soát quá mức, cứng nhắc, bất lực.", "tinh_duyen": "Người bạn đời chững chạc, làm chỗ dựa đáng tin cậy.", "cong_viec": "Thời điểm thiết lập trật tự, quản lý tài chính chuẩn xác."},
    "5_The_Hierophant": {"ten": "V - The Hierophant (Giáo Hoàng)", "nghia_xuoi": "Truyền thống, niềm tin đạo đức, học hỏi từ người đi trước, lời khuyên thông thái.", "nghia_nguoc": "Cổ hủ, giáo điều, phá vỡ quy chuẩn lỗi thời.", "tinh_duyen": "Tình yêu hướng tới hôn nhân gia đình truyền thống.", "cong_viec": "Tìm kiếm người thầy dẫn đường uy tín."},
    "6_The_Lovers": {"ten": "VI - The Lovers (Đôi Tình Nhân)", "nghia_xuoi": "Tình yêu đích thực, sự hòa hợp tâm hồn, sự lựa chọn mang tính đạo đức.", "nghia_nguoc": "Mâu thuẫn giá trị, bất đồng quan điểm, chọn sai hướng đi.", "tinh_duyen": "Sự hòa hợp tuyệt vời giữa hai con người đồng điệu.", "cong_viec": "Quan hệ đối tác hợp tác cùng có lợi tốt đẹp."},
    "7_The_Chariot": {"ten": "VII - The Chariot (Chiến Xa)", "nghia_xuoi": "Ý chí sắt đá, quyết tâm vượt qua mọi nghịch cảnh, chiến thắng vang dội.", "nghia_nguoc": "Mất kiểm soát, hung hăng hiếu thắng, gặp chướng ngại lớn.", "tinh_duyen": "Cùng nhau vượt qua rào cản từ gia đình hoặc xã hội.", "cong_viec": "Tiến nhanh về phía trước, đạt được mục tiêu đề ra."},
    "8_Strength": {"ten": "VIII - Strength (Sức Mạnh)", "nghia_xuoi": "Lòng dũng cảm, sự kiên nhẫn, kiểm soát bản năng bằng tình yêu thương.", "nghia_nguoc": "Tự ti, yếu lòng, nghi ngờ bản thân, hung hãn.", "tinh_duyen": "Dùng sự dịu dàng và kiên nhẫn cảm hóa đối phương.", "cong_viec": "Giữ vững bình tĩnh sẽ giải quyết được khủng hoảng phức tạp."},
    "9_The_Hermit": {"ten": "IX - The Hermit (Ẩn Sĩ)", "nghia_xuoi": "Tự soi rọi nội tâm, tìm kiếm chân lý, sự thông thái trong tĩnh lặng.", "nghia_nguoc": "Cô lập, cô đơn cùng cực, xa lánh thực tế một cách tiêu cực.", "tinh_duyen": "Cần khoảng không gian riêng để hiểu rõ lòng mình.", "cong_viec": "Nghiên cứu chuyên sâu, tập trung hoàn thiện kỹ năng cá nhân."},
    "10_Wheel_of_Fortune": {"ten": "X - Wheel of Fortune (Bánh Xe Số Phận)", "nghia_xuoi": "Vận may xoay vần, bước ngoặt định mệnh, thời cơ vàng đã đến.", "nghia_nguoc": "Gặp vận rủi tạm thời, chống lại sự thay đổi tất yếu.", "tinh_duyen": "Mối nhân duyên tiền định, sắp có chuyển biến bất ngờ.", "cong_viec": "Thời vận hanh thông, hãy đón nhận làn gió may mắn mới."},
    "11_Justice": {"ten": "XI - Justice (Công Lý)", "nghia_xuoi": "Công bằng, luật nhân quả, sự thật rõ ràng, quyết định sáng suốt.", "nghia_nguoc": "Bất công, thiên vị, trốn tránh trách nhiệm, kiện tụng bất lợi.", "tinh_duyen": "Cần sự thành thật và bình đẳng giữa hai bên.", "cong_viec": "Hợp đồng, giấy tờ pháp lý được xử lý minh bạch."},
    "12_The_Hanged_Man": {"ten": "XII - The Hanged Man (Kẻ Treo Ngược)", "nghia_xuoi": "Góc nhìn mới mẻ, chấp nhận hy sinh tạm thời vì mục đích lớn hơn, buông bỏ.", "nghia_nguoc": "Bế tắc vô ích, tử vì đạo mù quáng, chần chừ không hành động.", "tinh_duyen": "Hy sinh cho nhau nhưng cần biết điểm dừng.", "cong_viec": "Tạm dừng lại để đổi hướng tư duy chiến lược."},
    "13_Death": {"ten": "XIII - Death (Cái Chết & Tái Sinh)", "nghia_xuoi": "Kết thúc chu kỳ cũ, dọn đường cho sự tái sinh, chuyển hóa sâu sắc.", "nghia_nguoc": "Sợ thay đổi, níu kéo quá khứ đã mục nát, trì hoãn.", "tinh_duyen": "Khép lại đau thương để mở lòng đón nhận tình yêu mới.", "cong_viec": "Dứt khoát từ bỏ công việc không còn phù hợp."},
    "14_Temperance": {"ten": "XIV - Temperance (Tiết Độ)", "nghia_xuoi": "Cân bằng, dung hòa đối lập, kiên nhẫn, chữa lành tâm hồn.", "nghia_nguoc": "Mất cân bằng, cực đoan, xung đột nội tâm gay gắt.", "tinh_duyen": "Mối quan hệ êm đềm, biết lắng nghe và thấu hiểu.", "cong_viec": "Phối hợp nhịp nhàng giữa các bộ phận trong nhóm."},
    "15_The_Devil": {"ten": "XV - The Devil (Ác Quỷ)", "nghia_xuoi": "Cám dỗ vật chất, ám ảnh độc hại, nghiện ngập, ảo tưởng bị trói buộc.", "nghia_nguoc": "Tự do thoát khỏi xiềng xích, thức tỉnh nhận ra bản chất sự việc.", "tinh_duyen": "Mối quan hệ kiểm soát độc hại, mê đắm thể xác.", "cong_viec": "Cảnh giác trước những món hời bất chính có bẫy."},
    "16_The_Tower": {"ten": "XVI - The Tower (Tòa Tháp Đổ)", "nghia_xuoi": "Sụp đổ bất ngờ, sự thật trần trụi phơi bày, phá vỡ ảo tưởng giả tạo.", "nghia_nguoc": "Cố tránh thảm họa nhưng chỉ kéo dài đau khổ, xây dựng lại sau đổ vỡ.", "tinh_duyen": "Cú sốc tình cảm giúp bạn nhìn rõ lòng người.", "cong_viec": "Biến động lớn nhưng là cơ hội tái cấu trúc hoàn toàn mới."},
    "17_The_Star": {"ten": "XVII - The Star (Ngôi Sao Hy Vọng)", "nghia_xuoi": "Hy vọng tái sinh, bình yên, niềm tin mãnh liệt, nguồn cảm hứng dạt dào.", "nghia_nguoc": "Mất niềm tin, tuyệt vọng, bi quan về tương lai.", "tinh_duyen": "Tình yêu trong sáng, chữa lành mọi tổn thương xưa cũ.", "cong_viec": "Tương lai tươi sáng với nhiều triển vọng rực rỡ."},
    "18_The_Moon": {"ten": "XVIII - The Moon (Mặt Trăng)", "nghia_xuoi": "Bất an, hoang mang, ảo ảnh lừa dối, nỗi sợ vô hình từ tiềm thức.", "nghia_nguoc": "Sương mù tan biến, sự thật sáng tỏ, giải tỏa lo âu.", "tinh_duyen": "Nghi ngờ, ghen tuông không có căn cứ rõ ràng.", "cong_viec": "Chưa nên ký kết hợp đồng khi thông tin còn mập mờ."},
    "19_The_Sun": {"ten": "XIX - The Sun (Mặt Trời)", "nghia_xuoi": "Thành công vang dội, niềm vui ngập tràn, sinh khí dồi dào, chân lý rạng ngời.", "nghia_nguoc": "Lạc quan tếu, niềm vui bị trì hoãn một chút nhưng vẫn tới.", "tinh_duyen": "Tình yêu rạng rỡ, ngập tràn tiếng cười và sự ấm áp.", "cong_viec": "Đạt đỉnh cao sự nghiệp, được công nhận xứng đáng."},
    "20_Judgement": {"ten": "XX - Judgement (Phán Xét)", "nghia_xuoi": "Sự thức tỉnh tâm linh, tiếng gọi sứ mệnh, tha thứ, chuộc lỗi, bước sang trang mới.", "nghia_nguoc": "Tự trách bản thân, sợ bị phán xét, bỏ lỡ cơ hội đổi đời.", "tinh_duyen": "Đưa ra quyết định dứt khoát về tương lai hai người.", "cong_viec": "Nghe theo tiếng gọi đam mê và lý tưởng thực sự."},
    "21_The_World": {"ten": "XXI - The World (Thế Giới)", "nghia_xuoi": "Viên mãn, hoàn thành trọn vẹn mục tiêu lớn, thành công toàn cầu, tự do trọn vẹn.", "nghia_nguoc": "Chưa thể kết thúc trọn vẹn do còn một mắt xích thiếu sót.", "tinh_duyen": "Hạnh phúc sum vầy, cái kết có hậu như mơ.", "cong_viec": "Gặt hái thành quả rực rỡ sau chuỗi ngày nỗ lực bền bỉ."}
}

# Thêm đại diện Minor Arcana
MINOR_ARCANA_SAMPLES = {
    "Ace_of_Wands": {"ten": "Ace of Wands (Gậy Tiên Phong)", "nghia_xuoi": "Ngọn lửa cảm hứng bùng cháy, ý tưởng khởi nghiệp táo bạo, sinh lực tràn trề.", "nghia_nguoc": "Thiếu nhiệt huyết, trì hoãn khởi đầu."},
    "Two_of_Wands": {"ten": "Two of Wands", "nghia_xuoi": "Lập kế hoạch tương lai, mở rộng tầm nhìn ra thế giới.", "nghia_nguoc": "Sợ bước ra khỏi vùng an toàn."},
    "Three_of_Wands": {"ten": "Three of Wands", "nghia_xuoi": "Thuyền chở thành quả về bến, tầm nhìn xa trông rộng.", "nghia_nguoc": "Kỳ vọng quá cao dẫn đến thất vọng."},
    "Ace_of_Cups": {"ten": "Ace of Cups (Chén Tình Yêu)", "nghia_xuoi": "Dòng chảy cảm xúc dạt dào, tình yêu mới chớm nở, tâm hồn được tưới mát.", "nghia_nguoc": "Cảm xúc khô cằn, vết thương lòng chưa lành."},
    "Two_of_Cups": {"ten": "Two of Cups", "nghia_xuoi": "Tình yêu đôi lứa tương đầu ý hợp, hợp tác chân thành.", "nghia_nguoc": "Bất đồng, chia rẽ tình cảm."},
    "Three_of_Cups": {"ten": "Three of Cups", "nghia_xuoi": "Tiệc tùng ăn mừng, họp mặt bạn bè rộn rã niềm vui.", "nghia_nguoc": "Bè phái, đố kỵ trong hội nhóm."},
    "Ace_of_Swords": {"ten": "Ace of Swords (Kiếm Trí Tuệ)", "nghia_xuoi": "Tư duy sắc bén, sự thật phơi bày như lưỡi kiếm cắt đứt mập mờ.", "nghia_nguoc": "Nhầm lẫn, lời nói độc địa gây tổn thương."},
    "Two_of_Swords": {"ten": "Two of Swords", "nghia_xuoi": "Lưỡng lự trước ngã ba đường, cần cân nhắc lý trí.", "nghia_nguoc": "Bị ép phải đưa ra lựa chọn khó khăn."},
    "Ace_of_Pentacles": {"ten": "Ace of Pentacles (Đồng Tiền Vàng)", "nghia_xuoi": "Cơ hội tài chính vững chắc, khởi nghiệp có lãi, sức khỏe dồi dào.", "nghia_nguoc": "Bỏ lỡ cơ hội đầu tư, chi tiêu hoang phí."},
    "Ten_of_Pentacles": {"ten": "Ten of Pentacles", "nghia_xuoi": "Gia sản thịnh vượng bền vững qua nhiều thế hệ, gia đình sung túc.", "nghia_nguoc": "Tranh chấp tài sản gia đình."}
}
TAROT_CARDS.update(MINOR_ARCANA_SAMPLES)

# ==============================================================================
# 10. THẦN SỐ HỌC PITAGO (LIFE PATH & DESTINY)
# ==============================================================================
NUMEROLOGY_LIFE_PATH = {
    1: {"ten": "Số 1 - Nhà Tiên Phong, Lãnh Đạo Độc Lập", "dac_tinh": "Tự chủ, quyết đoán, tiên phong, ý chí kiên định.", "diem_manh": "Khả năng dẫn dắt xuất sắc, sáng tạo và dám chịu trách nhiệm.", "thach_thuc": "Có thể trở nên độc đoán, bảo thủ hoặc áp đặt người khác.", "nghe_nghiep": "Doanh nhân, nhà quản lý, giám đốc sáng tạo, chính trị gia."},
    2: {"ten": "Số 2 - Nhà Ngoại Giao, Sứ Giả Hòa Bình", "dac_tinh": "Nhạy cảm, khéo léo, giàu lòng trắc ẩn, yêu chuộng hòa bình.", "diem_manh": "Biết lắng nghe, gắn kết mọi người và giải quyết mâu thuẫn êm thấm.", "thach_thuc": "Dễ bị tổn thương, phụ thuộc cảm xúc, thiếu quyết đoán.", "nghe_nghiep": "Nhà ngoại giao, tư vấn tâm lý, hòa giải viên, nghệ thuật."},
    3: {"ten": "Số 3 - Người Truyền Cảm Hứng, Nghệ Sĩ Ngôn Từ", "dac_tinh": "Hoạt bát, hài hước, sáng tạo vô biên, giàu năng lượng tích cực.", "diem_manh": "Giao tiếp xuất sắc, truyền lửa và mang lại tiếng cười cho xung quanh.", "thach_thuc": "Nông nổi, thiếu tập trung, hay bị phân tán năng lượng.", "nghe_nghiep": "Diễn giả, nhà văn, MC, diễn viên, truyền thông, marketing."},
    4: {"ten": "Số 4 - Người Kiến Thiết, Bậc Thầy Kỷ Luật", "dac_tinh": "Thực tế, vững chãi, tỉ mỉ, đáng tin cậy và có tổ chức.", "diem_manh": "Làm việc có phương pháp, kiên nhẫn xây dựng nền tảng lâu dài.", "thach_thuc": "Quá cứng nhắc, bảo thủ, ngại đổi mới.", "nghe_nghiep": "Kỹ sư, kiến trúc sư, kế toán, quản lý tài chính, luật sư."},
    5: {"ten": "Số 5 - Nhà Thám Hiểm, Yêu Tự Do Bất Tận", "dac_tinh": "Thích phiêu lưu, linh hoạt, tò mò, thích nghi nhanh với cái mới.", "diem_manh": "Dám bước ra khỏi vùng an toàn, tư duy cấp tiến và nhiều tài lẻ.", "thach_thuc": "Nhanh chán, thiếu kiên định, dễ sa vào cám dỗ phóng túng.", "nghe_nghiep": "Hướng dẫn viên du lịch, nhà báo điều tra, phi công, tiếp thị."},
    6: {"ten": "Số 6 - Người Chăm Sóc, Tình Yêu Vô Điều Kiện", "dac_tinh": "Giàu tình thương, trách nhiệm cao, hướng về gia đình và cộng đồng.", "diem_manh": "Chăm sóc chu đáo, luôn che chở và chữa lành cho người khác.", "thach_thuc": "Hay ôm đồm, lo lắng thái quá, dễ bị lợi dụng lòng tốt.", "nghe_nghiep": "Bác sĩ, giáo viên, nhân viên xã hội, thiết kế nội thất."},
    7: {"ten": "Số 7 - Nhà Thông Thái, Người Tìm Kiếm Chân Lý", "dac_tinh": "Sâu sắc, triết lý, ham học hỏi chân lý, trực giác cao.", "diem_manh": "Tư duy phân tích sắc sảo, năng lực nghiên cứu độc lập vượt trội.", "thach_thuc": "Khép kín, đa nghi, khó hòa nhập với đám đông.", "nghe_nghiep": "Nhà khoa học, triết gia, lập trình viên, nghiên cứu sinh học."},
    8: {"ten": "Số 8 - Nhà Điều Hành, Vua Tài Chính Và Quyền Lực", "dac_tinh": "Tham vọng lớn, kỷ luật thép, hiểu rõ quy luật tiền tệ và quyền lực.", "diem_manh": "Quản lý dòng tiền và kinh doanh đại tài, kiên cường vượt nghịch cảnh.", "thach_thuc": "Thực dụng quá mức, dễ bị cuốn vào vòng xoáy kim tiền.", "nghe_nghiep": "Giám đốc tài chính, nhà đầu tư bất động sản, ngân hàng, CEO."},
    9: {"ten": "Số 9 - Nhà Nhân Đạo, Lý Tưởng Phụng Sự Xã Hội", "dac_tinh": "Vị tha, bao dung, lý tưởng sống cao đẹp, hướng tới nhân loại.", "diem_manh": "Tâm hồn rộng mở, thu hút lòng người bằng tình nhân ái chân thành.", "thach_thuc": "Mơ mộng viển vông, dễ thất vọng khi thực tế phũ phàng.", "nghe_nghiep": "Lãnh đạo phi chính phủ, nhà giáo dục nhân văn, họa sĩ."},
    11: {"ten": "Số Master 11 - Người Khai Sáng Tâm Linh", "dac_tinh": "Trực giác siêu phàm, nhạy bén tâm linh, ngọn hải đăng soi đường.", "diem_manh": "Truyền cảm hứng tầng sâu, kết nối trực giác với thực tại.", "thach_thuc": "Áp lực tinh thần rất lớn, hay lo âu trầm cảm nếu không cân bằng.", "nghe_nghiep": "Nhà khai vấn cuộc sống (Coach), tâm lý học, nhà tư tưởng."},
    22: {"ten": "Số Master 22 - Bậc Thầy Kiến Tạo Thế Giới", "dac_tinh": "Biến giấc mơ vĩ đại thành các công trình đồ sộ phục vụ triệu người.", "diem_manh": "Tầm nhìn thiên tài kết hợp năng lực thực thi vô song.", "thach_thuc": "Gánh nặng trách nhiệm khổng lồ đè nặng đôi vai.", "nghe_nghiep": "Kiến trúc sư các đại công trình quốc gia, nhà sáng lập tập đoàn."}
}

# ==============================================================================
# 11. TỬ VI 12 CON GIÁP & 12 CUNG HOÀNG ĐẠO
# ==============================================================================
ZODIAC_12_CON_GIAP = {
    "tý": {"ten": "Tuổi Tý (Chuột)", "menh_nam": "Thủy", "tinh_cach": "Thông minh, nhanh nhẹn, tháo vát, quản lý tiền bạc chặt chẽ.", "tam_hop": "Thân - Tý - Thìn", "tu_hanh_xung": "Tý - Ngọ - Mão - Dậu", "mau_may_man": "Xanh dương, Đen, Trắng"},
    "sửu": {"ten": "Tuổi Sửu (Trâu)", "menh_nam": "Thổ", "tinh_cach": "Cần cù, chăm chỉ, thật thà, kiên định với mục tiêu.", "tam_hop": "Tỵ - Dậu - Sửu", "tu_hanh_xung": "Thìn - Tuất - Sửu - Mùi", "mau_may_man": "Vàng, Nâu đất, Đỏ"},
    "dần": {"ten": "Tuổi Dần (Hổ)", "menh_nam": "Mộc", "tinh_cach": "Mạnh mẽ, quả cảm, khí chất lãnh đạo, dám nghĩ dám làm.", "tam_hop": "Dần - Ngọ - Tuất", "tu_hanh_xung": "Dần - Thân - Tỵ - Hợi", "mau_may_man": "Xanh lá cây, Đen, Xanh nước biển"},
    "mão": {"ten": "Tuổi Mão (Mèo)", "menh_nam": "Mộc", "tinh_cach": "Ôn hòa, khéo léo, tinh tế, giàu lòng nhân ái.", "tam_hop": "Hợi - Mão - Mùi", "tu_hanh_xung": "Tý - Ngọ - Mão - Dậu", "mau_may_man": "Xanh nõn chuối, Xám, Đen"},
    "thìn": {"ten": "Tuổi Thìn (Rồng)", "menh_nam": "Thổ", "tinh_cach": "Uy quyền, tham vọng lớn, phóng khoáng, số mệnh quý nhân.", "tam_hop": "Thân - Tý - Thìn", "tu_hanh_xung": "Thìn - Tuất - Sửu - Mùi", "mau_may_man": "Vàng kim, Tím, Nâu"},
    "tỵ": {"ten": "Tuổi Tỵ (Rắn)", "menh_nam": "Hỏa", "tinh_cach": "Nhạy bén, sắc sảo, bí ẩn, trực giác sâu sắc.", "tam_hop": "Tỵ - Dậu - Sửu", "tu_hanh_xung": "Dần - Thân - Tỵ - Hợi", "mau_may_man": "Đỏ, Cam, Hồng, Xanh lá"},
    "ngọ": {"ten": "Tuổi Ngọ (Ngựa)", "menh_nam": "Hỏa", "tinh_cach": "Yêu tự do, năng động, nhiệt huyết, thích bay nhảy ngao du.", "tam_hop": "Dần - Ngọ - Tuất", "tu_hanh_xung": "Tý - Ngọ - Mão - Dậu", "mau_may_man": "Tím, Đỏ mận, Vàng chanh"},
    "mùi": {"ten": "Tuổi Mùi (Dê)", "menh_nam": "Thổ", "tinh_cach": "Hiền lành, tình cảm, nhẫn nại, có khiếu nghệ thuật.", "tam_hop": "Hợi - Mão - Mùi", "tu_hanh_xung": "Thìn - Tuất - Sửu - Mùi", "mau_may_man": "Nâu nhạt, Vàng hoàng yến, Trắng"},
    "thân": {"ten": "Tuổi Thân (Khỉ)", "menh_nam": "Kim", "tinh_cach": "Nhanh trí, thông minh, hoạt bát, ứng biến linh hoạt trước nghịch cảnh.", "tam_hop": "Thân - Tý - Thìn", "tu_hanh_xung": "Dần - Thân - Tỵ - Hợi", "mau_may_man": "Trắng, Bạc, Vàng ánh kim"},
    "dậu": {"ten": "Tuổi Dậu (Gà)", "menh_nam": "Kim", "tinh_cach": "Nguyên tắc, đúng giờ, tự tin, giỏi quan sát chi tiết.", "tam_hop": "Tỵ - Dậu - Sửu", "tu_hanh_xung": "Tý - Ngọ - Mão - Dậu", "mau_may_man": "Ánh kim, Nâu đất, Vàng sẫm"},
    "tuất": {"ten": "Tuổi Tuất (Chó)", "menh_nam": "Thổ", "tinh_cach": "Trung thành, chính trực, bảo vệ lẽ phải, hết lòng vì bạn bè.", "tam_hop": "Dần - Ngọ - Tuất", "tu_hanh_xung": "Thìn - Tuất - Sửu - Mùi", "mau_may_man": "Đỏ đun, Xám tro, Vàng cam"},
    "hợi": {"ten": "Tuổi Hợi (Lợn)", "menh_nam": "Thủy", "tinh_cach": "Hào sảng, vô tư, phúc hậu, luôn mang lại bình an cho gia đình.", "tam_hop": "Hợi - Mão - Mùi", "tu_hanh_xung": "Dần - Thân - Tỵ - Hợi", "mau_may_man": "Xanh da trời, Đen tuyền, Trắng sữa"}
}

# ==============================================================================
# 12. CÔNG THỨC MÓN ĂN VIỆT TRUYỀN THỐNG
# ==============================================================================
VIETNAMESE_RECIPES = {
    "phở bò": {
        "ten": "Phở Bò Hà Nội Truyền Thống",
        "nguyen_lieu": ["Xương ống bò (1.5kg)", "Thịt thăn bò / bắp bò hoa (500g)", "Bánh phở tươi (1kg)", "Hành tây, gừng tươi, quế, hồi, thảo quả, hạt mùi", "Hành hoa, rau mùi ta, chanh tươi, ớt hiểm"],
        "cach_nau": "1. Rửa sạch xương bò, luộc sơ nước sôi 5 phút bỏ bọt bẩn, rửa lại bằng nước ấm.\n2. Nướng thơm hành tây, gừng, hoa hồi, quế, thảo quả rồi rửa sạch vỏ cháy, cho vào túi lọc.\n3. Hầm xương lửa nhỏ 4-6 tiếng cùng túi gia vị thơm, vớt bọt liên tục giữ nước trong.\n4. Nêm mắm nhĩ ngon, muối hạt và đường phèn vừa vị.\n5. Chần bánh phở, xếp thịt bò thái mỏng, rắc hành ngò thái nhỏ rồi chan nước dùng sôi sùng sục."
    },
    "bún chả": {
        "ten": "Bún Chả Hà Nội Than Hoa",
        "nguyen_lieu": ["Thịt ba chỉ thái mỏng (400g)", "Thịt nạc vai băm nhỏ (400g)", "Bún tươi sợi nhỏ", "Đu đủ xanh, cà rốt tỉa hoa làm dưa góp", "Hành khô, tỏi ớt băm, sả, nước hàng, nước mắm ngon, tiêu"],
        "cach_nau": "1. Ướp thịt ba chỉ và thịt băm với nước mắm, hành tỏi băm, nước hàng caramel, tiêu ít nhất 1 giờ.\n2. Thịt băm vo viên tròn dẹt, thịt miếng kẹp vào vỉ nướng than hoa cháy xém thơm lừng.\n3. Làm dưa góp: Đu đủ, cà rốt thái lát mỏng bóp muối rửa sạch, ngâm giấm đường chua ngọt.\n4. Pha nước mắm: Tỷ lệ 1 mắm : 1 đường : 1 giấm : 5 nước ấm, thêm tỏi ớt băm nhuyễn.\n5. Thả chả nóng và dưa góp vào bát nước mắm, ăn kèm bún và xà lách, tía tô, kinh giới."
    },
    "cá kho tộ": {
        "ten": "Cá Lóc Kho Tộ Miền Tây",
        "nguyen_lieu": ["Cá lóc (cá quả) tươi ngon (700g)", "Thịt ba chỉ thái con chì (150g)", "Nước màu dừa Bến Tre, nước mắm Phú Quốc", "Tỏi, hành tím băm, tiêu sọ đập dập, ớt chỉ thiên", "Hành lá thái khúc"],
        "cach_nau": "1. Cá làm sạch nhớt bằng muối và chanh, cắt khúc dày 3cm.\n2. Ướp cá với thịt ba chỉ, nước mắm ngon, nước màu dừa, hành tỏi băm, tiêu, ớt trong 30 phút.\n3. Xếp thịt ba chỉ xuống đáy nồi đất, xếp cá lên trên, đun lửa lớn cho cá săn lại.\n4. Châm thêm nước sôi xâm xấp mặt cá, hạ lửa liu riu cho nước sốt sánh keo đậm đà.\n5. Khi nước cạn sánh kẹo lại màu cánh gián, rắc nhiều tiêu và hành hoa, ăn cùng cơm nóng."
    },
    "nem rán": {
        "ten": "Nem Rán (Chả Giò) Hà Nội",
        "nguyen_lieu": ["Thịt nạc vai băm (300g)", "Tôm nõn tươi băm nhỏ (150g)", "Miến dong ngâm mềm, mộc nhĩ nấm hương băm nhuyễn", "Cà rốt nạo sợi, giá đỗ, hành hoa", "Trứng gà (2 quả)", "Bánh đa nem giòn"],
        "cach_nau": "1. Trộn đều thịt, tôm, miến, mộc nhĩ, cà rốt, giá đỗ, trứng gà và tiêu thơm (chú ý nhân không quá ướt).\n2. Trải bánh đa nem ra đĩa phẳng, phết chút giấm loãng cho vỏ giòn xốp lâu, cho nhân vào cuộn tròn vừa tay.\n3. Rán ngập dầu lửa vừa lần 1 cho chín tới.\n4. Trước khi ăn rán lại lửa lớn lần 2 cho vỏ ngoài vàng ruộm giòn tan.\n5. Chấm nước mắm chua ngọt tỏi ớt dưa góp đu đủ."
    }
}

# ==============================================================================
# 13. CÔNG THỨC PHA CHẾ ĐỒ UỐNG VIỆT
# ==============================================================================
BEVERAGE_RECIPES = {
    "cà phê muối": {
        "ten": "Cà Phê Muối Xứ Huế Chuẩn Vị",
        "nguyen_lieu": ["Cà phê bột nguyên chất (25g)", "Sữa đặc (25ml)", "Kem béo thực vật / Whipping cream (40ml)", "Muối hạt hồng hoặc muối biển (1/8 thìa cafe)", "Đá viên"],
        "cach_pha": "1. Cho cà phê vào phin, ủ nước sôi 93 độ C trong 2 phút rồi chiết xuất lấy 40-50ml nước cốt đen đậm đặc.\n2. Cho sữa đặc vào đáy ly.\n3. Đánh bông nhẹ hỗn hợp whipping cream cùng một nhúm muối ăn đến khi sánh mịn như mây.\n4. Cho đá vào ly sữa đặc, rót cà phê đen lên, phủ lớp kem muối béo ngậy lên trên cùng.\n5. Nhấp ngụm đầu để cảm nhận vị mặn ngọt béo đan xen vị đắng đậm sâu lắng."
    },
    "trà thảo mộc hoa cúc": {
        "ten": "Trà Thảo Mộc Hoa Cúc Táo Đỏ Kỷ Tử",
        "nguyen_lieu": ["Hoa cúc sấy khô (5 bông)", "Táo đỏ Tân Cương thái lát (3 quả)", "Kỷ tử đỏ (10 hạt)", "Đường phèn hoặc mật ong hoa nhãn (15ml)", "Nước sôi 90 độ C (350ml)"],
        "cach_pha": "1. Tráng ấm trà bằng nước sôi cho ấm nóng.\n2. Cho hoa cúc, táo đỏ, kỷ tử vào ấm, rót một ít nước sôi lắc nhẹ rồi đổ bỏ nước tráng.\n3. Rót 350ml nước sôi vào hãm trong 10-15 phút cho tinh chất thảo mộc hòa tan.\n4. Thêm đường phèn hoặc mật ong khuấy nhẹ.\n5. Thưởng thức ấm nóng giúp an thần, ngủ ngon sâu giấc, sáng mắt và thanh lọc cơ thể."
    },
    "trà nụ vối": {
        "ten": "Trà Nụ Vối Khô Truyền Thống Đồng Bằng Bắc Bộ",
        "nguyen_lieu": ["Nụ vối phơi khô hoặc ủ men (20g)", "Nước tinh khiết (1 lít)", "Gừng tươi đập dập (1 lát mỏng)"],
        "cach_pha": "1. Rửa sạch nụ vối khô bằng nước lạnh.\n2. Cho nụ vối và lát gừng vào ấm đun sôi với 1 lít nước trong 3-5 phút.\n3. Tắt bếp, ủ trà trong 10 phút cho ngấu và ra màu đỏ nâu trong vắt.\n4. Uống ấm vào mùa đông hoặc cho đá lạnh giải khát ngày hè, cực tốt cho tiêu hóa và hạ đường huyết."
    },
    "trà nấm linh chi": {
        "ten": "Trà Nấm Linh Chi Bổ Phế Tăng Miễn Dịch",
        "nguyen_lieu": ["Nấm linh chi đỏ thái lát mỏng (10g)", "Cam thảo bắc (3 lát) hoặc cỏ ngọt để giảm vị đắng", "Nước lọc (1.2 lít)"],
        "cach_pha": "1. Đun sôi nấm linh chi cùng 1.2 lít nước trên lửa nhỏ trong 20-30 phút.\n2. Thêm vài lát cam thảo để nước trà có hậu vị ngọt thanh dịu dàng.\n3. Rót ra bình giữ nhiệt uống thay nước lọc hàng ngày giúp giải độc gan, điều hòa huyết áp và kéo dài tuổi thọ."
    }
}

# ==============================================================================
# 14. TRUYỆN CỔ TÍCH VIỆT NAM & BÀI HỌC CHO BÉ
# ==============================================================================
FAIRY_TALES = {
    "tấm cám": {
        "ten": "Truyện Cổ Tích Tấm Cám",
        "tom_tat": "Tấm mồ côi mẹ từ nhỏ, sống với dì ghẻ và em Cám độc ác. Tấm chịu bao bất công nhưng nhờ lòng lương thiện và sự giúp đỡ của Bụt cùng ý chí sống mãnh liệt qua các lần hóa thân (chim vàng anh, cây xoan đào, khung cửi, quả thị), cuối cùng Tấm trở lại làm Hoàng hậu xinh đẹp, còn mẹ con Cám phải chịu quả báo thích đáng.",
        "bai_hoc": "Ở hiền gặp lành, cái thiện luôn chiến thắng cái ác; khuyên các bé luôn chăm chỉ, hiền hậu và biết vươn lên dù gặp hoàn cảnh khó khăn."
    },
    "cây tre trăm đốt": {
        "ten": "Cây Tre Trăm Đốt",
        "tom_tat": "Anh Khoai hiền lành cày thuê cho phú ông ba năm với lời hứa gả con gái. Hết hạn, phú ông lật lọng đòi sính lễ cây tre trăm đốt. Nhờ Bụt dạy câu thần chú 'Khắc nhập, khắc nhập' và 'Khắc xuất, khắc xuất', anh Khoai trừng trị được phú ông gian tham và cưới được người vợ hiền.",
        "bai_hoc": "Chăm chỉ lao động chân chính sẽ được đền đáp xứng đáng, kẻ lừa gạt gian manh nhất định sẽ bị trừng phạt."
    },
    "thạch sanh": {
        "ten": "Truyện Thạch Sanh Chém Chằn Tinh",
        "tom_tat": "Thạch Sanh mồ côi sống dưới gốc đa, được thần tiên truyền dạy võ nghệ và phép thần. Dù nhiều lần bị mẹ con Lý Thông hãm hại cướp công, Thạch Sanh vẫn dũng cảm diệt Chằn tinh, bắn Đại bàng cứu công chúa, dùng tiếng đàn cảm hóa quân giặc và dùng niêu cơm thần vô tận chiêu đãi quân 18 nước chư hầu.",
        "bai_hoc": "Lòng dũng cảm vô tư, vị tha và chuộng hòa bình; kẻ độc ác phản bội như Lý Thông cuối cùng bị sét đánh hóa thành bọ hung."
    },
    "ăn khế trả vàng": {
        "ten": "Cây Khế (Ăn Khế Trả Vàng)",
        "tom_tat": "Hai anh em chia gia tài, người anh tham lam lấy hết ruộng đất trâu bò, người em chỉ được túp lều và cây khế. Chim phượng hoàng đến ăn khế hứa 'Ăn một quả, trả cục vàng, may túi ba gang, mang đi mà đựng'. Người em đổi đời giàu có. Người anh tham lam may túi chín gang nên bị rơi xuống biển sâu.",
        "bai_hoc": "Lòng tham vô đáy sẽ tự dẫn đến diệt vong, sống biết ơn và chia sẻ thì cuộc đời luôn an vui hạnh phúc."
    }
}

# ==============================================================================
# 15. MẸO VẶT GIA ĐÌNH & ĐIỆN NƯỚC THÔNG MINH
# ==============================================================================
HOUSEHOLD_HACKS = {
    "khử mùi tủ lạnh": "Đặt một chén nhỏ bã cà phê tươi hoặc một củ sả đập dập hoặc vài lát chanh tươi rắc chút baking soda vào góc tủ. Mùi tanh của thực phẩm sẽ biến mất sau 12 giờ.",
    "chống ẩm mốc quần áo": "Đặt các túi hút ẩm silica gel hoặc một túi vôi sống nhỏ ở góc tủ áo. Mùa nồm ẩm nên dùng máy hút ẩm hoặc bật điều hòa chế độ Dry 2 tiếng mỗi ngày.",
    "thông tắc cống nghẹt": "Đổ 1 bát baking soda (muối nở) trực tiếp vào miệng cống, tiếp theo đổ 2 bát giấm trắng. Đậy nắp chờ 20 phút cho phản ứng sủi bọt đánh tan dầu mỡ rồi dội mạnh một ấm nước sôi 100 độ C.",
    "làm sạch vòi sen rỉ sét cặn canxi": "Buộc một túi nilon chứa giấm trắng ngập đầu vòi sen, ngâm qua đêm. Sáng hôm sau cặn vôi canxi tự rã hết, dùng bàn chải đánh răng chà nhẹ là sáng bóng như mới.",
    "khử mùi tanh bám trên thớt": "Rắc muối hạt lên mặt thớt gỗ, dùng nửa quả chanh chà xát mạnh vòng tròn rồi rửa sạch bằng nước ấm. Vừa sạch khuẩn vừa thơm mùi tinh dầu chanh tự nhiên.",
    "xử lý công tắc điện bị nóng": "Ngắt ngay aptomat (CB) tổng của nhánh đó. Kiểm tra xem các ốc siết đầu dây có bị lỏng gây phóng tia lửa điện sinh nhiệt không; nếu có mùi khét cần thay mới công tắc chịu tải lớn hơn ngay lập tức."
}

# ==============================================================================
# 16. TRA CỨU MÃ LỖI ĐIỆN TỬ (ĐIỀU HÒA, MÁY GIẶT, TỦ LẠNH)
# ==============================================================================
ELECTRONICS_ERROR_CODES = {
    "daikin": {
        "a6": "Lỗi động cơ quạt dàn lạnh bị kẹt hoặc hỏng mạch điều khiển quạt.",
        "e0": "Kích hoạt thiết bị bảo vệ tổng bộ dàn nóng.",
        "e5": "Lỗi động cơ máy nén (Block) bị kẹt cơ hoặc quá dòng.",
        "u0": "Lỗi thiếu môi chất lạnh (thiếu gas, rò rỉ đường ống đồng).",
        "u4": "Lỗi mất tín hiệu truyền thông kết nối giữa dàn nóng và dàn lạnh."
    },
    "panasonic": {
        "h11": "Lỗi mất kết nối giao tiếp tín hiệu giữa dàn nóng và dàn lạnh.",
        "h14": "Lỗi cảm biến nhiệt độ không khí phòng trong nhà.",
        "f91": "Lỗi dòng tải máy nén thấp, dấu hiệu hết sạch gas hoặc tắc nghẽn van tiết lưu."
    },
    "lg": {
        "ch05": "Lỗi tín hiệu đường truyền giữa dàn nóng và dàn lạnh.",
        "ie": "Lỗi cấp nước: Nước không chảy vào máy giặt trong thời gian quy định.",
        "oe": "Lỗi xả nước: Ống xả bị tắc nghẽn hoặc bơm xả bị kẹt rác.",
        "de": "Lỗi công tắc cửa chưa đóng chặt hoặc hỏng khóa điện từ."
    },
    "samsung": {
        "4c": "Nước không được cấp vào máy giặt (kiểm tra van cấp, vòi nước và lưới lọc).",
        "5c": "Nước không xả được ra ngoài (kiểm tra ống thoát và bộ lọc cặn).",
        "ub": "Lỗi mất cân bằng lồng giặt khi vắt (quần áo bị dồn về một phía)."
    },
    "electrolux": {
        "e10": "Nguồn cấp nước vào máy quá yếu hoặc bị khóa van nước.",
        "e20": "Đường thoát nước bị tắc nghẽn hoặc bơm xả không hoạt động.",
        "e40": "Cửa máy giặt chưa đóng kín hoặc hỏng chốt an toàn cửa."
    }
}

# ==============================================================================
# 17. NIÊN BIỂU CÁC TRIỀU ĐẠI LỊCH SỬ VIỆT NAM
# ==============================================================================
DYNASTIES_VN = [
    {"trieu_dai": "Thời kỳ Hồng Bàng (Nước Văn Lang)", "nien_dai": "Khoảng 2879 TCN – 258 TCN", "kinh_do": "Phong Châu (Phú Thọ)", "thanh_tuu": "Thời đại 18 đời Vua Hùng đặt nền móng dựng nước, văn hóa Đông Sơn rực rỡ với Trống đồng."},
    {"trieu_dai": "Nhà Thục (Nước Âu Lạc)", "nien_dai": "257 TCN – 179 TCN", "kinh_do": "Cổ Loa (Đông Anh, Hà Nội)", "thanh_tuu": "An Dương Vương hợp nhất Lạc Việt và Tây Âu, xây dựng Thành Cổ Loa xoắn ốc kiên cố và nỏ thần Liên Châu."},
    {"trieu_dai": "Khởi nghĩa Hai Bà Trưng", "nien_dai": "40 – 43", "kinh_do": "Mê Linh (Hà Nội)", "thanh_tuu": "Hai chị em Trưng Trắc - Trưng Nhị dấy binh đánh đuổi Tô Định, rửa nợ nước trả thù nhà, giành lại độc lập sau hơn 200 năm Bắc thuộc."},
    {"trieu_dai": "Nhà Tiền Lý (Nước Vạn Xuân)", "nien_dai": "544 – 602", "kinh_do": "Long Biên", "thanh_tuu": "Lý Bí (Lý Nam Đế) đánh đuổi quân Lương lập ra nước Vạn Xuân độc lập tự chủ, xây chùa Trấn Quốc."},
    {"trieu_dai": "Nhà Ngô", "nien_dai": "939 – 965", "kinh_do": "Cổ Loa", "thanh_tuu": "Ngô Quyền đại phá quân Nam Hán trên sông Bạch Đằng năm 938, chấm dứt hoàn toàn hơn 1000 năm Bắc thuộc tối tăm, mở ra kỷ nguyên độc lập lâu dài."},
    {"trieu_dai": "Nhà Đinh (Nước Đại Cồ Việt)", "nien_dai": "968 – 980", "kinh_do": "Hoa Lư (Ninh Bình)", "thanh_tuu": "Đinh Bộ Lĩnh dẹp loạn 12 sứ quân, xưng Hoàng đế (Đinh Tiên Hoàng), đúc tiền đồng Thái Bình Hưng Bảo đầu tiên của Việt Nam."},
    {"trieu_dai": "Nhà Tiền Lê", "nien_dai": "980 – 1009", "kinh_do": "Hoa Lư", "thanh_tuu": "Lê Hoàn (Lê Đại Hành) đánh tan quân xâm lược nhà Tống năm 981 trên sông Bạch Đằng và ải Chi Lăng, bình định Chiêm Thành."},
    {"trieu_dai": "Nhà Lý (Nước Đại Việt)", "nien_dai": "1009 – 1225", "kinh_do": "Thăng Long (Hà Nội)", "thanh_tuu": "Lý Thái Tổ dời đô về Thăng Long năm 1010; Lý Thường Kiệt đọc bản Tuyên ngôn độc lập đầu tiên 'Nam quốc sơn hà' trên sông Như Nguyệt năm 1077; xây dựng Văn Miếu Quốc Tử Giám."},
    {"trieu_dai": "Nhà Trần", "nien_dai": "1225 – 1400", "kinh_do": "Thăng Long", "thanh_tuu": "Hào khí Đông A ba lần đánh tan đế quốc Nguyên Mông hùng mạnh bậc nhất thế giới (1258, 1285, 1288) dưới sự thống lĩnh của Quốc công Tiết chế Hưng Đạo Đại Vương Trần Quốc Tuấn; Phật hoàng Trần Nhân Tông sáng lập Thiền phái Trúc Lâm."},
    {"trieu_dai": "Nhà Hồ (Nước Đại Ngu)", "nien_dai": "1400 – 1407", "kinh_do": "Tây Đô (Thanh Hóa)", "thanh_tuu": "Hồ Quý Ly cải cách tiền tệ (tiền giấy Thông Bảo Hội Sao), xây Thành nhà Hồ bằng đá nguyên khối di sản UNESCO."},
    {"trieu_dai": "Nhà Hậu Lê (Thời Lê Sơ)", "nien_dai": "1428 – 1527", "kinh_do": "Đông Kinh (Thăng Long)", "thanh_tuu": "Lê Lợi khởi nghĩa Lam Sơn 10 năm gian khổ đánh tan giặc Minh xâm lược; Nguyễn Trãi viết Bình Ngô Đại Cáo; vua Lê Thánh Tông ban hành Bộ luật Hồng Đức hoàn thiện bậc nhất lịch sử phong kiến."},
    {"trieu_dai": "Nhà Tây Sơn", "nien_dai": "1778 – 1802", "kinh_do": "Quy Nhơn / Phú Xuân", "thanh_tuu": "Người anh hùng áo vải cờ đào Quang Trung - Nguyễn Huệ đại phá 5 vạn quân Xiêm tại Rạch Gầm - Xoài Mút (1785) và thần tốc đại phá 29 vạn quân Mãn Thanh mùa xuân Kỷ Dậu (1789)."},
    {"trieu_dai": "Nhà Nguyễn (Quốc hiệu Việt Nam)", "nien_dai": "1802 – 1945", "kinh_do": "Phú Xuân (Huế)", "thanh_tuu": "Vua Gia Long thống nhất đất nước từ Mục Nam Quan đến Mũi Cà Mau; xác lập chủ quyền vững chắc trên hai quần đảo Hoàng Sa và Trường Sa; xây dựng quần thể Cố đô Huế."}
]

# ==============================================================================
# 18. MÃ VẠCH QUỐC GIA (GS1 PREFIX)
# ==============================================================================
BARCODE_COUNTRIES = {
    "893": "Việt Nam 🇻🇳",
    "690": "Trung Quốc 🇨🇳", "691": "Trung Quốc 🇨🇳", "692": "Trung Quốc 🇨🇳", "693": "Trung Quốc 🇨🇳", "694": "Trung Quốc 🇨🇳", "695": "Trung Quốc 🇨🇳", "696": "Trung Quốc 🇨🇳", "697": "Trung Quốc 🇨🇳", "698": "Trung Quốc 🇨🇳", "699": "Trung Quốc 🇨🇳",
    "880": "Hàn Quốc 🇰🇷",
    "450": "Nhật Bản 🇯🇵", "451": "Nhật Bản 🇯🇵", "452": "Nhật Bản 🇯🇵", "453": "Nhật Bản 🇯🇵", "454": "Nhật Bản 🇯🇵", "455": "Nhật Bản 🇯🇵", "456": "Nhật Bản 🇯🇵", "457": "Nhật Bản 🇯🇵", "458": "Nhật Bản 🇯🇵", "459": "Nhật Bản 🇯🇵", "490": "Nhật Bản 🇯🇵", "491": "Nhật Bản 🇯🇵", "492": "Nhật Bản 🇯🇵", "493": "Nhật Bản 🇯🇵", "494": "Nhật Bản 🇯🇵", "495": "Nhật Bản 🇯🇵", "496": "Nhật Bản 🇯🇵", "497": "Nhật Bản 🇯🇵", "498": "Nhật Bản 🇯🇵", "499": "Nhật Bản 🇯🇵",
    "885": "Thái Lan 🇹🇭",
    "888": "Singapore 🇸🇬",
    "955": "Malaysia 🇲🇾",
    "899": "Indonesia 🇮🇩",
    "471": "Đài Loan (Trung Quốc) 🇹🇼",
    "489": "Hồng Kông (Trung Quốc) 🇭🇰",
    "000": "Hoa Kỳ & Canada 🇺🇸 🇨🇦", "001": "Hoa Kỳ 🇺🇸", "002": "Hoa Kỳ 🇺🇸", "003": "Hoa Kỳ 🇺🇸", "004": "Hoa Kỳ 🇺🇸", "005": "Hoa Kỳ 🇺🇸", "006": "Hoa Kỳ 🇺🇸", "007": "Hoa Kỳ 🇺🇸", "008": "Hoa Kỳ 🇺🇸", "009": "Hoa Kỳ 🇺🇸", "010": "Hoa Kỳ 🇺🇸",
    "400": "Đức 🇩🇪", "401": "Đức 🇩🇪", "402": "Đức 🇩🇪", "403": "Đức 🇩🇪", "404": "Đức 🇩🇪", "440": "Đức 🇩🇪",
    "500": "Vương Quốc Anh 🇬🇧", "501": "Vương Quốc Anh 🇬🇧", "502": "Vương Quốc Anh 🇬🇧",
    "300": "Pháp 🇫🇷", "301": "Pháp 🇫🇷", "302": "Pháp 🇫🇷", "379": "Pháp 🇫🇷",
    "800": "Ý 🇮🇹", "801": "Ý 🇮🇹", "802": "Ý 🇮🇹", "839": "Ý 🇮🇹",
    "930": "Úc 🇦🇺", "931": "Úc 🇦🇺", "932": "Úc 🇦🇺",
    "940": "New Zealand 🇳🇿"
}

# ==============================================================================
# 19. NGÀY LỄ & SỰ KIỆN VIỆT NAM
# ==============================================================================
VIETNAMESE_HOLIDAYS = [
    {"ngay": "01/01", "ten": "Tết Dương Lịch", "loai": "Dương lịch", "nghi": "Nghỉ 1 ngày hưởng nguyên lương"},
    {"ngay": "03/02", "ten": "Ngày thành lập Đảng Cộng sản Việt Nam (1930)", "loai": "Kỷ niệm", "nghi": "Không nghỉ"},
    {"ngay": "08/03", "ten": "Ngày Quốc tế Phụ nữ", "loai": "Sự kiện", "nghi": "Không nghỉ"},
    {"ngay": "10/03 AL", "ten": "Giỗ Tổ Hùng Vương (10 tháng 3 Âm lịch)", "loai": "Âm lịch", "nghi": "Nghỉ 1 ngày hưởng nguyên lương"},
    {"ngay": "30/04", "ten": "Ngày Giải phóng Miền Nam, Thống nhất Đất nước (1975)", "loai": "Dương lịch", "nghi": "Nghỉ 1 ngày hưởng nguyên lương"},
    {"ngay": "01/05", "ten": "Ngày Quốc tế Lao động", "loai": "Dương lịch", "nghi": "Nghỉ 1 ngày hưởng nguyên lương"},
    {"ngay": "19/05", "ten": "Ngày sinh Chủ tịch Hồ Chí Minh (1890)", "loai": "Kỷ niệm", "nghi": "Không nghỉ"},
    {"ngay": "01/06", "ten": "Ngày Quốc tế Thiếu nhi", "loai": "Sự kiện", "nghi": "Không nghỉ"},
    {"ngay": "27/07", "ten": "Ngày Thương binh Liệt sĩ", "loai": "Kỷ niệm", "nghi": "Không nghỉ"},
    {"ngay": "19/08", "ten": "Ngày Cách mạng Tháng Tám thành công (1945)", "loai": "Kỷ niệm", "nghi": "Không nghỉ"},
    {"ngay": "02/09", "ten": "Ngày Quốc khánh Nước CHXHCN Việt Nam (1945)", "loai": "Dương lịch", "nghi": "Nghỉ 2 ngày hưởng nguyên lương"},
    {"ngay": "20/10", "ten": "Ngày Phụ nữ Việt Nam (1930)", "loai": "Kỷ niệm", "nghi": "Không nghỉ"},
    {"ngay": "20/11", "ten": "Ngày Nhà giáo Việt Nam", "loai": "Kỷ niệm", "nghi": "Không nghỉ"},
    {"ngay": "22/12", "ten": "Ngày thành lập Quân đội Nhân dân Việt Nam (1944)", "loai": "Kỷ niệm", "nghi": "Không nghỉ"},
    {"ngay": "01/01 AL", "ten": "Tết Nguyên Đán (Tết Cổ Truyền Việt Nam)", "loai": "Âm lịch", "nghi": "Nghỉ từ 5 đến 7 ngày theo quy định Chính phủ"},
    {"ngay": "15/01 AL", "ten": "Tết Nguyên Tiêu (Rằm tháng Giêng)", "loai": "Âm lịch", "nghi": "Lễ hội truyền thống"},
    {"ngay": "05/05 AL", "ten": "Tết Đoan Ngọ (Giết sâu bọ)", "loai": "Âm lịch", "nghi": "Lễ hội dân gian"},
    {"ngay": "15/07 AL", "ten": "Lễ Vu Lan Báo Hiếu & Xá tội vong nhân", "loai": "Âm lịch", "nghi": "Lễ hội văn hóa Phật giáo"},
    {"ngay": "15/08 AL", "ten": "Tết Trung Thu (Tết Trông Trăng của thiếu nhi)", "loai": "Âm lịch", "nghi": "Lễ hội truyền thống"}
]

# ==============================================================================
# 20. BỘ TỪ GHÉP NỐI TỪ TIẾNG VIỆT
# ==============================================================================
WORD_CHAIN_DICT = {
    "hoa": ["hồng", "cúc", "mai", "sen", "lan", "đào", "súng", "huệ", "tiêu"],
    "hồng": ["hào", "nhan", "phúc", "ngọc", "tâm", "đức"],
    "hào": ["hoa", "hùng", "kiệt", "hiệp", "quang", "sảng"],
    "hùng": ["vĩ", "dũng", "hậu", "cường", "tráng", "bi"],
    "vĩ": ["đại", "tuyến", "nhân", "mô"],
    "đại": ["học", "gia", "đao", "lộ", "phú", "thắng"],
    "học": ["hành", "tập", "sinh", "vị", "hỏi", "thức"],
    "hành": ["động", "trình", "chính", "tỏi", "vi", "quân"],
    "động": ["lực", "viên", "não", "đất", "phòng", "cơ"],
    "lực": ["lượng", "sĩ", "học", "điền", "hút"],
    "lượng": ["tử", "giác", "thứ", "hóa", "hình"],
    "tử": ["tế", "vi", "thần", "chiến", "hình", "đoán"],
    "tế": ["bào", "nhị", "điển", "lễ", "độ"],
    "bào": ["ngư", "chế", "mòn", "thai", "chữa"],
    "ngư": ["dân", "nghiệp", "ông", "lưới"],
    "dân": ["chủ", "tộc", "gian", "ca", "trí", "sinh"],
    "chủ": ["nghĩa", "động", "trì", "tọa", "nhật", "quản"],
    "nghĩa": ["khí", "vụ", "trang", "hiệp", "dũng"],
    "khí": ["quyển", "chất", "thế", "cụ", "hậu", "tượng"],
    "quyển": ["sách", "vở", "kinh", "tập"],
    "sách": ["vở", "lược", "báo", "giáo khoa"],
    "vở": ["kịch", "bài tập", "tuồng"],
    "kịch": ["bản", "sĩ", "liệt", "trường"],
    "bản": ["lĩnh", "thân", "đồ", "sắc", "tính", "năng"],
    "lĩnh": ["vực", "thổ", "nam", "tụ"],
    "vực": ["thẳm", "dậy", "sâu"],
    "thẳm": ["sâu", "xa"],
    "sâu": ["sắc", "bọ", "răng", "hoắm"],
    "sắc": ["đẹp", "màu", "thái", "bén", "sảo"]
}
