import asyncio
import logging

from bluesky import RunEngine, Msg
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.log import config_bluesky_logging
from bluesky.plans import count
from databroker import catalog

from caproto import config_caproto_logging

from ophyd_addon.areadetector.document_builders import NewPerkinElmerDetector
from ophyd_addon.perkin_elmer_diffraction_plan import pe_count

from ophyd.log import config_ophyd_logging

# config_bluesky_logging(level=logging.DEBUG)
# config_caproto_logging(level=logging.DEBUG)
# config_ophyd_logging(level=logging.DEBUG)


logging.getLogger("TiffWriter").setLevel(logging.DEBUG)
logging.getLogger("TiffWriter").addHandler(logging.StreamHandler())


def run():
    """
    # setup for simulated IOC
    EPICS_CA_ADDR_LIST=127.0.0.1:5064
    EPICS_CA_AUTO_ADDR_LIST=NO

    Run mongo or you will get "All EventDispatch queues are empty."

    Run simulated IOC.
    """
    # arg_parser = argparse.ArgumentParser()
    # arg_parser.add_argument("--agent-name", required=True, type=str)
    # arg_parser.add_argument("--episode-count", required=True, type=int)

    # args = arg_parser.parse_args()

    class MyRunEngine(RunEngine):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        async def _wait_for_status(self, msg):
            """
            Block progress until every status object is done.
            Expected message object is:
                Msg('wait_for_status', None, *statuses)
            where ``statuses`` is an iterable of StatusBase objects
            """
            assert msg.obj is None
            assert not msg.kwargs
            pardon_failures = self._pardon_failures

            statuses = msg.args
            futures = []

            for _status in statuses:
                self.log.info("*** wait for status %s", _status)
                _p_event = asyncio.Event(loop=self._loop_for_kwargs)

                # do closure via defaults,
                def done_callback(status=None, *, p_event=_p_event):
                    self.log.debug(
                        "The status object %r reports set is done with status %r",
                        status,
                        status.success,
                    )
                    task = self._loop.call_soon_threadsafe(
                        self._status_object_completed, status, p_event, pardon_failures
                    )
                    self._status_tasks.append(task)

                try:
                    _status.add_callback(done_callback)
                except AttributeError:
                    # for ophyd < v0.8.0
                    _status.finished_cb = done_callback
                futures.append(_p_event.wait)
            try:
                if self.waiting_hook is not None:
                    # Notify the waiting_hook function that the RunEngine is
                    # waiting for these status_objs to complete. Users can use
                    # the information these encapsulate to create a progress
                    # bar.
                    self.waiting_hook(statuses)
                    await self._wait_for(Msg("wait_for", None, futures))
            finally:
                if self.waiting_hook is not None:
                    # Notify the waiting_hook function that we have moved on by
                    # sending it `None`. If all goes well, it could have
                    # inferred this from the status_obj, but there are edge
                    # cases.
                    self.waiting_hook(None)

    RE = MyRunEngine()
    RE.register_command(name="wait_for_status", func=RE._wait_for_status)

    bec = BestEffortCallback()

    RE.subscribe(bec)

    db = catalog["mab"]  # this is set up by entrypoint

    RE.subscribe(db.v1.insert)

    RE(
        pe_count(
            filename="",
            exposure=1,
            num_images=1,
            num_dark_images=1,
            num_repetitions=1,
            delay=2,
        )
    )


if __name__ == "__main__":
    run()
