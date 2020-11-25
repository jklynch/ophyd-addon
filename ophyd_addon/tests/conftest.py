from contextlib import contextmanager
from pathlib import Path

import intake
from mongobox import MongoBox
import pytest

from bluesky.tests.conftest import RE  # noqa


@pytest.fixture(scope="function")
def databroker(request, tmp_path):
    @contextmanager
    def _databroker():
        mongo_box = MongoBox()
        try:
            mongo_box.start()
            mongo_client = mongo_box.client()
            mongo_host, mongo_port = mongo_client.address
            mongo_uri = f"mongodb://{mongo_host}:{mongo_port}"
            catalog_descriptor_path = tmp_path / Path("mad.yml")
            with open(catalog_descriptor_path, "w") as f:
                f.write(
                    f"""\
sources:
  mad:
    description: Made up beamline
    driver: "bluesky-mongo-normalized-catalog"
    container: catalog
    args:
      metadatastore_db: {mongo_uri}
      asset_registry_db: {mongo_uri}
      handler_registry:
        NPY_SEQ: ophyd.sim.NumpySeqHandler
    metadata:
      beamline: "00-ID"
"""
                )

            yield intake.open_catalog(catalog_descriptor_path)
        finally:
            mongo_box.stop()

    return _databroker
