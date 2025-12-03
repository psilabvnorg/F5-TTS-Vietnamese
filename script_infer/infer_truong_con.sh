# Add to your infer.sh or set in environment
export HF_HOME="/home/psilab/.cache/huggingface"
export HF_HUB_CACHE="/home/psilab/.cache/huggingface/hub"

f5-tts_infer-cli \
--model "F5TTS_Base" \
--ref_audio "original_voice_ref/truong_con/truong_con_trimmed.wav" \
--ref_text "có một người em nó ở hòa bình, vào làm phụ hồ, ở trong sài gòn ở quận một, mà em nó không có tiền" \
--gen_text "trong một thị trường chịu tác động mạnh của dòng tiền ngắn hạn, như việt nam khi quan sát thị trường, theo từng phiên, hoặc từng tuần, nhà đầu tư dễ cảm thấy vi en in đếch biến động thất thường, và thiếu một cấu trúc rõ ràng, nhưng khi đặt dữ liệu trong khung thời gian đủ dài, cụ thể là thống kê lợi nhuận theo tháng, của vi en in đếch từ đến hai không hai lăm, hành vi thị trường lại trở nên rất nhất quán, không phải ngẫu nhiên mà, những nhà đầu tư có tầm nhìn dài hạn luôn có kết quả tốt hơn, bản chất của thị trường là sideway, nhưng cấu trúc của thị trường lại là tăng trưởng" \
--speed 1.69 \
--vocoder_name vocos \
--vocab_file model/vocab.txt \
--ckpt_file model/model_last.pt \
--output_dir "output" \
--output_file "truong_con_trimmed_output.wav"