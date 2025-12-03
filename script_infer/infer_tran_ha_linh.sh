# Add to your infer.sh or set in environment
export HF_HOME="/home/psilab/.cache/huggingface"
export HF_HUB_CACHE="/home/psilab/.cache/huggingface/hub"

f5-tts_infer-cli \
--model "F5TTS_Base" \
--ref_audio "original_voice_ref/tran_ha_linh/tran_ha_linh_trimmed.wav" \
--ref_text "công khai điểm luôn, hồi đó là toán tám phẩy năm, văn sau phẩy năm, tiếng anh chín phẩy bao nhiêu ấy, còn lịch sử cũng chín phẩy bao nhiêu luôn, được chưa, vô đê lên coi, có bảng điểm trên thớt đó" \
--gen_text "đường phía trước đông đúc, dường như để không phải chờ đợi, chiếc xe tải đột ngột chuyển làn sang phải, đầu xe húc vào đuôi xe con ở làn này, khiến xe con xoay ngang, chiếc sedan bị ủi một đoạn, hất sang làn ngược chiều, đúng lúc này, một xe khách đi tới nên tiếp tục húc trúng xe con, chưa rõ thương vong và thiệt hại về tài sản" \
--speed 1.0 \
--vocoder_name vocos \
--vocab_file model/vocab.txt \
--ckpt_file model/model_last.pt \
--output_dir "output" \
--output_file "tran_ha_linh_trimmed_output.wav"