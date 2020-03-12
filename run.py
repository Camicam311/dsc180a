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
OBAMA_DATA_PARAMS = 'config/obama-data-params.json'
OBAMA_PROCESS_PARAMS = 'config/obama-process-params.json'
OBAMA_M_STAT_PARAMS = 'config/obama-m-stat-params.json'
ANARCHISM_DATA_PARAMS = 'config/anarchism-data-params.json'
ANARCHISM_PROCESS_PARAMS = 'config/anarchism-process-params.json'
ANARCHISM_M_STAT_PARAMS = 'config/anarchism-m-stat-params.json'


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

    if 'anarchism' in targets:
        cfg = load_params(ANARCHISM_DATA_PARAMS)
        get_data(**cfg)
        remove_dir('data/raw')
        cfg = load_params(ANARCHISM_PROCESS_PARAMS)
        process_data(**cfg)
        remove_dir('data/temp')
        cfg = load_params(ANARCHISM_M_STAT_PARAMS)
        analyze_m_stat_data(**cfg)

    if 'obama' in targets:
        for i in range(6):
            cfg = load_params(OBAMA_DATA_PARAMS.replace('params', 'params-' + str(i + 1)))
            get_data(**cfg)
            remove_dir('data/raw')
            cfg = load_params(OBAMA_PROCESS_PARAMS.replace('params', 'params-' + str(i + 1)))
            process_data(**cfg)
            remove_dir('data/temp')
            cfg = load_params(OBAMA_M_STAT_PARAMS.replace('params', 'params-' + str(i + 1)))
            analyze_m_stat_data(**cfg)
            remove_dir('data/out')
    return


if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)
