from contextlib import contextmanager
import multiprocessing
import time

from caproto.server import run
from caproto.threading.client import Context as CaprotoThreadingClient

from ophyd_addon.simulated_perkin_elmer_detector_ioc import (
    PluginBasePVGroup,
    FilePluginPVGroup,
    ArrayBasePVGroup,
    SimulatedPerkinElmerDetectorIoc,
)
from ophyd_addon.areadetector.document_builders import NewPerkinElmerDetector


@contextmanager
def ioc_process():
    # this function will run in the external process created below
    def start_ioc():
        logger = multiprocessing.get_logger()
        logger.warning("starting ioc")

        ioc = SimulatedPerkinElmerDetectorIoc(
            prefix="Sim[det1]",
            name="ioc",
            macros=dict(
                camera="cam1",
            ),
        )
        logger.warning(ioc.pvdb)
        run(ioc.pvdb, module_name="caproto.asyncio.server")
        logger.warning("ioc stopped")

    # create an external process for the ioc
    _ioc_process = multiprocessing.Process(
        target=start_ioc,
        daemon=True,
    )
    _ioc_process.start()
    time.sleep(5)

    try:
        yield _ioc_process
    finally:
        _ioc_process.terminate()
        _ioc_process.join()


def validate_char_array_pv_pair(caproto_client, setpoint_pv_name, initial_value, test_values):
    (setpoint_pv,) = caproto_client.get_pvs(setpoint_pv_name)
    (readback_pv,) = caproto_client.get_pvs(setpoint_pv_name + "_RBV")

    # how is this supposed to be done?
    assert setpoint_pv.read().data.tobytes().decode() == initial_value

    for test_value in test_values:
        setpoint_pv.write(test_value)
        assert setpoint_pv.read().data.tobytes().decode() == test_value
        assert readback_pv.read().data.tobytes().decode() == test_value


def validate_int_pv_pair(caproto_client, setpoint_pv_name, initial_value, test_values):
    (setpoint_pv,) = caproto_client.get_pvs(setpoint_pv_name)
    (readback_pv,) = caproto_client.get_pvs(setpoint_pv_name + "_RBV")

    # how is this supposed to be done?
    assert setpoint_pv.read().data == initial_value

    for test_value in test_values:
        setpoint_pv.write(test_value)
        assert setpoint_pv.read().data == test_value
        assert readback_pv.read().data == test_value


def test_pv_file_name():

    with ioc_process() as ioc:

        client = CaprotoThreadingClient()

        validate_char_array_pv_pair(
            caproto_client=client,
            setpoint_pv_name="Sim[det1]:TIFF1:FileName",
            initial_value="_file_name",
            test_values=("a new file name",),
        )

        validate_int_pv_pair(
            caproto_client=client,
            setpoint_pv_name="Sim[det1]:TIFF1:EnableCallbacks",
            initial_value=PluginBasePVGroup.EnableCallbacks.DISABLE,
            test_values=PluginBasePVGroup.EnableCallbacks,
        )

        validate_int_pv_pair(
            caproto_client=client,
            setpoint_pv_name="Sim[det1]:TIFF1:BlockingCallbacks",
            initial_value=PluginBasePVGroup.BlockingCallbacks.NO,
            test_values=PluginBasePVGroup.BlockingCallbacks,
        )


def test_array_base():
    with ioc_process() as ioc:
        client = CaprotoThreadingClient()

        validate_int_pv_pair(
            caproto_client=client,
            setpoint_pv_name="Sim[det1]:cam1:ArrayCallbacks",
            initial_value=ArrayBasePVGroup.ArrayCallbacks.DISABLE,
            test_values=ArrayBasePVGroup.ArrayCallbacks,
        )


def test_trigger_mode():
    """
    Do the two TriggerMode IntEnums agree?
    Do all the NewPerkinElmerDetector.TriggertModes read and write as expected?
    """
    with ioc_process() as ioc:
        client = CaprotoThreadingClient()
        setpoint_pv, readback_pv = client.get_pvs(
            "Sim[det1]:cam1:TriggerMode", "Sim[det1]:cam1:TriggerMode_RBV"
        )

        trigger_mode_setpoint = setpoint_pv.read().data
        trigger_mode_readback = readback_pv.read().data

        # expect the trigger mode to be INTERNAL when the IOC starts up
        assert (
            trigger_mode_setpoint
            == SimulatedPerkinElmerDetectorIoc.TriggerMode.INTERNAL
        )
        assert (
            trigger_mode_readback
            == SimulatedPerkinElmerDetectorIoc.TriggerMode.INTERNAL
        )
        assert trigger_mode_setpoint == NewPerkinElmerDetector.TriggerMode.INTERNAL
        assert trigger_mode_readback == NewPerkinElmerDetector.TriggerMode.INTERNAL

        for trigger_mode_client, trigger_mode_server in zip(
            NewPerkinElmerDetector.TriggerMode,
            SimulatedPerkinElmerDetectorIoc.TriggerMode,
        ):
            setpoint_pv.write(trigger_mode_client)

            trigger_mode_setpoint = setpoint_pv.read().data
            trigger_mode_readback = readback_pv.read().data

            assert trigger_mode_setpoint == trigger_mode_client
            assert trigger_mode_readback == trigger_mode_client
            assert trigger_mode_setpoint == trigger_mode_server
            assert trigger_mode_readback == trigger_mode_server
