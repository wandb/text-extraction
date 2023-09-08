import argparse

import wandb
import weave

import settings
import util

from arg_config import parser

parser.add_argument("--wandb", action="store_true")
parser.add_argument("--dataset_uri", type=str, required=True)

def batch_predict(dataset, model):
    predict_result = []

    for dataset_row in dataset.rows:
        result = model.predict(dataset_row["example"])
        predict_result.append({
            'dataset_id': dataset_row['id'],
            'prediction': result,
        })
    return {'prediction_table': predict_result}


def main(model_class):
    args = parser.parse_args()

    if args.wandb:
        entity, project = settings.wandb_project.split("/")
        run = wandb.init(job_type='batch_predict', entity=entity, project=project, config=args)

        # Copy because we have to modify below because of an issue
        args = {**wandb.config}

    if args["dataset_uri"].startswith("zzz-"):
        args["dataset_uri"] = args["dataset_uri"][4:]

    dataset = weave.storage.get(args["dataset_uri"])
    model = model_class.from_args(args)

    result = batch_predict(dataset, model)

    if args['wandb']:
        run.log({"prediction_table": util.make_wandb_table(result["prediction_table"])})