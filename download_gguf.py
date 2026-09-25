import os
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_URL = "https://huggingface.co/bartowski/google_gemma-3-12b-it-GGUF/resolve/main/google_gemma-3-12b-it-Q4_K_M.gguf"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "models", "google_gemma-3-12b-it-Q4_K_M.gguf")
TOKEN = os.getenv("HF_TOKEN", os.getenv("HUGGING_FACE_HUB_TOKEN", ""))
NUM_THREADS = 16

def get_final_url_and_size():
    headers = {"User-Agent": "Mozilla/5.0"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with requests.get(REPO_URL, headers=headers, stream=True, allow_redirects=True, timeout=20) as r:
        r.raise_for_status()
        final_url = r.url
        content_length = int(r.headers.get("content-length", 0))
        return final_url, content_length

def download_part(url, start_byte, end_byte, part_index, part_file):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Range": f"bytes={start_byte}-{end_byte}"
    }
    retries = 3
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(part_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            return part_index, True
        except Exception as e:
            if attempt == retries:
                raise e
            time.sleep(1.0)
    return part_index, False

def main():
    print("Resolving final AWS CDN URL...", flush=True)
    final_url, total_size = get_final_url_and_size()
    total_mb = total_size / (1024 * 1024)
    print(f"Total size: {total_mb:.1f} MB across {NUM_THREADS} parallel parts", flush=True)

    chunk_size = total_size // NUM_THREADS
    part_files = []
    tasks = []

    for i in range(NUM_THREADS):
        start = i * chunk_size
        end = total_size - 1 if i == NUM_THREADS - 1 else (start + chunk_size - 1)
        part_file = f"{OUTPUT_FILE}.part{i}"
        part_files.append(part_file)
        tasks.append((final_url, start, end, i, part_file))

    start_time = time.time()
    completed_parts = 0

    print(f"Starting parallel download with {NUM_THREADS} workers...", flush=True)
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = {
            executor.submit(download_part, url, start, end, idx, pf): idx
            for (url, start, end, idx, pf) in tasks
        }
        for future in as_completed(futures):
            idx, success = future.result()
            completed_parts += 1
            elapsed = time.time() - start_time
            pct = (completed_parts / NUM_THREADS) * 100
            print(f"Part {idx+1}/{NUM_THREADS} finished [{completed_parts}/{NUM_THREADS} completed ({pct:.0f}%)] in {elapsed:.1f}s", flush=True)

    print("All 16 parts downloaded successfully! Merging into final GGUF file...", flush=True)
    with open(OUTPUT_FILE, "wb") as outfile:
        for p in part_files:
            with open(p, "rb") as infile:
                while True:
                    data = infile.read(8 * 1024 * 1024)
                    if not data:
                        break
                    outfile.write(data)
            try:
                os.remove(p)
            except Exception:
                pass

    final_size = os.path.getsize(OUTPUT_FILE)
    total_elapsed = time.time() - start_time
    avg_speed = (final_size / 1024 / 1024) / total_elapsed
    print(f"COMPLETE! Final file: {final_size / 1024 / 1024:.1f} MB in {total_elapsed:.1f}s ({avg_speed:.1f} MB/s)", flush=True)

if __name__ == "__main__":
    main()
