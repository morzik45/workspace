import logging
import os
import traceback

from kikimr.public.sdk.python import client as ydb
from kikimr.public.sdk.python.iam import ServiceAccountCredentials


class Storage(object):
    def __init__(
        self,
        *,
        path: str,
        endpoint: str = None,
        database: str = None,
        account_id: str = None,
        key_id: str = None,
        private_key: str = None,
    ) -> None:

        self._endpoint = endpoint
        if not self._endpoint:
            self._endpoint = os.environ.get("DB_ENDPOINT")

        self._database = database
        if not self._database:
            self._database = os.environ.get("DB_DATABASE")

        self._account_id = account_id
        if not self._account_id:
            self._account_id = os.environ.get("YC_SERVICE_ACCOUNT")

        self._key_id = key_id
        if not self._key_id:
            self._key_id = os.environ.get("YC_ACCESS_KEY")

        self._private_key = private_key
        if not self._private_key:
            self._private_key = os.environ.get("YC_PRIVATE_KEY")

        self._driver_config = self.make_driver_config()
        self._full_path: str = os.path.join(self._database, path)

        self.session_pool = self.session_pool_maker(self._driver_config)

    def transaction(self, query, parameters={}):
        def make_transaction(session: ydb.Session):
            tx = session.transaction(ydb.SerializableReadWrite()).begin()
            try:
                prepared_query = session.prepare(query)
            except Exception as e:
                return e
            return tx.execute(
                prepared_query,
                parameters=parameters,
                commit_tx=True,
            )

        return self.session_pool.retry_operation_sync(make_transaction)

    def make_driver_config(self):
        return ydb.DriverConfig(
            self._endpoint,
            self._database,
            credentials=ServiceAccountCredentials(
                service_account_id=self._account_id,
                access_key_id=self._key_id,
                private_key=self._private_key,
                iam_endpoint="iam.api.cloud.yandex.net:443",
                iam_channel_credentials={},
            ),
        )

    def session_pool_maker(self, driver_config: ydb.DriverConfig, size=1, workers_threads_count=1):
        driver = ydb.Driver(driver_config)
        try:
            logging.info("connecting to the database")
            driver.wait(timeout=5)
        except TimeoutError:
            logging.critical(
                f"connection failed\n" f"last reported errors by discovery: {driver.discovery_debug_details()}"
            )
            logf = open("error.log", "w")
            traceback.print_exc(file=logf)
            logf.close()
            raise
        return ydb.SessionPool(driver, size=size, workers_threads_count=workers_threads_count)