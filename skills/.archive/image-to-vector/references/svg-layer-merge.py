#!/usr/bin/env python3
"""
SVG Layer Merge Pipeline
=========================
Full pipeline: generate AI image → potrace vectorize → multi-layer SVG merge
→ transparent background PNG.

Usage:
  # From prompt (generates image first):
  python svg-layer-merge.py --prompt "A minimalist panda logo..." --output logo

  # From existing PNG (skip generation):
  python svg-layer-merge.py --input input.png --output logo

  # Custom colors:
  python svg-layer-merge.py --input input.png --output logo --fill "#1a1a2e" --accent "#00CED1"

Dependencies: PIL (pillow), potrace (apt-get install potrace)
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from collections import deque

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Missing dependencies: pip install pillow numpy", file=sys.stderr)
    sys.exit(1)


# ── Config ──────────────────────────────────────────────────────────

NUWA_BASE_URL = os.environ.get("NUWAFLUX_BASE_URL", "https://api.nuwaflux.com/v1")
NUWA_API_KEY = os.environ.get("NUWA_API_KEY", "")
DEFAULT_MODEL = "gpt-image-2"


# ── Stage 1: Generate image from prompt ─────────────────────────────

def generate_image(prompt: str, output_path: str, model: str = DEFAULT_MODEL) -> str:
    """Generate an image via NUWA gpt-image-2 and save as PNG.
    Returns the path to the saved PNG."""
    import urllib.request

    if not NUWA_API_KEY:
        print("ERROR: NUWA_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{NUWA_BASE_URL}/images/generations",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {NUWA_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    b64 = data.get("data", [{}])[0].get("b64_json", "")
    if not b64:
        print("ERROR: No image data in response", json.dumps(data, indent=2)[:500], file=sys.stderr)
        sys.exit(1)

    png_data = base64.b64decode(b64)
    Path(output_path).write_bytes(png_data)
    print(f"[1/4] Generated: {output_path} ({len(png_data)} bytes)")
    return output_path


# ── Stage 2: Extract color layers from image ────────────────────────

def extract_layers(png_path: str,
                   fill_color: str = "#000000",
                   accent_color: str = "#00CED1"):
    """Extract dark/edge/cyan layers from an image for separate potrace processing.
    Returns dict of {layer_name: pbm_path}."""
    img = Image.open(png_path).convert("RGB")
    arr = np.array(img)
    h, w = arr.shape[:2]
    layers = {}

    # --- Dark layer: low-brightness pixels ---
    dark = (np.mean(arr.astype(float), axis=2) < 100) * 255
    pbm = "/tmp/_layer_dark.pbm"
    Image.fromarray(dark.astype(np.uint8), "L").save(pbm)
    layers["dark"] = pbm

    # --- Edge layer: edge detection ---
    from PIL import ImageFilter
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_arr = np.array(edges)
    edge_bw = (edge_arr > 60) * 255
    pbm = "/tmp/_layer_edges.pbm"
    Image.fromarray(edge_bw.astype(np.uint8), "L").save(pbm)
    layers["edges"] = pbm

    # --- Accent layer: cyan-ish pixels ---
    r, g, b = arr[:, :, 0].astype(float), arr[:, :, 1].astype(float), arr[:, :, 2].astype(float)
    cyan_mask = ((g > 150) & (b > 150) & (r < 100)) * 255
    pbm = "/tmp/_layer_accent.pbm"
    Image.fromarray(cyan_mask.astype(np.uint8), "L").save(pbm)
    layers["accent"] = pbm

    print(f"[2/4] Layers extracted: dark={dark.sum()//255}px, "
          f"edges={(edge_bw>0).sum()}px, "
          f"accent={(cyan_mask>0).sum()}px")
    return layers


# ── Stage 3: Trace each layer with potrace ──────────────────────────

def trace_layer(pbm_path: str, turdsize: int = 20) -> list:
    """Run potrace on a PBM file and return list of path data strings.
    The background rectangle path is filtered out automatically."""
    svg_path = pbm_path.replace(".pbm", ".svg")
    result = subprocess.run(
        ["potrace", "-s", "--turdsize", str(turdsize), "-o", svg_path, pbm_path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"potrace error: {result.stderr}", file=sys.stderr)
        return []

    svg_text = Path(svg_path).read_text()
    paths = re.findall(r'<path\s+d="([^"]*)"', svg_text)
    # Filter out background rectangles (full-canvas fills)
    clean = []
    for d in paths:
        d_clean = d.replace("\n", " ").strip()
        d_clean = re.sub(r"\s+", " ", d_clean)
        if _is_background(d_clean):
            continue
        clean.append(d_clean)
    return clean


def _is_background(d: str) -> bool:
    """Heuristic: background rects cover the full canvas."""
    return ("M0 " in d and "5120" in d) or ("l0 -5120" in d)


# ── Stage 4: Assemble multi-layer SVG ───────────────────────────────

def assemble_svg(paths_dark: list,
                 paths_edges: list,
                 paths_accent: list,
                 fill_color: str = "#000000",
                 accent_color: str = "#00CED1",
                 edge_color: str = "#333333",
                 output: str = "output.svg",
                 width: int = 1024,
                 height: int = 1024) -> str:
    """Merge multiple path layers into a single SVG with proper transforms."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"'
        f' width="{width}" height="{height}">',
    ]

    # Dark fill layer
    if paths_dark:
        lines.append(f'  <!-- Dark fill -->')
        lines.append(f'  <g transform="translate(0,{height}) scale(0.1,-0.1)" fill="{fill_color}" stroke="none">')
        for d in paths_dark:
            lines.append(f'    <path d="{d}"/>')
        lines.append('  </g>')

    # Edge layer (thin lines)
    if paths_edges:
        lines.append(f'  <!-- Edge outlines -->')
        lines.append(f'  <g transform="translate(0,{height}) scale(0.1,-0.1)" fill="none" stroke="{edge_color}" stroke-width="0.5">')
        for d in paths_edges:
            lines.append(f'    <path d="{d}"/>')
        lines.append('  </g>')

    # Accent layer (cyan elements)
    if paths_accent:
        lines.append(f'  <!-- Accent elements -->')
        lines.append(f'  <g transform="translate(0,{height}) scale(0.1,-0.1)" fill="{accent_color}" stroke="none">')
        for d in paths_accent:
            lines.append(f'    <path d="{d}"/>')
        lines.append('  </g>')

    lines.append('</svg>')
    svg = "\n".join(lines)
    Path(output).write_text(svg, encoding="utf-8")
    print(f"[3/4] SVG assembled: {output} ({len(svg)} bytes, "
          f"{len(paths_dark)} dark + {len(paths_edges)} edges + {len(paths_accent)} accent paths)")
    return output


# ── Stage 5: Generate transparent-background PNG ────────────────────

def make_transparent_png(png_path: str, output: str = "output_transparent.png",
                         threshold: int = 30):
    """Remove background via flood-fill from edges. Returns output path."""
    img = Image.open(png_path).convert("RGB")
    arr = np.array(img)
    h, w = arr.shape[:2]

    # Estimate background color from corners
    corners = np.concatenate([
        arr[0:5, 0:5].reshape(-1, 3),
        arr[0:5, w-5:w].reshape(-1, 3),
        arr[h-5:h, 0:5].reshape(-1, 3),
        arr[h-5:h, w-5:w].reshape(-1, 3),
    ])
    bg_color = corners.mean(axis=0)

    visited = np.zeros((h, w), dtype=bool)
    q = deque()

    def is_bg(y, x):
        return np.max(np.abs(arr[y, x].astype(float) - bg_color)) < threshold

    # Seed from edges
    for y in range(h):
        for x in [0, w - 1]:
            if not visited[y, x] and is_bg(y, x):
                visited[y, x] = True
                q.append((y, x))
    for x in range(1, w - 1):
        for y in [0, h - 1]:
            if not visited[y, x] and is_bg(y, x):
                visited[y, x] = True
                q.append((y, x))

    # Flood fill
    while q:
        y, x = q.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx] and is_bg(ny, nx):
                visited[ny, nx] = True
                q.append((ny, nx))

    alpha = np.where(visited, 0, 255).astype(np.uint8)
    rgba = np.dstack([arr, alpha])
    Image.fromarray(rgba, "RGBA").save(output)
    print(f"[4/4] Transparent PNG: {output} "
          f"({(alpha>0).sum()}/{alpha.size} px kept, {(alpha==0).sum()/alpha.size*100:.0f}% transparent)")
    return output


# ── CLI ─────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="SVG Layer Merge Pipeline")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt", help="AI image generation prompt")
    group.add_argument("--input", help="Existing PNG to process (skip generation)")
    p.add_argument("--output", default="output", help="Output basename (default: output)")
    p.add_argument("--fill", default="#000000", help="Dark fill color (default: #000000)")
    p.add_argument("--accent", default="#00CED1", help="Accent color (default: #00CED1)")
    p.add_argument("--edge", default="#333333", help="Edge line color (default: #333333)")
    p.add_argument("--model", default=DEFAULT_MODEL, help="Image model (default: gpt-image-2)")
    p.add_argument("--turdsize", type=int, default=20, help="potrace turdsize (default: 20)")
    return p.parse_args()


def main():
    args = parse_args()
    basename = args.output

    # Stage 1: Generate or use existing
    if args.prompt:
        png_path = f"/tmp/{basename}_raw.png"
        generate_image(args.prompt, png_path, args.model)
    else:
        png_path = args.input
        print(f"[1/4] Using existing: {png_path}")

    # Stage 2: Extract layers
    layers = extract_layers(png_path, args.fill, args.accent)

    # Stage 3: Trace each layer
    dark_paths = trace_layer(layers["dark"], args.turdsize)
    edge_paths = trace_layer(layers["edges"], args.turdsize)
    accent_paths = trace_layer(layers["accent"], args.turdsize)

    # Stage 4: Assemble SVG
    svg_path = f"{basename}.svg"
    assemble_svg(dark_paths, edge_paths, accent_paths,
                 fill_color=args.fill, accent_color=args.accent, edge_color=args.edge,
                 output=svg_path)

    # Stage 5: Transparent PNG
    png_out = f"{basename}_transparent.png"
    make_transparent_png(png_path, png_out)

    print(f"\n✅ Done! Files:")
    print(f"   SVG:       {svg_path}")
    print(f"   Transparent PNG: {png_out}")
    print(f"   (Raw PNG:        {png_path})")


if __name__ == "__main__":
    main()
