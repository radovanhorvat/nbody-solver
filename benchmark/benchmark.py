import os
import platform
import psutil
import timeit
import logging
import numpy as np
import functools
import json

from simulator.space import Space
import kernels.brute_force as kernbf
import kernels.octree_c as kernoct_c


logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)


def vel_func(pos_vec):
    return np.array((0., 0., 0.))


def mass_func(pos_vec):
    return 1.0


class Benchmark:
    def __init__(self, write_results=True):
        self._write_results = write_results
        self._results = {}

    def _get_system_info(self):
        info={}
        info['platform']=platform.system()
        info['platform-release']=platform.release()
        info['platform-version']=platform.version()
        info['processor']=platform.processor()
        info['cores'] = psutil.cpu_count()
        info['memory'] = round(psutil.virtual_memory().total / (1024.0**3))
        return info

    def run(self):
        logging.info('Start benchmark')
        logging.info('Gathering system information')
        self._results['sys_info'] = self._get_system_info()
        logging.info('Running brute-force, N=10000')
        self._run_brute_force(10000)
        logging.info('Running brute-force, N=30000')
        self._run_brute_force(30000)
        logging.info('Running Barnes-Hut, N=100000, theta=0.75')
        self._run_barnes_hut(100000)
        logging.info('Running Barnes-Hut, N=500000, theta=0.75')
        self._run_barnes_hut(500000)
        logging.info('Running Barnes-Hut, N=1000000, theta=0.75')
        self._run_barnes_hut(1000000)
        if self._write_results:
            logging.info('Dumping results to json')
            self._dump_to_json()
        logging.info('End benchmark')

    def _run_brute_force(self, num_particles):        
        space = Space()
        space.add_cuboid(num_particles, np.array((0., 0., 0.)), 1., 1., 1., vel_func, mass_func)
        t = timeit.Timer(functools.partial(kernbf.calculate_accs_pp_wrap, space.r, space.m, 1.0, 0.))    
        res = t.timeit(5) / 5
        self._results['brute_force_' + str(num_particles)] = res

    def _run_barnes_hut(self, num_particles):        
        space = Space()
        space.add_cuboid(num_particles, np.array((0., 0., 0.)), 1., 1., 1., vel_func, mass_func)
        t = timeit.Timer(functools.partial(kernoct_c.calc_accs_wrap_wrap_c, 1., 0., 0., 0., space.r, space.m, 1.0, 0., 0.75))
        res = t.timeit(5) / 5
        self._results['barnes-hut_' + str(num_particles)] = res

    def _dump_to_json(self):
        ofp = os.path.abspath(os.path.join(os.path.dirname(__file__), 'results.json'))
        with open(ofp, 'w') as fp:
            json.dump(self._results, fp)


if __name__ == '__main__':
    b = Benchmark()
    b.run()
