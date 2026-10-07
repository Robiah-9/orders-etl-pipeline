# Orders ETL Pipeline

A small end-to-end ETL pipeline in Python. It generates a deliberately messy orders dataset, cleans it with pandas, loads it into PostgreSQL through SQLAlchemy, and answers business questions with SQLAlchemy queries.

Running the script twice does **not** create duplicate rows.

## What it does

| Stage | What happens |
|-------|--------------|
| **Extract** | Generates ~1,000 fake orders and saves them to `orders_raw.csv`, with deliberate mess: duplicate `order_id`s, null prices, negative quantities, and inconsistent status casing (`shipped`, `SHIPPED`, `Shipped`). |
| **Transform** | Uses pandas to drop duplicates, normalize status text, parse dates, split out invalid rows, and add a `total` column. |
| **Load** | Defines `customers` and `orders` tables as SQLAlchemy models and loads the clean data into PostgreSQL using upserts (`INSERT ... ON CONFLICT`). |
| **Analyze** | Runs three SQLAlchemy queries: revenue per month, top 5 customers by spend, and order count per status. |

```
generate_csv -> read CSV -> transform -> load -> analyze
```

## Tech stack

- Python 3
- pandas
- SQLAlchemy 2.0
- PostgreSQL (via `psycopg2`)
- python-dotenv

## Setup (Windows)

1. **Clone the repo and create a virtual environment**

```
   git clone <your-repo-url>
   cd <your-repo-folder>
   python -m venv .venv
```

2. **Activate the environment and install dependencies**

```
   .venv\Scripts\activate
   pip install -r requirements.txt
```

   If PowerShell blocks the activate step with an error about scripts being disabled, run this once in that window and try again:

```
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

3. **Create an empty PostgreSQL database**

```sql
   CREATE DATABASE orders_etl;
```

4. **Add your credentials.** Copy the example file and fill in your values:

```
   copy .env.example .env
```

```
   DB_USER=your_user
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=orders_etl
```

   The script checks that all five variables are set and stops with a clear message if any are missing.

## Run

```
python etl_orders.py
```

Run it a second time to confirm it is repeatable: the output is identical and the row counts stay the same (985 orders, 50 customers).

## Sample output

```
Orders per status
  shipped    220
  reversed   208
  ordered    195
  returned   185
  pending    177
Top 5 customers by spend
  C025  52,930.07
  C016  46,337.24
  C043  43,027.10
  C020  41,622.77
  C045  41,270.44
Revenue per month
  2025-01     60,819.02
  ...
  2026-06     50,074.68
  TOTAL    1,346,115.32
```

## How the data flows

Of the 1,025 raw rows:

- 25 are duplicate `order_id`s and are dropped
- 15 are invalid (null price or non-positive quantity) and are separated out
- 985 clean rows are loaded

The total revenue computed in SQL (1,346,115.32) matches the total computed in pandas, which is a quick check that no data was lost on the way into the database.

## Design notes

- **Repeatable loads.** Customers use `ON CONFLICT DO NOTHING`. Orders use `ON CONFLICT DO UPDATE`, so new orders are inserted and existing ones are refreshed instead of duplicated.
- **One transaction.** Customers and orders are loaded in a single transaction, so a failure rolls everything back instead of leaving half-loaded data. Customers load first because of the foreign key.
- **Invalid rows are kept, not deleted.** The transform step returns a separate `rejected` DataFrame so bad rows can be inspected.
- **Reproducible data.** The generator is seeded, so every run produces the same dataset.
- **Credentials stay out of the code.** They are read from `.env` (which is git-ignored), and the connection URL is built with `URL.create` so special characters in a password cannot break it.

## Project structure

```
.
├── etl_orders.py       # the whole pipeline
├── requirements.txt
├── .env.example        # template for credentials
├── .gitignore
└── README.md
```

## Possible next steps

- Add logging for rows read, dropped, and loaded
- Save the rejected rows to a file
- Move file names and settings into constants or a config file
- Add tests for the transform step
- Handle deletions, since upserts never remove old rows

## Author

Robiat