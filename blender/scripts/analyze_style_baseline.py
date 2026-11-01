"""定量自检（对象区域）：对比默认 PBR 与三渲二渲染，量化「色阶分明 / 描边可见 / 无连续渐变」。

用 before/after 差异掩码隔离立方体+球体，避免背景稀释指标。
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / 'blender' / 'style_baseline_before.png'
AFTER = ROOT / 'blender' / 'style_baseline_render.png'
OUT = ROOT / 'blender' / 'style_baseline_metrics.json'


def rgb(path):
    return np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) / 255.0


def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def gradient(L):
    gx = np.zeros_like(L); gy = np.zeros_like(L)
    gx[:, :-1] = np.abs(np.diff(L, axis=1))
    gy[:-1, :] = np.abs(np.diff(L, axis=0))
    return gx, gy, np.hypot(gx, gy)


def local_range(L, k=3):
    pad = k // 2
    P = np.pad(L, pad, mode='edge')
    out = np.zeros_like(L)
    for dy in range(k):
        for dx in range(k):
            out = np.maximum(out, P[dy:dy + L.shape[0], dx:dx + L.shape[1]])
    mn = np.full_like(L, 1.0)
    for dy in range(k):
        for dx in range(k):
            mn = np.minimum(mn, P[dy:dy + L.shape[0], dx:dx + L.shape[1]])
    return out - mn


def stats(L, mask, gx, gy, mag, lr):
    v = L[mask]
    hist, _ = np.histogram(v, bins=64, range=(0.0, 1.0))
    p = hist.astype(np.float64) / max(1, hist.sum())
    nz = p[p > 0]
    entropy = float(-(nz * np.log2(nz)).sum() / np.log2(64))
    top3 = float(np.sort(p)[::-1][:3].sum())
    unique = int(len(np.unique(np.round(v * 64))))
    edge = float((mag[mask] > 0.08).mean())
    flat = float((lr[mask] < 0.02).mean())
    return {'pixels': int(mask.sum()), 'mean_lum': round(float(v.mean()), 4),
            'mean_grad': round(float((gx[mask].mean() + gy[mask].mean()) / 2), 5),
            'edge_density': round(edge, 4), 'unique_levels': unique,
            'hist_entropy': round(entropy, 4), 'top3_bin_share': round(top3, 4),
            'flat_fraction': round(flat, 4)}


a_before, a_after = rgb(BEFORE), rgb(AFTER)
diff = np.abs(a_after - a_before).sum(axis=2)
mask = diff > 0.02
ys, xs = np.where(mask)
print('MASK_BBOX', int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), 'pixels', int(mask.sum()))

Lb, La = lum(a_before), lum(a_after)
gxb, gyb, magb = gradient(Lb)
gxa, gya, maga = gradient(La)
lrb, lra = local_range(Lb), local_range(La)

before_stats = stats(Lb, mask, gxb, gyb, magb, lrb)
after_stats = stats(La, mask, gxa, gya, maga, lra)
result = {'region': 'objects (diff mask)', 'mask_pixels': int(mask.sum()),
          'before_pbr': before_stats, 'after_npr': after_stats}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))

checks = {
    'banded(entropy_lower)': after_stats['hist_entropy'] < before_stats['hist_entropy'],
    'concentrated(top3_share_higher)': after_stats['top3_bin_share'] > before_stats['top3_bin_share'],
    'outline_or_edges(edge_density_higher)': after_stats['edge_density'] > before_stats['edge_density'],
}
informational = {
    'unique_levels': [before_stats['unique_levels'], after_stats['unique_levels']],
    'flat_fraction': [before_stats['flat_fraction'], after_stats['flat_fraction']],
    'note': 'unique_levels/flat_fraction 受抗锯齿与描边过渡像素影响，不作为判据，仅记录。',
}
print(json.dumps(checks, ensure_ascii=False, indent=2))
print(json.dumps(informational, ensure_ascii=False, indent=2))
print('STYLE_BASELINE_METRICS_OK' if all(checks.values()) else 'STYLE_BASELINE_METRICS_PARTIAL')
