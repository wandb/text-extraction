import glob
import json
import os

import weave

import settings
import base_types
import cli


def read_dataset():
    dataset_rows = []
    raw_labels = json.load(open(os.path.join("dataset", "labels.json")))
    for p in glob.glob(os.path.join("dataset", "*.txt")):
        # Have to do replace here because of weave '.' access issues
        example_id = os.path.basename(p).replace(".", "_")
        label = raw_labels.get(example_id)
        if label:
            dataset_rows.append(
                {"id": example_id, "example": open(p).read(), "label": label}
            )
    return base_types.Dataset(rows=weave.WeaveList(dataset_rows))


def publish():
    dataset = read_dataset()
    return cli.publish(dataset, "dataset")


if __name__ == "__main__":
    publish()
