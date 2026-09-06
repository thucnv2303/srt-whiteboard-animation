from __future__ import annotations

from .renderer import ASPECT_RATIOS


def preview_frame_size(
    container_width: int,
    container_height: int,
    aspect_ratio: str,
) -> tuple[int, int]:
    """Tính khung preview lớn nhất giữ đúng tỷ lệ đầu ra trong vùng chứa."""
    width = max(1, container_width)
    height = max(1, container_height)
    spec = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS["16:9"])

    if width * spec.height >= height * spec.width:
        target_height = height
        target_width = int(height * spec.width / spec.height)
    else:
        target_width = width
        target_height = int(width * spec.height / spec.width)
    return max(1, target_width), max(1, target_height)
