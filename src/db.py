import sqlite3
import pandas as pd

DB_PATH = "portfolio.db"

class SQLiteDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

    def ingest_excel(self, df:pd.DataFrame, table_name: str):
        df.to_sql(table_name, self.conn, if_exists="replace", index=False)
        self.conn.commit()

    def get_table(self, table_name: str) -> pd.DataFrame:
        return pd.read_sql(f"SELECT * FROM {table_name}", self.conn)

    def init_db(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                portfolio TEXT,
                ticker TEXT,
                asset_name TEXT,
                asset_class TEXT,
                currency TEXT,
                action TEXT,
                quantity REAL,
                value REAL,
                value_base REAL,
                price_per_unit REAL,
                year INTEGER
            )
            """
        )

        self.conn.commit()

    def insert_transactions_from_df(self, df: pd.DataFrame):
        """
        Insert rows from a pandas DataFrame into the transactions table.
        """

        for _, row in df.iterrows():
            self.cursor.execute(
                """
                INSERT INTO transactions (
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
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(pd.to_datetime(row["Date"]).date()) if pd.notna(row["Date"]) else None,
                    row["Portfolio"],
                    row["Ticker"],
                    row["Asset Name"],
                    row["Asset Class"],
                    row["Currency"],
                    row["Action"],
                    row["Quantity"],
                    row["Value"],
                    row["Value (base)"],
                    row["Price per Unit"],
                    int(row["Year"]) if pd.notna(row["Year"]) else None,
                ),
            )

        self.conn.commit()

    def close(self):
        self.conn.close()


