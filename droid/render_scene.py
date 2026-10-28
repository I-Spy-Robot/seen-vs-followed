"""Render one DROID scene at rest: full-res camera frames + the 224 px policy view. Usage: python render_scene.py 4_note"""
import sys
from pathlib import Path
import numpy as np


def main(scene: str):
    from isaaclab.app import AppLauncher
    app = AppLauncher(headless=True, enable_cameras=True).app
    import gymnasium as gym, mediapy, sim_evals.environments  # noqa: F401
    from isaaclab_tasks.utils import parse_env_cfg
    from openpi_client import image_tools
    cfg = parse_env_cfg("DROID", device="cuda:0", num_envs=1, use_fabric=True)
    cfg.set_scene(scene)
    env = gym.make("DROID", cfg=cfg)
    env.reset(); obs, _ = env.reset()             # second reset loads materials
    out = Path("renders") / scene; out.mkdir(parents=True, exist_ok=True)
    pol = obs["policy"]
    views = {k: pol[k][0].cpu().numpy() for k in ("external_cam", "wrist_cam") if k in pol}
    for k, img in views.items():
        mediapy.write_image(out / f"{k}_full.png", img)
    policy_view = np.concatenate([image_tools.resize_with_pad(views["external_cam"], 224, 224),
                                  image_tools.resize_with_pad(views["wrist_cam"], 224, 224)], axis=1)
    mediapy.write_image(out / "policy_view_224.png", policy_view)
    print("RENDERED", scene, {k: v.shape for k, v in views.items()})
    env.close(); app.close()


if __name__ == "__main__":
    main(sys.argv[1])
