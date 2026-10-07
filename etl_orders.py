import os
import random
from datetime import date, timedelta

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (Date, Float, ForeignKey, Integer, String,
                        create_engine, func, select)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


load_dotenv()

required = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]

missing = []
for name in required:
    if os.getenv(name) is None:
        missing.append(name)

if missing:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

url = URL.create(
    "postgresql+psycopg2",
    username=db_user,
    password=db_password,
    host=db_host,
    port=int(db_port),
    database=db_name,
)
engine = create_engine(url)


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"
    customer_id: Mapped[str] = mapped_column(String, primary_key=True)


class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"))
    product: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    order_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String)
    total: Mapped[float] = mapped_column(Float)


def generate_csv(path, n=1000, seed=42):
    rng = random.Random(seed)

    products = {"Laptop": 899.99, "Mouse": 19.99, "Keyboard": 500.41, "CPU": 900,
                "Printer": 655.19, "Pen": 16.9, "Book": 20.99}
    statuses = ["pending", "returned", "ordered", "reversed", "shipped"]
    customers = []
    for i in range(1, 51):
        customers.append(f"C{i:03d}")

    rows = []
    start_date = date(2025, 1, 1)
    for i in range(1, n + 1):
        product = rng.choice(list(products))
        order = {
            "order_id": i,
            "customer_id": rng.choice(customers),
            "product": product,
            "quantity": rng.randint(1, 5),
            "unit_price": products[product],
            "order_date": (start_date + timedelta(days=rng.randint(0, 540))).isoformat(),
            "status": rng.choice(statuses),
        }
        rows.append(order)

    for order in rng.sample(rows, 12):
        order["unit_price"] = None

    for order in rng.sample(rows, 3):
        order["quantity"] = order["quantity"] * -1

    for order in rng.sample(rows, 200):
        if rng.random() < 0.5:
            order["status"] = order["status"].upper()
        else:
            order["status"] = order["status"].title()

    for order in rng.sample(rows, 25):
        rows.append(order.copy())

    rng.shuffle(rows)

    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)


def transform(raw):
    df = raw.copy()
    df = df.drop_duplicates(subset="order_id")
    df["status"] = df["status"].str.strip().str.lower()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    valid = (df["unit_price"].notna()) & (df["quantity"] > 0) & (df["order_date"].notna())
    rejected = df[~valid]
    clean = df[valid].copy()
    clean["total"] = clean["unit_price"] * clean["quantity"]
    return clean, rejected


def load(clean, engine):
    Base.metadata.create_all(engine)

    customers = []
    for cid in clean["customer_id"].unique():
        customers.append({"customer_id": cid})

    orders_df = clean.copy()
    orders_df["order_date"] = orders_df["order_date"].dt.date
    orders = orders_df.to_dict("records")

    with Session(engine) as session, session.begin():
        session.execute(insert(Customer).on_conflict_do_nothing(), customers)

        stmt = insert(Order)
        stmt = stmt.on_conflict_do_update(
            index_elements=["order_id"],
            set_={
                "customer_id": stmt.excluded.customer_id,
                "product": stmt.excluded.product,
                "quantity": stmt.excluded.quantity,
                "unit_price": stmt.excluded.unit_price,
                "order_date": stmt.excluded.order_date,
                "status": stmt.excluded.status,
                "total": stmt.excluded.total,
            },
        )
        session.execute(stmt, orders)

    return len(orders)


def analyze(engine):
    with Session(engine) as session:

        print("Orders per status")
        status_stmt = (
            select(Order.status, func.count().label("n"))
            .group_by(Order.status)
            .order_by(func.count().desc())
        )
        for status, n in session.execute(status_stmt):
            print(f"  {status:<10} {n}")

        print("Top 5 customers by spend")
        top_stmt = (
            select(Order.customer_id, func.sum(Order.total).label("spend"))
            .group_by(Order.customer_id)
            .order_by(func.sum(Order.total).desc())
            .limit(5)
        )
        for customer_id, spend in session.execute(top_stmt):
            print(f"  {customer_id}  {round(spend, 2):,.2f}")

        print("Revenue per month")
        month = func.to_char(Order.order_date, "YYYY-MM").label("month")
        month_stmt = (
            select(month, func.sum(Order.total).label("revenue"))
            .group_by(month)
            .order_by(month)
        )
        for m, revenue in session.execute(month_stmt):
            print(f"  {m}  {round(revenue, 2):>12,.2f}")

        grand_total = session.scalar(select(func.sum(Order.total)))
        print(f"  TOTAL    {round(grand_total, 2):>12,.2f}")


def main():
    generate_csv("orders_raw.csv")
    raw = pd.read_csv("orders_raw.csv")

    clean, rejected = transform(raw)
    loaded = load(clean, engine)
    analyze(engine)


if __name__ == "__main__":
    main()