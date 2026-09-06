from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .renderer import ASPECT_RATIOS
from .voice import load_settings_data, save_settings_data, settings_path


@dataclass(frozen=True)
class VideoPreferences:
    aspect_ratio: str = "16:9"
    pen_brand: str = "Ăn dặm mẹ Dâu"

    @classmethod
    def load(cls, path: Path | None = None) -> "VideoPreferences":
        target = path or settings_path()
        data = load_settings_data(target)
        ratio = data.get("lastAspectRatio", "16:9")
        brand = data.get("lastPenBrand", "Ăn dặm mẹ Dâu")
        return cls(
            aspect_ratio=ratio if isinstance(ratio, str) and ratio in ASPECT_RATIOS else "16:9",
            pen_brand=brand if isinstance(brand, str) else "Ăn dặm mẹ Dâu",
        )

    def save(self, path: Path | None = None) -> None:
        target = path or settings_path()
        data = load_settings_data(target)
        data.update(
            {
                "lastAspectRatio": self.aspect_ratio,
                "lastPenBrand": self.pen_brand,
            }
        )
        save_settings_data(data, target)
