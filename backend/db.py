
import json
import asyncpg
import ssl
from constants import FetchType,Constants
from logger import get_logger

log = get_logger("db")
class Rimiru:
    """
    Asynchronous DB access layer for Ouroboros.
    - Async CRUD using asyncpg
    - Async function calls
    - Built-in transaction helper
    - Uses a connection pool internally
    configured via class factory `Rimiru.shion()`

    """
    _instance = None          
    _pool: asyncpg.Pool = None # type: ignore
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    # ----------------------------------------------------
    # FACTORY: Create async Rimiru instance
    # ----------------------------------------------------
    @classmethod
    async def shion(cls):
        if cls._instance is not None:
            return cls._instance

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        log.info("creating connection pool host=%s db=%s", Constants.PGHOST, Constants.PGDATABASE)
        cls._pool = await asyncpg.create_pool(
            host=Constants.PGHOST,
            port=Constants.PGPORT,
            database=Constants.PGDATABASE,
            user=Constants.PGUSER,
            password=Constants.PGPASSWORD,
            ssl=ssl_ctx,
            min_size=2,
            max_size=10,
        )
        log.info("connection pool created (min=2 max=10)")

        cls._instance = cls(cls._pool)
        return cls._instance

    # ----------------------------------------------------
    # TRANSACTION HELPER
    # ----------------------------------------------------
    async def transaction(self):
        """
        Usage:
            async with db.transaction():
                await db.async_create(...)
                await db.async_update(...)
        """
        return self.pool.transaction() # type: ignore

    # ----------------------------------------------------
    #  CRUD
    # ----------------------------------------------------
    async def select(self, table: str, columns: list|None = None, filters: dict|None = None, 
                raw_where: str|None = None, raw_params: list|None = None,
                order_by: str|None = None, limit: int|None = None) -> list[dict]:
        """
        Select records with optional filtering
        
        :param table: Table name
        :param columns: List of columns to select (default: all)
        :param filters: Dictionary of column=value filters
        :param raw_where: Raw WHERE clause (use with raw_params for safety)
        :param raw_params: Parameters for raw_where clause
        :param order_by: Column to order by
        :param limit: Maximum number of records to return
        """
        cols = ", ".join(columns) if columns else "*"
        sql = f"SELECT {cols} FROM {table}"
        params = []
        param_count = 1
        
        if filters:
            where_clauses = []
            for key, value in filters.items():
                where_clauses.append(f"{key} = ${param_count}")
                params.append(value)
                param_count += 1
            sql += f" WHERE {' AND '.join(where_clauses)}"
            
        if raw_where:
            if filters:
                sql += f" AND ({raw_where})"
            else:
                sql += f" WHERE {raw_where}"
            if raw_params:
                params.extend(raw_params)
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        sql += ";"
        
        log.debug("select %s filters=%s raw_where=%s", table, filters, raw_where)
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            result = [dict(r) for r in rows]
            log.debug("select %s -> %s row(s)", table, len(result))
            return result

    async def selectOne(self, table: str, columns: list|None = None, filters: dict|None = None, order_by: str|None = None):
        """
        Select a single record with optional filtering
        
        :param table: Table name
        :param columns: List of columns to select (default: all)
        :param filters: Dictionary of column=value filters
        :param order_by: Column to order by (e.g., "created_at DESC")
        """
        row = await self.select(table, columns, filters, order_by, limit=1)
        return row[0] if row else None
   
    # -------------------------
    # UPSERT (INSERT or UPDATE)
    # -------------------------
    async def upsert(self, table: str, data: dict, conflict_column: str|None = None):
        """Insert or update a record based on conflict column
            To use this method, provide the following
            its important you know the unique constraint of the table you are upserting to.  The conflict_column parameter should be set to that unique constraint column.
            
                parameters:
                    :param table: Table name
                    :param data: Dictionary of column-value pairs
                    :param conflict_column: Column name to check for conflicts
            """
        try:
            columns = list(data.keys())
            values = [
                json.dumps(v) if isinstance(v, (dict, list)) else v
                for v in data.values()
            ]

            placeholders = ", ".join(f"${i+1}" for i in range(len(values)))
            cols = ", ".join(columns)
            update_cols = ", ".join(f"{k} = EXCLUDED.{k}" for k in columns if k != conflict_column)

            conflict_action = f"DO UPDATE SET {update_cols}" if update_cols else "DO NOTHING"
            returning_clause = "RETURNING *;" if update_cols else ";"

            sql = f"""
                INSERT INTO {table} ({cols}) 
                VALUES ({placeholders})
                ON CONFLICT ({conflict_column}) 
                {conflict_action}
                {returning_clause}
            """

            log.debug("upsert %s data=%s conflict=%s", table, data, conflict_column)
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, *values)
                result = dict(row) if row else None
                log.info("upsert %s (conflict=%s) -> %s", table, conflict_column, result)
                return result
        except Exception as e:
            log.exception("upsert %s failed: %s", table, type(e).__name__)
            raise
    # -------------------------
    async def delete(self, table: str, filters: dict):
        """Delete records matching filters. List values use ANY() for multi-match."""
        conditions = []
        params = []
        for i, (k, v) in enumerate(filters.items(), start=1):
            if isinstance(v, list):
                conditions.append(f"{k} = ANY(${i})")
            else:
                conditions.append(f"{k} = ${i}")
            params.append(v)

        where_clause = " AND ".join(conditions)
        sql = f"DELETE FROM {table} WHERE {where_clause} RETURNING *;"

        log.debug("delete %s filters=%s", table, filters)
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            log.info("delete %s filters=%s -> %s row(s) removed", table, filters, len(rows))
            return rows
    # ----------------------------------------------------
    # ASYNC FUNCTION CALLS
    # ----------------------------------------------------
    

    
    async def call_function(self, fn: str, params=None, fetch_type=None):
        #TODO: test if the dict lambda works here
        """
        fetch_type can be:
        - FetchType.FETCH: returns list of Record objects
        - FetchType.FETCHVAL: returns single scalar value
        - FetchType.FETCHROW: returns single Record object
        """
        params = params or []
        fetch_type = fetch_type or FetchType.FETCH.value  # Default to FETCH
        
        placeholders = ", ".join(f"${i+1}" for i in range(len(params)))
        sql = f"SELECT * FROM {fn}({placeholders});"

        log.debug("call_function %s params=%s fetch_type=%s", fn, params, fetch_type)
        async with self.pool.acquire() as conn:
            if fetch_type == FetchType.FETCHVAL.value:
                result = await conn.fetchval(sql, *params)
            elif fetch_type == FetchType.FETCHROW.value:
                result = await conn.fetchrow(sql, *params)
            else:  # FetchType.FETCH
                result = await conn.fetch(sql, *params)
            log.info("call_function %s -> %r", fn, result)
            return result

    async def execute(self, sql: str, params: list | None = None, fetch: bool = True):
        """Run raw SQL for cases the CRUD helpers don't cover (joins, INSERT...SELECT, etc).
        Always use $1, $2... placeholders for values — never string-interpolate
        user-controlled data into `sql`. Table/column names still must come from
        trusted code, never request data.
        :param fetch: True returns list[dict] via conn.fetch; False runs conn.execute
                    (for statements with no rows to return, e.g. bulk INSERT/UPDATE).
        """
        params = params or []
        one_line = " ".join(sql.split())
        log.debug("execute sql=%r params=%s fetch=%s", one_line[:200], params, fetch)
        async with self.pool.acquire() as conn:
            if fetch:
                rows = await conn.fetch(sql, *params)
                result = [dict(r) for r in rows]
                log.info("execute -> %s row(s)  [%s]", len(result), one_line[:80])
                return result
            status = await conn.execute(sql, *params)
            log.info("execute -> %s  [%s]", status, one_line[:80])
            return status

 
       