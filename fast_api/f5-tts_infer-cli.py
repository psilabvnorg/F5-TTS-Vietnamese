# Simplified version of what f5-tts_infer-cli does internally

import torch
import torchaudio
from f5_tts.model import DiT
from f5_tts.infer.utils_infer import (
    load_vocoder,
    load_model,
    preprocess_ref_audio_text,
    infer_process,
    remove_silence_edges
)

# 1. Load the model
model = load_model(
    model_cls=DiT,  # Diffusion Transformer
    model_cfg=model_config,
    ckpt_path=args.ckpt_file,
    vocab_file=args.vocab_file,
    device="cuda" if torch.cuda.is_available() else "cpu"
)

# 2. Load vocoder (converts mel-spectrogram to audio)
vocoder = load_vocoder(
    vocoder_name=args.vocoder_name,  # "vocos" or "bigvgan"
    is_local=False
)

# 3. Process reference audio
ref_audio, ref_text = preprocess_ref_audio_text(
    ref_audio_path=args.ref_audio,
    ref_text=args.ref_text,
    device=model.device
)

# 4. Run inference (text → mel-spectrogram)
generated_mel = infer_process(
    ref_audio=ref_audio,
    ref_text=ref_text,
    gen_text=args.gen_text,
    model=model,
    vocoder=vocoder,
    speed=args.speed,
    cross_fade_duration=0.15
)

# 5. Vocoder converts mel → waveform
with torch.no_grad():
    generated_wave = vocoder.decode(generated_mel)

# 6. Post-process and save
if remove_silence:
    generated_wave = remove_silence_edges(generated_wave)

torchaudio.save(
    output_path,
    generated_wave,
    sample_rate=vocoder.sample_rate
)