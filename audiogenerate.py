from rvc_python.infer import RVCInference
from audio_separator.separator import Separator
from yt_dlp import YoutubeDL
from pydub import AudioSegment, effects
from pedalboard import Compressor, Gain, Pedalboard, Reverb
from pedalboard.io import AudioFile

## todo: make this a class or something -> refactor

def init(rvcmodel, rvcindex):
    global rvc, separator, dereverb
    rvc = RVCInference(device="cuda:0")
    rvc.load_model(rvcmodel, index_path=rvcindex)
    rvc.set_params(f0method="rmvpe")

    separator = Separator()
    separator.load_model("model_bs_roformer_ep_368_sdr_12.9628.ckpt")
    dereverb = Separator()
    dereverb.load_model("dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt")


def ytdownload(link):
    if not link or not isinstance(link, str):
        logging.error("Invalid link provided.")
        return "Error: Invalid link"

    try:
        now_dir = os.getcwd()
    except OSError as e:
        logging.error(f"Error accessing current working directory: {e}")
        return "Error: Unable to access current working directory"

    output_dir = os.path.join(now_dir, "audio_files", "original_files")
    os.makedirs(output_dir, exist_ok=True)

    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    command = [
        "yt-dlp",
        "-x",
        "--audio-format",
        "wav",
        "--output",
        output_template,
        "--cookies",
        "./configs.txt",
        link,
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info(f"Download successful: {result.stdout}")
        return "Music downloaded successfully"
    except FileNotFoundError:
        logging.error("yt-dlp is not installed. Please install it first.")
        return "Error: yt-dlp not found"
    except subprocess.CalledProcessError as e:
        logging.error(f"Download failed: {e.stderr}")
        return f"Error: {e.stderr}"



def addEffects(input, output):
    # Make a Pedalboard object, containing multiple audio plugins:
    board = Pedalboard(
        [
            Compressor(ratio=4, threshold_db=-10),
            Reverb(room_size=0.2, damping=0.7, dry_level=0.6, wet_level=0.15),
            Gain(gain_db=1),
        ]
    )
    # Open an audio file for reading, just like a regular file:
    with AudioFile(input) as f:
    
        # Open an audio file to write to:
        with AudioFile(output, 'w', f.samplerate, f.num_channels) as o:
        
            # Read one second of audio at a time, until the file is empty:
            while f.tell() < f.frames:
                chunk = f.read(f.samplerate)
                
                # Run the audio through our pedalboard:
                effected = board(chunk, f.samplerate, reset=False)
                
                # Write the output to our output file:
                o.write(effected)


# generate
def generateAudioTrack(url, outputfile = "output.wav"):
    ytdownload(url)
    output_files = separator.separate('song.wav')
    dereverb_files = dereverb.separate(output_files[1])

    rvc.infer_file(dereverb_files[1], outputfile)
    song = AudioSegment.from_wav(outputfile)
    song = effects.normalize(song)  
    song.export(outputfile, "wav")
    return (outputfile, output_files[0])

#create("https://www.youtube.com/watch?v=fKyXvNkGQKc", "kingslayer.wav")
#create("https://www.youtube.com/watch?v=kXYiU_JCYtU", "numb.wav")
#https://www.youtube.com/watch?v=fKyXvNkGQKc kingslayer
#https://www.youtube.com/watch?v=I4rtcJnRd6s nightglow
