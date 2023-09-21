## Setup project

edit entity and project in settings.py

```
mkdir -p dataset
cp example_data/* dataset/
python bootstrap_project.py
```

## visit the UI

Now you can Browse to https://weave.wandb.ai/browse/wandb/<entity>/<project> to find
your boards.

NOTE: this repo currently relies on unreleased weave and wandb changes, so you need to use
the weave server on localhost in devmode instead of weave.wandb.ai
