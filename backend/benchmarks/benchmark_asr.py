"""
Offline Benchmark Utility: IndicConformer CTC vs RNNT.

Evaluates IndicConformer-600M-Multi decoding strategies:
- IndicConformer + CTC
- IndicConformer + RNNT

Measures:
- Transcription output
- Inference latency (ms)
- Process memory usage (RAM RSS in MB)
- Word Error Rate (WER) when reference ground truth text is provided

Usage:
    python -m backend.benchmarks.benchmark_asr --audio-path path/to/sample.wav --language ta
    python -m backend.benchmarks.benchmark_asr --audio-path path/to/sample.wav --language hi --reference-text "..."
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
import argparse
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("asr_benchmark")

def calculate_wer(reference: str, hypothesis: str) -> float:
    """Calculate Word Error Rate (WER) between reference and hypothesis texts."""
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                substitution = d[i - 1][j - 1] + 1
                insertion = d[i][j - 1] + 1
                deletion = d[i - 1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)

    wer = float(d[len(ref_words)][len(hyp_words)]) / float(len(ref_words))
    return round(wer, 4)

def run_asr_benchmark(
    audio_path: str,
    language: str = "ta",
    reference_text: Optional[str] = None,
    use_mock: bool = False
) -> Dict[str, Any]:
    """Run CTC vs RNNT comparative benchmark."""
    if not os.path.exists(audio_path):
        return {
            "status": "error",
            "message": f"Audio file '{audio_path}' not found. Provide a valid WAV/FLAC file to benchmark."
        }

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    import psutil
    process = psutil.Process()

    if use_mock:
        from app.services.asr.indic_conformer import MockIndicConformerAdapter
        adapter = MockIndicConformerAdapter()
    else:
        from app.services.asr.indic_conformer import IndicConformerAdapter
        adapter = IndicConformerAdapter()

    results: Dict[str, Any] = {
        "audio_path": audio_path,
        "language": language,
        "reference_text": reference_text,
        "decoders": {}
    }

    for decoder_type in ["ctc", "rnnt"]:
        mem_before = process.memory_info().rss / (1024 * 1024)
        start_time = time.perf_counter()

        try:
            transcript = adapter.transcribe(audio_bytes=audio_bytes, language=language, decoder=decoder_type)
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            mem_after = process.memory_info().rss / (1024 * 1024)

            decoder_metrics: Dict[str, Any] = {
                "transcription": transcript,
                "latency_ms": duration_ms,
                "ram_rss_mb": round(mem_after, 2),
                "ram_delta_mb": round(mem_after - mem_before, 2),
            }

            if reference_text:
                decoder_metrics["wer"] = calculate_wer(reference_text, transcript)

            results["decoders"][decoder_type] = decoder_metrics
        except Exception as e:
            results["decoders"][decoder_type] = {
                "error": str(e),
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2)
            }

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IndicConformer CTC vs RNNT Benchmarking")
    parser.add_argument("--audio-path", type=str, required=True, help="Path to audio file (16kHz WAV/FLAC)")
    parser.add_argument("--language", type=str, default="ta", help="Target Indian language code (e.g. 'ta', 'hi', 'en')")
    parser.add_argument("--reference-text", type=str, default=None, help="Ground truth reference text for WER")
    parser.add_argument("--mock", action="store_true", help="Use mock adapter for offline verification")

    args = parser.parse_args()
    report = run_asr_benchmark(
        audio_path=args.audio_path,
        language=args.language,
        reference_text=args.reference_text,
        use_mock=args.mock
    )
    import json
    print(json.dumps(report, indent=2, ensure_ascii=False))