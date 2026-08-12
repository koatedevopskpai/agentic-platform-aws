import yaml
import hashlib
from pathlib import Path
from typing import Optional


class PromptRegistry:
    def __init__(self, registry_path: str = "prompts/registry"):
        self.registry_path = Path(registry_path)

    def list_prompts(self) -> list[dict]:
        prompts = []
        if not self.registry_path.exists():
            return prompts
        for f in sorted(self.registry_path.glob("*.yaml")):
            with open(f) as fh:
                data = yaml.safe_load(fh)
                prompts.append({
                    "name": data.get("name", f.stem),
                    "version": data.get("version", "0.0.0"),
                    "author": data.get("author", "unknown"),
                    "file": f.name,
                    "overlays": list(data.get("overlays", {}).keys()),
                    "test_count": len(data.get("tests", [])),
                })
        return prompts

    def get_prompt(
        self, name: str, overlay: Optional[str] = None
    ) -> dict:
        path = self.registry_path / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Prompt '{name}' not found at {path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        prompt = dict(data["prompt"])
        model = data.get("model", "claude-sonnet-4")

        if overlay and overlay in data.get("overlays", {}):
            overlay_data = data["overlays"][overlay]
            if "prompt" in overlay_data:
                for key in ("system", "user"):
                    if key in overlay_data["prompt"]:
                        prompt[key] = overlay_data["prompt"][key]
            if "model" in overlay_data:
                model = overlay_data["model"]

        return {
            "system": prompt.get("system", ""),
            "user": prompt.get("user", ""),
            "model": model,
            "hash": self._hash(prompt),
            "version": data["version"],
            "name": data["name"],
        }

    def get_tests(self, name: str) -> list[dict]:
        path = self.registry_path / f"{name}.yaml"
        if not path.exists():
            return []
        with open(path) as f:
            data = yaml.safe_load(f)
        return data.get("tests", [])

    @staticmethod
    def _hash(prompt: dict) -> str:
        content = yaml.dump(prompt, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
