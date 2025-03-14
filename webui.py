import os
import shutil
import gradio as gr
from pydub import AudioSegment
import audiogenerate
import requests
import zipfile
from io import BytesIO

# Set up fixed folders
RVC_FOLDER = "./rvc"
os.makedirs(RVC_FOLDER, exist_ok=True)

def list_files_with_ext(folder, ext):
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(ext)]

def get_pth_files():
    return list_files_with_ext(RVC_FOLDER, ".pth")

def get_index_files():
    return list_files_with_ext(RVC_FOLDER, ".index")

def download_model(huggingface_url):
    """
    Download a ZIP file from the provided Hugging Face URL and extract its contents
    into the RVC folder.
    """
    try:
        response = requests.get(huggingface_url, stream=True)
        if response.status_code == 200:
            zip_file = zipfile.ZipFile(BytesIO(response.content))
            zip_file.extractall(RVC_FOLDER)
            zip_file.close()
            return f"Download and extraction complete. Files saved in '{RVC_FOLDER}'."
        else:
            return f"Failed to download. Status code: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def mixAudio(wav1, wav2, mixed_path):
    """
    Overlay two WAV files and export the mixed audio.
    """
    sound1 = AudioSegment.from_wav(wav1)
    sound2 = AudioSegment.from_wav(wav2)
    mixed = sound1.overlay(sound2)
    mixed.export(mixed_path, format="wav")

def generate_audio(pth_file, index_file, url):
    """
    Run the audio generation process using the selected model files and input URL.
    This function initializes the audio generation, creates the output audio files,
    mixes them, applies effects, and cleans up extra files.
    """
    try:
        # Initialize the generation process with the selected model files
        audiogenerate.init(pth_file, index_file)
    except Exception as e:
        return f"Error initializing audiogenerate: {str(e)}"
    
    output_folder = "outputs"
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        # Generate the base audio tracks (vocals and instrumental)
        wav1, wav2 = audiogenerate.generateAudioTrack(url, os.path.join(output_folder, "output.wav"))
    except Exception as e:
        return f"Error generating audio track: {str(e)}"
    
    # Create a mixed audio track
    mixed_path = os.path.join(output_folder, "mixed.wav")
    mixAudio(wav1, wav2, mixed_path)
    
    # Apply effects and mix with instrumental
    effects = os.path.join(output_folder, "effects.wav")
    mixedEffects = os.path.join(output_folder, "mixedEffects.wav")
    try:
        audiogenerate.addEffects(wav1, effects)
    except Exception as e:
        return f"Error adding effects: {str(e)}"
    mixAudio(effects, wav2, mixedEffects)
    
    # Optional: move any extra .wav files to the output folder
    remfiles = list_files_with_ext(".", ".wav")
    for rem in remfiles:
        try:
            shutil.move(rem, os.path.join(output_folder, os.path.basename(rem)))
        except Exception:
            pass
    
    return wav1, wav2, mixed_path, mixedEffects

def refresh_model_files():
    """
    Return the updated lists of .pth and .index files.
    """
    return get_pth_files(), get_index_files()

# Build the Gradio Blocks UI
with gr.Blocks(title="Youtube to RVC Audio Generator") as demo:
    gr.Markdown("# Youtube to RVC Audio Generator")
    
    with gr.Tabs():
        
        with gr.TabItem("Audio Generation"):
            gr.Markdown("## Generate Audio")
            with gr.Row():
                pth_dropdown = gr.Dropdown(choices=get_pth_files(), label="Select .pth file", interactive=True)
                index_dropdown = gr.Dropdown(choices=get_index_files(), label="Select .index file", interactive=True)
                refresh_button = gr.Button("Refresh Model Files")
            refresh_button.click(fn=refresh_model_files, inputs=[], outputs=[pth_dropdown, index_dropdown])
            
            url_input = gr.Textbox(label="Enter URL", placeholder="Enter the URL for audio generation")
            generate_button = gr.Button("Generate Audio")
            
            with gr.Row():
                audio_vocals = gr.Audio(label="Vocals", type="filepath")
                audio_instrumental = gr.Audio(label="Instrumental", type="filepath")
            with gr.Row():
                audio_mixed = gr.Audio(label="Mixed Audio", type="filepath")
                audio_effects = gr.Audio(label="Effects", type="filepath")
            
            generate_button.click(
                fn=generate_audio,
                inputs=[pth_dropdown, index_dropdown, url_input],
                outputs=[audio_vocals, audio_instrumental, audio_mixed, audio_effects]
            )
        with gr.TabItem("Download Model"):
            gr.Markdown("## Download Model from Hugging Face")
            huggingface_url_input = gr.Textbox(
                label="Hugging Face Model ZIP URL",
                placeholder="Enter the URL to download the model ZIP file"
            )
            download_button = gr.Button("Download and Extract")
            download_output = gr.Textbox(label="Status", interactive=False)
            
            download_button.click(fn=download_model, inputs=[huggingface_url_input], outputs=[download_output])
        
    
    gr.Markdown("© 2025 Youtube to RVC Audio Generator")

if __name__ == "__main__":
    demo.launch()
