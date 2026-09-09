# Retry Without Backoff: Lab

This lab measures how retry backoff affects CPU usage when clients repeatedly call a server that can fail.

## Prerequisites

Before running the lab, make sure the following are installed on your machine:

- Bash shell
- Docker Engine
- Docker Compose plugin

## Run the scenario

From this folder, run:

```bash
./run_scenario.sh
```

## What the script does

The script will:

- start the `server` and `client` services with Docker Compose
- run multiple retry scenarios across several backoff settings and concurrency levels
- collect Docker CPU statistics for each scenario
- stop the stack after each scenario and move to the next one

## Where the output goes

The generated metrics are written to:

```text
./metrics/
```

Inside that folder you will find files such as:

- `0ms-1c-docker-stats.tsv`
- `10ms-1c-docker-stats.tsv`
- `1000ms-4c-docker-stats.tsv`

Each file is a TSV containing CPU samples for the scenario. The file format is:

```text
Timestamp_Ms  NAME                 CPU %
...
```

The metrics directory will contain one `.tsv` file per backoff/concurrency combination. Those files are the raw inputs for the analysis step.

## What is in the output files

Each generated TSV file contains:

- a timestamp (in milliseconds)
- the Docker container/service name (`retry-backoff-client` or `retry-backoff-server`)
- the CPU usage percentage for that container at that moment

This lets you compare how CPU load changes as the backoff increases and as client concurrency changes.
