#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


def run(command):
    """Run a shell command and stop on failure."""
    print(f"\n> {' '.join(command)}")
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Build and push all Docker images in subdirectories containing a Dockerfile."
    )

    parser.add_argument(
        "--username",
        required=True,
        help="Docker Hub username"
    )

    parser.add_argument(
        "--prefix",
        default="nau_",
        help="Image name prefix (default: nau_)"
    )

    parser.add_argument(
        "--tag",
        default="latest",
        help="Docker image tag (default: latest)"
    )

    parser.add_argument(
        "--root",
        default=".",
        help="Root directory to search (default: current directory)"
    )

    args = parser.parse_args()

    root = Path(args.root).resolve()

    print(f"Searching for Dockerfiles under: {root}")

    found = False

    for directory in sorted(root.iterdir()):
        if not directory.is_dir():
            continue

        dockerfile = directory / "Dockerfile"

        if dockerfile.exists():
            found = True

            image_name = f"{args.prefix}{directory.name}"
            full_tag = f"{args.username}/{image_name}:{args.tag}"

            print("\n" + "=" * 60)
            print(f"Directory : {directory.name}")
            print(f"Image     : {full_tag}")

            run([
                "docker",
                "build",
                "-t",
                full_tag,
                str(directory)
            ])

            run([
                "docker",
                "push",
                full_tag
            ])

    if not found:
        print("No Dockerfiles found.")

    print("\nDone!")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nCommand failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)