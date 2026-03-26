"""Image to PDF conversion using ImageMagick."""

from __future__ import annotations

import subprocess
from pathlib import Path


def convert_image_to_pdf(
    image_path: Path,
    output_dir: Path,
    filename: str | None = None,
    density: int = 150,
) -> Path:
    """Convert an image to PDF using ImageMagick.

    If filename is not provided, the image stem is used with .pdf extension.
    The final filename may be renamed later after metadata extraction.
    """
    if filename:
        pdf_name = filename if filename.endswith(".pdf") else f"{filename}.pdf"
    else:
        pdf_name = f"{image_path.stem}.pdf"

    pdf_path = output_dir / pdf_name

    subprocess.run(
        ["magick", str(image_path), "-density", str(density), str(pdf_path)],
        check=True,
        capture_output=True,
    )
    return pdf_path


def rename_pdf(pdf_path: Path, new_name: str) -> Path:
    """Rename a PDF file. Returns the new path."""
    new_path = pdf_path.parent / new_name
    pdf_path.rename(new_path)
    return new_path


def get_pdf_page_count(pdf_path: Path) -> int:
    """Return the number of pages in a PDF."""
    result = subprocess.run(
        ["magick", "identify", str(pdf_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return 1
    return len(result.stdout.strip().splitlines())


def split_pdf_to_images(pdf_path: Path, output_dir: Path) -> list[Path]:
    """Split a multi-page PDF into one PNG per page.

    Returns list of image paths in page order.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = pdf_path.stem

    subprocess.run(
        [
            "magick", str(pdf_path),
            "-density", "200",
            str(output_dir / f"{stem}-page-%03d.png"),
        ],
        check=True,
        capture_output=True,
    )

    pages = sorted(output_dir.glob(f"{stem}-page-*.png"))
    return pages
