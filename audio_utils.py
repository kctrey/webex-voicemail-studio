import os
import subprocess

DISCLAIMER_PATH = "disclaimer.mp3"

def ensure_disclaimer_exists():
    """Create a dummy disclaimer if one doesn't exist for testing."""
    if not os.path.exists(DISCLAIMER_PATH):
        # Generate a 2-second silent audio as placeholder
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=8000:cl=mono", 
            "-t", "2", DISCLAIMER_PATH
        ], check=False) # don't fail if ffmpeg is missing during dummy creation, main logic will fail later

def process_voicemail_audio(input_file_path: str, output_file_path: str):
    """
    Reads the recorded audio, appends a short pause and the legal disclaimer,
    then exports as 8000 Hz, mono, u-Law encoded wav file.
    """
    ensure_disclaimer_exists()
    
    # We want: input + 1 sec pause + disclaimer
    # We can use ffmpeg filter_complex to concatenate
    # [0:a] is input
    # [1:a] is 1 sec silence
    # [2:a] is disclaimer
    
    # Create a temporary 1s silence file, or just use lavfi directly
    # filter: 
    # anullsrc=r=8000:cl=mono:d=1[silence];
    # [0:a][silence][1:a]concat=n=3:v=0:a=1[outa]
    
    filter_complex = (
        "[0:a]aresample=8000,aformat=sample_fmts=s16:channel_layouts=mono[in1]; "
        "[1:a]aresample=8000,aformat=sample_fmts=s16:channel_layouts=mono[in2]; "
        "anullsrc=r=8000:cl=mono:d=1[silence]; "
        "[in1][silence][in2]concat=n=3:v=0:a=1[outa]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file_path,
        "-i", DISCLAIMER_PATH,
        "-filter_complex", filter_complex,
        "-map", "[outa]",
        "-ar", "8000",
        "-ac", "1",
        "-c:a", "pcm_mulaw",
        output_file_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        
    return output_file_path
