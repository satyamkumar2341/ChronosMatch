# ChronosMatch

Educational HFT engine simulation developed during the Infotact Python Development Program.

## Features

* Price-time priority order book and FIFO queues
* Python and Cython matching engines
* mmap and struct shared-memory ring buffer
* Asynchronous order production and matching pipeline
* SQLite trade persistence and order-based history filters
* Terminal trading dashboard
* Automated tests

## Installation

python -m pip install cython setuptools pytest

## Run

python -m src.dashboard
python -m src.ipc\_benchmark
python -m src.matching\_benchmark
python -m src.engine\_comparison
python -m pytest -q
python setup.py build\_ext --inplace

\## Latest Benchmark Snapshot



Tested on the local development environment.



| Benchmark | Result |

|---|---:|

| IPC throughput (1M orders) | 647,086 orders/sec |

| Python matching (10K pairs) | 287,105 pairs/sec |

| Cython matching (10K pairs) | 446,159 pairs/sec |

| Cython throughput improvement | 55.4% |

| Python average latency | 2.20 µs |

| Cython average latency | 1.15 µs |

| Automated tests | 84 passed |



Results depend on hardware and runtime conditions. These are simulation benchmarks, not production exchange performance measurements.

## Scope

Synthetic orders only. No live exchange connection. This is an educational simulation, not a production trading system.

