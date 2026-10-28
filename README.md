Orders ETL Pipeline

I built this project to practise moving data from a CSV file into PostgreSQL, cleaning it along the way, and using SQL to answer questions about the data.

The dataset is intentionally messy. It contains duplicate orders, missing prices, negative quantities, and inconsistent status values. The idea was to work through some of the problems that can come up when handling data instead of starting with a perfectly clean dataset.

I used Python and pandas for the extraction and cleaning steps, SQLAlchemy to work with PostgreSQL, and SQL queries to analyse the results.

One thing I wanted to get right was making the pipeline safe to run more than once without creating duplicate records.

How it works

The pipeline follows four steps:

"Generate data → Clean data → Load into PostgreSQL → Analyse results"

Extract: Generate around 1,000 sample orders and save them to "orders_raw.csv". Some records contain duplicates or inconsistent values on purpose.

Transform: Use pandas to remove duplicate order IDs, standardise order statuses, parse dates, separate invalid rows, and calculate the total for each order.

Load: Create "customers" and "orders" tables in PostgreSQL using SQLAlchemy, then load the cleaned data using upserts.

Analyse: Run queries to find monthly revenue, the five customers who spent the most, and the number of orders in each status.

Tools used

- Python 3
- pandas
- SQLAlchemy 2.0
- PostgreSQL
- psycopg2
- python-dotenv

Getting started

These instructions are for Windows.

1. Clone the repository

git clone https://github.com/Robiah-9/orders-etl-pipeline.git
cd orders-etl-pipeline
python -m venv .venv

2. Activate the environment and install the dependencies

.venv\Scripts\activate
pip install -r requirements.txt

If PowerShell blocks the activation script because script execution is disabled, run this in the same terminal and try again:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

3. Create the database

Open PostgreSQL and create an empty database:

CREATE DATABASE orders_etl;

4. Configure your database connection

Copy ".env.example" to ".env":

copy .env.example .env

Open ".env" and enter your PostgreSQL credentials:

DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=orders_etl

The script checks that all five variables are present before connecting. If any are missing, it stops and displays an error message.

Keep your actual ".env" file private. It is included in ".gitignore" so your credentials aren't committed to the repository.

5. Run the pipeline

python etl_orders.py

You can run the script again to check that the pipeline is repeatable. With the same generated data, the output remains consistent, and the database retains 985 orders and 50 customers.

What came out of the pipeline?

The original dataset contains 1,025 rows. After cleaning:

- 25 duplicate rows were removed.
- 15 invalid rows were separated because they had a missing price or a non-positive quantity.
- 985 clean orders were loaded into PostgreSQL.

I also compared the revenue calculated with pandas against the revenue calculated in PostgreSQL. Both returned 1,346,115.32.

That comparison gave me a useful check that the data was being processed consistently before and after it was loaded into the database.

Sample output

Here are some of the results from the analysis queries.

Orders by status

shipped    220
reversed   208
ordered    195
returned   185
pending    177

Top five customers by spend

C025    52,930.07
C016    46,337.24
C043    43,027.10
C020    41,622.77
C045    41,270.44

Monthly revenue

2025-01       60,819.02
...
2026-06       50,074.68
TOTAL      1,346,115.32

A few decisions I made

I used upserts instead of inserting everything from scratch.

Customers use "ON CONFLICT DO NOTHING", while orders use "ON CONFLICT DO UPDATE". This lets the pipeline insert new records and update existing orders without creating duplicates.

I loaded customers before orders.

The orders table references the customers table through a foreign key, so the customers need to exist first. Both loads run in a single transaction, meaning a failure rolls back the changes rather than leaving a partially completed load.

I kept invalid records separate.

Instead of simply discarding every bad row, the transformation step returns a separate "rejected" DataFrame. This makes it possible to inspect the records that didn't pass validation.

I made the data reproducible.

The data generator uses a fixed seed, so it produces the same dataset each time. That makes it easier to test the pipeline and compare results between runs.

I kept database credentials out of the script.

The connection details come from environment variables in ".env". I also used SQLAlchemy's "URL.create" to build the connection URL, which handles special characters in passwords more safely.

What I'd improve next

There are a few things I'd like to add as I continue working on this project:

- Logging to track how many rows are read, rejected, and loaded.
- Saving rejected records to a file so they can be reviewed later.
- Tests for the transformation logic.
- A configuration file for settings that may change.
- A way to handle deleted records, since upserts alone don't remove records that no longer exist in the source data.

Project structure

orders-etl-pipeline/
├── etl_orders.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

Author

Robiat
