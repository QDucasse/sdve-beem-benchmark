# Simple DiVinE BEEM Benchmark

Translation of the [BEEM Benchmark][1]  to Simple DiVinE, a translation of DiVinE to a simple guard/effect list. A simple script to extract stats from the benchmark is made available. This script keeps a record of:

- Name of the experiment
- Number of `transient` variable declarations
- Number of non-`transient` variable declarations
- Number of `processes`
- Maximum number of operations per `guard`
- Maximum number of operations per `effect`
- Mean number of operations per `guard`
- Mean number of operations per `effect`

The whole `csv` file can be regenerated by calling:

```bash
$ python stats.py
```



[1 ]: https://github.com/plug-obp/beem-benchmark




