"""
Download the precomputed supplementary datasets into the shared `data/` folder.
"""

import argparse
import json
import os
from urllib.request import urlopen


DATA_URL = "https://file.biolab.si/visual-explanations/supplement/data"
DATASET_FILES = ("embedding.csv", "features.csv", "metadata.json")


def download_file(url: str, destination: str, force: bool = False) -> None:
    if os.path.exists(destination) and not force:
        print(f"skip  {destination}")
        return

    os.makedirs(os.path.dirname(destination), exist_ok=True)
    print(f"fetch {url}")
    with urlopen(url) as response:
        with open(destination, "wb") as output_file:
            output_file.write(response.read())
    print(f"wrote {destination}")


def load_dataset_names() -> list[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "datasets.json")

    with open(config_path, "r") as config_file:
        config = json.load(config_file)

    if isinstance(config, list):
        return config
    return config["datasets"]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Download shared supplementary datasets"
    )
    parser.add_argument(
        "--base-url",
        default=DATA_URL,
        help="Base URL containing one subdirectory per dataset",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing local files",
    )
    args = parser.parse_args(argv)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    datasets = load_dataset_names()

    for dataset in datasets:
        for filename in DATASET_FILES:
            url = f"{args.base_url.rstrip('/')}/{dataset}/{filename}"
            destination = os.path.join(data_dir, dataset, filename)
            download_file(url, destination, force=args.force)


if __name__ == "__main__":
    main()
