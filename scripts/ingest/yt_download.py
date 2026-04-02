import os
import argparse
import subprocess
import sys

def download_audio(url, output_dir):
    """
    Downloads audio from a YouTube URL and converts it to MP3.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # yt-dlp command template
    # -x: extract audio
    # --audio-format mp3: convert to mp3
    # -o: output template
    # --audio-quality 0: best quality
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
        url
    ]

    try:
        print(f"Downloading: {url}")
        subprocess.run(cmd, check=True)
        print("Download and conversion complete!")
    except subprocess.CalledProcessError as e:
        print(f"Error during download: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="YouTube Audio Download Pipeline")
    parser.add_argument("--url", type=str, help="YouTube URL to download")
    parser.add_argument("--file", type=str, help="Path to a text file containing YouTube URLs (one per line)")
    parser.add_argument("--outdir", type=str, default="data/audio/raw", help="Directory to save downloaded files")

    args = parser.parse_args()

    # Use absolute path for output directory relative to project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    output_dir = os.path.join(project_root, args.outdir)

    if args.url:
        download_audio(args.url, output_dir)
    elif args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return
        
        with open(args.file, "r", encoding="utf-8") as f:
            urls = []
            for line in f:
                line = line.split("#")[0].strip()
                if line:
                    urls.append(line)
        
        print(f"Found {len(urls)} URLs. Starting batch download...")
        for url in urls:
            download_audio(url, output_dir)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
