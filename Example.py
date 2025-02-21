# Example usage:
if __name__ == "__main__":
    # Initialize with your RVC model name
    processor = AudioProcessor("your_rvc_model_name")
    
    # Process YouTube URL
    result = processor.process_track(
        "https://www.youtube.com/watch?v=fKyXvNkGQKc",
        "kingslayer_processed.wav",
        pitch_shift=0
    )
    print(f"Processed audio saved to {result[0]}")
