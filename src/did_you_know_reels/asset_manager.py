"""Background asset selection with placeholder fallback."""

from __future__ import annotations

from pathlib import Path

from .models import Scene


class AssetManager:
    """Chooses local assets or placeholder backgrounds for scenes."""

    def __init__(self, asset_root: str, background_colors: list[str]) -> None:
        self.asset_root = Path(asset_root)
        self.background_colors = background_colors

    def build_scene_assets(self, scenes: list[Scene]) -> list[dict[str, str]]:
        """Resolve scene assets or use background color placeholders."""

        assets: list[dict[str, str]] = []
        backgrounds = sorted(self.asset_root.glob("*"))
        for index, scene in enumerate(scenes):
            asset_path = backgrounds[index % len(backgrounds)] if backgrounds else None
            assets.append(
                {
                    "scene_id": f"scene_{scene.scene_number:02}",
                    "asset_type": "image" if asset_path else "placeholder_color",
                    "asset_path": str(asset_path) if asset_path else "",
                    "placeholder_color": self.background_colors[index % len(self.background_colors)],
                }
            )
        return assets
