import sys
import subprocess

# Check if running in Google Colab
if "google.colab" in sys.modules:
    subprocess.run([
        "pip", "install",
        "https://github.com/TheNeodev/fairseq-fix/releases/download/fix/fairseq_fixed-0.13.0-cp311-cp311-linux_x86_64.whl"
    ], check=True)
