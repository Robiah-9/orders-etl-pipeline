Orders ETL Pipeline

I built this project to practise moving data from a CSV file into PostgreSQL, cleaning it along the way, and using SQL to answer questions about the data.

The dataset is intentionally messy. It contains duplicate orders, missing prices, negative quantities, and inconsistent order statuses. I wanted to work through some of the problems that can come up when handling real-world data rather than starting with a perfectly clean dataset.

I used Python and pandas to process the data, SQLAlchemy to work with PostgreSQL, and SQL queries to analyse the results.

I also wanted to make sure the pipeline could run more than once without creating duplicate records.

How It Works

The pipeline follows four steps:

Extract → Transform → Load → Analyse

1. Extract: Generate around 1,000 sample orders and save them to "orders_raw.csv".
2. Transform: Remove duplicate order IDs, standardise order statuses, parse dates, separate invalid records, and calculate each order's total.
3. Load: Create "customers" and "orders" tables in PostgreSQL and load the cleaned data using upserts.
4. Analyse: Query the database to calculate monthly revenue, identify the top five customers by spending, and count orders by status.

Tech Stack

- Python 3
- pandas
- SQLAlchemy 2.0
- PostgreSQL
- psycopg2
- python-dotenv

Getting Started

These instructions are for Windows.

1. Clone the Repository

git clone https://github.com/Robiah-9/orders-etl-pipeline.git
cd orders-etl-pipeline
python -m venv .venv

2. Install Dependencies

Activate the virtual environment and install the required packages:

.venv\Scripts\activate
pip install -r requirements.txt

If PowerShell blocks the activation script because script execution is disabled, run this in the same terminal and try again:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

3. Create the Database

Open PostgreSQL and create an empty database:

CREATE DATABASE orders_etl;

4. Configure the Database Connection

Copy the example environment file:

copy .env.example .env

Open ".env" and add your PostgreSQL credentials:

DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=orders_etl

The script checks that all five variables are set before connecting. If any are missing, it stops and displays an error message.

Your ".env" file is included in ".gitignore" to help prevent your credentials from being committed to GitHub.

5. Run the Pipeline

python etl_orders.py

Run the script again to check that it is repeatable. With the same generated data, the output should remain consistent, and the database should retain 985 orders and 50 customers.

Results

The original dataset contains 1,025 rows. After cleaning:

- 25 duplicate rows were removed.
- 15 invalid rows were separated because they contained a missing price or a non-positive quantity.
- 985 clean orders were loaded into PostgreSQL.

I also calculated total revenue using both pandas and PostgreSQL. Both returned 1,346,115.32.

Comparing the two results helped me check that the revenue calculation was consistent before and after loading the data into the database.

Sample Output

Orders by Status

shipped    220
reversed   208
ordered    195
returned   185
pending    177

Top Five Customers by Spend

C025    52,930.07
C016    46,337.24
C043    43,027.10
C020    41,622.77
C045    41,270.44

Monthly Revenue

2025-01       60,819.02
...
2026-06       50,074.68
TOTAL      1,346,115.32

Some Decisions I Made

Using Upserts

I used "ON CONFLICT DO NOTHING" for customers and "ON CONFLICT DO UPDATE" for orders.

This allows new records to be inserted and existing orders to be updated without creating duplicate records when the pipeline runs again.

Loading Customers First

The orders table references the customers table through a foreign key, so customers need to be loaded first.

Both loads run within a single transaction. If something fails during the load, the transaction can be rolled back instead of leaving a partially completed load.

Keeping Invalid Records Separate

Rather than losing track of records that fail validation, the transformation step returns a separate "rejected" DataFrame. This makes it possible to inspect the invalid records.

Making the Data Reproducible

The data generator uses a fixed seed, so it produces the same dataset on each run. This makes testing and comparing results easier.

Keeping Credentials Out of the Code

Database credentials are stored in ".env" instead of being hardcoded in the script.

I also used SQLAlchemy's "URL.create" to build the database connection URL, which handles special characters in passwords more safely.

What I'd Like to Improve

There are a few things I'd like to work on next:

- Add logging to track how many rows are read, rejected, and loaded.
- Save rejected records to a file for easier inspection.
- Write tests for the transformation logic.
- Move configurable settings into a separate configuration file.
- Add a way to handle deleted records, since upserts alone don't remove records that no longer exist in the source data.

Project Structure

orders-etl-pipeline/
├── etl_orders.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

Author

Robiat
