import numpy as np
import networkx as nx
import cPickle as cp
import random
import ctypes
import os
import sys
import time
import re
from tqdm import tqdm

sys.path.append( '%s/mvc_lib' % os.path.dirname(os.path.realpath(__file__)) )
from mvc_lib import MvcLib

def find_model_file(opt):
    max_n = int(opt['max_n'])
    min_n = int(opt['min_n'])
    log_file = '%s/log-%d-%d.txt' % (opt['save_dir'], min_n, max_n)

    best_r = 1000000
    best_it = -1
    with open(log_file, 'r') as f:
        for line in f:
            if 'average' in line:
                line = line.split(' ')
                it = int(line[1].strip())
                r = float(line[-1].strip())
                if r < best_r:
                    best_r = r
                    best_it = it
    assert best_it >= 0
    print 'using iter=', best_it, 'with r=', best_r
    return '%s/nrange_%d_%d_iter_%d.model' % (opt['save_dir'], min_n, max_n, best_it)

if __name__ == '__main__':
    api = MvcLib(sys.argv)

    opt = {}
    for i in range(1, len(sys.argv), 2):
        opt[sys.argv[i][1:]] = sys.argv[i + 1]

    model_file = find_model_file(opt)
    assert model_file is not None
    print 'loading', model_file
    sys.stdout.flush()
    api.LoadModel(model_file)

    isec = int(opt['isec'])
    for filename in os.listdir(opt['data_dir']):
        if filename.endswith(".export.pp2graph.pkl"):
            filepath = '%s/%s' % (opt['data_dir'], filename)
            f = open(filepath, 'rb')
            g = cp.load(f)
            g_nodes = [int(n) for n in g.nodes]
            for i in range(isec):
                g = nx.convert_node_labels_to_integers(g)
                frac = 0.0

                filename = re.sub('\.pkl$', '', filename)
                result_file = '%s/%s.clr.%d' % (opt['output_dir'], filename, i)

                with open(result_file, 'w') as f_out:
                    print 'testing'
                    sys.stdout.flush()

                    api.InsertGraph(g, is_test=True, gid=i)
                    t1 = time.time()
                    val, sol = api.GetSol(i, nx.number_of_nodes(g))
                    t2 = time.time()

                    mvc_nodes = set()
                    for j in range(sol[0]):
                        f_out.write('%d ' % g_nodes[sol[j + 1]])
                        mvc_nodes.add(sol[j + 1])

                    mis_nodes = set(g.nodes).difference(mvc_nodes)
                    for n in sorted(list(mis_nodes), reverse=True):
                        g_nodes.pop(n)
                    g.remove_nodes_from(mis_nodes)

                    frac += val
                print 'average size of vc: ', frac
