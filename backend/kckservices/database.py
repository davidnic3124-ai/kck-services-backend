from contextlib import contextmanager
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from kckservices.config import settings

# dict_row -> every fetched row is a dict, e.g. row["brand"]
# prepare_threshold=None keeps it compatible with the Supabase connection pooler
pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=10,
    open=True,
    kwargs={"row_factory": dict_row, "prepare_threshold": None},
)

@contextmanager
def get_db():
    with pool.connection() as conn:
        yield conn
