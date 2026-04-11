import sqlite3
import pandas as pd
from src.date_utils import SAVED_DATE_FORMAT

DB_PATH = "portfolio.db"

class SQLiteDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def ingest_excel(self, df:pd.DataFrame, table_name: str):
        df.to_sql(table_name, self.conn, if_exists="replace", index=False)
        self.conn.commit()

    def get_table(self, table_name: str) -> pd.DataFrame:
        return pd.read_sql(f"SELECT * FROM {table_name}", self.conn)

    def insert_transactions_from_df(self, df: pd.DataFrame):
        """
        Insert rows from a pandas DataFrame into the transactions table.
        """

        for _, row in df.iterrows():
            self.cursor.execute(
                """
                INSERT INTO transactions (
                    Date,
                    Portfolio,
                    Ticker,
                    "Asset Name",
                    "Asset Class",
                    Currency,
                    Action,
                    Quantity,
                    Value,
                    "Value (base)",
                    "Price per Unit",
                    Year
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pd.to_datetime(row.get("Date")).strftime(SAVED_DATE_FORMAT) if pd.notna(row.get("Date")) else None,
                    row.get("Portfolio"),
                    row.get("Ticker"),
                    row.get("Asset Name"),
                    row.get("Asset Class"),
                    row.get("Currency"),
                    row.get("Action"),
                    row.get("Quantity"),
                    row.get("Value"),
                    row.get("Value (base)"),
                    row.get("Price per Unit"),
                    int(row.get("Year")) if pd.notna(row.get("Year")) else None,
                ),
            )

        self.conn.commit()

    def close(self):
        self.conn.close()


db = SQLiteDB()