import os
from datetime import datetime

from kikimr.public.sdk.python import client as ydb
from utils.storage import Storage


class Users(object):
    __slots__ = ("user_id", "username", "lang", "refferal", "created_at", "stickers", "_storage")

    def __init__(
        self,
        user_id: int,
        username: str = "",
        lang: str = "ru",
        refferal: str = "",
        created_at: datetime = datetime.utcnow(),
        stickers: int = 0,
        storage: Storage = None,
    ):

        self._storage = storage
        if self._storage is None:
            from loader import storage

            self._storage = storage

        query = f"""
            PRAGMA TablePathPrefix("{storage._full_path}");
            DECLARE $user_id AS Uint64;
            SELECT * FROM users WHERE user_id = $user_id;
            """

        parameters = {"$user_id": user_id}

        result = self._storage.transaction(query=query, parameters=parameters)
        if isinstance(result, ydb.SchemeError) and result.issues[0].issues[0].issues[0].message.startswith(
            "Cannot find table"
        ):
            self.__create_table()
            del result
            result = self._storage.transaction(query=query, parameters=parameters)[0].rows

        else:
            result = result[0].rows

        if len(result) == 0:
            query2 = f"""
                PRAGMA TablePathPrefix("{self._storage._full_path}");
                DECLARE $user_id AS Uint64;
                DECLARE $username AS Utf8;
                DECLARE $lang AS Utf8;
                DECLARE $refferal AS Utf8;
                DECLARE $created_at AS DateTime;
                DECLARE $stickers AS Int64;
                INSERT INTO users (user_id, username, lang, refferal, created_at, stickers) VALUES
                ($user_id, $username, $lang, $refferal, $created_at, $stickers);
                """

            parameters2 = {
                "$user_id": int(user_id),
                "$username": username,
                "$lang": lang,
                "$refferal": refferal if refferal is not None else "",
                "$created_at": int(datetime.utcnow().timestamp()),
                "$stickers": 0,
            }

            self._storage.transaction(query=query2, parameters=parameters2)

            result = self._storage.transaction(query=query, parameters=parameters)[0].rows

        r = result[0]
        self.user_id = r.user_id
        self.username = r.username
        self.lang = r.lang
        self.refferal = r.refferal
        self.created_at = datetime.fromtimestamp(r.created_at)
        self.stickers = r.stickers

    def __create_table(self):
        def make_transaction(session: ydb.Session):
            return session.create_table(
                os.path.join(self._storage._full_path, "users"),
                ydb.TableDescription()
                .with_column(ydb.Column("user_id", ydb.OptionalType(ydb.PrimitiveType.Uint64)))
                .with_column(ydb.Column("username", ydb.OptionalType(ydb.PrimitiveType.Utf8)))
                .with_column(ydb.Column("lang", ydb.OptionalType(ydb.PrimitiveType.Utf8)))
                .with_column(ydb.Column("refferal", ydb.OptionalType(ydb.PrimitiveType.Utf8)))
                .with_column(ydb.Column("created_at", ydb.OptionalType(ydb.PrimitiveType.Datetime)))
                .with_column(ydb.Column("stickers", ydb.OptionalType(ydb.PrimitiveType.Int64)))
                .with_primary_key("user_id"),
            )

        self._storage.session_pool.retry_operation_sync(make_transaction)

    def stickers_count_incr(self) -> None:
        query = f"""
            PRAGMA TablePathPrefix("{self._storage._full_path}");
            DECLARE $user_id AS Uint64;
            UPDATE users
            SET stickers  = stickers + 1
            WHERE user_id = $user_id;
            """
        parameters = {
            "$user_id": int(self.user_id),
        }

        self._storage.transaction(query=query, parameters=parameters)
        self.stickers += 1
