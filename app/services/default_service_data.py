import json

DEFAULT_SERVICE_DETAILS = {
    "van-chuyen-di-doi": {
        "hero_heading": "Dịch vụ vận chuyển, di dời trọn gói chuyên nghiệp & an toàn.",
        "content": (
            "Oshin Thời Đại cung cấp giải pháp vận chuyển và di dời trọn gói từ nhà ở, căn hộ chung cư "
            "đến văn phòng, cơ quan và kho xưởng. Với quy trình bọc lót nhiều lớp, phương tiện xe tải đa dạng "
            "và đội ngũ bốc xếp chuyên nghiệp, cẩn trọng, chúng tôi cam kết bảo vệ tài sản của quý khách an toàn tuyệt đối."
        ),
        "scope_of_work": json.dumps([
            "Vận chuyển nhà phố, căn hộ chung cư, phòng trọ trọn gói",
            "Di dời văn phòng làm việc, bàn ghế hội trường, thiết bị điện tử",
            "Di dời nhà xưởng, kho bãi, máy móc và vật tư công nghiệp nhẹ",
            "Đóng gói, bao bọc màng PE, bọc xốp chống va đập, trầy xước",
            "Tháo dỡ và lắp đặt giường tủ, máy lạnh, thiết bị gia dụng cơ bản",
            "Bốc xếp hai đầu, hỗ trợ khuân vác thang bộ và di chuyển thang máy an toàn"
        ], ensure_ascii=False),
        "process": json.dumps([
            {"step": "01", "title": "Tiếp nhận thông tin", "desc": "Ghi nhận địa điểm đi, điểm đến, khối lượng đồ đạc và thời gian dự kiến."},
            {"step": "02", "title": "Khảo sát & Báo giá", "desc": "Khảo sát thực tế hoặc qua hình ảnh/video để lên phương án xe và chi phí tối ưu."},
            {"step": "03", "title": "Đóng gói & Phân loại", "desc": "Bọc lót màng bảo vệ, phân loại thùng carton, đánh dấu tài sản cẩn thận."},
            {"step": "04", "title": "Vận chuyển & Bốc dỡ", "desc": "Di chuyển an toàn theo lộ trình và sắp xếp vào đúng vị trí tại nơi ở mới."},
            {"step": "05", "title": "Nghiệm thu & Bàn giao", "desc": "Khách hàng kiểm tra đầy đủ số lượng và hiện trạng đồ đạc trước khi thanh toán."}
        ], ensure_ascii=False),
        "benefits": json.dumps([
            {"title": "An toàn tài sản", "desc": "Quy trình bao bọc nhiều lớp hạn chế tối đa nguy cơ trầy xước, rơi vỡ tài sản."},
            {"title": "Đội ngũ chuyên nghiệp", "desc": "Nhân viên bốc xếp khỏe mạnh, cẩn thận, trung thực và có kỹ năng tháo lắp đồ gỗ, điện tử."},
            {"title": "Linh hoạt thời gian", "desc": "Sẵn sàng phục vụ 24/7, bao gồm cả ngoài giờ hành chính, ban đêm và ngày nghỉ cuối tuần."},
            {"title": "Tiết kiệm chi phí", "desc": "Điều phối đúng tải trọng xe và lượng nhân lực thực tế, không phát sinh chi phí vô lý."}
        ], ensure_ascii=False),
        "faq": json.dumps([
            {"q": "Công ty có hỗ trợ tháo lắp giường tủ và máy lạnh không?", "a": "Dạ có ạ. Đội ngũ kỹ thuật viên của Oshin Thời Đại hỗ trợ tháo dỡ và lắp ráp lại các vật dụng nội thất cơ bản theo yêu cầu của quý khách."},
            {"q": "Đồ đạc dễ vỡ được bảo quản như thế nào?", "a": "Dạ toàn bộ đồ gốm sứ, kính, điện tử được bọc xốp bóng khí (bubble wrap), chèn màng PE và đóng thùng carton ghi chú rõ ràng."},
            {"q": "Nếu chỉ cần thuê nhân công bốc xếp hoặc xe tải riêng thì có được không?", "a": "Dạ hoàn toàn được ạ. Quý khách có thể chọn gói trọn gói hoặc chỉ thuê xe / nhân công bốc xếp tùy theo nhu cầu thực tế."}
        ], ensure_ascii=False),
        "seo_title": "Dịch Vụ Vận Chuyển, Di Dời Trọn Gói - Oshin Thời Đại",
        "seo_description": "Dịch vụ vận chuyển nhà ở, văn phòng, kho xưởng trọn gói uy tín, chuyên nghiệp. Đóng gói cẩn thận, bốc xếp an toàn, phục vụ tận tâm 24/7."
    },
    "ve-sinh-cong-nghiep": {
        "hero_heading": "Giải pháp vệ sinh công nghiệp chuyên nghiệp cho không gian của bạn.",
        "content": (
            "Dịch vụ vệ sinh công nghiệp của Oshin Thời Đại ứng dụng hệ thống máy chà sàn, máy hút bụi công nghiệp "
            "công suất cao và hóa chất chuyên dụng an toàn. Chúng tôi xử lý triệt để vết sơn, xi măng sau xây dựng, bụi mịn "
            "và vết ố lâu ngày, trả lại bề mặt sạch sẽ, sáng bóng và vệ sinh cho mọi công trình."
        ),
        "scope_of_work": json.dumps([
            "Tổng vệ sinh công trình sau xây dựng hoặc sau cải tạo, sửa chữa",
            "Vệ sinh định kỳ tòa nhà, cao ốc văn phòng, showroom, trường học",
            "Chà sàn, hút bụi công nghiệp, tẩy vết ố sơn, ximăng và keo dán",
            "Lau kính mặt trong và lau kính mặt dựng ngoài trời chuyên nghiệp",
            "Giặt thảm trải sàn văn phòng, giặt ghế sofa, ghế làm việc tại chỗ",
            "Khử mùi, khử khuẩn không gian và xử lý ẩm mốc chuyên sâu"
        ], ensure_ascii=False),
        "process": json.dumps([
            {"step": "01", "title": "Khảo sát hiện trạng", "desc": "Đo đạc diện tích, kiểm tra chất liệu mặt sàn, kính và mức độ bám bẩn thực tế."},
            {"step": "02", "title": "Lập kế hoạch thi công", "desc": "Bố trí máy móc công nghiệp, hóa chất phù hợp và định lượng nhân lực."},
            {"step": "03", "title": "Thu gom rác & Hút bụi thô", "desc": "Dọn dẹp xà bần, rác thô và hút bụi sạch sẽ từ trên cao xuống sàn."},
            {"step": "04", "title": "Vệ sinh chuyên sâu", "desc": "Chà sàn máy, tẩy ố góc cạnh, lau kính hai mặt, vệ sinh khung cửa và toilet."},
            {"step": "05", "title": "Kiểm tra chất lượng & Bàn giao", "desc": "Cùng khách hàng kiểm tra từng hạng mục theo checklist đến khi hài lòng."}
        ], ensure_ascii=False),
        "benefits": json.dumps([
            {"title": "Trang thiết bị hiện đại", "desc": "Sở hữu máy chà sàn, máy hút bụi nước công nghiệp giúp làm sạch sâu mọi ngóc ngách."},
            {"title": "Hóa chất an toàn", "desc": "Sử dụng hóa chất làm sạch chuyên dụng có nguồn gốc rõ ràng, không gây hư hại bề mặt và an toàn cho người dùng."},
            {"title": "Quy trình kiểm tra khắt khe", "desc": "Đội ngũ giám sát trực tiếp nghiệm thu từng mét vuông trước khi bàn giao cho khách hàng."},
            {"title": "Tiến độ chuẩn xác", "desc": "Cam kết hoàn thành đúng thời gian thỏa thuận, sẵn sàng tăng ca đêm để bàn giao kịp khai trương."}
        ], ensure_ascii=False),
        "faq": json.dumps([
            {"q": "Công ty có nhận vệ sinh công trình mới hoàn thiện xây dựng không?", "a": "Dạ có ạ. Đây là thế mạnh của bên em, xử lý sạch bụi ximăng, vết sơn tường, keo silicon trên kính và ron gạch sàn."},
            {"q": "Thời gian vệ sinh một căn nhà hoặc văn phòng mất bao lâu?", "a": "Dạ tùy theo diện tích và khối lượng thực tế, bên em sẽ điều phối số lượng nhân sự tương ứng để hoàn tất gọn gàng trong ngày."},
            {"q": "Bên em có mang theo máy móc và hóa chất không hay gia chủ phải chuẩn bị?", "a": "Dạ đội ngũ Oshin Thời Đại tự chuẩn bị đầy đủ 100% trang thiết bị, máy móc công nghiệp và hóa chất chuyên dụng ạ."}
        ], ensure_ascii=False),
        "seo_title": "Dịch Vụ Vệ Sinh Công Nghiệp Chuyên Nghiệp - Oshin Thời Đại",
        "seo_description": "Dịch vụ vệ sinh công nghiệp sau xây dựng, văn phòng, nhà xưởng sạch bong kin kít. Trang bị máy móc hiện đại, khảo sát miễn phí tận nơi."
    },
    "trang-tri-sua-chua": {
        "hero_heading": "Dịch vụ trang trí, sửa chữa & cải tạo không gian uy tín.",
        "content": (
            "Dịch vụ trang trí và sửa chữa của Oshin Thời Đại chuyên cải tạo, bảo trì, xử lý sự cố điện nước, chống thấm, "
            "sơn sửa và làm mới không gian sống, làm việc. Chúng tôi mang đến giải pháp thi công nhanh chóng, an toàn và thẩm mỹ cao."
        ),
        "scope_of_work": json.dumps([
            "Sửa chữa, khắc phục sự cố hệ thống điện dân dụng và văn phòng",
            "Xử lý rò rỉ nước, thay thế vòi sen, lavabo, bồn cầu và đường ống nước",
            "Sơn mới, sơn dặm vá tường, xử lý bong tróc và ẩm mốc",
            "Chống thấm dột mái tôn, sàn mái, ban công và nhà vệ sinh",
            "Thi công vách thạch cao, ốp lát gạch nền và gạch tường",
            "Cải tạo, trang trí hoàn thiện không gian theo yêu cầu gia chủ"
        ], ensure_ascii=False),
        "process": json.dumps([
            {"step": "01", "title": "Khảo sát thực tế", "desc": "Kiểm tra nguyên nhân hư hỏng, đo đạc khối lượng cần sửa chữa hoặc cải tạo."},
            {"step": "02", "title": "Tư vấn giải pháp", "desc": "Đề xuất vật tư chất lượng và phương án khắc phục triệt để, tiết kiệm chi phí."},
            {"step": "03", "title": "Chuẩn bị & Che chắn", "desc": "Bao bọc đồ đạc xung quanh khu vực thi công tránh bụi bẩn và trầy xước."},
            {"step": "04", "title": "Tiến hành sửa chữa", "desc": "Thi công chuẩn kỹ thuật, bảo đảm an toàn lao động và độ thẩm mỹ."},
            {"step": "05", "title": "Dọn dẹp & Nghiệm thu", "desc": "Vệ sinh sạch sẽ hiện trường và kiểm tra vận hành trước khi bàn giao."}
        ], ensure_ascii=False),
        "benefits": json.dumps([
            {"title": "Khắc phục triệt để", "desc": "Tìm đúng nguyên nhân sự cố để xử lý dứt điểm, không làm tạm bợ."},
            {"title": "Thợ lành nghề", "desc": "Kỹ thuật viên có tay nghề cao, tác phong lịch sự, trung thực và cẩn thận."},
            {"title": "Vật tư chính hãng", "desc": "Tư vấn vật liệu chất lượng bền đẹp, có nguồn gốc rõ ràng."},
            {"title": "Bảo hành trách nhiệm", "desc": "Hỗ trợ kiểm tra và bảo hành sau khi hoàn thành công việc."}
        ], ensure_ascii=False),
        "faq": json.dumps([
            {"q": "Công ty có nhận sửa các việc nhỏ trong nhà không?", "a": "Dạ có ạ. Bên em nhận từ các việc nhỏ như thay bóng đèn, sửa vòi nước rỉ đến cải tạo cả căn nhà."},
            {"q": "Có khảo sát và báo giá trước khi làm không?", "a": "Dạ luôn luôn có ạ. Kỹ thuật viên sẽ kiểm tra trực tiếp và báo giá chi tiết, quý khách đồng ý mới tiến hành thi công."},
            {"q": "Vật tư do công ty mua hay chủ nhà tự chuẩn bị?", "a": "Dạ quý khách có thể tự chuẩn bị hoặc bên em cung cấp trọn gói theo đúng thương hiệu quý khách yêu cầu."}
        ], ensure_ascii=False),
        "seo_title": "Dịch Vụ Trang Trí, Sửa Chữa Nhà Ở & Văn Phòng - Oshin Thời Đại",
        "seo_description": "Dịch vụ sửa chữa điện nước, chống thấm, sơn sửa nhà, cải tạo không gian sống chuyên nghiệp. Thợ lành nghề, khảo sát tận nơi nhanh chóng."
    },
    "cung-cap-quan-ly-lao-dong": {
        "hero_heading": "Cung cấp & quản lý nguồn lao động uy tín, linh hoạt.",
        "content": (
            "Oshin Thời Đại cung cấp và điều phối nguồn nhân lực lao động phổ thông, công nhân thời vụ, nhân sự phụ kho, "
            "bốc xếp và gia công đóng gói cho các doanh nghiệp, nhà xưởng và công trình. Đảm bảo nguồn lao động nhanh chóng, "
            "đúng giờ và quản lý kỷ luật lao động chặt chẽ."
        ),
        "scope_of_work": json.dumps([
            "Cung ứng lao động thời vụ theo ca, theo ngày, tuần hoặc tháng",
            "Nhân lực bốc dỡ hàng hóa container, sắp xếp kho bãi và chuyển hàng",
            "Công nhân phụ việc sản xuất, gia công, đóng gói và dán nhãn sản phẩm",
            "Lao động phụ việc công trình, dọn dẹp mặt bằng thi công",
            "Quản lý, điều phối và giám sát chấm công nhân sự tại hiện trường",
            "Hỗ trợ thay thế nhân sự kịp thời khi có yêu cầu phát sinh"
        ], ensure_ascii=False),
        "process": json.dumps([
            {"step": "01", "title": "Tiếp nhận yêu cầu", "desc": "Ghi nhận số lượng lao động, tính chất công việc, địa điểm và thời gian làm việc."},
            {"step": "02", "title": "Tuyển chọn & Phổ biến", "desc": "Sàng lọc nhân sự phù hợp sức khỏe, kỹ năng và phổ biến nội quy công việc."},
            {"step": "03", "title": "Bàn giao nhân sự", "desc": "Đưa nhân lực đến địa điểm làm việc đúng giờ và làm quen công việc."},
            {"step": "04", "title": "Giám sát & Quản lý", "desc": "Theo dõi tiến độ, chấm công và giải quyết các vấn đề phát sinh trong ca làm."},
            {"step": "05", "title": "Tổng kết & Quyết toán", "desc": "Đối soát bảng công và tổng kết đánh giá chất lượng công việc định kỳ."}
        ], ensure_ascii=False),
        "benefits": json.dumps([
            {"title": "Đáp ứng nhanh chóng", "desc": "Cung ứng đủ số lượng lao động cần thiết trong thời gian ngắn, giúp duy trì chuỗi vận hành."},
            {"title": "Lao động có trách nhiệm", "desc": "Nhân sự khỏe mạnh, có lý lịch rõ ràng, tuân thủ kỷ luật và an toàn lao động."},
            {"title": "Linh hoạt thời vụ", "desc": "Giúp doanh nghiệp chủ động tăng giảm quy mô nhân lực theo mùa vụ mà không chịu gánh nặng biên chế."},
            {"title": "Đầy đủ hợp đồng", "desc": "Ký kết hợp đồng rõ ràng, thủ tục minh bạch và bảo đảm quyền lợi đôi bên."}
        ], ensure_ascii=False),
        "faq": json.dumps([
            {"q": "Doanh nghiệp cần gấp lao động trong ngày có đáp ứng được không?", "a": "Dạ bên em có sẵn lực lượng lao động sẵn sàng điều động để hỗ trợ các nhu cầu gấp trong ngày."},
            {"q": "Nếu công nhân làm việc không đạt yêu cầu thì có được đổi người không?", "a": "Dạ có ạ. Bên em cam kết hỗ trợ thay thế nhân sự kịp thời để không ảnh hưởng đến tiến độ của doanh nghiệp."},
            {"q": "Bên công ty có xuất hóa đơn VAT đầy đủ không?", "a": "Dạ có ạ. Oshin Thời Đại cung cấp đầy đủ hợp đồng cung ứng lao động và hóa đơn giá trị gia tăng hợp lệ."}
        ], ensure_ascii=False),
        "seo_title": "Cung Cấp & Quản Lý Nguồn Lao Động Thời Vụ - Oshin Thời Đại",
        "seo_description": "Dịch vụ cung cấp lao động phổ thông, công nhân đóng gói, bốc xếp kho bãi uy tín. Nguồn nhân lực dồi dào, điều phối linh hoạt, quản lý chuyên nghiệp."
    },
    "giup-viec": {
        "hero_heading": "Dịch vụ giúp việc theo giờ & định kỳ tận tâm, an tâm.",
        "content": (
            "Dịch vụ giúp việc theo giờ và định kỳ của Oshin Thời Đại giúp ngôi nhà của bạn luôn gọn gàng, sạch sẽ "
            "mà không làm xáo trộn không gian sinh hoạt riêng tư. Nhân viên giúp việc được tuyển chọn kỹ lưỡng, trung thực, "
            "thạo việc và phục vụ theo khung giờ linh hoạt của gia đình."
        ),
        "scope_of_work": json.dumps([
            "Dọn dẹp phòng khách, phòng ngủ, sắp xếp nhà cửa ngăn nắp",
            "Lau chùi khu vực bếp, bồn rửa chén, khử mùi dầu mỡ",
            "Cọ rửa, tẩy ố và khử trùng nhà tắm, bồn cầu sạch sẽ",
            "Giặt giũ quần áo, phơi đồ, gấp đồ gọn gàng vào tủ",
            "Hỗ trợ sơ chế nguyên liệu nấu ăn, nấu cơm gia đình theo khẩu vị",
            "Làm việc linh hoạt: 2-4 tiếng/buổi, theo ca sáng/chiều hoặc cố định các ngày trong tuần"
        ], ensure_ascii=False),
        "process": json.dumps([
            {"step": "01", "title": "Đăng ký nhu cầu", "desc": "Ghi nhận diện tích nhà, các công việc cần hỗ trợ và khung giờ mong muốn."},
            {"step": "02", "title": "Sắp xếp nhân sự", "desc": "Lựa chọn nhân viên giúp việc phù hợp với yêu cầu và địa bàn gần nhà quý khách."},
            {"step": "03", "title": "Đến làm việc đúng giờ", "desc": "Nhân viên mang trang phục chỉnh tề, đến đúng giờ hẹn và bắt tay vào việc."},
            {"step": "04", "title": "Làm theo checklist", "desc": "Thực hiện đầy đủ các hạng mục theo quy chuẩn vệ sinh gia đình."},
            {"step": "05", "title": "Gia chủ nghiệm thu", "desc": "Chủ nhà kiểm tra sự sạch sẽ, hài lòng trước khi nhân viên ra về."}
        ], ensure_ascii=False),
        "benefits": json.dumps([
            {"title": "Lý lịch minh bạch", "desc": "100% nhân viên có căn cước công dân xác thực, lý lịch rõ ràng và kiểm tra tư cách kỹ càng."},
            {"title": "Kỹ năng thành thạo", "desc": "Được đào tạo kỹ năng dọn dẹp khoa học, bảo quản đồ dùng gia đình và thái độ nhã nhặn."},
            {"title": "Linh hoạt thời gian", "desc": "Chỉ thuê theo số giờ thực tế phát sinh, giúp tiết kiệm chi phí so với người giúp việc ở lại nhà."},
            {"title": "Đổi người nếu không hợp", "desc": "Sẵn sàng hỗ trợ điều chỉnh hoặc đổi nhân viên khác nếu quý khách chưa hoàn toàn ưng ý."}
        ], ensure_ascii=False),
        "faq": json.dumps([
            {"q": "Nhân viên giúp việc có tự mang theo đồ dùng lau dọn không?", "a": "Dạ thông thường quý khách chuẩn bị dụng cụ gia đình (chổi, cây lau nhà, xà phòng). Nếu cần bên em mang theo dụng cụ, vui lòng báo trước khi đặt lịch ạ."},
            {"q": "Tôi có thể yêu cầu cố định 1 người làm quen việc được không?", "a": "Dạ được ạ. Với các gói giúp việc định kỳ, bên em ưu tiên bố trí cố định một nhân viên để gia đình luôn an tâm."},
            {"q": "Nếu có việc bận đột xuất muốn đổi lịch có được không?", "a": "Dạ quý khách chỉ cần báo trước với bên em tối thiểu 2-3 tiếng để hỗ trợ dời lịch linh hoạt ạ."}
        ], ensure_ascii=False),
        "seo_title": "Dịch Vụ Giúp Việc Theo Giờ, Định Kỳ - Oshin Thời Đại",
        "seo_description": "Dịch vụ giúp việc nhà theo giờ, định kỳ chuyên nghiệp, tận tâm. Nhân viên trung thực, thạo việc, lý lịch rõ ràng, thời gian linh hoạt."
    },
    "cham-soc-cay-canh": {
        "hero_heading": "Dịch vụ chăm sóc mảng xanh & cây cảnh chuyên nghiệp.",
        "content": (
            "Dịch vụ chăm sóc cây cảnh của Oshin Thời Đại mang lại không gian sống xanh mát, trong lành và tràn đầy sức sống. "
            "Chúng tôi nhận chăm sóc, cắt tỉa, bón phân, phòng trừ sâu bệnh và bảo dưỡng cây xanh cho nhà phố, biệt thự, "
            "quán cà phê, văn phòng và khuôn viên doanh nghiệp."
        ),
        "scope_of_work": json.dumps([
            "Cắt tỉa cành nhánh khô, tạo dáng thẩm mỹ cho cây cảnh và cây bóng mát",
            "Tưới nước, nhổ cỏ dại, xới đất làm tơi xốp gốc cây",
            "Bón phân hữu cơ và vi lượng phù hợp với từng giai đoạn phát triển của cây",
            "Phun thuốc sinh học phòng trừ rệp sáp, bọ trĩ, sâu ăn lá và nấm bệnh",
            "Thay đất dinh dưỡng, thay chậu và phục hồi cây cảnh nội thất bị suy yếu",
            "Bảo dưỡng cảnh quan sân vườn biệt thự, tiểu cảnh ban công định kỳ"
        ], ensure_ascii=False),
        "process": json.dumps([
            {"step": "01", "title": "Khảo sát mảng xanh", "desc": "Đánh giá tình trạng sinh trưởng của cây, độ ẩm đất, ánh sáng và sâu bệnh hại."},
            {"step": "02", "title": "Lập phác đồ chăm sóc", "desc": "Đề xuất chế độ dinh dưỡng, cắt tỉa và tần suất chăm sóc phù hợp."},
            {"step": "03", "title": "Vệ sinh & Cắt tỉa", "desc": "Cắt bỏ cành sâu bệnh, lá vàng úa và tỉa tán cây gọn gàng, đẹp mắt."},
            {"step": "04", "title": "Bón phân & Trừ sâu", "desc": "Bổ sung đất hữu cơ, bón phân gốc và phun xịt thuốc sinh học an toàn."},
            {"step": "05", "title": "Dọn dẹp & Hướng dẫn", "desc": "Dọn sạch lá rụng, tưới nước hoàn thiện và hướng dẫn gia chủ cách tưới giữ ẩm."}
        ], ensure_ascii=False),
        "benefits": json.dumps([
            {"title": "Hiểu biết sinh lý cây", "desc": "Kỹ thuật viên am hiểu đặc tính từng loại cây cảnh, giúp cây luôn xanh tốt, bền đẹp."},
            {"title": "Thuốc sinh học an toàn", "desc": "Ưu tiên chế phẩm hữu cơ, sinh học an toàn cho trẻ nhỏ và vật nuôi trong gia đình."},
            {"title": "Phục hồi cây yếu", "desc": "Cứu chữa và phục hồi hiệu quả các chậu cây nội thất bị vàng lá, thiếu chất, úng rễ."},
            {"title": "Tiết kiệm thời gian", "desc": "Giúp bạn sở hữu khu vườn xanh mát mà không cần tốn nhiều công sức tự chăm bón."}
        ], ensure_ascii=False),
        "faq": json.dumps([
            {"q": "Công ty có nhận chăm sóc cây định kỳ theo tháng không?", "a": "Dạ có ạ. Bên em có gói bảo dưỡng định kỳ 1-2 lần/tuần hoặc 2-4 lần/tháng tùy theo quy mô sân vườn của quý khách."},
            {"q": "Cây trong văn phòng bị vàng lá rụng nhiều thì có phục hồi được không?", "a": "Dạ bên em sẽ kiểm tra độ ẩm đất và ánh sáng, bổ sung vi lượng hoặc đưa ra vị trí phù hợp để cây hồi phục lại ạ."},
            {"q": "Bên em có cung cấp chậu và đất dinh dưỡng mới không?", "a": "Dạ có sẵn đầy đủ đất sạch hữu cơ, phân trùn quế và chậu các kích thước theo yêu cầu ạ."}
        ], ensure_ascii=False),
        "seo_title": "Dịch Vụ Chăm Sóc Cây Cảnh & Mảng Xanh - Oshin Thời Đại",
        "seo_description": "Dịch vụ chăm sóc cây cảnh, bảo dưỡng sân vườn biệt thự, cắt tỉa cây xanh chuyên nghiệp. Đảm bảo mảng xanh luôn tươi tốt, tràn đầy sức sống."
    },
    "diet-con-trung": {
        "hero_heading": "Dịch vụ diệt côn trùng & kiểm soát dịch hại an toàn.",
        "content": (
            "Dịch vụ diệt côn trùng của Oshin Thời Đại bảo vệ gia đình và cơ sở kinh doanh của bạn khỏi muỗi, gián, kiến, "
            "chuột và mối mọt gây hại. Chúng tôi sử dụng hóa chất sinh học được Bộ Y Tế cấp phép, quy trình phun xịt khoa học "
            "và thiết bị chuyên dụng, bảo đảm hiệu quả diệt trừ cao và tuyệt đối an toàn cho sức khỏe."
        ),
        "scope_of_work": json.dumps([
            "Phun sương ULV diệt muỗi, ruồi phòng ngừa sốt xuất huyết và dịch bệnh",
            "Xử lý và phòng chống mối mọt cho nền móng công trình và đồ nội thất gỗ",
            "Đặt gel diệt gián Đức, gián Mỹ và diệt tận gốc tổ kiến sinh học",
            "Đặt bẫy, kiểm soát chuột cho nhà hàng, kho thực phẩm, siêu thị, nhà xưởng",
            "Khử trùng, diệt khuẩn không gian sống, phòng ốc và nhà kho",
            "Tư vấn giải pháp bịt kín đường xâm nhập của côn trùng từ bên ngoài"
        ], ensure_ascii=False),
        "process": json.dumps([
            {"step": "01", "title": "Khảo sát thực địa", "desc": "Xác định loại côn trùng gây hại, mật độ phân bố và nguồn gốc ổ phát sinh."},
            {"step": "02", "title": "Lựa chọn phương pháp", "desc": "Đề xuất loại thuốc phù hợp, nồng độ an toàn và kỹ thuật phun xịt/đặt bả."},
            {"step": "03", "title": "Hướng dẫn che chắn", "desc": "Hỗ trợ khách hàng che phủ đồ ăn, nước uống, hồ cá trước khi thi công."},
            {"step": "04", "title": "Triển khai xử lý", "desc": "Phun tồn lưu ngóc ngách, phun không gian ULV và đặt bả sinh học chuyên dụng."},
            {"step": "05", "title": "Nghiệm thu & Bảo hành", "desc": "Kiểm tra hiệu quả sau xử lý, hướng dẫn cách phòng ngừa và cam kết bảo hành."}
        ], ensure_ascii=False),
        "benefits": json.dumps([
            {"title": "Hóa chất chuẩn Bộ Y Tế", "desc": "Chỉ sử dụng thuốc nằm trong danh mục lưu hành của Bộ Y Tế, thân thiện với môi trường."},
            {"title": "Hiệu quả triệt để", "desc": "Tiêu diệt tận gốc các ổ côn trùng cứng đầu và tạo lớp màng tồn lưu ngăn tái phát lâu dài."},
            {"title": "Không độc hại, không ố sàn", "desc": "Mùi hương nhẹ hoặc không mùi, không để lại vết ố trên tường, sàn nhà hay đồ đạc."},
            {"title": "Chính sách bảo hành rõ ràng", "desc": "Có phiếu bảo hành và sẵn sàng phun xịt lại miễn phí nếu côn trùng xuất hiện trở lại trong thời hạn bảo hành."}
        ], ensure_ascii=False),
        "faq": json.dumps([
            {"q": "Thuốc diệt muỗi có gây độc hại cho trẻ nhỏ và thú cưng không?", "a": "Dạ thuốc bên em dùng là chế phẩm sinh học được Bộ Y Tế cấp phép. Gia đình chỉ cần ra ngoài khoảng 1-2 tiếng sau khi phun để thuốc khô là sinh hoạt bình thường ạ."},
            {"q": "Sau khi phun thuốc bao lâu thì có hiệu quả?", "a": "Dạ côn trùng bay như muỗi, ruồi sẽ hạ gục ngay trong lúc phun. Các loại côn trùng ẩn nấp như gián, kiến sẽ ăn bả và chết sạch trong 24-48 giờ."},
            {"q": "Dịch vụ có bảo hành không?", "a": "Dạ bên em có chính sách bảo hành rõ ràng tùy theo gói dịch vụ, hỗ trợ xử lý lại hoàn toàn miễn phí nếu có phát sinh trong thời gian bảo hành."}
        ], ensure_ascii=False),
        "seo_title": "Dịch Vụ Diệt Côn Trùng An Toàn, Tận Gốc - Oshin Thời Đại",
        "seo_description": "Dịch vụ diệt muỗi, diệt mối, diệt gián, chuột cho nhà ở, văn phòng, nhà xưởng uy tín. Hóa chất Bộ Y Tế an toàn, hiệu quả dài lâu, có bảo hành."
    }
}
