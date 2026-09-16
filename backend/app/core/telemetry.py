import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_system_resources() -> Dict[str, Any]:
    """Report memory and device resources safely."""
    info: Dict[str, Any] = {}
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        info['ram_rss_mb'] = round(mem_info.rss / (1024 * 1024), 2)
        info['ram_percent'] = psutil.virtual_memory().percent
    except Exception as e:
        info['ram_error'] = str(e)

    try:
        import torch
        info['cuda_available'] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info['vram_allocated_mb'] = round(torch.cuda.memory_allocated() / (1024 * 1024), 2)
            info['vram_reserved_mb'] = round(torch.cuda.memory_reserved() / (1024 * 1024), 2)
            info['gpu_device_name'] = torch.cuda.get_device_name(0)
    except Exception as e:
        info['gpu_error'] = str(e)

    return info

def resolve_device(configured_device: Optional[str] = None) -> str:
    """Determine device: GPU if available, else CPU. Respect explicit config."""
    if configured_device and configured_device.lower() in ["cuda", "cpu"]:
        return configured_device.lower()
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"
