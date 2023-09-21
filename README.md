## Setup project

Setup a pyenv

```
pyenv virtualenv 3.10.7 text-extraction
pyenv local text-extraction
pip install -r requirements.txt
```

IMPORTANT: now edit `entity` and `project` in settings.py

The next block creates the following:

- The first dataset version
- Two models
- Evaluations of both models
- Three boards: dataset browser, model browser, model comparsion

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

You can also see the underlying artifacts at https://wandb.ai/<entity>/<project>/artifacts
