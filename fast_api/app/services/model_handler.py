"""
Model Handler for F5-TTS API
Preloads models at startup and provides inference interface
"""

import os
import re
from importlib.resources import files
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import numpy as np
import soundfile as sf
from cached_path import cached_path
from omegaconf import OmegaConf

from f5_tts.infer.utils_infer import (
    mel_spec_type as default_mel_spec_type,
    target_rms as default_target_rms,
    cross_fade_duration as default_cross_fade_duration,
    nfe_step as default_nfe_step,
    cfg_strength as default_cfg_strength,
    sway_sampling_coef as default_sway_sampling_coef,
    speed as default_speed,
    fix_duration as default_fix_duration,
    infer_process,
    load_model,
    load_vocoder,
    preprocess_ref_audio_text,
    remove_silence_for_generated_wav,
)
from f5_tts.model import DiT, UNetT  # noqa: F401. used for config


class F5TTSModelHandler:
    """
    Handler class for F5-TTS model that preloads models at startup
    and provides inference methods for API calls.
    """

    def __init__(
        self,
        model_name: str = "F5TTS_v1_Base",
        ckpt_file: str = "",
        vocab_file: str = "",
        model_cfg_path: str = "",
        vocoder_name: str = "vocos",
        load_vocoder_from_local: bool = False,
        vocoder_local_path: str = "",
    ):
        """
        Initialize and preload models.

        Args:
            model_name: Model name (F5TTS_v1_Base, F5TTS_Base, E2TTS_Base, etc.)
            ckpt_file: Path to model checkpoint file
            vocab_file: Path to vocabulary file
            model_cfg_path: Path to model config YAML file
            vocoder_name: Vocoder type (vocos or bigvgan)
            load_vocoder_from_local: Whether to load vocoder from local directory
            vocoder_local_path: Local path to vocoder if loading locally
        """
        print("Initializing F5-TTS Model Handler...")
        
        self.model_name = model_name
        self.vocoder_name = vocoder_name
        self.vocab_file = vocab_file
        
        # Default inference parameters (can be overridden per request)
        self.default_params = {
            "target_rms": default_target_rms,
            "cross_fade_duration": default_cross_fade_duration,
            "nfe_step": default_nfe_step,
            "cfg_strength": default_cfg_strength,
            "sway_sampling_coef": default_sway_sampling_coef,
            "speed": default_speed,
            "fix_duration": default_fix_duration,
        }
        
        # Load vocoder
        print(f"Loading vocoder: {vocoder_name}...")
        self.vocoder = self._load_vocoder(
            vocoder_name, load_vocoder_from_local, vocoder_local_path
        )
        print("Vocoder loaded successfully!")
        
        # Load TTS model
        print(f"Loading TTS model: {model_name}...")
        self.ema_model, self.model_cfg = self._load_tts_model(
            model_name, ckpt_file, model_cfg_path, vocoder_name, vocab_file
        )
        print("TTS model loaded successfully!")
        
        print("F5-TTS Model Handler initialized and ready!")

    def _load_vocoder(
        self,
        vocoder_name: str,
        load_from_local: bool,
        local_path: str = "",
    ):
        """Load vocoder model."""
        if not local_path:
            if vocoder_name == "vocos":
                local_path = "../checkpoints/vocos-mel-24khz"
            elif vocoder_name == "bigvgan":
                local_path = "../checkpoints/bigvgan_v2_24khz_100band_256x"
        
        return load_vocoder(
            vocoder_name=vocoder_name,
            is_local=load_from_local,
            local_path=local_path
        )

    def _load_tts_model(
        self,
        model_name: str,
        ckpt_file: str,
        model_cfg_path: str,
        vocoder_name: str,
        vocab_file: str,
    ):
        """Load TTS model and configuration."""
        # Load model config
        if not model_cfg_path:
            model_cfg_path = str(files("f5_tts").joinpath(f"configs/{model_name}.yaml"))
        
        model_cfg = OmegaConf.load(model_cfg_path).model
        model_cls = globals()[model_cfg.backbone]
        
        # Determine checkpoint details
        repo_name, ckpt_step, ckpt_type = "F5-TTS", 1250000, "safetensors"
        model_for_checkpoint = model_name  # Separate variable for checkpoint resolution
        
        if model_name != "F5TTS_Base":
            assert vocoder_name == model_cfg.mel_spec.mel_spec_type
        
        # Override for previous models
        if model_name == "F5TTS_Base":
            if vocoder_name == "vocos":
                ckpt_step = 1200000
            elif vocoder_name == "bigvgan":
                model_for_checkpoint = "F5TTS_Base_bigvgan"
                ckpt_type = "pt"
        elif model_name == "E2TTS_Base":
            repo_name = "E2-TTS"
            ckpt_step = 1200000
        
        # Get checkpoint file
        if not ckpt_file:
            ckpt_file = str(cached_path(
                f"hf://SWivid/{repo_name}/{model_for_checkpoint}/model_{ckpt_step}.{ckpt_type}"
            ))
        
        # Load model
        ema_model = load_model(
            model_cls,
            model_cfg.arch,
            ckpt_file,
            mel_spec_type=vocoder_name,
            vocab_file=vocab_file
        )
        
        return ema_model, model_cfg

    def infer(
        self,
        ref_audio: str,
        ref_text: str,
        gen_text: str,
        output_path: str,
        voices: Optional[Dict[str, Dict[str, str]]] = None,
        save_chunks: bool = False,
        remove_silence: bool = False,
        # Inference parameters (optional overrides)
        target_rms: Optional[float] = None,
        cross_fade_duration: Optional[float] = None,
        nfe_step: Optional[int] = None,
        cfg_strength: Optional[float] = None,
        sway_sampling_coef: Optional[float] = None,
        speed: Optional[float] = None,
        fix_duration: Optional[float] = None,
    ) -> Tuple[str, int]:
        """
        Run inference with preloaded models.

        Args:
            ref_audio: Path to reference audio file
            ref_text: Transcript of reference audio
            gen_text: Text to generate speech for
            output_path: Path to save output audio file
            voices: Dictionary of voice configurations (optional)
            save_chunks: Whether to save individual chunks
            remove_silence: Whether to remove silence from output
            target_rms: Target RMS value (uses default if None)
            cross_fade_duration: Cross-fade duration (uses default if None)
            nfe_step: Number of function evaluations (uses default if None)
            cfg_strength: CFG strength (uses default if None)
            sway_sampling_coef: Sway sampling coefficient (uses default if None)
            speed: Speech speed (uses default if None)
            fix_duration: Fixed duration (uses default if None)

        Returns:
            Tuple of (output_file_path, sample_rate)
        """
        # Use default parameters if not provided
        params = {
            "target_rms": target_rms or self.default_params["target_rms"],
            "cross_fade_duration": cross_fade_duration or self.default_params["cross_fade_duration"],
            "nfe_step": nfe_step or self.default_params["nfe_step"],
            "cfg_strength": cfg_strength or self.default_params["cfg_strength"],
            "sway_sampling_coef": sway_sampling_coef or self.default_params["sway_sampling_coef"],
            "speed": speed or self.default_params["speed"],
            "fix_duration": fix_duration or self.default_params["fix_duration"],
        }
        
        # Setup voices
        main_voice = {"ref_audio": ref_audio, "ref_text": ref_text}
        if voices is None:
            voices = {"main": main_voice}
        else:
            voices["main"] = main_voice
        
        # Preprocess reference audios
        for voice_name in voices:
            voices[voice_name]["ref_audio"], voices[voice_name]["ref_text"] = preprocess_ref_audio_text(
                voices[voice_name]["ref_audio"], voices[voice_name]["ref_text"]
            )
        
        # Generate audio segments
        generated_audio_segments = []
        final_sample_rate = None
        
        # Split text by voice tags
        reg1 = r"(?=\[\w+\])"
        chunks = re.split(reg1, gen_text)
        reg2 = r"\[(\w+)\]"
        
        # Setup chunk directory if needed
        output_chunk_dir = None
        if save_chunks:
            output_chunk_dir = os.path.join(
                os.path.dirname(output_path),
                f"{Path(output_path).stem}_chunks"
            )
            os.makedirs(output_chunk_dir, exist_ok=True)
        
        for text in chunks:
            if not text.strip():
                continue
            
            # Determine voice
            match = re.match(reg2, text)
            if match:
                voice = match[1]
            else:
                voice = "main"
            
            if voice not in voices:
                voice = "main"
            
            # Remove voice tag from text
            text = re.sub(reg2, "", text)
            gen_text_chunk = text.strip()
            
            if not gen_text_chunk:
                continue
            
            # Get voice references
            ref_audio_chunk = voices[voice]["ref_audio"]
            ref_text_chunk = voices[voice]["ref_text"]
            
            # Run inference
            audio_segment, final_sample_rate, spectrogram = infer_process(
                ref_audio_chunk,
                ref_text_chunk,
                gen_text_chunk,
                self.ema_model,
                self.vocoder,
                mel_spec_type=self.vocoder_name,
                **params
            )
            
            generated_audio_segments.append(audio_segment)
            
            # Save chunk if requested
            if save_chunks and output_chunk_dir:
                chunk_text = gen_text_chunk[:200] + "..." if len(gen_text_chunk) > 200 else gen_text_chunk
                chunk_path = os.path.join(
                    output_chunk_dir,
                    f"{len(generated_audio_segments)-1}_{chunk_text}.wav"
                )
                sf.write(chunk_path, audio_segment, final_sample_rate)
        
        # Concatenate and save final audio
        if generated_audio_segments:
            final_wave = np.concatenate(generated_audio_segments)
            
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save audio file
            sf.write(output_path, final_wave, final_sample_rate)
            
            # Remove silence if requested
            if remove_silence:
                remove_silence_for_generated_wav(output_path)
            
            return output_path, final_sample_rate
        else:
            raise ValueError("No audio generated. Check input text.")

    def update_default_params(self, **kwargs):
        """Update default inference parameters."""
        for key, value in kwargs.items():
            if key in self.default_params and value is not None:
                self.default_params[key] = value

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            "model_name": self.model_name,
            "vocoder_name": self.vocoder_name,
            "vocab_file": self.vocab_file,
            "default_params": self.default_params,
        }
