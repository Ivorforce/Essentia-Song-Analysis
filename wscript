#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

top = '.'
out = 'build'

ESSENTIA_DIR = 'essentia'
ESSENTIA_LIB = os.path.join(ESSENTIA_DIR, 'build', 'src')
ESSENTIA_INC = os.path.join(ESSENTIA_DIR, 'src')


def options(ctx):
    ctx.load('compiler_cxx')


def configure(ctx):
    ctx.load('compiler_cxx')

    # Build essentia as a static library using its own waf
    print('→ Configuring essentia...')
    subprocess.check_call(
        [sys.executable, 'waf', 'configure',
         '--build-static', "--lightweight=", '--fft=KISS', '--std=c++17'],
        cwd=os.path.abspath(ESSENTIA_DIR),
    )

    # Detect Eigen (needed for essentia headers)
    ctx.check_cfg(package='eigen3', uselib_store='EIGEN3',
                  args=['--cflags'])

    ctx.env.ESSENTIA_INC = os.path.abspath(ESSENTIA_INC)
    ctx.env.ESSENTIA_LIB = os.path.abspath(ESSENTIA_LIB)


def build(ctx):
    # Build essentia first
    print('→ Building essentia...')
    subprocess.check_call(
        [sys.executable, 'waf', 'build'],
        cwd=os.path.abspath(ESSENTIA_DIR),
    )

    cxxflags = ['/std:c++17'] if sys.platform == 'win32' else ['-std=c++17']

    ctx.program(
        source='src/main.cpp',
        target='song-analyzer',
        includes=[ctx.env.ESSENTIA_INC],
        use='EIGEN3',
        stlib=['essentia'],
        stlibpath=[ctx.env.ESSENTIA_LIB],
        cxxflags=cxxflags,
    )
