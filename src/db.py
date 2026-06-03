import os
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

load_dotenv()

APP_TO_DB_COLUMNS = {
    "Date": "date",
    "Portfolio": "portfolio",
    "Ticker": "ticker",
    "Asset Name": "asset_name",
    "Asset Class": "asset_class",
    "Currency": "currency",
    "Action": "action",
    "Quantity": "quantity",
    "Value": "value",
    "Value (base)": "value_base",
    "Price per Unit": "price_per_unit",
    "Year": "year",
}

DB_TO_APP_COLUMNS = {db_col: app_col for app_col, db_col in APP_TO_DB_COLUMNS.items()}

TRANSACTIONS_SELECT = """
SELECT
    id,
    date,
    portfolio,
    ticker,
    asset_name,
    asset_class,
    currency,
    action,
    quantity,
    value,
    value_base,
    price_per_unit,
    year
FROM transactions
ORDER BY id
"""


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")

    try:
        if "DATABASE_URL" in st.secrets:
            url = str(st.secrets["DATABASE_URL"])
    except (AttributeError, RuntimeError):
        pass

    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to .streamlit/secrets.toml locally "
            "or Streamlit Cloud secrets."
        )

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

    if "sslmode=" not in url:
        url += "&sslmode=require" if "?" in url else "?sslmode=require"

    return url


def _map_db_df_to_app(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["id", *APP_TO_DB_COLUMNS.keys()])

    mapped = df.rename(columns=DB_TO_APP_COLUMNS)
    ordered_cols = ["id", *APP_TO_DB_COLUMNS.keys()]
    return mapped[[col for col in ordered_cols if col in mapped.columns]]


class PostgresDB:
    def __init__(self):
        self._engine: Engine | None = None

    @property
    def engine(self) -> Engine:
        if self._engine is not None:
            return self._engine

        url = get_database_url()
        host = urlparse(url).hostname or ""
        if host.startswith("db.") and host.endswith(".supabase.co"):
            raise RuntimeError(
                "DATABASE_URL uses Supabase direct host (db.*.supabase.co), which is "
                "IPv6-only on many projects. Use the IPv4 pooler string from "
                "Supabase → Project Settings → Database → Connection pooling "
                "(e.g. aws-1-ap-southeast-1.pooler.supabase.com:6543, user "
                "postgres.<project-ref>)."
            )

        engine_kwargs: dict = {
            "pool_pre_ping": True,
            "connect_args": {"connect_timeout": 10},
        }
        if urlparse(url).port == 6543:
            engine_kwargs["poolclass"] = NullPool

        self._engine = create_engine(url, **engine_kwargs)
        return self._engine

    def ingest_excel(self, df: pd.DataFrame, table_name: str):
        if table_name == "transactions":
            renamed = df.rename(columns=APP_TO_DB_COLUMNS)
            db_cols = list(APP_TO_DB_COLUMNS.values())
            payload = renamed[[col for col in db_cols if col in renamed.columns]]
        else:
            payload = df
        payload.to_sql(table_name, self.engine, if_exists="replace", index=False)

    def get_table(self, table_name: str) -> pd.DataFrame:
        df = pd.read_sql(f"SELECT * FROM {table_name}", self.engine)
        if table_name == "transactions":
            return _map_db_df_to_app(df)
        return df

    def get_transactions(self) -> pd.DataFrame:
        df = pd.read_sql(TRANSACTIONS_SELECT, self.engine)
        return _map_db_df_to_app(df)

    def insert_transactions_from_df(self, df: pd.DataFrame):
        insert_sql = text("""
            INSERT INTO transactions (
                date, portfolio, ticker, asset_name, asset_class, currency,
                action, quantity, value, value_base, price_per_unit, year
            )
            VALUES (
                :date, :portfolio, :ticker, :asset_name, :asset_class, :currency,
                :action, :quantity, :value, :value_base, :price_per_unit, :year
            )
            """)

        with self.engine.begin() as conn:
            for _, row in df.iterrows():
                conn.execute(
                    insert_sql,
                    {
                        "date": (
                            pd.to_datetime(row.get("Date"))
                            if pd.notna(row.get("Date"))
                            else None
                        ),
                        "portfolio": row.get("Portfolio"),
                        "ticker": row.get("Ticker"),
                        "asset_name": row.get("Asset Name"),
                        "asset_class": row.get("Asset Class"),
                        "currency": row.get("Currency"),
                        "action": row.get("Action"),
                        "quantity": (
                            int(row.get("Quantity"))
                            if pd.notna(row.get("Quantity"))
                            else None
                        ),
                        "value": row.get("Value"),
                        "value_base": row.get("Value (base)"),
                        "price_per_unit": row.get("Price per Unit"),
                        "year": (
                            int(row.get("Year")) if pd.notna(row.get("Year")) else None
                        ),
                    },
                )

    def delete_transaction(self, transaction_id: int):
        with self.engine.begin() as conn:
            conn.execute(
                text("DELETE FROM transactions WHERE id = :id"),
                {"id": transaction_id},
            )

    def update_transaction(self, transaction_id: int, updates: dict):
        if not updates:
            return

        set_parts = []
        params: dict = {"id": transaction_id}

        for key, value in updates.items():
            if key == "id":
                continue
            db_col = APP_TO_DB_COLUMNS.get(key)
            if db_col is None:
                continue

            if key == "Date" and pd.notna(value):
                value = pd.to_datetime(value)
            if key == "Year" and pd.notna(value):
                value = int(value)
            if key == "Quantity" and pd.notna(value):
                value = int(value)

            set_parts.append(f"{db_col} = :{db_col}")
            params[db_col] = value

        if not set_parts:
            return

        sql = text(f"UPDATE transactions SET {', '.join(set_parts)} WHERE id = :id")
        with self.engine.begin() as conn:
            conn.execute(sql, params)

    def close(self):
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None


db = PostgresDB()
SQLiteDB = PostgresDB  # notebooks/scripts
