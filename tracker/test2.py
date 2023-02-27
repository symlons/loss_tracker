#!/usr/bin/env python
import wandb

wandb.init(project="test2", entity="sym")
for i in range(50000):
    wandb.log({"loss": i})
