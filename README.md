# ChronosMatch

Educational HFT engine simulation developed during the Infotact Python Development Program.

## Features
- Price-time priority order book and FIFO queues
- Python and Cython matching engines
- mmap and struct shared-memory ring buffer
- Asynchronous order production and matching pipeline
- SQLite trade persistence and order-based history filters
- Terminal trading dashboard
- Automated tests

## Installation
python -m pip install cython setuptools pytest

## Run
python -m src.dashboard
python -m src.ipc_benchmark
python -m src.matching_benchmark
python -m src.engine_comparison
python -m pytest -q
python setup.py build_ext --inplace

## Latest Benchmark Snapshot
- IPC: 619,744 orders/sec
- Python matching: 198,425 pairs/sec
- Cython matching: 313,181 pairs/sec
- Cython improvement: 57.8%
- Tests: 84 passed

Results depend on hardware and runtime. Dashboard throughput is an asynchronous in-process simulation metric.

## Scope
Synthetic orders only. No live exchange connection. This is an educational simulation, not a production trading system.
