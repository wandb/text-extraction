## Setup project

edit settings.py

## publish boards

python board_datasets.py

## publish the starter dataset

```
mkdir dataset
cp -R example_data/* dataset/
python publish_dataset.py
```

## visit the UI

Now you can Browse to https://weave.wandb.ai/browse/wandb/<entity>/<project> to find
your board. Click it to load up your dataset
