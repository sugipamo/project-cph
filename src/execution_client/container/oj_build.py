import subprocess
import os

DOCKERFILE = "contest_env/oj.Dockerfile"
IMAGE_NAME = "cph_image_ojtools"

def build_ojtools_image():
    if not os.path.exists(DOCKERFILE):
        print(f"[ERROR] Dockerfile not found: {DOCKERFILE}")
        exit(1)
    cmd = [
        "docker", "build",
        "-f", DOCKERFILE,
        "-t", IMAGE_NAME,
        "."
    ]
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print(f"[OK] Built {IMAGE_NAME}")
    else:
        print(f"[ERROR] Build failed")

if __name__ == "__main__":
    build_ojtools_image() 