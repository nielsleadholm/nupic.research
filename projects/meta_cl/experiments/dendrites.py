#  Numenta Platform for Intelligent Computing (NuPIC)
#  Copyright (C) 2020, Numenta, Inc.  Unless you have an agreement
#  with Numenta, Inc., for a separate license for this software code, the
#  following terms and conditions apply:
#
#  This program is free software you can redistribute it and/or modify
#  it under the terms of the GNU Affero Public License version 3 as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU Affero Public License for more details.
#
#  You should have received a copy of the GNU Affero Public License
#  along with this program.  If not, see htt"://www.gnu.org/licenses.
#
#  http://numenta.org/licenses/
#

from copy import deepcopy

from experiment_classes import DendritesExperiment
from networks import (
    DendriticNetwork,
    MimicANMLDendriticNetwork,
    ReplicateANMLDendriticNetwork,
)

from .anml_replicate import ANMLTransform, metacl_anml_replicate
from .oml_replicate import metacl_oml_replicate


# Alternative to run on a single GPU
def run_experiment(config):
    exp = config.get("experiment_class")()
    exp.setup_experiment(config)
    print(f"Training started....")
    while not exp.should_stop():
        result = exp.run_epoch()
        print(f"Accuracy: {result['mean_accuracy']:.4f}")
    print(f"....Training finished")


meta_test_test_kwargs = dict(
    # Setup the meta-testing phase and allow it to run.
    run_meta_test=True,

    # This resets the fast params (in this case the output layer of the OMLNetwork)
    reset_fast_params=True,

    # Results reported over 15 sampled.
    test_train_sample_size=15,

    # The best lr was chosen among the following; done separately for each number of
    # classes trained on.
    lr_sweep_range=[0.03, 0.01, 0.003, 0.001, 0.0003, 0.0001, 0.00003, 0.00001],
)


# A dendritic network trained with meta-continual learning
# |----------------------------------------------------------------|
# |   Num Classes | Meta-test test   | Meta-test train   |    LR   |
# |--------------:|:-----------------|:------------------|--------:|
# |            10 | 0.20 ± 0.08      | 0.21 ± 0.07       | 0.001   |
# |            50 | 0.04 ± 0.01      | 0.04 ± 0.01       | 0.001   |
# |           100 | 0.03 ± 0.01      | 0.03 ± 0.01       | 0.001   |
# |           200 | 0.01 ± 0.01      | 0.01 ± 0.01       | 0.001   |
# |           600 | 0.00 ± 0.00      | 0.01 ± 0.00       | 0.001   |
# |----------------------------------------------------------------|
#
metacl_dendrites = deepcopy(metacl_oml_replicate)
metacl_dendrites.update(
    model_class=DendriticNetwork,
    model_args=dict(num_classes=963,
                    num_segments=4,
                    dim_context=20,
                    module_sparsity=0.75,
                    dendrite_sparsity=0.50),
    wandb_args=dict(
        name="metacl_dendrites",
        project="metacl",
        notes="Dendritic Networks applied to OML Problem. Test 1"
    ),
    optimizer_args=dict(lr=1e-3),

    # Update the prediction layer and the gating_layer during meta-train training.
    fast_params=["prediction.*", "gating_layer.*"],

    # Update only the linear module of the gating_layer during meta-test training.
    test_train_params=["gating_layer.module*"],

    # Identify the params of the output layer.
    output_layer_params=["gating_layer.module.weight", "gating_layer.module.bias"],

    # Update with meta_test testing arguments.
    **deepcopy(meta_test_test_kwargs),
)


# An updated version of the dendrites model.
# |---------------------------------------------------------------|
# |   Num Classes | Meta-test test   | Meta-test train   |     LR |
# |--------------:|:-----------------|:------------------|-------:|
# |            10 | 0.78 ± 0.08      | 0.90 ± 0.04       | 0.001  |
# |            50 | 0.76 ± 0.03      | 0.94 ± 0.02       | 0.001  |
# |           100 | 0.71 ± 0.02      | 0.94 ± 0.01       | 0.0006 |
# |           200 | 0.66 ± 0.02      | 0.93 ± 0.01       | 0.0006 |
# |           600 | 0.49 ± 0.01      | 0.85 ± 0.01       | 0.0006 |
# |---------------------------------------------------------------|
#
metacl_anml_dendrites = deepcopy(metacl_anml_replicate)
metacl_anml_dendrites.update(
    experiment_class=DendritesExperiment,

    epochs=20000,
    model_class=MimicANMLDendriticNetwork,
    model_args=dict(num_classes=963,
                    num_segments=20,
                    dim_context=100,
                    dendrite_sparsity=0.70),
    dataset_args=dict(
        root="~/nta/datasets",
        transform=ANMLTransform(),
    ),

    wandb_args=dict(
        name="metacl_anml_dendrites",
        project="metacl",
        notes="""
        Dendritic Networks applied to OML Problem. Test 2: This employs a different
        series of average pooling for an architecture closer to ANML's.
        """
    ),

    # Learning rate for inner loop.
    adaptation_lr=0.03,
    optimizer_args=dict(lr=1e-4),

    # Run meta-testing over 10 classes.
    num_meta_test_classes=[10, 50, 100, 200, 600],

    # Update the prediction layer and the gating_layer during meta-train training.
    fast_params=["prediction.*", "classifier.*"],

    # Update only the linear module of the gating_layer during meta-test training.
    test_train_params=["classifier.*"],

    # Identify the params of the output layer.
    output_layer_params=["classifier.weight", "classifier.bias"],
)


# A 2000 epoch model for quick iterations and debugging.
# |--------------------------------------------------------------|
# |   Num Classes | Meta-test test   | Meta-test train   |    LR |
# |--------------:|:-----------------|:------------------|------:|
# |            10 | 0.36 ± 0.05      | 0.40 ± 0.07       | 0.001 |
# |            50 | 0.43 ± 0.03      | 0.69 ± 0.02       | 0.001 |
# |--------------------------------------------------------------|
#
metacl_anml_dendrites_2000 = deepcopy(metacl_anml_dendrites)
metacl_anml_dendrites_2000.update(
    epochs=2000,
    num_meta_test_classes=[50],
    wandb_args=dict(name="metacl_anml_dendrites_2000", project="metacl"),
)


# The following adjust the lr to ensure it's identical to that used by ANML.
# |--------------------------------------------------------------|
# |   Num Classes | Meta-test test   | Meta-test train   |    LR |
# |--------------:|:-----------------|:------------------|------:|
# |            10 | 0.84 ± 0.06      | 0.92 ± 0.03       | 0.001 |
# |            50 | 0.86 ± 0.02      | 0.98 ± 0.01       | 0.001 |
# |           100 | 0.81 ± 0.02      | 0.98 ± 0.01       | 0.001 |
# |           200 | 0.75 ± 0.02      | 0.97 ± 0.01       | 0.001 |
# |           600 | 0.62 ± 0.01      | 0.94 ± 0.00       | 0.001 |
# |--------------------------------------------------------------|
#
metacl_anml_dendrites_adjust_lr = deepcopy(metacl_anml_dendrites)
metacl_anml_dendrites_adjust_lr.update(
    # Learning rate for inner loop and outer loop.
    adaptation_lr=0.1,  # applied in inner loop via SGD like update rule
    optimizer_args=dict(lr=1e-3),
    wandb_args=dict(
        name="metacl_anml_dendrites_adjust_lr",
        project="metacl",
    ),
)


# A 2000 epoch model for quick iterations and debugging.
# |--------------------------------------------------------------|
# |   Num Classes | Meta-test test   | Meta-test train   |    LR |
# |--------------:|:-----------------|:------------------|------:|
# |            50 | 0.73 ± 0.02      | 0.95 ± 0.01       | 0.001 |
# |--------------------------------------------------------------|
#
metacl_anml_dendrites_adjust_lr_2000 = deepcopy(metacl_anml_dendrites_adjust_lr)
metacl_anml_dendrites_adjust_lr_2000.update(
    epochs=2000,
    num_meta_test_classes=[50],
    wandb_args=dict(
        name="metacl_anml_dendrites_adjust_lr_2000",
        project="metacl",
    ),
)


# This is a network closer in implementation to anml.
# |--------------------------------------------------------------|
# |   Num Classes | Meta-test test   | Meta-test train   |    LR |
# |--------------:|:-----------------|:------------------|------:|
# |            10 | 0.86 ± 0.05      | 0.92 ± 0.03       | 0.001 |
# |            50 | 0.89 ± 0.03      | 0.98 ± 0.01       | 0.001 |
# |           100 | 0.86 ± 0.02      | 0.98 ± 0.01       | 0.001 |
# |           200 | 0.80 ± 0.01      | 0.97 ± 0.01       | 0.001 |
# |           600 | 0.68 ± 0.01      | 0.93 ± 0.00       | 0.001 |
# |--------------------------------------------------------------|
#
anml_replicated_with_dendrites = deepcopy(metacl_anml_dendrites_adjust_lr)
anml_replicated_with_dendrites.update(
    model_class=ReplicateANMLDendriticNetwork,
    model_args=dict(
        num_classes=963,
        num_segments=1,
        dendrite_sparsity=0,
        dendrite_bias=True,
    ),
    wandb_args=dict(name="anml_replicated_with_dendrites", project="metacl"),
)


# A 2000 epoch model for quick iterations and debugging.
# |--------------------------------------------------------------|
# |   Num Classes | Meta-test test   | Meta-test train   |    LR |
# |--------------:|:-----------------|:------------------|------:|
# |            50 | 0.82 ± 0.02      | 0.94 ± 0.02       | 0.001 |
# |--------------------------------------------------------------|#
#
anml_replicated_with_dendrites_2000 = deepcopy(anml_replicated_with_dendrites)
anml_replicated_with_dendrites_2000.update(
    epochs=2000,
    num_meta_test_classes=[50],
    wandb_args=dict(name="anml_replicated_with_dendrites_2000", project="metacl"),
)


# Export configurations in this file
CONFIGS = dict(
    metacl_dendrites=metacl_dendrites,
    metacl_anml_dendrites=metacl_anml_dendrites,
    metacl_anml_dendrites_2000=metacl_anml_dendrites_2000,
    metacl_anml_dendrites_adjust_lr=metacl_anml_dendrites_adjust_lr,
    metacl_anml_dendrites_adjust_lr_2000=metacl_anml_dendrites_adjust_lr_2000,
    anml_replicated_with_dendrites=anml_replicated_with_dendrites,
    anml_replicated_with_dendrites_2000=anml_replicated_with_dendrites_2000,
)
