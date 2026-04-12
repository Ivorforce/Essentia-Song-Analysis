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

CHROMAPRINT_DIR = 'chromaprint'
CHROMAPRINT_BUILD = os.path.join(CHROMAPRINT_DIR, 'build')
CHROMAPRINT_INC = os.path.join(CHROMAPRINT_DIR, 'src')


def options(ctx):
    ctx.load('compiler_cxx')


def configure(ctx):
    ctx.load('compiler_cxx')

    if ctx.env.CXX_NAME == 'msvc':
        ctx.fatal('MSVC is not supported. Use MinGW (g++) or Clang instead.')

    # Build essentia as a static library using its own waf
    # C++14 is the minimum for Eigen
    print('-> Configuring essentia...')
    essentia_args = [sys.executable, 'waf', 'configure',
                     '--build-static', '--lightweight=', '--fft=KISS', '--std=c++14']
    if sys.platform == 'win32':
        essentia_args += ['--check-cxx-compiler=g++', '--check-c-compiler=gcc']
    subprocess.check_call(essentia_args, cwd=os.path.abspath(ESSENTIA_DIR))

    if sys.platform == 'win32':
        # Essentia's wscript adds MSVC flags (-W2, -EHsc) on win32 regardless
        # of the compiler. Patch the cached config to use GCC equivalents.
        cache_file = os.path.join(ESSENTIA_DIR, 'build', 'c4che', '_cache.py')
        with open(cache_file) as f:
            cache = f.read()
        cache = (cache
                 .replace("'-W2'", "'-Wall', '-D_USE_MATH_DEFINES'")
                 .replace(", '-EHsc'", ""))
        with open(cache_file, 'w') as f:
            f.write(cache)

    # Detect Eigen (needed for essentia headers)
    ctx.check_cfg(package='eigen3', uselib_store='EIGEN3',
                  args=['--cflags'])

    ctx.env.ESSENTIA_INC = os.path.abspath(ESSENTIA_INC)
    ctx.env.ESSENTIA_LIB = os.path.abspath(ESSENTIA_LIB)

    # Configure chromaprint via its CMake, statically, with bundled KissFFT
    print('-> Configuring chromaprint...')
    chromaprint_build_abs = os.path.abspath(CHROMAPRINT_BUILD)
    chromaprint_src_abs = os.path.abspath(CHROMAPRINT_DIR)
    if not os.path.isdir(chromaprint_build_abs):
        os.makedirs(chromaprint_build_abs)
    cmake_args = ['cmake',
                  '-DBUILD_SHARED_LIBS=OFF',
                  '-DBUILD_TOOLS=OFF',
                  '-DBUILD_TESTS=OFF',
                  '-DFFT_LIB=kissfft',
                  '-DCMAKE_POSITION_INDEPENDENT_CODE=ON',
                  '-DCMAKE_BUILD_TYPE=Release',
                  '-DCMAKE_POLICY_VERSION_MINIMUM=3.5',
                  chromaprint_src_abs]
    if sys.platform == 'win32':
        cmake_args.insert(1, '-G')
        cmake_args.insert(2, 'MinGW Makefiles')
    subprocess.check_call(cmake_args, cwd=chromaprint_build_abs)

    ctx.env.CHROMAPRINT_INC = os.path.abspath(CHROMAPRINT_INC)
    ctx.env.CHROMAPRINT_LIB = os.path.join(chromaprint_build_abs, 'src')


def build(ctx):
    # Build essentia first
    print('-> Building essentia...')
    subprocess.check_call(
        [sys.executable, 'waf', 'build'],
        cwd=os.path.abspath(ESSENTIA_DIR),
    )

    # Build chromaprint static lib
    print('-> Building chromaprint...')
    subprocess.check_call(
        ['cmake', '--build', '.', '--config', 'Release'],
        cwd=os.path.abspath(CHROMAPRINT_BUILD),
    )

    # Generate version.h from VERSION file
    version = open('VERSION').read().strip()
    essentia_version = open(os.path.join(ESSENTIA_DIR, 'VERSION')).read().strip()
    with open('src/version.h', 'w') as f:
        f.write('#ifndef VERSION_H_\n')
        f.write('#define VERSION_H_\n')
        f.write(f'#define SONG_ANALYZER_VERSION "{version}"\n')
        f.write(f'#define ESSENTIA_VERSION "{essentia_version}"\n')
        f.write('#endif\n')

    ctx.program(
        source=['src/main.cpp', 'src/analyze.cpp'],
        target='song-analyzer',
        includes=['src', ctx.env.ESSENTIA_INC, ctx.env.CHROMAPRINT_INC],
        use='EIGEN3',
        stlib=['essentia', 'chromaprint'],
        stlibpath=[ctx.env.ESSENTIA_LIB, ctx.env.CHROMAPRINT_LIB],
        # CHROMAPRINT_NODLL: chromaprint.h marks symbols __declspec(dllimport)
        # on Windows by default; we link statically so disable that.
        defines=['CHROMAPRINT_NODLL'],
        cxxflags=['-std=c++14', '-O2'],
    )
