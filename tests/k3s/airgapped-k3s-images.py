#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p "python3.withPackages (ps: [ ps.requests ])" -p nix-prefetch-docker

import re
import subprocess

import requests

commit = "f7dcc139ffb328a5fe4a6d44c223e6add8e936ed"

url = f"https://raw.githubusercontent.com/k3s-io/k3s/{commit}/scripts/airgap/image-list.txt"

# file looks like this:
# docker.io/rancher/klipper-helm:v0.6.6-build20211022
# docker.io/rancher/klipper-lb:v0.3.4
# docker.io/rancher/local-path-provisioner:v0.0.20
# docker.io/rancher/mirrored-coredns-coredns:1.8.4
# docker.io/rancher/mirrored-library-busybox:1.32.1
# docker.io/rancher/mirrored-library-traefik:2.5.0
# docker.io/rancher/mirrored-metrics-server:v0.5.0
# docker.io/rancher/mirrored-pause:3.1

image_regex = r"(?P<image>[^:]+):(?P<tag>[^:]+)"

if __name__ == "__main__":
    r = requests.get(url)
    # split lines
    lines = r.text.splitlines()
    # parse lines
    images = [re.match(image_regex, line).groupdict() for line in lines]
    # prefetch images
    imageNix = []
    for image in images:
        print(f"prefetching {image['image']}:{image['tag']}")
        p = subprocess.run(
            ["nix-prefetch-docker", f"{image['image']}", f"{image['tag']}"],
            capture_output=True,
        )
        # stdout contains nix code to neccessary to fetch the image
        imageNix.append(p.stdout.decode("utf-8"))
    # write to file
    with open("airgapped-k3s-images.nix", "w") as f:
        f.write(
            f"""[
{"".join(imageNix)}
]"""
        )
    print("done")
