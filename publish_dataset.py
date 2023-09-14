import glob
import json
import os

import weave

import settings
import base_types


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
    return dataset_rows


def publish():
    dataset_rows = read_dataset()
    dataset = base_types.Dataset(rows=dataset_rows)
    entity, project = settings.wandb_project.split("/")
    res = weave.storage.publish(dataset, f"{project}/dataset")
    print("RES", res)


if __name__ == "__main__":
    publish()
