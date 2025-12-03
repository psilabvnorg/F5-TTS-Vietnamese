# Add to your infer.sh or set in environment
export HF_HOME="/home/psilab/.cache/huggingface"
export HF_HUB_CACHE="/home/psilab/.cache/huggingface/hub"

f5-tts_infer-cli \
--model "F5TTS_Base" \
--ref_audio "original_voice_ref/thoi_su_nam_ha_noi/thoi_su_nam1_trimmed.wav" \
--ref_text "kính chào quý vị mời quý vị cùng theo dõi bản tin, bão ca mơ ghi khoảng đêm nay rạng sáng mai sẽ đi vào biển đông, trở thành cơn bão số mười ba trong năm nay, dự báo bão rất mạnh ở" \
--gen_text "trong một thị trường chịu tác động mạnh của dòng tiền ngắn hạn, như việt nam khi quan sát thị trường, theo từng phiên, hoặc từng tuần, nhà đầu tư dễ cảm thấy vi en in đếch biến động thất thường, và thiếu một cấu trúc rõ ràng, nhưng khi đặt dữ liệu trong khung thời gian đủ dài, cụ thể là thống kê lợi nhuận theo tháng, của vi en in đếch từ đến hai không hai lăm, hành vi thị trường lại trở nên rất nhất quán, không phải ngẫu nhiên mà, những nhà đầu tư có tầm nhìn dài hạn luôn có kết quả tốt hơn, bản chất của thị trường là sai uây, nhưng cấu trúc của thị trường lại là tăng trưởng" \
--speed 1.0 \
--vocoder_name vocos \
--vocab_file model/vocab.txt \
--ckpt_file model/model_last.pt \
--output_dir "output" \
--output_file "thoi_su_nam1_trimmed_output.wav"