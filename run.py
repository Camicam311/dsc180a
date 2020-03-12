#!/usr/bin/env python

import sys
import json
import shutil


sys.path.insert(0, 'src') # add library code to path
from src.etl import get_data, process_data, remove_dir
from src.m_stat import analyze_m_stat_data

DATA_PARAMS = 'config/data-params.json'
PROCESS_PARAMS = 'config/process-params.json'
M_STAT_PARAMS = 'config/m-stat-params.json'
TEST_DATA_PARAMS = 'config/test-data-params.json'
TEST_PROCESS_PARAMS = 'config/test-process-params.json'
TEST_M_STAT_PARAMS = 'config/test-m-stat-params.json'


def load_params(fp):
    with open(fp) as fh:
        param = json.load(fh)

    return param


def main(targets):

    # make the clean target
    if 'clean' in targets:
        shutil.rmtree('data/temp', ignore_errors=True)
        shutil.rmtree('data/out', ignore_errors=True)
        shutil.rmtree('data/test', ignore_errors=True)

    # make the data target
    if 'data' in targets:
        cfg = load_params(DATA_PARAMS)
        get_data(**cfg)

    # make the test data target
    if 'test-data' in targets:
        cfg = load_params(TEST_DATA_PARAMS)
        get_data(**cfg)

    # cleans and prepares the data for analysis
    if 'process' in targets:
        cfg = load_params(PROCESS_PARAMS)
        process_data(**cfg)

    # cleans and prepares the test data for analysis
    if 'test-process' in targets:
        cfg = load_params(TEST_PROCESS_PARAMS)
        process_data(**cfg)

    # runs m-statistic on processed data
    if 'm-stat' in targets:
        cfg = load_params(M_STAT_PARAMS)
        analyze_m_stat_data(**cfg)

    # runs m-statistic on processed test data
    if 'test-m-stat' in targets:
        cfg = load_params(TEST_M_STAT_PARAMS)
        analyze_m_stat_data(**cfg)

    if 'complete' in targets:
        cfg = load_params(DATA_PARAMS)
        get_data(**cfg)
        remove_dir('data/raw')
        cfg = load_params(PROCESS_PARAMS)
        process_data(**cfg)
        cfg = load_params(M_STAT_PARAMS)
        analyze_m_stat_data(**cfg)

    return


if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)
