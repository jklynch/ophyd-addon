import logging

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.plans import count
from databroker import catalog

from ophyd_addon.areadetector.document_builders import NewPerkinElmerDetector


logging.getLogger("TiffWriter").setLevel(logging.DEBUG)
logging.getLogger("TiffWriter").addHandler(logging.StreamHandler())


def run():
    """
    # setup for simulated IOC
    EPICS_CA_ADDR_LIST=127.0.0.1:5064
    EPICS_CA_AUTO_ADDR_LIST=NO

    Run mongo.

    Run simulated IOC.
    """
    # arg_parser = argparse.ArgumentParser()
    # arg_parser.add_argument("--agent-name", required=True, type=str)
    # arg_parser.add_argument("--episode-count", required=True, type=int)

    # args = arg_parser.parse_args()

    RE = RunEngine()

    bec = BestEffortCallback()

    RE.subscribe(bec)

    db = catalog["mad"]  # this is set up by entrypoint

    RE.subscribe(db.v1.insert)

    tiff_sim_detector = NewPerkinElmerDetector(
        prefix="Sim{{det1}}:", name="tiff_sim_detector"
    )
    RE(count([tiff_sim_detector]))


if __name__ == "__main__":
    run()
