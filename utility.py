"""Contains common utility functions."""
#  Copyright (c) 2018 PaddlePaddle Authors. All Rights Reserve.
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import re
import six
import time
import shutil
import tempfile
import subprocess
import distutils.util
import numpy as np
import sys
import paddle.fluid as fluid
import multiprocessing as mp


def print_arguments(args):
    """Print argparse's arguments.

    Usage:

    .. code-block:: python

        parser = argparse.ArgumentParser()
        parser.add_argument("name", default="Jonh", type=str, help="User name.")
        args = parser.parse_args()
        print_arguments(args)

    :param args: Input argparse.Namespace for printing.
    :type args: argparse.Namespace
    """
    print("-----------  Configuration Arguments -----------")
    for arg, value in sorted(six.iteritems(vars(args))):
        print("%s: %s" % (arg, value))
    print("------------------------------------------------")


def add_arguments(argname, type, default, help, argparser, **kwargs):
    """Add argparse's argument.

    Usage:

    .. code-block:: python

        parser = argparse.ArgumentParser()
        add_argument("name", str, "Jonh", "User name.", parser)
        args = parser.parse_args()
    """
    type = distutils.util.strtobool if type == bool else type
    argparser.add_argument(
        "--" + argname,
        default=default,
        type=type,
        help=help + ' Default: %(default)s.',
        **kwargs)


def fmt_time():
    """ get formatted time for now
    """
    now_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    return now_str


def recall_topk_ori(fea, lab, k):
    fea = np.array(fea)
    fea = fea.reshape(fea.shape[0], -1)
    n = np.sqrt(np.sum(fea**2, 1)).reshape(-1, 1)
    fea = fea / n
    a = np.sum(fea**2, 1).reshape(-1, 1)
    b = a.T
    ab = np.dot(fea, fea.T)
    d = a + b - 2 * ab
    d = d + np.eye(len(fea)) * 1e8
    sorted_index = np.argsort(d, 1)
    res = 0
    for i in range(len(fea)):
        for j in range(k):
            pred = lab[sorted_index[i][j]]
            if lab[i] == pred:
                res += 1.0
                break
    res = res / len(fea)
    return res


def func(param):
    sharedlist, s, e = param
    fea, a, b = sharedlist
    ab = np.dot(fea[s:e], fea.T)
    d = a[s:e] + b - 2 * ab
    for i in range(e - s):
        d[i][s + i] += 1e8
    sorted_index = np.argsort(d, 1)[:, :10]
    return sorted_index


def recall_topk_parallel(fea, lab, k):
    fea = np.array(fea)
    fea = fea.reshape(fea.shape[0], -1)
    n = np.sqrt(np.sum(fea**2, 1)).reshape(-1, 1)
    fea = fea / n
    a = np.sum(fea**2, 1).reshape(-1, 1)
    b = a.T
    sharedlist = mp.Manager().list()
    sharedlist.append(fea)
    sharedlist.append(a)
    sharedlist.append(b)

    N = 100
    L = fea.shape[0] / N
    params = []
    for i in range(N):
        if i == N - 1:
            s, e = int(i * L), int(fea.shape[0])
        else:
            s, e = int(i * L), int((i + 1) * L)
        params.append([sharedlist, s, e])

    pool = mp.Pool(processes=4)
    sorted_index_list = pool.map(func, params)
    pool.close()
    pool.join()
    sorted_index = np.vstack(sorted_index_list)

    res = 0
    for i in range(len(fea)):
        for j in range(k):
            pred = lab[sorted_index[i][j]]
            if lab[i] == pred:
                res += 1.0
                break
    res = res / len(fea)
    return res


def recall_topk(fea, lab, k=1):
    if fea.shape[0] < 20:
        return recall_topk_ori(fea, lab, k)
    else:
        return recall_topk_parallel(fea, lab, k)


def get_gpu_num():
    visibledevice = os.getenv('CUDA_VISIBLE_DEVICES')
    if visibledevice:
        devicenum = len(visibledevice.split(','))
    else:
        devicenum = subprocess.check_output(
            [str.encode('nvidia-smi'), str.encode('-L')]).decode('utf-8').count(
                '\n')
    return devicenum

def check_cuda(use_cuda, err = \
    "\nYou can not set use_cuda = True in the model because you are using paddlepaddle-cpu.\n \
    Please: 1. Install paddlepaddle-gpu to run your models on GPU or 2. Set use_cuda = False to run models on CPU.\n"
                                                                                                                     ):
    try:
        if use_cuda is True and fluid.is_compiled_with_cuda() is False:
            print(err)
            sys.exit(1)
    except Exception as e:
        print(e)
        pass


def _load_state(path):
    if os.path.exists(path + '.pdopt'):
        # XXX another hack to ignore the optimizer state
        tmp = tempfile.mkdtemp()
        dst = os.path.join(tmp, os.path.basename(os.path.normpath(path)))
        shutil.copy(path + '.pdparams', dst + '.pdparams')
        state = fluid.io.load_program_state(dst)
        shutil.rmtree(tmp)
    else:
        state = fluid.io.load_program_state(path)
    return state


def load_params(exe, prog, path, ignore_params=None):
    """
    Load model from the given path.
    Args:
        exe (fluid.Executor): The fluid.Executor object.
        prog (fluid.Program): load weight to which Program object.
        path (string): local model path.
        ignore_params (list): ignore variable to load when finetuning.
    """
    if not (os.path.isdir(path) or os.path.exists(path + '.pdparams')):
        raise ValueError("Model pretrain path {} does not "
                         "exists.".format(path))

    print('Loading parameters from {}...'.format(path))

    ignore_set = set()
    state = _load_state(path)

    # ignore the parameter which mismatch the shape
    # between the model and pretrain weight.
    all_var_shape = {}
    for block in prog.blocks:
        for param in block.all_parameters():
            all_var_shape[param.name] = param.shape
    ignore_set.update([
        name for name, shape in all_var_shape.items()
        if name in state and shape != state[name].shape
    ])

    if ignore_params:
        all_var_names = [var.name for var in prog.list_vars()]
        ignore_list = filter(
            lambda var: any([re.match(name, var) for name in ignore_params]),
            all_var_names)
        ignore_set.update(list(ignore_list))

    if len(ignore_set) > 0:
        for k in ignore_set:
            if k in state:
                print('warning: variable {} is already excluded automatically'.
                      format(k))
                del state[k]

    fluid.io.set_program_state(prog, state)
