entity = "shawn"

project = "text-extract26"

predictions_stream_name = "stream"

wandb = True

dev_mode = False

if dev_mode:
    from weave import use_frontend_devmode

    # we just do this so we print correct frontend urls
    # when publishing objects
    use_frontend_devmode()
