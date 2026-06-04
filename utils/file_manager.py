from pathlib import Path


def read_file(filepath: Path) -> str:
    if not filepath.exists():
        return ""
    return filepath.read_text(encoding="utf-8")


def write_file(filepath: Path, content: str) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")


def spec_file_exists(filepath: Path) -> bool:
    if not filepath.exists():
        return False
    return len(filepath.read_text(encoding="utf-8").strip()) > 0


def load_all_specs(spec_directory: str) -> dict:
    base = Path(spec_directory)
    product_path = base / "product.md"
    requirements_path = base / "requirements.md"
    design_path = base / "design.json"

    return {
        "product_content": read_file(product_path),
        "requirements_content": read_file(requirements_path),
        "design_content": read_file(design_path),
        "product_exists": spec_file_exists(product_path),
        "requirements_exists": spec_file_exists(requirements_path),
        "design_exists": spec_file_exists(design_path),
    }
