"""
Voice configurations for F5-TTS Vietnamese
"""

# Available voices with metadata
VOICES = {
    "tran_ha_linh": {
        "name": "Trần Hà Linh",
        "description": "Female voice, clear pronunciation, suitable for narration",
        "language": "vi",
        "gender": "female",
        "audio": "tran_ha_linh/tran_ha_linh_trimmed.wav",
        "ref_text": "công khai điểm luôn, hồi đó là toán tám phẩy năm, văn sau phẩy năm, tiếng anh chín phẩy bao nhiêu ấy, còn lịch sử cũng chín phẩy bao nhiêu luôn, được chưa, vô đê lên coi, có bảng điểm trên thớt đó",
        "thumbnail": "/static/thumbnails/tran_ha_linh.jpg",
        "sample_audio": "/static/samples/tran_ha_linh_sample.wav"
    },
    "kha_banh": {
        "name": "Khá Bảnh",
        "description": "Male voice, energetic tone, conversational style",
        "language": "vi",
        "gender": "male",
        "audio": "kha_banh/kha_banh.wav",
        "ref_text": "đang khai trương ở quế võ thì à hôm đấy đi ăn, đi ăn thì uống rượu say ở quế võ rồi, thế xong là anh em ở quế võ lại rủ lên ba quê võ, thì là đến lúc nó đi lên ba",
        "thumbnail": "/static/thumbnails/kha_banh.jpg",
        "sample_audio": "/static/samples/kha_banh_sample.wav"
    },
    "chi_hang": {
        "name": "Chi Hang",
        "description": "Female voice, warm tone, friendly style",
        "language": "vi",
        "gender": "female",
        "audio": "chi_hang/chi_hang_trimmed.wav",
        "ref_text": "mày kể cho tao nghe trời ơi này ông cưng mày lắm nha, ông cưng lắm mà biết sao cuối cùng cũng chính mày kể cho tao nghe là ông bỏ mày ông đi theo coi như con hương tràm",
        "thumbnail": "/static/thumbnails/chi_hang.jpg",
        "sample_audio": "/static/samples/chi_hang_sample.wav"
    },
    "quang_linh_vlog": {
        "name": "Quang Linh Vlog",
        "description": "Male voice, enthusiastic tone, vlog style",
        "language": "vi",
        "gender": "male",
        "audio": "quang_linh_vlog/quang_linh_trimmed.wav",
        "ref_text": "ối dồi ôi, sao lại như thế này, sao lại lên được một nghìn, nghìn, ối dồi ôi, không biết là các bạn có, có bấm bấm vui, hay là theo cái nhịp điệu của mình mà mọi người cứ",
        "thumbnail": "/static/thumbnails/quang_linh.jpg",
        "sample_audio": "/static/samples/quang_linh_sample.wav"
    },
    "son_tung_mtp": {
        "name": "Sơn Tùng M-TP",
        "description": "Male voice, smooth tone, music style",
        "language": "vi",
        "gender": "male",
        "audio": "son_tung_mtp/mtp_trimmed.wav",
        "ref_text": "và nếu như mọi người để ý rằng từ trước đến nay thì cách dùng mạng xã hội của em ý, thì, nó không có gì thay đổi cả, nhiều khi gọi điện cho bố mẹ em",
        "thumbnail": "/static/thumbnails/son_tung.jpg",
        "sample_audio": "/static/samples/son_tung_sample.wav"
    }
    ,
    "chi_phien": {
        "name": "Chi Phiến",
        "description": "Female voice, expressive speech",
        "language": "vi",
        "gender": "female",
        "audio": "chi_phien/chi_phien_trimmed.wav",
        "ref_text": "cả năm nay chị đã rất điêu đứng rồi, cho nên hãy yêu thương chị đi, để kết thúc mọi chuyện, chị sẽ tặng em một câu nói, bằng bốn thứ tiếng",
        "thumbnail": "/static/thumbnails/chi_phien.jpg",
        "sample_audio": "/static/samples/chi_phien_chi_phien_trimmed.wav"
    },
    "huan_hoa_hong": {
        "name": "Huấn Hoa Hồng",
        "description": "Male voice, motivational street style",
        "language": "vi",
        "gender": "male",
        "audio": "huan_hoa_hong/huan_rose_trimmed.wav",
        "ref_text": "em có làm cái gì đi nữa, nếu có phải trả giá em cũng xin chấp nhận, bởi vì anh, anh biết đấy. ra xã hội làm ăn buơn trải, liều thì ăn nhiều",
        "thumbnail": "/static/thumbnails/huan_hoa_hong.jpg",
        "sample_audio": "/static/samples/huan_hoa_hong_huan_rose_trimmed.wav"
    },
    "phim_tai_lieu": {
        "name": "Phim Tài Liệu",
        "description": "Male narration, formal documentary tone",
        "language": "vi",
        "gender": "male",
        "audio": "phim_tai_lieu/le_chuc_trimmed.wav",
        "ref_text": "huống chi thành đại la, kinh đô cũ của cao vương ở và nơi trung tâm trời đất, được thế rồng cuộn hổ ngồi, chính giữa nam bắc đông tây",
        "thumbnail": "/static/thumbnails/phim_tai_lieu.jpg",
        "sample_audio": "/static/samples/phim_tai_lieu_le_chuc_trimmed.wav"
    },
    "thoi_su_nam_ha_noi": {
        "name": "Thời Sự Nam Hà Nội",
        "description": "Male news anchor, northern accent",
        "language": "vi",
        "gender": "male",
        "audio": "thoi_su_nam_ha_noi/thoi_su_nam1_trimmed.wav",
        "ref_text": "kính chào quý vị mời quý vị cùng theo dõi bản tin, bão ca mơ ghi khoảng đêm nay rạng sáng mai sẽ đi vào biển đông, trở thành cơn bão số mười ba trong năm nay, dự báo bão rất mạnh ở",
        "thumbnail": "/static/thumbnails/thoi_su_nam_ha_noi.jpg",
        "sample_audio": "/static/samples/thoi_su_nam_ha_noi_thoi_su_nam1_trimmed.wav"
    },
    "thoi_su_nam_sai_gon": {
        "name": "Thời Sự Nam Sài Gòn",
        "description": "Male news anchor, southern accent",
        "language": "vi",
        "gender": "male",
        "audio": "thoi_su_nam_sai_gon/thoi_su_nam_sg_trimmed.wav",
        "ref_text": "thương hiệu phụ kiện ô tô hàng đầu việt nam với gần năm trăm đại lý trên toàn quốc, đã cho ra mắt sản phẩm bóng đèn pha ô tô, mang đến giải pháp chiếu sáng cho hàng triệu xe hơi phổ thông, tại việt nam",
        "thumbnail": "/static/thumbnails/thoi_su_nam_sai_gon.jpg",
        "sample_audio": "/static/samples/thoi_su_nam_sai_gon_thoi_su_nam_sg_trimmed.wav"
    },
    "thoi_su_nu_ha_noi": {
        "name": "Thời Sự Nữ Hà Nội",
        "description": "Female news anchor, northern accent",
        "language": "vi",
        "gender": "female",
        "audio": "thoi_su_nu_ha_noi/thoi_su_nu_trimmed.wav",
        "ref_text": "mời quý khán giả theo dõi bản tin của đài truyền hình việt nam, tỉnh khánh hòa và tỉnh đắc lắc hưởng ứng chiến dịch quang trung thần tốc xây dựng, và sửa chữa nhà cho các hộ dân bị thiệt hại sau lũ, khánh hòa khởi công",
        "thumbnail": "/static/thumbnails/thoi_su_nu_ha_noi.jpg",
        "sample_audio": "/static/samples/thoi_su_nu_ha_noi_thoi_su_nu_trimmed.wav"
    },
    "thoi_su_nu_sai_gon": {
        "name": "Thời Sự Nữ Sài Gòn",
        "description": "Female news anchor, southern accent",
        "language": "vi",
        "gender": "female",
        "audio": "thoi_su_nu_sai_gon/thoi_su_nu2_trimmed.wav",
        "ref_text": "để chuẩn bị xây dựng các văn kiện trình đại hội mười ba của đảng, hôm nay đồng chí phạm minh chính, ủy viên bộ chính trị, bí thư trung ương đảng, trưởng ban tổ chức trung ương, đã khảo sát và làm việc",
        "thumbnail": "/static/thumbnails/thoi_su_nu_sai_gon.jpg",
        "sample_audio": "/static/samples/thoi_su_nu_sai_gon_thoi_su_nu2_trimmed.wav"
    },
    "tien_bip": {
        "name": "Tiến Bịp",
        "description": "Male voice, colloquial style",
        "language": "vi",
        "gender": "male",
        "audio": "tien_bip/tien_bip2_trimmed.wav",
        "ref_text": "anh ơi đến giờ phút này ý anh ạ để mà nói rằng ý em là em ô kê hết anh thích thế nào em cũng chiều luôn đấy anh ạ không ngán con vợ nào cả",
        "thumbnail": "/static/thumbnails/tien_bip.jpg",
        "sample_audio": "/static/samples/tien_bip_tien_bip2_trimmed.wav"
    },
    "truong_con": {
        "name": "Trưởng Con",
        "description": "Male voice, emotional storytelling",
        "language": "vi",
        "gender": "male",
        "audio": "truong_con/truong_con_trimmed.wav",
        "ref_text": "có một người em nó ở hòa bình, vào làm phụ hồ, ở trong sài gòn ở quận một, mà em nó không có tiền",
        "thumbnail": "/static/thumbnails/truong_con.jpg",
        "sample_audio": "/static/samples/truong_con_truong_con_trimmed.wav"
    },
    "36": {
        "name": "36",
        "description": "Female conversational tone",
        "language": "vi",
        "gender": "female",
        "audio": "36/36_trimmed.wav",
        "ref_text": "mua năm mươi cái nem chua thanh hóa về, bỏ ra ăn hai ngày mới hết, ô trời anh nói vừa vừa phải phải thôi anh chi mà anh đúng, là phóng đại lên gớm",
        "thumbnail": "/static/thumbnails/36.jpg",
        "sample_audio": "/static/samples/36_36_trimmed.wav"
    },
    "37": {
        "name": "37",
        "description": "Male news-style narration",
        "language": "vi",
        "gender": "male",
        "audio": "37/37_trimmed.wav",
        "ref_text": "trước những ảnh hưởng lạm phát trên thế giới, các doanh nghiệp dệt may da giày việt nam, lâm vào trình trạng vô cùng khó khăn do đơn hàng sụt giảm, nhiều công ty",
        "thumbnail": "/static/thumbnails/37.jpg",
        "sample_audio": "/static/samples/37_37_trimmed.wav"
    }
}
