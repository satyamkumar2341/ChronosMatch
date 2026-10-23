\# ChronosMatch



\*\*ChronosMatch\*\* is a high-frequency trading engine simulation developed as part of the Infotact Python Development Program. The project explores order matching, price-time priority, shared-memory communication, and performance benchmarking.



\## Features



\- \*\*Order Book:\*\* Maintains Buy and Sell orders grouped by price, with FIFO queues at each price level.

\- \*\*Matching Engine:\*\* Matches compatible Buy and Sell orders and records executed trades.

\- \*\*Cython Order Book:\*\* Provides a Cython-based implementation for testing and performance comparison.

\- \*\*Shared-Memory Ring Buffer:\*\* Uses `mmap` and `struct` for inter-process order communication.

\- \*\*Performance Benchmarks:\*\* Measures IPC throughput, matching throughput, and matching latency.

\- \*\*Terminal Dashboard:\*\* Displays simulated trading activity, best bid/ask, spread, throughput, and latency metrics.



> The dashboard uses synthetic demo orders; it is not connected to a live exchange.



\## Project Structure



```text

ChronosMatch/

├── src/

│   ├── order.py

│   ├── order\_book.py

│   ├── matching\_engine.py

│   ├── fast\_engine.pyx

│   ├── ring\_buffer.py

│   ├── ipc\_benchmark.py

│   ├── market\_firehose.py

│   ├── matching\_benchmark.py

│   └── dashboard.py

├── tests/

├── setup.py

└── README.md

```



\## Requirements



\- Python 3.13 (development environment)

\- Cython

\- setuptools

\- pytest

\- A compatible C/C++ build toolchain for compiling the Cython extension on Windows



Install the Python dependencies in your virtual environment as needed.



\## Run the Project



Activate your virtual environment, then run commands from the repository root.



\### 1. Terminal dashboard



```powershell

python -m src.dashboard

```



Press `Ctrl+C` to stop the dashboard.



\### 2. Shared-memory IPC benchmark



```powershell

python -m src.ipc\_benchmark

```



\### 3. Matching engine benchmark



```powershell

python -m src.matching\_benchmark

```



\### 4. Test suite



```powershell

python -m pytest -q

```



\### 5. Build the Cython extension



```powershell

python setup.py build\_ext --inplace

```



Building the extension on Windows requires Microsoft C++ Build Tools with a compatible compiler.



\## Verified Performance Results



\### Shared-memory IPC benchmark



A benchmark run transferred one million orders between the producer and consumer processes.



| Metric | Observed result |

|---|---:|

| Orders sent | 1,000,000 |

| Orders received | 1,000,000 |

| Elapsed time | 1.131 seconds |

| Throughput | 884,125 orders/second |

| Configured throughput target | 100,000 orders/second |

| Target achieved | Yes |



\### Matching engine benchmark



A previously recorded benchmark run reported:



| Metric | Observed result |

|---|---:|

| Orders matched | 10,000 |

| Trades | 10,000 |

| Elapsed time | 0.0427 seconds |

| Matching throughput | 234,130 pairs/second |

| Average latency | 2.797 microseconds |

| P99 latency | 5.8 microseconds |



Benchmark results depend on the machine, runtime, and test conditions. IPC throughput and matching throughput measure different operations and should not be compared as if they were the same metric.



\## Test Results



The project test suite completed successfully in the recorded run:



```text

41 passed

```



Run the test suite again after making changes to verify the current state.



\## Project Scope



ChronosMatch is an educational trading-engine simulation. It is intended to demonstrate order-book data structures, matching logic, inter-process communication, and performance measurement. It is not a production trading system and does not connect to a real exchange.
