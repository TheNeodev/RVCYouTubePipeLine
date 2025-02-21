from lib.infer import infer_audio
from audio_separator.separator import Separator
from yt_dlp import YoutubeDL
from pydub import AudioSegment, effects
from pedalboard import Compressor, Gain, Pedalboard, Reverb
from pedalboard.io import AudioFile


class AudioProcessor:
    def __init__(self, model_name: str):
        """
        Initialize audio processing pipeline with specified RVC model.
        Loads separation and dereverberation models.
        """
        self.model_name = model_name
        self._load_models()

    def _load_models(self):
        """Initialize and load audio separation models"""
        self.separator = Separator()
        self.separator.load_model("model_bs_roformer_ep_368_sdr_12.9628.ckpt")
        
        self.dereverb = Separator()
        self.dereverb.load_model("dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt")

    def _download_audio(self, url: str):
        """
        Download audio from YouTube URL and convert to WAV format.
        Uses yt-dlp with FFmpeg extraction for audio conversion.
        """
        ydl_opts = {
            "source_address": "0.0.0.0",
            "outtmpl": "song.%(ext)s",
            "format": "140",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }],
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def _apply_effects(self, input_path: str, output_path: str):
        """
        Apply audio effects chain to enhance vocal clarity.
        Includes compression, reverb, and gain staging.
        """
        processing_chain = Pedalboard([
            Compressor(ratio=4, threshold_db=-10),
            Reverb(room_size=0.2, damping=0.7, dry_level=0.6, wet_level=0.15),
            Gain(gain_db=1),
        ])

        with AudioFile(input_path) as input_file:
            with AudioFile(output_path, 'w', input_file.samplerate, input_file.num_channels) as output_file:
                while input_file.tell() < input_file.frames:
                    chunk = input_file.read(input_file.samplerate)
                    processed = processing_chain(chunk, input_file.samplerate)
                    output_file.write(processed)

    def process_track(self, youtube_url: str, output_path: str = "output.wav", 
                     pitch_shift: int = 0, f0_method: str = "hybrid[rmvpe+fcpe]") -> tuple:
        """
        Full processing pipeline for YouTube audio:
        1. Download audio
        2. Separate vocal/instrumental
        3. Apply dereverberation
        4. Process through RVC model
        5. Post-process and normalize
        
        Returns tuple of (processed_path, instrumental_path)
        """
        # Download and separate tracks
        self._download_audio(youtube_url)
        separated_tracks = self.separator.separate('song.wav')
        
        # Dereverb vocals
        dereverb_tracks = self.dereverb.separate(separated_tracks[1])
        
        # Process through RVC model
        rvc_processed = infer_audio(
            MODEL_NAME=self.model_name,
            SOUND_PATH=dereverb_tracks[1],
            F0_CHANGE=pitch_shift,
            F0_METHOD=f0_method,
        )

        # Final normalization and export
        audio = AudioSegment.from_wav(rvc_processed)
        audio = effects.normalize(audio)
        audio.export(output_path, format="wav")
        
        return (output_path, separated_tracks[0])


