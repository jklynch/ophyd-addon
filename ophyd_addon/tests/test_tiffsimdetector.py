import pytest

from bluesky.plans import count

from ophyd import _caproto_shim
from ophyd_addon.areadetector.document_builders import NewPerkinElmerDetector


@pytest.mark.skip
def test_tiffsimdetector(RE, databroker):
    tiff_sim_detector = NewPerkinElmerDetector(name="sim")

    with databroker() as db:
        RE.subscribe(db.insert)
        RE(count([tiff_sim_detector]))
