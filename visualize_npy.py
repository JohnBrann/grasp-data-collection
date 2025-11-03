# # #!/usr/bin/env python3
# # import argparse
# # from pathlib import Path
# # import time
# # import sys

# # import numpy as np
# # import matplotlib.pyplot as plt
# # import cv2

# # def robust_depth_normalize(depth: np.ndarray):
# #     """Normalize depth to [0,1] for visualization (ignoring zeros)."""
# #     d = depth.copy()
# #     mask = d > 0
# #     if mask.any():
# #         vmin, vmax = np.percentile(d[mask], [2, 98])
# #         if vmax <= vmin:
# #             vmax = d[mask].max()
# #             vmin = d[mask].min()
# #         d = np.clip((d - vmin) / max(vmax - vmin, 1e-6), 0, 1)
# #     else:
# #         d[:] = 0
# #     return d

# # def load_bundle(input_path: Path):
# #     """
# #     Load a sensor bundle from:
# #       - .npz file with keys like 'depth_imgs', 'extrinsics', optionally 'seg'
# #       - directory containing 'depth_imgs.npy' and 'extrinsics.npy' (and optionally 'seg.npy')
# #       - a single .npy depth file (fallback)
# #     Returns dict with {'depth_imgs', 'extrinsics', 'seg' (optional)}.
# #     """
# #     inp = Path(input_path)
# #     bundle = {}

# #     if inp.is_file():
# #         if inp.suffix == ".npz":
# #             data = np.load(inp, allow_pickle=True)
# #             # best-effort key discovery
# #             key_map = {
# #                 "depth_imgs": None,
# #                 "extrinsics": None,
# #                 "seg": None
# #             }
# #             for k in data.files:
# #                 lk = k.lower()
# #                 if "depth" in lk and key_map["depth_imgs"] is None:
# #                     key_map["depth_imgs"] = k
# #                 elif ("extr" in lk or "pose" in lk) and key_map["extrinsics"] is None:
# #                     key_map["extrinsics"] = k
# #                 elif "seg" in lk and key_map["seg"] is None:
# #                     key_map["seg"] = k
# #             if key_map["depth_imgs"] is None:
# #                 raise ValueError("Couldn't find depth array in npz.")
# #             bundle["depth_imgs"] = data[key_map["depth_imgs"]]
# #             if key_map["extrinsics"] is not None:
# #                 bundle["extrinsics"] = data[key_map["extrinsics"]]
# #             if key_map["seg"] is not None:
# #                 bundle["seg"] = data[key_map["seg"]]
# #         elif inp.suffix == ".npy":
# #             arr = np.load(inp)
# #             # assume this is a depth stack
# #             bundle["depth_imgs"] = arr
# #         else:
# #             raise ValueError(f"Unsupported file type: {inp.suffix}")
# #     else:
# #         # directory
# #         d = inp
# #         d_depth = d / "depth_imgs.npy"
# #         d_extr = d / "extrinsics.npy"
# #         d_seg  = d / "seg.npy"
# #         if d_depth.exists():
# #             bundle["depth_imgs"] = np.load(d_depth)
# #         else:
# #             # fallback: try to find a .npy with 'depth' in name
# #             cands = list(d.glob("*depth*.npy"))
# #             if not cands:
# #                 raise FileNotFoundError("No depth .npy found in directory.")
# #             bundle["depth_imgs"] = np.load(cands[0])
# #         if d_extr.exists():
# #             bundle["extrinsics"] = np.load(d_extr)
# #         if d_seg.exists():
# #             bundle["seg"] = np.load(d_seg)
# #     # Ensure depth is [N, H, W]
# #     depths = bundle["depth_imgs"]
# #     if depths.ndim == 2:
# #         depths = depths[None, ...]
# #     bundle["depth_imgs"] = depths.astype(np.float32)
# #     # Optional segmentation
# #     if "seg" in bundle:
# #         seg = bundle["seg"]
# #         if seg.ndim == 2:
# #             seg = seg[None, ...]
# #         bundle["seg"] = seg
# #     return bundle

# # def save_depth_16bit_png(path: Path, depth: np.ndarray, scale_mm: float = 1000.0):
# #     """Save metric depth as 16-bit PNG (millimeters by default)."""
# #     depth_mm = np.clip(depth * scale_mm, 0, np.iinfo(np.uint16).max).astype(np.uint16)
# #     path.parent.mkdir(parents=True, exist_ok=True)
# #     cv2.imwrite(str(path), depth_mm)

# # def save_depth_viz_png(path: Path, depth: np.ndarray):
# #     """Save an 8-bit colormapped visualization."""
# #     d = (robust_depth_normalize(depth) * 255).astype(np.uint8)
# #     vis = cv2.applyColorMap(d, cv2.COLORMAP_TURBO)
# #     path.parent.mkdir(parents=True, exist_ok=True)
# #     cv2.imwrite(str(path), vis)

# # def seg_to_color(seg: np.ndarray):
# #     """Quick-and-dirty random-color visualization for segmentation IDs."""
# #     ids = np.unique(seg)
# #     # Keep 0 black by convention
# #     rng = np.random.RandomState(1234)
# #     lut = {int(i): (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256)) for i in ids if i != 0}
# #     h, w = seg.shape
# #     rgb = np.zeros((h, w, 3), np.uint8)
# #     for i in ids:
# #         if i == 0: 
# #             continue
# #         rgb[seg == i] = lut[int(i)]
# #     return rgb

# # def main():
# #     ap = argparse.ArgumentParser()
# #     ap.add_argument("input", type=Path, help="Path to .npz/.npy or a directory containing depth/extrinsics npy files")
# #     ap.add_argument("--delay", type=float, default=1.0, help="Seconds between frames in autoplay")
# #     ap.add_argument("--autoplay", action="store_true", help="Automatically cycle through frames")
# #     ap.add_argument("--save-png", action="store_true", help="Export PNGs for all frames")
# #     ap.add_argument("--out", type=Path, default=Path("png_out"), help="Output directory for PNG export")
# #     ap.add_argument("--mm-scale", type=float, default=1000.0, help="Depth meters->millimeters scale for 16-bit PNG")
# #     ap.add_argument("--show-seg", action="store_true", help="If seg present, show an extra window with colored IDs")
# #     args = ap.parse_args()

# #     bundle = load_bundle(args.input)
# #     depths = bundle["depth_imgs"]
# #     segs = bundle.get("seg", None)

# #     print(f"Loaded: {depths.shape} (N,H,W) depth frames")
# #     if "extrinsics" in bundle:
# #         print(f"Extrinsics shape: {bundle['extrinsics'].shape}")

# #     # Set up windows
# #     plt.ion()
# #     fig, ax = plt.subplots(num="Depth (normalized colormap)")
# #     im = ax.imshow(robust_depth_normalize(depths[0]), cmap="turbo", vmin=0, vmax=1)
# #     ax.set_title("Depth (normalized) — frame 0")
# #     plt.show(block=False)

# #     seg_win = None
# #     if args.show_seg and segs is not None:
# #         seg_win = "Segmentation (colored)"
# #         cv2.namedWindow(seg_win, cv2.WINDOW_NORMAL)
# #         cv2.imshow(seg_win, seg_to_color(segs[0]))

# #     def update_frame(idx):
# #         ax.images[0].set_data(robust_depth_normalize(depths[idx]))
# #         ax.set_title(f"Depth (normalized) — frame {idx}")
# #         fig.canvas.draw_idle()
# #         fig.canvas.flush_events()
# #         if seg_win and segs is not None:
# #             cv2.imshow(seg_win, seg_to_color(segs[idx]))
# #             cv2.waitKey(1)

# #     if args.save_png:
# #         outdir = args.out
# #         for i in range(depths.shape[0]):
# #             save_depth_16bit_png(outdir / f"depth_{i:03d}.png", depths[i], scale_mm=args.mm_scale)
# #             save_depth_viz_png(outdir / f"depth_viz_{i:03d}.png", depths[i])
# #             if segs is not None:
# #                 cv2.imwrite(str(outdir / f"seg_{i:03d}.png"), segs[i].astype(np.uint16))
# #                 cv2.imwrite(str(outdir / f"seg_viz_{i:03d}.png"), seg_to_color(segs[i]))
# #         print(f"Saved PNGs to: {outdir.resolve()}")

# #     idx = 0
# #     update_frame(idx)

# #     if args.autoplay:
# #         try:
# #             while True:
# #                 time.sleep(args.delay)
# #                 idx = (idx + 1) % depths.shape[0]
# #                 update_frame(idx)
# #         except KeyboardInterrupt:
# #             pass
# #     else:
# #         print("Controls: n=next, p=prev, q=quit, s=save current PNGs")
# #         while True:
# #             ch = input("> ").strip().lower()
# #             if ch == "q":
# #                 break
# #             elif ch == "n":
# #                 idx = (idx + 1) % depths.shape[0]
# #                 update_frame(idx)
# #             elif ch == "p":
# #                 idx = (idx - 1) % depths.shape[0]
# #                 update_frame(idx)
# #             elif ch == "s":
# #                 outdir = args.out
# #                 save_depth_16bit_png(outdir / f"depth_{idx:03d}.png", depths[idx], scale_mm=args.mm_scale)
# #                 save_depth_viz_png(outdir / f"depth_viz_{idx:03d}.png", depths[idx])
# #                 if segs is not None:
# #                     cv2.imwrite(str(outdir / f"seg_{idx:03d}.png"), segs[idx].astype(np.uint16))
# #                     cv2.imwrite(str(outdir / f"seg_viz_{idx:03d}.png"), seg_to_color(segs[idx]))
# #                 print(f"Saved frame {idx} to {outdir}")
# #             else:
# #                 print("n/p/q/s ?")

# #     plt.close("all")
# #     if seg_win:
# #         cv2.destroyWindow(seg_win)

# # if __name__ == "__main__":
# #     main()


# # # python visualize_npy.py labeled_data/blocks/scenes/0b9d6be305284fd8a589bcb768d161b3_per_object.npz   --save-png --out png_out --show-seg


# # #!/usr/bin/env python3
# # import argparse
# # from pathlib import Path
# # import time
# # import sys

# # import numpy as np
# # import matplotlib.pyplot as plt
# # import cv2

# # # ---------------------------
# # # Utilities
# # # ---------------------------
# # def robust_depth_normalize(depth: np.ndarray):
# #     """Normalize depth to [0,1] for visualization (ignoring zeros)."""
# #     d = depth.astype(np.float32, copy=True)
# #     mask = d > 0
# #     if mask.any():
# #         vmin, vmax = np.percentile(d[mask], [2, 98])
# #         if vmax <= vmin:
# #             vmax = d[mask].max()
# #             vmin = d[mask].min()
# #         rng = max(vmax - vmin, 1e-6)
# #         d = np.clip((d - vmin) / rng, 0, 1)
# #     else:
# #         d[:] = 0
# #     return d

# # def guess_depth_key(files):
# #     for k in files:
# #         lk = k.lower()
# #         if "depth" in lk:
# #             return k
# #     return None

# # def guess_seg_key(files):
# #     for k in files:
# #         lk = k.lower()
# #         if "seg" in lk or "mask" in lk:
# #             return k
# #     return None

# # def guess_extr_key(files):
# #     for k in files:
# #         lk = k.lower()
# #         if "extr" in lk or "pose" in lk:
# #             return k
# #     return None

# # def load_bundle(input_path: Path):
# #     """
# #     Load as much as possible from:
# #       - .npz: loose key detection for depth/seg/extrinsics
# #       - dir : look for *depth*.npy, *seg*.npy, *extr*.npy
# #       - .npy: ints->seg, floats->depth
# #     Returns subset of {'depth_imgs','seg','extrinsics'}.
# #     """
# #     inp = Path(input_path)
# #     out = {}

# #     if inp.is_file():
# #         if inp.suffix == ".npz":
# #             data = np.load(inp, allow_pickle=True)
# #             files = list(data.files)
# #             dkey = guess_depth_key(files)
# #             skey = guess_seg_key(files)
# #             ekey = guess_extr_key(files)

# #             if dkey is None:
# #                 for k in files:
# #                     arr = data[k]
# #                     if arr.ndim in (2, 3) and np.issubdtype(arr.dtype, np.floating):
# #                         dkey = k
# #                         break
# #             if skey is None:
# #                 for k in files:
# #                     arr = data[k]
# #                     if arr.ndim in (2, 3, 4) and np.issubdtype(arr.dtype, np.integer):
# #                         skey = k
# #                         break

# #             if dkey is not None:
# #                 depth = data[dkey]
# #                 if depth.ndim == 2:
# #                     depth = depth[None, ...]
# #                 out["depth_imgs"] = depth.astype(np.float32)
# #             if skey is not None:
# #                 seg = data[skey]
# #                 if seg.ndim == 2:
# #                     seg = seg[None, ...]
# #                 out["seg"] = seg
# #             if ekey is not None:
# #                 out["extrinsics"] = data[ekey].astype(np.float32)

# #         elif inp.suffix == ".npy":
# #             arr = np.load(inp, allow_pickle=True)
# #             if np.issubdtype(arr.dtype, np.integer):
# #                 if arr.ndim == 2:
# #                     arr = arr[None, ...]
# #                 out["seg"] = arr
# #             else:
# #                 if arr.ndim == 2:
# #                     arr = arr[None, ...]
# #                 out["depth_imgs"] = arr.astype(np.float32)
# #         else:
# #             raise ValueError(f"Unsupported file type: {inp.suffix}")

# #     else:
# #         d = inp
# #         depth_paths = [p for p in [
# #             d / "depth_imgs.npy",
# #             *d.glob("*depth*.npy"),
# #             *d.glob("*Depth*.npy"),
# #         ] if p.exists()]
# #         seg_paths = [p for p in [
# #             d / "seg.npy",
# #             *d.glob("*seg*.npy"),
# #             *d.glob("*mask*.npy"),
# #             *d.glob("*Seg*.npy"),
# #         ] if p.exists()]
# #         extr_paths = [p for p in [
# #             d / "extrinsics.npy",
# #             *d.glob("*extr*.npy"),
# #             *d.glob("*pose*.npy"),
# #         ] if p.exists()]

# #         if depth_paths:
# #             depth = np.load(depth_paths[0])
# #             if depth.ndim == 2:
# #                 depth = depth[None, ...]
# #             out["depth_imgs"] = depth.astype(np.float32)
# #         if seg_paths:
# #             seg = np.load(seg_paths[0])
# #             if seg.ndim == 2:
# #                 seg = seg[None, ...]
# #             out["seg"] = seg
# #         if extr_paths:
# #             out["extrinsics"] = np.load(extr_paths[0]).astype(np.float32)

# #     if "depth_imgs" not in out and "seg" not in out:
# #         raise FileNotFoundError("No depth or segmentation arrays found.")
# #     return out

# # def save_depth_16bit_png(path: Path, depth: np.ndarray, scale_mm: float = 1000.0):
# #     depth_mm = np.clip(depth * scale_mm, 0, np.iinfo(np.uint16).max).astype(np.uint16)
# #     path.parent.mkdir(parents=True, exist_ok=True)
# #     cv2.imwrite(str(path), depth_mm)

# # def save_depth_viz_png(path: Path, depth: np.ndarray):
# #     d = (robust_depth_normalize(depth) * 255).astype(np.uint8)
# #     vis = cv2.applyColorMap(d, cv2.COLORMAP_TURBO)
# #     path.parent.mkdir(parents=True, exist_ok=True)
# #     cv2.imwrite(str(path), vis)

# # def labels_to_color(labels_2d: np.ndarray):
# #     """
# #     Colorize a 2D label map (0 = background).
# #     """
# #     ids = np.unique(labels_2d)
# #     rng = np.random.RandomState(1234)
# #     lut = {int(i): (int(rng.randint(0,256)),
# #                     int(rng.randint(0,256)),
# #                     int(rng.randint(0,256))) for i in ids if i != 0}
# #     h, w = labels_2d.shape
# #     rgb = np.zeros((h, w, 3), np.uint8)
# #     for i in ids:
# #         if i == 0:
# #             continue
# #         rgb[labels_2d == i] = lut[int(i)]
# #     return rgb

# # def per_object_to_labels(seg_khw: np.ndarray):
# #     """
# #     Convert per-object masks (K,H,W) to a single label image (H,W) with IDs 1..K.
# #     If multiple objects overlap, earlier indices win.
# #     """
# #     seg_khw = (seg_khw != 0)  # ensure boolean
# #     K, H, W = seg_khw.shape
# #     labels = np.zeros((H, W), dtype=np.uint16)
# #     for k in range(K):
# #         mask = seg_khw[k]
# #         labels[(labels == 0) & mask] = k + 1
# #     return labels

# # def seg_any_to_labels(seg):
# #     """
# #     Accept (H,W), (N,H,W) -> returns (H,W) for a chosen frame slice.
# #     Accept (K,H,W) -> fuse to labels 1..K.
# #     """
# #     if seg.ndim == 2:
# #         return seg.astype(np.uint16)
# #     elif seg.ndim == 3:
# #         # caller should pass seg[idx]; but if not, fuse across axis 0 as per-object
# #         return per_object_to_labels(seg)
# #     else:
# #         raise ValueError(f"Unexpected seg ndim: {seg.ndim}")

# # # ---------------------------
# # # Viewer
# # # ---------------------------
# # def main():
# #     ap = argparse.ArgumentParser()
# #     ap.add_argument("input", type=Path, help="Path to .npz/.npy or a directory")
# #     ap.add_argument("--delay", type=float, default=1.0, help="Seconds between frames in autoplay")
# #     ap.add_argument("--autoplay", action="store_true", help="Automatically cycle through frames")
# #     ap.add_argument("--save-png", action="store_true", help="Export PNGs for all frames")
# #     ap.add_argument("--out", type=Path, default=Path("png_out"), help="Output directory for PNG export")
# #     ap.add_argument("--mm-scale", type=float, default=1000.0, help="Depth meters->millimeters scale for 16-bit PNG")
# #     ap.add_argument("--show-seg", action="store_true", help="If seg present, show a window with colored labels")
# #     ap.add_argument("--save-individual-masks", action="store_true",
# #                     help="If seg is per-object (N,K,H,W), also save each object's mask as its own PNG")
# #     args = ap.parse_args()

# #     bundle = load_bundle(args.input)
# #     depths = bundle.get("depth_imgs", None)   # (N,H,W) float32 or None
# #     segs   = bundle.get("seg", None)          # (N,H,W) or (N,K,H,W) int or None
# #     extr   = bundle.get("extrinsics", None)

# #     if depths is not None:
# #         print(f"Loaded depth: {depths.shape} (N,H,W)")
# #     if segs is not None:
# #         print(f"Loaded seg:   {segs.shape} (N,H,W) or (N,K,H,W)")
# #     if extr is not None:
# #         print(f"Extrinsics:   {extr.shape}")

# #     # Determine frame count
# #     n_depth = depths.shape[0] if depths is not None else 0
# #     if segs is None:
# #         n_seg = 0
# #     else:
# #         n_seg = segs.shape[0]  # works for both (N,H,W) and (N,K,H,W)
# #     N = max(n_depth, n_seg)
# #     if N == 0:
# #         print("Nothing to display.")
# #         return

# #     # Prepare windows
# #     plt.ion()
# #     have_depth_view = depths is not None
# #     if have_depth_view:
# #         fig, ax = plt.subplots(num="Depth (normalized colormap)")
# #         im = ax.imshow(robust_depth_normalize(depths[0]), cmap="turbo", vmin=0, vmax=1)
# #         ax.set_title("Depth (normalized) — frame 0")
# #         plt.show(block=False)
# #     else:
# #         fig = ax = None

# #     seg_win = None
# #     if args.show_seg and segs is not None:
# #         seg_win = "Segmentation (colored)"
# #         cv2.namedWindow(seg_win, cv2.WINDOW_NORMAL)
# #         # First frame seg to colored
# #         seg0 = segs[0]
# #         if seg0.ndim == 3:   # (K,H,W) per-object
# #             label0 = per_object_to_labels(seg0)
# #         elif seg0.ndim == 2: # (H,W)
# #             label0 = seg0.astype(np.uint16)
# #         else:
# #             raise ValueError(f"Unexpected seg slice ndim: {seg0.ndim}")
# #         cv2.imshow(seg_win, labels_to_color(label0))
# #         cv2.waitKey(1)

# #     def update_frame(idx):
# #         if have_depth_view:
# #             d_idx = idx if n_depth > 0 else 0
# #             d_idx %= max(n_depth, 1)
# #             ax.images[0].set_data(robust_depth_normalize(depths[d_idx]))
# #             ax.set_title(f"Depth (normalized) — frame {d_idx}")
# #             fig.canvas.draw_idle()
# #             fig.canvas.flush_events()
# #         if seg_win and segs is not None:
# #             s_idx = idx if n_seg > 0 else 0
# #             s_idx %= max(n_seg, 1)
# #             seg_slice = segs[s_idx]
# #             if seg_slice.ndim == 3:   # (K,H,W)
# #                 labels = per_object_to_labels(seg_slice)
# #             else:                     # (H,W)
# #                 labels = seg_slice.astype(np.uint16)
# #             cv2.imshow(seg_win, labels_to_color(labels))
# #             cv2.waitKey(1)

# #     # Bulk export
# #     if args.save_png:
# #         outdir = args.out
# #         outdir.mkdir(parents=True, exist_ok=True)
# #         for i in range(N):
# #             if depths is not None and i < n_depth:
# #                 save_depth_16bit_png(outdir / f"depth_{i:03d}.png", depths[i], scale_mm=args.mm_scale)
# #                 save_depth_viz_png(outdir / f"depth_viz_{i:03d}.png", depths[i])
# #             if segs is not None and i < n_seg:
# #                 seg_i = segs[i]
# #                 if seg_i.ndim == 3:
# #                     # per-object -> fuse to label map + optionally save individual masks
# #                     labels = per_object_to_labels(seg_i)
# #                     cv2.imwrite(str(outdir / f"seg_labels_{i:03d}.png"), labels)
# #                     cv2.imwrite(str(outdir / f"seg_labels_viz_{i:03d}.png"), labels_to_color(labels))
# #                     if args.save_individual_masks:
# #                         obj_dir = outdir / f"seg_objects_{i:03d}"
# #                         obj_dir.mkdir(parents=True, exist_ok=True)
# #                         K = seg_i.shape[0]
# #                         for k in range(K):
# #                             mask = (seg_i[k] != 0).astype(np.uint8) * 255
# #                             cv2.imwrite(str(obj_dir / f"obj_{k+1:02d}.png"), mask)
# #                 else:
# #                     labels = seg_i.astype(np.uint16)
# #                     cv2.imwrite(str(outdir / f"seg_{i:03d}.png"), labels)
# #                     cv2.imwrite(str(outdir / f"seg_viz_{i:03d}.png"), labels_to_color(labels))
# #         print(f"Saved PNGs to: {outdir.resolve()}")

# #     idx = 0
# #     update_frame(idx)

# #     if args.autoplay:
# #         try:
# #             while True:
# #                 time.sleep(args.delay)
# #                 idx = (idx + 1) % N
# #                 update_frame(idx)
# #         except KeyboardInterrupt:
# #             pass
# #     else:
# #         if have_depth_view or (args.show_seg and segs is not None):
# #             print("Controls: n=next, p=prev, q=quit, s=save current PNGs")
# #         else:
# #             print("Nothing to interact with (no depth view and --show-seg not set). Exiting.")
# #             return

# #         while True:
# #             try:
# #                 ch = input("> ").strip().lower()
# #             except EOFError:
# #                 break
# #             if ch == "q":
# #                 break
# #             elif ch == "n":
# #                 idx = (idx + 1) % N
# #                 update_frame(idx)
# #             elif ch == "p":
# #                 idx = (idx - 1) % N
# #                 update_frame(idx)
# #             elif ch == "s":
# #                 outdir = args.out
# #                 outdir.mkdir(parents=True, exist_ok=True)
# #                 if depths is not None and idx < n_depth:
# #                     save_depth_16bit_png(outdir / f"depth_{idx:03d}.png", depths[idx], scale_mm=args.mm_scale)
# #                     save_depth_viz_png(outdir / f"depth_viz_{idx:03d}.png", depths[idx])
# #                 if segs is not None and idx < n_seg:
# #                     seg_i = segs[idx]
# #                     if seg_i.ndim == 3:
# #                         labels = per_object_to_labels(seg_i)
# #                         cv2.imwrite(str(outdir / f"seg_labels_{idx:03d}.png"), labels)
# #                         cv2.imwrite(str(outdir / f"seg_labels_viz_{idx:03d}.png"), labels_to_color(labels))
# #                     else:
# #                         labels = seg_i.astype(np.uint16)
# #                         cv2.imwrite(str(outdir / f"seg_{idx:03d}.png"), labels)
# #                         cv2.imwrite(str(outdir / f"seg_viz_{idx:03d}.png"), labels_to_color(labels))
# #                 print(f"Saved frame {idx} to {outdir}")
# #             else:
# #                 print("n/p/q/s ?")

# #     plt.close("all")
# #     if seg_win:
# #         cv2.destroyWindow(seg_win)

# # if __name__ == "__main__":
# #     main()


# #####

# #!/usr/bin/env python3
# import argparse
# from pathlib import Path
# import time
# import sys

# import numpy as np
# import matplotlib.pyplot as plt
# import cv2

# # ---------------------------
# # Utilities
# # ---------------------------
# def robust_depth_normalize(depth: np.ndarray):
#     """Normalize depth to [0,1] for visualization (ignoring zeros)."""
#     d = depth.astype(np.float32, copy=True)
#     mask = d > 0
#     if mask.any():
#         vmin, vmax = np.percentile(d[mask], [2, 98])
#         if vmax <= vmin:
#             vmax = float(d[mask].max())
#             vmin = float(d[mask].min())
#         rng = max(vmax - vmin, 1e-6)
#         d = np.clip((d - vmin) / rng, 0, 1)
#     else:
#         d[:] = 0
#     return d

# def guess_depth_key(files):
#     for k in files:
#         lk = k.lower()
#         if "depth" in lk:
#             return k
#     return None

# def guess_seg_key(files):
#     # prefer full-scene seg if both are present
#     for pref in ["seg_imgs", "seg"]:
#         if pref in files:
#             return pref
#     for k in files:
#         lk = k.lower()
#         if "seg" in lk and "per_obj" not in lk and "mask" not in lk:
#             return k
#     # fallback: any integer-looking array
#     return None

# def guess_extr_key(files):
#     for k in files:
#         lk = k.lower()
#         if "extr" in lk or "pose" in lk:
#             return k
#     return None

# def load_bundle(input_path: Path):
#     """
#     Load as much as possible from:
#       - .npz: loose key detection for depth/seg/extrinsics (+ per_obj_masks, angles if present)
#       - dir : look for *depth*.npy, *seg*.npy, *extr*.npy
#       - .npy: ints->seg, floats->depth
#     Returns a dict subset of:
#       {
#         'depth_imgs': (N,H,W) float32,
#         'seg':        (N,H,W) uint{16,32},
#         'extrinsics': (N,7)   float32,
#         'per_obj_masks': (N,K,H,W) uint8,
#         'obj_uids':   (K,) int32,
#         'view_theta_deg': (N,) float32,
#         'view_phi_deg':   (N,) float32,
#         'scene_id': str
#       }
#     """
#     inp = Path(input_path)
#     out = {}

#     if inp.is_file():
#         if inp.suffix == ".npz":
#             data = np.load(inp, allow_pickle=True)
#             files = list(data.files)

#             # Optional direct keys
#             if "depth_imgs" in files:
#                 d = data["depth_imgs"]
#                 if d.ndim == 2: d = d[None, ...]
#                 out["depth_imgs"] = d.astype(np.float32)

#             if "seg_imgs" in files:
#                 s = data["seg_imgs"]
#                 if s.ndim == 2: s = s[None, ...]
#                 out["seg"] = s

#             if "per_obj_masks" in files:
#                 pom = data["per_obj_masks"]
#                 # expect (N,K,H,W) or (K,H,W). Normalize to (N,K,H,W)
#                 if pom.ndim == 3:
#                     pom = pom[None, ...]
#                 out["per_obj_masks"] = pom.astype(np.uint8)

#             if "obj_uids" in files:
#                 out["obj_uids"] = data["obj_uids"].astype(np.int32)

#             if "extrinsics" in files:
#                 out["extrinsics"] = data["extrinsics"].astype(np.float32)

#             # Angle metadata for naming
#             if "view_theta_deg" in files:
#                 out["view_theta_deg"] = data["view_theta_deg"].astype(np.float32)
#             if "view_phi_deg" in files:
#                 out["view_phi_deg"] = data["view_phi_deg"].astype(np.float32)

#             if "scene_id" in files:
#                 # may be stored as 0-d array
#                 sid = data["scene_id"]
#                 if isinstance(sid, np.ndarray):
#                     sid = sid.item()
#                 out["scene_id"] = str(sid)

#             # If some standard keys are missing, try to guess
#             if "depth_imgs" not in out:
#                 dkey = guess_depth_key(files)
#                 if dkey is not None:
#                     d = data[dkey]
#                     if d.ndim == 2: d = d[None, ...]
#                     out["depth_imgs"] = d.astype(np.float32)

#             if "seg" not in out:
#                 skey = guess_seg_key(files)
#                 if skey is not None:
#                     s = data[skey]
#                     if s.ndim == 2: s = s[None, ...]
#                     out["seg"] = s

#             if "extrinsics" not in out:
#                 ekey = guess_extr_key(files)
#                 if ekey is not None:
#                     out["extrinsics"] = data[ekey].astype(np.float32)

#         elif inp.suffix == ".npy":
#             arr = np.load(inp, allow_pickle=True)
#             if np.issubdtype(arr.dtype, np.integer):
#                 if arr.ndim == 2: arr = arr[None, ...]
#                 out["seg"] = arr
#             else:
#                 if arr.ndim == 2: arr = arr[None, ...]
#                 out["depth_imgs"] = arr.astype(np.float32)
#         else:
#             raise ValueError(f"Unsupported file type: {inp.suffix}")

#     else:
#         d = inp
#         depth_paths = [p for p in [
#             d / "depth_imgs.npy",
#             *d.glob("*depth*.npy"),
#             *d.glob("*Depth*.npy"),
#         ] if p.exists()]
#         seg_paths = [p for p in [
#             d / "seg_imgs.npy",
#             d / "seg.npy",
#             *d.glob("*seg*.npy"),
#             *d.glob("*mask*.npy"),
#             *d.glob("*Seg*.npy"),
#         ] if p.exists()]
#         extr_paths = [p for p in [
#             d / "extrinsics.npy",
#             *d.glob("*extr*.npy"),
#             *d.glob("*pose*.npy"),
#         ] if p.exists()]
#         perobj_paths = [p for p in [
#             d / "per_obj_masks.npy",
#             *d.glob("*per_object*.npy"),
#             *d.glob("*per_obj*.npy"),
#         ] if p.exists()]
#         theta_paths = [p for p in [
#             d / "view_theta_deg.npy",
#         ] if p.exists()]
#         phi_paths = [p for p in [
#             d / "view_phi_deg.npy",
#         ] if p.exists()]

#         if depth_paths:
#             depth = np.load(depth_paths[0])
#             if depth.ndim == 2: depth = depth[None, ...]
#             out["depth_imgs"] = depth.astype(np.float32)
#         if seg_paths:
#             seg = np.load(seg_paths[0])
#             if seg.ndim == 2: seg = seg[None, ...]
#             out["seg"] = seg
#         if extr_paths:
#             out["extrinsics"] = np.load(extr_paths[0]).astype(np.float32)
#         if perobj_paths:
#             pom = np.load(perobj_paths[0])
#             if pom.ndim == 3: pom = pom[None, ...]
#             out["per_obj_masks"] = pom.astype(np.uint8)
#         if theta_paths:
#             out["view_theta_deg"] = np.load(theta_paths[0]).astype(np.float32)
#         if phi_paths:
#             out["view_phi_deg"] = np.load(phi_paths[0]).astype(np.float32)

#     if "depth_imgs" not in out and "seg" not in out and "per_obj_masks" not in out:
#         raise FileNotFoundError("No depth, segmentation, or per-object masks found.")
#     return out

# def save_depth_16bit_png(path: Path, depth: np.ndarray, scale_mm: float = 1000.0):
#     depth_mm = np.clip(depth * scale_mm, 0, np.iinfo(np.uint16).max).astype(np.uint16)
#     path.parent.mkdir(parents=True, exist_ok=True)
#     cv2.imwrite(str(path), depth_mm)

# def save_depth_viz_png(path: Path, depth: np.ndarray):
#     d = (robust_depth_normalize(depth) * 255).astype(np.uint8)
#     vis = cv2.applyColorMap(d, cv2.COLORMAP_TURBO)
#     path.parent.mkdir(parents=True, exist_ok=True)
#     cv2.imwrite(str(path), vis)

# def labels_to_color(labels_2d: np.ndarray):
#     """
#     Colorize a 2D label map (0 = background).
#     """
#     ids = np.unique(labels_2d)
#     rng = np.random.RandomState(1234)
#     lut = {int(i): (int(rng.randint(0,256)),
#                     int(rng.randint(0,256)),
#                     int(rng.randint(0,256))) for i in ids if i != 0}
#     h, w = labels_2d.shape
#     rgb = np.zeros((h, w, 3), np.uint8)
#     for i in ids:
#         if i == 0:
#             continue
#         rgb[labels_2d == i] = lut[int(i)]
#     return rgb

# def per_object_to_labels(seg_khw: np.ndarray):
#     """
#     Convert per-object masks (K,H,W) to a single label image (H,W) with IDs 1..K.
#     If multiple objects overlap, earlier indices win.
#     """
#     seg_khw = (seg_khw != 0)  # ensure boolean
#     K, H, W = seg_khw.shape
#     labels = np.zeros((H, W), dtype=np.uint16)
#     for k in range(K):
#         mask = seg_khw[k]
#         labels[(labels == 0) & mask] = k + 1
#     return labels

# def seg_any_to_labels(seg):
#     """
#     Accept (H,W), (N,H,W) -> returns (H,W) for a chosen frame slice.
#     Accept (K,H,W) -> fuse to labels 1..K.
#     """
#     if seg.ndim == 2:
#         return seg.astype(np.uint16)
#     elif seg.ndim == 3:
#         return per_object_to_labels(seg)
#     else:
#         raise ValueError(f"Unexpected seg ndim: {seg.ndim}")

# def angle_tag(theta_deg_array, i):
#     """Return the integer angle tag for frame i, or i if not available."""
#     if theta_deg_array is None:
#         return f"{i:03d}"
#     val = float(theta_deg_array[i])
#     return f"{int(round(val))}"

# # ---------------------------
# # Viewer
# # ---------------------------
# def main():
#     ap = argparse.ArgumentParser()
#     ap.add_argument("input", type=Path, help="Path to .npz/.npy or a directory (supports *_all.npz)")
#     ap.add_argument("--delay", type=float, default=1.0, help="Seconds between frames in autoplay")
#     ap.add_argument("--autoplay", action="store_true", help="Automatically cycle through frames")
#     ap.add_argument("--save-png", action="store_true", help="Export PNGs for all frames")
#     ap.add_argument("--out", type=Path, default=Path("png_out"), help="Output directory for PNG export")
#     ap.add_argument("--mm-scale", type=float, default=1000.0, help="Depth meters->millimeters scale for 16-bit PNG")
#     ap.add_argument("--show-seg", action="store_true", help="If seg present, show a window with colored labels")
#     ap.add_argument("--save-individual-masks", action="store_true",
#                     help="If per_obj_masks present, also save each object's mask per view as <angle>_<idx>.png")
#     args = ap.parse_args()

#     bundle = load_bundle(args.input)
#     depths = bundle.get("depth_imgs", None)        # (N,H,W) float32 or None
#     segs   = bundle.get("seg", None)               # (N,H,W) int or None (full-scene)
#     extr   = bundle.get("extrinsics", None)
#     per_obj_masks = bundle.get("per_obj_masks", None)  # (N,K,H,W) uint8 or None
#     obj_uids = bundle.get("obj_uids", None)

#     theta_deg = bundle.get("view_theta_deg", None) # (N,) float32 or None

#     if depths is not None:
#         print(f"Loaded depth:        {depths.shape} (N,H,W)")
#     if segs is not None:
#         print(f"Loaded scene seg:    {segs.shape} (N,H,W)")
#     if per_obj_masks is not None:
#         print(f"Loaded per-obj masks:{per_obj_masks.shape} (N,K,H,W)")
#     if extr is not None:
#         print(f"Extrinsics:          {extr.shape}")
#     if theta_deg is not None:
#         print(f"Angles (theta°):     {theta_deg.shape}")

#     # Determine frame count (N)
#     n_depth = depths.shape[0] if depths is not None else 0
#     n_seg = segs.shape[0] if segs is not None else 0
#     n_pom = per_obj_masks.shape[0] if per_obj_masks is not None else 0
#     N = max(n_depth, n_seg, n_pom)
#     if N == 0:
#         print("Nothing to display.")
#         return

#     # Prepare windows
#     plt.ion()
#     have_depth_view = depths is not None
#     if have_depth_view:
#         fig, ax = plt.subplots(num="Depth (normalized colormap)")
#         im = ax.imshow(robust_depth_normalize(depths[0]), cmap="turbo", vmin=0, vmax=1)
#         ax.set_title("Depth (normalized) — frame 0")
#         plt.show(block=False)
#     else:
#         fig = ax = None

#     seg_win = None
#     if args.show_seg and (segs is not None or per_obj_masks is not None):
#         seg_win = "Segmentation (colored)"
#         cv2.namedWindow(seg_win, cv2.WINDOW_NORMAL)
#         # First frame: prefer full-scene seg for the colored window; else fuse per-obj
#         if segs is not None:
#             label0 = segs[0].astype(np.uint16)
#         else:
#             label0 = per_object_to_labels(per_obj_masks[0])
#         cv2.imshow(seg_win, labels_to_color(label0))
#         cv2.waitKey(1)

#     def update_frame(idx):
#         if have_depth_view:
#             d_idx = idx % max(n_depth, 1)
#             ax.images[0].set_data(robust_depth_normalize(depths[d_idx]))
#             ax.set_title(f"Depth (normalized) — frame {d_idx}")
#             fig.canvas.draw_idle()
#             fig.canvas.flush_events()
#         if seg_win:
#             # Prefer showing the full scene seg, else fuse per-object masks.
#             if segs is not None:
#                 s_idx = idx % max(n_seg, 1)
#                 labels = segs[s_idx].astype(np.uint16)
#             else:
#                 p_idx = idx % max(n_pom, 1)
#                 labels = per_object_to_labels(per_obj_masks[p_idx])
#             cv2.imshow(seg_win, labels_to_color(labels))
#             cv2.waitKey(1)

#     # ---------- Bulk export ----------
#     if args.save_png:
#         outdir = args.out
#         outdir.mkdir(parents=True, exist_ok=True)
#         for i in range(N):
#             tag = angle_tag(theta_deg, i)  # angle in degrees (int) if available, else index
#             # Depth exports (kept by index as before, can be long)
#             if depths is not None and i < n_depth:
#                 save_depth_16bit_png(outdir / f"depth_{i:03d}.png", depths[i], scale_mm=args.mm_scale)
#                 save_depth_viz_png(outdir / f"depth_viz_{i:03d}.png", depths[i])

#             # Whole-scene segmentation image for this view: <angle>_scene.png
#             if segs is not None and i < n_seg:
#                 scene_labels = segs[i].astype(np.uint16)
#                 # Save a colored visualization for convenience:
#                 cv2.imwrite(str(outdir / f"{tag}_scene.png"), labels_to_color(scene_labels))

#             # Per-object masks for this view: <angle>_<obj-idx:03d>.png
#             # Only if we have per_obj_masks, otherwise you can skip/disable
#             if per_obj_masks is not None and i < n_pom:
#                 K = per_obj_masks.shape[1]
#                 for k in range(K):
#                     mask = (per_obj_masks[i, k] != 0).astype(np.uint8) * 255
#                     cv2.imwrite(str(outdir / f"{tag}_{k+1:03d}.png"), mask)

#         print(f"Saved PNGs to: {outdir.resolve()}")

#     # ---------- Interactive viewer ----------
#     idx = 0
#     update_frame(idx)

#     if args.autoplay:
#         try:
#             while True:
#                 time.sleep(args.delay)
#                 idx = (idx + 1) % N
#                 update_frame(idx)
#         except KeyboardInterrupt:
#             pass
#     else:
#         if have_depth_view or (args.show_seg and (segs is not None or per_obj_masks is not None)):
#             print("Controls: n=next, p=prev, q=quit, s=save current PNGs")
#         else:
#             print("Nothing to interact with (no depth view and --show-seg not set). Exiting.")
#             return

#         while True:
#             try:
#                 ch = input("> ").strip().lower()
#             except EOFError:
#                 break
#             if ch == "q":
#                 break
#             elif ch == "n":
#                 idx = (idx + 1) % N
#                 update_frame(idx)
#             elif ch == "p":
#                 idx = (idx - 1) % N
#                 update_frame(idx)
#             elif ch == "s":
#                 outdir = args.out
#                 outdir.mkdir(parents=True, exist_ok=True)
#                 tag = angle_tag(theta_deg, idx)
#                 if depths is not None and idx < n_depth:
#                     save_depth_16bit_png(outdir / f"depth_{idx:03d}.png", depths[idx], scale_mm=args.mm_scale)
#                     save_depth_viz_png(outdir / f"depth_viz_{idx:03d}.png", depths[idx])
#                 # Save current scene seg and per-obj masks with angle-based names
#                 if segs is not None and idx < n_seg:
#                     labels = segs[idx].astype(np.uint16)
#                     cv2.imwrite(str(outdir / f"{tag}_scene.png"), labels_to_color(labels))
#                 if per_obj_masks is not None and idx < n_pom:
#                     K = per_obj_masks.shape[1]
#                     for k in range(K):
#                         mask = (per_obj_masks[idx, k] != 0).astype(np.uint8) * 255
#                         cv2.imwrite(str(outdir / f"{tag}_{k+1:03d}.png"), mask)
#                 print(f"Saved frame {idx} to {outdir}")
#             else:
#                 print("n/p/q/s ?")

#     plt.close("all")
#     cv2.destroyAllWindows()

# if __name__ == "__main__":
#     main()




#!/usr/bin/env python3
import argparse
from pathlib import Path
import time
import sys

import numpy as np
import matplotlib.pyplot as plt
import cv2

# ---------------------------
# Utilities
# ---------------------------
def robust_depth_normalize(depth: np.ndarray):
    """Normalize depth to [0,1] for visualization (ignoring zeros)."""
    d = depth.astype(np.float32, copy=True)
    mask = d > 0
    if mask.any():
        vmin, vmax = np.percentile(d[mask], [2, 98])
        if vmax <= vmin:
            vmax = float(d[mask].max())
            vmin = float(d[mask].min())
        rng = max(vmax - vmin, 1e-6)
        d = np.clip((d - vmin) / rng, 0, 1)
    else:
        d[:] = 0
    return d

def guess_depth_key(files):
    for k in files:
        lk = k.lower()
        if "depth" in lk:
            return k
    return None

def guess_seg_key(files):
    # prefer full-scene seg if both are present
    for pref in ["seg_imgs", "seg"]:
        if pref in files:
            return pref
    for k in files:
        lk = k.lower()
        if "seg" in lk and "per_obj" not in lk and "mask" not in lk:
            return k
    # fallback: any integer-looking array
    return None

def guess_extr_key(files):
    for k in files:
        lk = k.lower()
        if "extr" in lk or "pose" in lk:
            return k
    return None

def load_bundle(input_path: Path):
    """
    Load as much as possible from:
      - .npz: loose key detection for depth/seg/extrinsics (+ per_obj_masks, angles if present)
      - dir : look for *depth*.npy, *seg*.npy, *extr*.npy
      - .npy: ints->seg, floats->depth
    Returns a dict subset of:
      {
        'depth_imgs': (N,H,W) float32,
        'seg':        (N,H,W) uint{16,32},
        'extrinsics': (N,7)   float32,
        'per_obj_masks': (N,K,H,W) uint8,
        'per_obj_seg_uids': (N,K,H,W) int32,
        'uid_color_lut': (K,4) uint8,
        'obj_uids':   (K,) int32,
        'view_theta_deg': (N,) float32,
        'view_phi_deg':   (N,) float32,
        'scene_id': str
      }
    """
    inp = Path(input_path)
    out = {}

    if inp.is_file():
        if inp.suffix == ".npz":
            data = np.load(inp, allow_pickle=True)
            files = list(data.files)

            # Optional direct keys
            if "depth_imgs" in files:
                d = data["depth_imgs"]
                if d.ndim == 2: d = d[None, ...]
                out["depth_imgs"] = d.astype(np.float32)

            if "seg_imgs" in files:
                s = data["seg_imgs"]
                if s.ndim == 2: s = s[None, ...]
                out["seg"] = s

            if "per_obj_masks" in files:
                pom = data["per_obj_masks"]
                # expect (N,K,H,W) or (K,H,W). Normalize to (N,K,H,W)
                if pom.ndim == 3:
                    pom = pom[None, ...]
                out["per_obj_masks"] = pom.astype(np.uint8)

            if "per_obj_seg_uids" in files:
                posu = data["per_obj_seg_uids"]
                if posu.ndim == 3:
                    posu = posu[None, ...]
                out["per_obj_seg_uids"] = posu.astype(np.int32)

            if "uid_color_lut" in files:
                out["uid_color_lut"] = data["uid_color_lut"].astype(np.uint8)

            if "obj_uids" in files:
                out["obj_uids"] = data["obj_uids"].astype(np.int32)

            if "extrinsics" in files:
                out["extrinsics"] = data["extrinsics"].astype(np.float32)

            # Angle metadata for naming
            if "view_theta_deg" in files:
                out["view_theta_deg"] = data["view_theta_deg"].astype(np.float32)
            if "view_phi_deg" in files:
                out["view_phi_deg"] = data["view_phi_deg"].astype(np.float32)

            if "scene_id" in files:
                # may be stored as 0-d array
                sid = data["scene_id"]
                if isinstance(sid, np.ndarray):
                    sid = sid.item()
                out["scene_id"] = str(sid)

            # If some standard keys are missing, try to guess
            if "depth_imgs" not in out:
                dkey = guess_depth_key(files)
                if dkey is not None:
                    d = data[dkey]
                    if d.ndim == 2: d = d[None, ...]
                    out["depth_imgs"] = d.astype(np.float32)

            if "seg" not in out:
                skey = guess_seg_key(files)
                if skey is not None:
                    s = data[skey]
                    if s.ndim == 2: s = s[None, ...]
                    out["seg"] = s

            if "extrinsics" not in out:
                ekey = guess_extr_key(files)
                if ekey is not None:
                    out["extrinsics"] = data[ekey].astype(np.float32)

        elif inp.suffix == ".npy":
            arr = np.load(inp, allow_pickle=True)
            if np.issubdtype(arr.dtype, np.integer):
                if arr.ndim == 2: arr = arr[None, ...]
                out["seg"] = arr
            else:
                if arr.ndim == 2: arr = arr[None, ...]
                out["depth_imgs"] = arr.astype(np.float32)
        else:
            raise ValueError(f"Unsupported file type: {inp.suffix}")

    else:
        d = inp
        depth_paths = [p for p in [
            d / "depth_imgs.npy",
            *d.glob("*depth*.npy"),
            *d.glob("*Depth*.npy"),
        ] if p.exists()]
        seg_paths = [p for p in [
            d / "seg_imgs.npy",
            d / "seg.npy",
            *d.glob("*seg*.npy"),
            *d.glob("*mask*.npy"),
            *d.glob("*Seg*.npy"),
        ] if p.exists()]
        extr_paths = [p for p in [
            d / "extrinsics.npy",
            *d.glob("*extr*.npy"),
            *d.glob("*pose*.npy"),
        ] if p.exists()]
        perobj_paths = [p for p in [
            d / "per_obj_masks.npy",
            *d.glob("*per_object*.npy"),
            *d.glob("*per_obj*.npy"),
        ] if p.exists()]
        theta_paths = [p for p in [
            d / "view_theta_deg.npy",
        ] if p.exists()]
        phi_paths = [p for p in [
            d / "view_phi_deg.npy",
        ] if p.exists()]

        if depth_paths:
            depth = np.load(depth_paths[0])
            if depth.ndim == 2: depth = depth[None, ...]
            out["depth_imgs"] = depth.astype(np.float32)
        if seg_paths:
            seg = np.load(seg_paths[0])
            if seg.ndim == 2: seg = seg[None, ...]
            out["seg"] = seg
        if extr_paths:
            out["extrinsics"] = np.load(extr_paths[0]).astype(np.float32)
        if perobj_paths:
            pom = np.load(perobj_paths[0])
            if pom.ndim == 3: pom = pom[None, ...]
            out["per_obj_masks"] = pom.astype(np.uint8)
        if theta_paths:
            out["view_theta_deg"] = np.load(theta_paths[0]).astype(np.float32)
        if phi_paths:
            out["view_phi_deg"] = np.load(phi_paths[0]).astype(np.float32)

    if "depth_imgs" not in out and "seg" not in out and "per_obj_masks" not in out:
        raise FileNotFoundError("No depth, segmentation, or per-object masks found.")
    return out

def save_depth_16bit_png(path: Path, depth: np.ndarray, scale_mm: float = 1000.0):
    depth_mm = np.clip(depth * scale_mm, 0, np.iinfo(np.uint16).max).astype(np.uint16)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), depth_mm)

def save_depth_viz_png(path: Path, depth: np.ndarray):
    d = (robust_depth_normalize(depth) * 255).astype(np.uint8)
    vis = cv2.applyColorMap(d, cv2.COLORMAP_TURBO)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), vis)

def labels_to_color_with_lut(labels_2d: np.ndarray, uid_color_lut: np.ndarray, obj_uids: np.ndarray):
    """
    Colorize a 2D label map using the provided UID color lookup table.
    labels_2d: (H,W) array where values are UIDs (0 = background)
    uid_color_lut: (K,4) RGBA colors
    obj_uids: (K,) UIDs corresponding to rows in uid_color_lut
    """
    h, w = labels_2d.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Create UID -> color mapping
    uid_to_color = {}
    for i, uid in enumerate(obj_uids):
        uid_to_color[int(uid)] = uid_color_lut[i, :3]  # RGB only
    
    # Apply colors
    for uid, color in uid_to_color.items():
        mask = (labels_2d == uid)
        rgb[mask] = color
    
    return rgb

def labels_to_color(labels_2d: np.ndarray):
    """
    Fallback: Colorize a 2D label map (0 = background) with random colors.
    Used when uid_color_lut is not available.
    """
    ids = np.unique(labels_2d)
    rng = np.random.RandomState(1234)
    lut = {int(i): (int(rng.randint(0,256)),
                    int(rng.randint(0,256)),
                    int(rng.randint(0,256))) for i in ids if i != 0}
    h, w = labels_2d.shape
    rgb = np.zeros((h, w, 3), np.uint8)
    for i in ids:
        if i == 0:
            continue
        rgb[labels_2d == i] = lut[int(i)]
    return rgb

def per_object_to_labels(seg_khw: np.ndarray, obj_uids: np.ndarray = None):
    """
    Convert per-object masks (K,H,W) to a single label image (H,W).
    If obj_uids is provided, use UIDs as labels; otherwise use indices 1..K.
    If multiple objects overlap, earlier indices win.
    """
    seg_khw = (seg_khw != 0)  # ensure boolean
    K, H, W = seg_khw.shape
    labels = np.zeros((H, W), dtype=np.int32)
    
    for k in range(K):
        mask = seg_khw[k]
        if obj_uids is not None:
            label_val = int(obj_uids[k])
        else:
            label_val = k + 1
        labels[(labels == 0) & mask] = label_val
    
    return labels

def per_object_seg_uids_to_labels(seg_uids_khw: np.ndarray):
    """
    Convert per-object UID-labeled masks (K,H,W) to a single label image (H,W).
    Each (K,H,W) slice contains UID values where the object is present, 0 elsewhere.
    Combine by taking max across K dimension (assumes no overlap).
    """
    # Take the maximum UID value across all object layers
    labels = np.max(seg_uids_khw, axis=0).astype(np.int32)
    return labels

def seg_any_to_labels(seg, obj_uids=None):
    """
    Accept (H,W), (N,H,W) -> returns (H,W) for a chosen frame slice.
    Accept (K,H,W) -> fuse to labels with UIDs if available.
    """
    if seg.ndim == 2:
        return seg.astype(np.int32)
    elif seg.ndim == 3:
        return per_object_to_labels(seg, obj_uids)
    else:
        raise ValueError(f"Unexpected seg ndim: {seg.ndim}")

def angle_tag(theta_deg_array, i):
    """Return the integer angle tag for frame i, or i if not available."""
    if theta_deg_array is None:
        return f"{i:03d}"
    val = float(theta_deg_array[i])
    return f"{int(round(val))}"

# ---------------------------
# Viewer
# ---------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="Path to .npz/.npy or a directory (supports *_all.npz)")
    ap.add_argument("--delay", type=float, default=1.0, help="Seconds between frames in autoplay")
    ap.add_argument("--autoplay", action="store_true", help="Automatically cycle through frames")
    ap.add_argument("--save-png", action="store_true", help="Export PNGs for all frames")
    ap.add_argument("--out", type=Path, default=Path("png_out"), help="Output directory for PNG export")
    ap.add_argument("--mm-scale", type=float, default=1000.0, help="Depth meters->millimeters scale for 16-bit PNG")
    ap.add_argument("--show-seg", action="store_true", help="If seg present, show a window with colored labels")
    ap.add_argument("--save-individual-masks", action="store_true",
                    help="If per_obj_masks present, also save each object's mask per view as <angle>_<idx>.png")
    args = ap.parse_args()

    bundle = load_bundle(args.input)
    depths = bundle.get("depth_imgs", None)        # (N,H,W) float32 or None
    segs   = bundle.get("seg", None)               # (N,H,W) int or None (full-scene)
    extr   = bundle.get("extrinsics", None)
    per_obj_masks = bundle.get("per_obj_masks", None)  # (N,K,H,W) uint8 or None
    per_obj_seg_uids = bundle.get("per_obj_seg_uids", None)  # (N,K,H,W) int32 or None
    uid_color_lut = bundle.get("uid_color_lut", None)  # (K,4) uint8 or None
    obj_uids = bundle.get("obj_uids", None)

    theta_deg = bundle.get("view_theta_deg", None) # (N,) float32 or None

    if depths is not None:
        print(f"Loaded depth:        {depths.shape} (N,H,W)")
    if segs is not None:
        print(f"Loaded scene seg:    {segs.shape} (N,H,W)")
    if per_obj_masks is not None:
        print(f"Loaded per-obj masks:{per_obj_masks.shape} (N,K,H,W)")
    if per_obj_seg_uids is not None:
        print(f"Loaded per-obj UIDs: {per_obj_seg_uids.shape} (N,K,H,W)")
    if uid_color_lut is not None:
        print(f"Loaded UID color LUT:{uid_color_lut.shape} (K,4)")
        if obj_uids is not None:
            print("UID -> Color mapping:")
            for i, uid in enumerate(obj_uids):
                rgb = uid_color_lut[i, :3]
                print(f"  UID {uid}: RGB({rgb[0]}, {rgb[1]}, {rgb[2]})")
    if extr is not None:
        print(f"Extrinsics:          {extr.shape}")
    if theta_deg is not None:
        print(f"Angles (theta°):     {theta_deg.shape}")

    # Determine frame count (N)
    n_depth = depths.shape[0] if depths is not None else 0
    n_seg = segs.shape[0] if segs is not None else 0
    n_pom = per_obj_masks.shape[0] if per_obj_masks is not None else 0
    n_posu = per_obj_seg_uids.shape[0] if per_obj_seg_uids is not None else 0
    N = max(n_depth, n_seg, n_pom, n_posu)
    if N == 0:
        print("Nothing to display.")
        return

    # Prepare windows
    plt.ion()
    have_depth_view = depths is not None
    if have_depth_view:
        fig, ax = plt.subplots(num="Depth (normalized colormap)")
        im = ax.imshow(robust_depth_normalize(depths[0]), cmap="turbo", vmin=0, vmax=1)
        ax.set_title("Depth (normalized) — frame 0")
        plt.show(block=False)
    else:
        fig = ax = None

    seg_win = None
    if args.show_seg and (segs is not None or per_obj_masks is not None or per_obj_seg_uids is not None):
        seg_win = "Segmentation (colored)"
        cv2.namedWindow(seg_win, cv2.WINDOW_NORMAL)
        
        # First frame: prefer per_obj_seg_uids for consistent colors, then full-scene seg, then fuse per-obj
        if per_obj_seg_uids is not None and uid_color_lut is not None and obj_uids is not None:
            label0 = per_object_seg_uids_to_labels(per_obj_seg_uids[0])
            cv2.imshow(seg_win, labels_to_color_with_lut(label0, uid_color_lut, obj_uids))
        elif segs is not None:
            label0 = segs[0].astype(np.int32)
            if uid_color_lut is not None and obj_uids is not None:
                cv2.imshow(seg_win, labels_to_color_with_lut(label0, uid_color_lut, obj_uids))
            else:
                cv2.imshow(seg_win, labels_to_color(label0))
        elif per_obj_masks is not None:
            label0 = per_object_to_labels(per_obj_masks[0], obj_uids)
            if uid_color_lut is not None and obj_uids is not None:
                cv2.imshow(seg_win, labels_to_color_with_lut(label0, uid_color_lut, obj_uids))
            else:
                cv2.imshow(seg_win, labels_to_color(label0))
        cv2.waitKey(1)

    def update_frame(idx):
        if have_depth_view:
            d_idx = idx % max(n_depth, 1)
            ax.images[0].set_data(robust_depth_normalize(depths[d_idx]))
            ax.set_title(f"Depth (normalized) — frame {d_idx}")
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
        if seg_win:
            # Priority: per_obj_seg_uids > full scene seg > per_obj_masks
            if per_obj_seg_uids is not None and uid_color_lut is not None and obj_uids is not None:
                p_idx = idx % max(n_posu, 1)
                labels = per_object_seg_uids_to_labels(per_obj_seg_uids[p_idx])
                cv2.imshow(seg_win, labels_to_color_with_lut(labels, uid_color_lut, obj_uids))
            elif segs is not None:
                s_idx = idx % max(n_seg, 1)
                labels = segs[s_idx].astype(np.int32)
                if uid_color_lut is not None and obj_uids is not None:
                    cv2.imshow(seg_win, labels_to_color_with_lut(labels, uid_color_lut, obj_uids))
                else:
                    cv2.imshow(seg_win, labels_to_color(labels))
            elif per_obj_masks is not None:
                p_idx = idx % max(n_pom, 1)
                labels = per_object_to_labels(per_obj_masks[p_idx], obj_uids)
                if uid_color_lut is not None and obj_uids is not None:
                    cv2.imshow(seg_win, labels_to_color_with_lut(labels, uid_color_lut, obj_uids))
                else:
                    cv2.imshow(seg_win, labels_to_color(labels))
            cv2.waitKey(1)

    # ---------- Bulk export ----------
    if args.save_png:
        outdir = args.out
        outdir.mkdir(parents=True, exist_ok=True)
        for i in range(N):
            tag = angle_tag(theta_deg, i)  # angle in degrees (int) if available, else index
            
            # Depth exports (kept by index as before, can be long)
            if depths is not None and i < n_depth:
                save_depth_16bit_png(outdir / f"depth_{i:03d}.png", depths[i], scale_mm=args.mm_scale)
                save_depth_viz_png(outdir / f"depth_viz_{i:03d}.png", depths[i])

            # Whole-scene segmentation image for this view: <angle>_scene.png
            # Use UID-based coloring if available
            if per_obj_seg_uids is not None and i < n_posu and uid_color_lut is not None and obj_uids is not None:
                scene_labels = per_object_seg_uids_to_labels(per_obj_seg_uids[i])
                cv2.imwrite(str(outdir / f"{tag}_scene.png"), 
                           labels_to_color_with_lut(scene_labels, uid_color_lut, obj_uids))
            elif segs is not None and i < n_seg:
                scene_labels = segs[i].astype(np.int32)
                if uid_color_lut is not None and obj_uids is not None:
                    cv2.imwrite(str(outdir / f"{tag}_scene.png"), 
                               labels_to_color_with_lut(scene_labels, uid_color_lut, obj_uids))
                else:
                    cv2.imwrite(str(outdir / f"{tag}_scene.png"), labels_to_color(scene_labels))

            # Per-object masks for this view: <angle>_obj<UID>.png with consistent colors
            if per_obj_masks is not None and i < n_pom:
                K = per_obj_masks.shape[1]
                for k in range(K):
                    mask = per_obj_masks[i, k]
                    
                    # Create colored version if we have the color LUT
                    if uid_color_lut is not None and obj_uids is not None:
                        colored_mask = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
                        colored_mask[mask != 0] = uid_color_lut[k, :3]
                        uid = int(obj_uids[k])
                        cv2.imwrite(str(outdir / f"{tag}_obj{uid:03d}.png"), colored_mask)
                    
                    # Also save binary mask
                    # binary_mask = (mask != 0).astype(np.uint8) * 255
                    # uid_str = f"{int(obj_uids[k]):03d}" if obj_uids is not None else f"{k+1:03d}"
                    # cv2.imwrite(str(outdir / f"{tag}_obj{uid_str}.png"), binary_mask)

        print(f"Saved PNGs to: {outdir.resolve()}")

    # ---------- Interactive viewer ----------
    idx = 0
    update_frame(idx)

    if args.autoplay:
        try:
            while True:
                time.sleep(args.delay)
                idx = (idx + 1) % N
                update_frame(idx)
        except KeyboardInterrupt:
            pass
    else:
        if have_depth_view or (args.show_seg and (segs is not None or per_obj_masks is not None)):
            print("Controls: n=next, p=prev, q=quit, s=save current PNGs")
        else:
            print("Nothing to interact with (no depth view and --show-seg not set). Exiting.")
            return

        while True:
            try:
                ch = input("> ").strip().lower()
            except EOFError:
                break
            if ch == "q":
                break
            elif ch == "n":
                idx = (idx + 1) % N
                update_frame(idx)
            elif ch == "p":
                idx = (idx - 1) % N
                update_frame(idx)
            elif ch == "s":
                outdir = args.out
                outdir.mkdir(parents=True, exist_ok=True)
                tag = angle_tag(theta_deg, idx)
                if depths is not None and idx < n_depth:
                    save_depth_16bit_png(outdir / f"depth_{idx:03d}.png", depths[idx], scale_mm=args.mm_scale)
                    save_depth_viz_png(outdir / f"depth_viz_{idx:03d}.png", depths[idx])
                
                # Save current scene seg with UID-based colors
                if per_obj_seg_uids is not None and idx < n_posu and uid_color_lut is not None and obj_uids is not None:
                    labels = per_object_seg_uids_to_labels(per_obj_seg_uids[idx])
                    cv2.imwrite(str(outdir / f"{tag}_scene.png"), 
                               labels_to_color_with_lut(labels, uid_color_lut, obj_uids))
                elif segs is not None and idx < n_seg:
                    labels = segs[idx].astype(np.int32)
                    if uid_color_lut is not None and obj_uids is not None:
                        cv2.imwrite(str(outdir / f"{tag}_scene.png"), 
                                   labels_to_color_with_lut(labels, uid_color_lut, obj_uids))
                    else:
                        cv2.imwrite(str(outdir / f"{tag}_scene.png"), labels_to_color(labels))
                
                # Save per-object masks with consistent colors
                if per_obj_masks is not None and idx < n_pom:
                    K = per_obj_masks.shape[1]
                    for k in range(K):
                        mask = per_obj_masks[idx, k]
                        if uid_color_lut is not None and obj_uids is not None:
                            colored_mask = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
                            colored_mask[mask != 0] = uid_color_lut[k, :3]
                            uid = int(obj_uids[k])
                            cv2.imwrite(str(outdir / f"{tag}_obj{uid:03d}_color.png"), colored_mask)
                        
                        binary_mask = (mask != 0).astype(np.uint8) * 255
                        uid_str = f"{int(obj_uids[k]):03d}" if obj_uids is not None else f"{k+1:03d}"
                        cv2.imwrite(str(outdir / f"{tag}_obj{uid_str}.png"), binary_mask)
                
                print(f"Saved frame {idx} to {outdir}")
            else:
                print("n/p/q/s ?")

    plt.close("all")
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()




# python visualize_npy.py labeled_data/blocks/scenes/96ad972dcd1d46c0bcef6606041b55f0_all.npz   --save-png --out png_out --show-seg