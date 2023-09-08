import typing
import wandb
import weave

# HACK, launch doesn't give us /tmp space
import os
os.environ['WEAVE_LOCAL_ARTIFACT_DIR'] = './weave-fs'

# HACK, Weave Object type can't be deserialized since it doesn't
# exist in pypi package yet. We need to handle anonymous objects in Weave
@weave.type()
class Dataset:
    rows: list[typing.Any]


def make_wandb_table(list_of_dicts):
    table = wandb.Table(columns=list(list_of_dicts[0].keys()), allow_mixed_types=True)
    for d in list_of_dicts:
        table.add_data(*d.values())
    return table