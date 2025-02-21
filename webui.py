import os
import shutil
import time
import gradio as gr
from pydub import AudioSegment
import audiogenerate
from audiogenerate import AudioProcessor

# Set up fixed folders
RVC_FOLDER = "./rvc"
os.makedirs(RVC_FOLDER, exist_ok=True)


def list_files_with_ext(folder, ext):
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(ext)]


def get_pth_files():
    return list_files_with_ext(RVC_FOLDER, ".pth")


def get_index_files():
    return list_files_with_ext(RVC_FOLDER, ".index")





def create_ui():
    with gr.Blocks(title="Audio Processing Studio", theme=gr.themes.Default()) as demo:
        gr.Markdown("# 🎵 Youtube to RVC")
        gr.Markdown("Transform YouTube audio with AI processing, vocal separation, and effects")
        
        with gr.Row():
            with gr.Column():
                yt_url = gr.Textbox(label="YouTube URL", placeholder="https://youtube.com/...")
                model_name = gr.Textbox(
                    label="RVC Model",
                    label="RVC Model"
                )
                pitch_shift = gr.Slider(-12, 12, value=0, step=1, label="Pitch Shift (semitones)")
                f0_method = gr.Dropdown(
                    label="Pitch Detection Method",
                    choices=["hybrid[rmvpe+fcpe]", "rmvpe", "fcpe", "crepe"],
                    value="hybrid[rmvpe+fcpe]"
                )
                submit_btn = gr.Button("Process Audio", variant="primary")

            with gr.Column():
                processed_audio = gr.Audio(label="Processed Vocals", type="filepath")
                instrumental_audio = gr.Audio(label="Instrumental Track", type="filepath")
                status = gr.Textbox(label="Processing Status", interactive=False)

        def process_audio(url, model, pitch, f0_method):
            try:
                if not url.startswith("https://www.youtube.com/"):
                    raise gr.Error("Please enter a valid YouTube URL")
                
                processor = AudioProcessor(model_name=model)
                processed_path, instrumental_path = processor.process_track(
                    youtube_url=url,
                    pitch_shift=pitch,
                    f0_method=f0_method
                )
                
                return [processed_path, instrumental_path, "Processing complete!"]
            
            except Exception as e:
                return [None, None, f"Error: {str(e)}"]

        submit_btn.click(
            fn=process_audio,
            inputs=[yt_url, model_name, pitch_shift, f0_method],
            outputs=[processed_audio, instrumental_audio, status]
        )


    return demo

if __name__ == "__main__":
    ui = create_ui()
    ui.launch(server_name="0.0.0.0", share=False)
