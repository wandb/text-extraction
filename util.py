import wandb

def make_wandb_table(list_of_dicts):
    table = wandb.Table(columns=list(list_of_dicts[0].keys()), allow_mixed_types=True)
    for d in list_of_dicts:
        table.add_data(*d.values())
    return table