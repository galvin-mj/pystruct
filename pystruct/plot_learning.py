#!/usr/bin/python
"""
This module provides a callable for easy evaluation of stored models.
"""
import argparse
import matplotlib.pyplot as plt
import numpy as np

from pystruct.utils import SaveLogger


def main():

    parser = argparse.ArgumentParser(description='Plot learning progress for one or several SSVMs.')
    parser.add_argument('pickles', metavar='N', type=str, nargs='+',
                        help='pickle files containing SSVMs')
    parser.add_argument('--time', dest='time', action='store_const',
                        const=True, default=False, help='Plot against '
                       'wall-clock time (default: plot against iterations.)')

    args = parser.parse_args()

    ssvms = []
    for file_name in args.pickles:
        print("loading %s ..." % file_name)
        ssvms.append(SaveLogger(file_name=file_name).load())
    if np.any([hasattr(ssvm, 'loss_curve_') for ssvm in ssvms]):
        n_plots = 2
    else:
        n_plots = 1
    fig, axes = plt.subplots(1, n_plots)
    for ssvm, file_name in zip(ssvms, args.pickles):
        prefix = ""
        if len(ssvms) > 1:
            prefix = file_name[:-7] + " "
        plot_learning(ssvm, axes=axes, prefix=prefix, time=args.time)
    plt.show()


def plot_learning(ssvm, time=True, axes=None, prefix=""):
    """Plot optimization curves and cache hits.

    Create a plot summarizing the optimization / learning process of an SSVM.
    It plots the primal and cutting plane objective (if applicable) and also
    the target loss on the training set against training time.
    For one-slack SSVMs with constraint caching, cached constraints are also
    contrasted against inference runs.

    Parameters
    -----------
    ssvm : object
        Learner to evaluate. Should work with all learners.

    time : boolean, default=True
        Whether to use wall clock time instead of iterations as the x-axis.

    prefix : string, default=""
        Prefix for legend.

    Notes
    -----
    Warm-starting a model might mess up the alignment of the curves.
    So if you warm-started a model, please don't count on proper alignment
    of time, cache hits and objective.
    """
    print(ssvm)
    if hasattr(ssvm, 'base_ssvm'):
        ssvm = ssvm.base_ssvm

    if hasattr(ssvm, 'iterations_'):
        # BCFW remembers when we computed the objective
        iterations = ssvm.iterations_
    elif hasattr(ssvm, 'dual_objective_curve_'):
        iterations = np.arange(len(ssvm.dual_objective_curve_))
        print("Dual Objective: %f" % ssvm.dual_objective_curve_[-1])
    else:
        iterations = np.arange(len(ssvm.primal_objective_curve_))
        print("Primal Objective: %f" % ssvm.primal_objective_curve_[-1])

    print("Iterations: %d" % (np.max(iterations) + 1))  # we count from 0
    inference_run = None
    if hasattr(ssvm, 'cached_constraint_'):
        if np.any(ssvm.cached_constraint_):
            # we don't want to do this if there was no constraint caching
            inference_run = ~np.array(ssvm.cached_constraint_)
    if hasattr(ssvm, "loss_curve_"):
        n_plots = 2
    else:
        n_plots = 1
    if axes is None:
        fig, axes = plt.subplots(1, n_plots)
    if not isinstance(axes, list):
        axes = [axes]

    if time:
        inds = np.array(ssvm.timestamps_)
        inds = inds[1:] / 60.
        axes[0].set_xlabel('training time (min)')
    else:
        axes[0].set_xlabel('Passes through training data')
        inds = iterations

    axes[0].set_title("Objective")
    if hasattr(ssvm, "dual_objective_curve_"):
        axes[0].plot(inds, ssvm.dual_objective_curve_, '--', label=prefix + "dual objective")
        axes[0].set_yscale('log')
    if hasattr(ssvm, "primal_objective_curve_"):
        axes[0].plot(inds, ssvm.primal_objective_curve_,
                     label=prefix + "cached primal objective" if inference_run is not None
                     else prefix + "primal objective")
    if inference_run is not None:
        inference_run = inference_run[:len(ssvm.dual_objective_curve_)]
        axes[0].plot(inds[inference_run],
                     np.array(ssvm.primal_objective_curve_)[inference_run],
                     'o', label=prefix + "primal")
    axes[0].legend(loc='best')
    if n_plots == 2:
        if time:
            axes[1].set_xlabel('training time (min)')
        else:
            axes[1].set_xlabel('Passes through training data')

        try:
            axes[1].plot(inds[::ssvm.show_loss_every], ssvm.loss_curve_)
        except:
            axes[1].plot(ssvm.loss_curve_)

        axes[1].set_title("Training Error")
        axes[1].set_yscale('log')
    return axes


if __name__ == "__main__":
    main()
