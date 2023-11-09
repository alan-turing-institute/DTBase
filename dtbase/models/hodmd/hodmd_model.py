#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
from pydmd import HODMD, ModesTuner
from pydmd.plotter import plot_eigs
from sklearn.preprocessing import StandardScaler


def plot_data(
    xtrain_timestamp,
    xtrain,
    xtest_timestamp,
    xtest,
    plot_label,
    save_path=None,
    save_suffix="",
):
    if isinstance(plot_label, list):
        plot_label_train = [label + "_train" for label in plot_label]
        plot_label_forecast = [label + "_forecast" for label in plot_label]
    else:  # it's a string
        plot_label_train = plot_label + "_train"
        plot_label_forecast = plot_label + "_forecast"
    fig, ax = plt.subplots(figsize=(17, 4.5))
    ax.plot(xtrain_timestamp, xtrain, label=plot_label_train)
    ax.plot(xtest_timestamp, xtest, label=plot_label_forecast)
    ax.legend(loc="best")
    if save_path is not None:
        fig.savefig(save_path + "/data{0}.png".format(save_suffix))
    return fig


def hodmd_pipeline(
    timestamps,
    xdata,
    labels,
    hodmd_d=250,
    train_test_split=0.8,
    save_path=None,
    save_suffix="",
):
    # data shape: num_samples x num_sensor_measures (1 for now)
    if xdata.ndim == 1:
        xdata = np.expand_dims(xdata, axis=1)
        labels_ = labels[0]
    else:
        labels_ = labels
    num_train_samples = int(train_test_split * len(xdata))

    xtrain_timestamp = timestamps[:num_train_samples]
    xtrain = xdata[:num_train_samples, :]
    xtest_timestamp = timestamps[num_train_samples:]
    xtest = xdata[num_train_samples:, :]

    # scaling data
    scaler = StandardScaler(with_std=True, with_mean=True, copy=True)
    scaler = scaler.fit(xtrain)
    xtrain_normalized = scaler.transform(xtrain)
    xtest_normalized = scaler.transform(xtest)
    plot_data(
        xtrain_timestamp,
        xtrain_normalized,
        xtest_timestamp,
        xtest_normalized,
        labels_,
        save_path,
        save_suffix,
    )

    snapshots = xtrain_normalized.T
    model = HODMD(
        svd_rank=0.99,
        svd_rank_extra=0.9,
        exact=True,
        opt=True,
        d=hodmd_d,
        forward_backward=True,
        sorted_eigs="real",
    )
    model = model.fit(snapshots)
    filename = (
        None
        if save_path is None
        else save_path + "/eigs_before_mode_tuning{0}.png".format(save_suffix)
    )
    plot_eigs(model, show_axes=True, show_unit_circle=True, filename=filename)
    model.dmd_time["tend"] = len(xdata) - 1

    mtuner = ModesTuner(model)
    mtuner.select("integral_contribution", n=50)
    mtuner.stabilize(inner_radius=0.5, outer_radius=1.5)
    tunedDMD = mtuner._dmds[0]
    model = tunedDMD
    filename = (
        None
        if save_path is None
        else save_path + "/eigs_after_mode_tuning{0}.png".format(save_suffix)
    )
    plot_eigs(model, show_axes=True, show_unit_circle=True, filename=filename)

    xreconstructed = model.reconstructed_data.real

    if save_path is not None:
        suffixes = (
            [save_suffix]
            if len(labels) == 1
            else [save_suffix + "_" + label for label in labels]
        )
        for idx, label in enumerate(labels):
            fig, ax = plt.subplots(figsize=(17, 4.5))
            ax.plot(
                xtrain_timestamp,
                xtrain_normalized[:, idx],
                label=label + "_train",
                c="k",
                linewidth=1,
            )
            ax.plot(
                xtest_timestamp,
                xtest_normalized[:, idx],
                label=label + "_forecast",
                c="k",
                linewidth=1,
            )
            ax.plot(
                xtrain_timestamp,
                xreconstructed[idx, :num_train_samples].T,
                label="prediction_train",
                c="r",
                linewidth=1,
            )
            ax.plot(
                xtest_timestamp,
                xreconstructed[idx, num_train_samples:].T,
                ":",
                label="prediction_forecast",
                c="r",
                linewidth=1,
            )
            ax.legend(loc="best")
            fig.savefig(save_path + "/hodmd_predictions{0}.png".format(suffixes[idx]))
    plt.close("all")

    return xreconstructed, timestamps
