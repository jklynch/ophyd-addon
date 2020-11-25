from collections import deque
import logging
from pathlib import Path

from event_model import compose_resource
from ophyd import BlueskyInterface, Component as Cpt, DeviceStatus, Kind
from ophyd.areadetector import plugins, SingleTrigger
from ophyd.areadetector.detectors import PerkinElmerDetector
from ophyd.areadetector.filestore_mixins import FileStoreTIFFIterativeWrite
from ophyd.status import SubscriptionStatus


class TiffWriter(plugins.TIFFPlugin, FileStoreTIFFIterativeWrite):
    """
    A combination of areadetector TIFFPlugin and a bluesky document builder

    This is not a good name.
    BlueskyTiffPlugin? not great
    """

    def __init__(self, *args, resource_root_path, relative_write_path, **kwargs):
        # TODO: write_path_template=resource_root_path is not quite right
        super().__init__(*args, write_path_template=resource_root_path, **kwargs)

        self.resource_root_path = resource_root_path
        self.relative_write_path = relative_write_path

        # for FileStoreTIFFIterativeWrite
        self._asset_docs_cache = deque()

        # bluesky document building
        self._resource_document = None
        self._datum_factory = None
        self._asset_docs_cache = None

        self.logger = logging.getLogger("TiffWriter")

    def get_full_file_path(self):
        full_file_path = (
            self.resource_root_path / self.relative_write_path / self.file_name.get()
        )
        return full_file_path

    def stage(self):
        # for FileStoreTIFFIterativeWrite
        self._asset_docs_cache = deque()
        super().stage()
        self.logger.debug("stage")
        print(f"stage TiffWriter")
        resource_root_path = str(self.resource_root_path)
        resource_relative_path = str(
            self.relative_write_path / Path(self.file_name.get())
        )
        self._resource_document, self._datum_factory, _ = compose_resource(
            start={
                "uid": "must be a string now but will be replaced by the RunEngine with a real uid"
            },
            spec="ADC_TIFF",
            root=resource_root_path,
            resource_path=resource_relative_path,
            resource_kwargs={},
        )
        self._resource_document.pop("run_start")

        self._asset_docs_cache = deque()
        self._asset_docs_cache.append(("resource", self._resource_document))

    def generate_datum(self, key, timestamp, datum_kwargs):
        datum = super().generate_datum(key, timestamp, datum_kwargs)
        print("TiffWriter got generate_datum!")
        return datum

    def unstage(self):
        super().unstage()
        print(f"unstage TiffWriter")
        self._resource_document = None
        self._datum_factory = None


class NDFile:
    class FileWriteMode:
        SINGLE = "Single"
        CAPTURE = "Capture"
        STREAM = "Stream"

    class FileWriteModeRBV:
        SINGLE = "Single"
        CAPTURE = "Capture"
        STREAM = "Stream"

    class WriteFile:
        DONE = int(0)
        WRITE = int(1)

    class WriteFileRBV:
        DONE = int(0)
        WRITING = int(1)


class PerkinElmerCamera:
    # this enum should be defined in the camera class
    class Acquire:
        DONE = int(0)
        ACQUIRE = int(1)

    # this enum should be defined in the camera class
    class AcquireOffset:
        DONE = int(0)
        ACQUIRE = int(1)

    class ImageMode:
        SINGLE = int(0)
        MULTIPLE = int(1)
        CONTINUOUS = int(2)

    class PerkinElmerImageMode:
        # AVERAGE is unique to the PerkinElmer detector
        AVERAGE = int(3)

    class TriggerMode:
        INTERNAL = int(0)
        EXTERNAL = int(1)
        FREE_RUNNING = int(2)
        SOFT_TRIGGER = int(3)


def acquire_high_to_low(value, old_value, **kwargs):
    print(f"acquire_high_to_low value={value} old_value={old_value}")
    if old_value == PerkinElmerCamera.Acquire.ACQUIRE and value == PerkinElmerCamera.Acquire.DONE:
        return True

    return False


class NewPerkinElmerDetector(SingleTrigger, PerkinElmerDetector):

    tiff_writer = Cpt(
        TiffWriter,
        suffix="TIFF1:",
        resource_root_path=Path("/tmp"),
        relative_write_path=Path("tiff/sim/detector"),
        # file_name="sim-detector.tiff"
        kind=Kind.normal
    )

    def __init__(self, *args, name, **kwargs):
        super().__init__(*args, name=name, **kwargs)

        self.logger = logging.getLogger("NewPerkinElmerDetector")

    def stage(self):
        self.logger.debug("stage")
        print(f"NewPerkinElmerDetector stage")
        super().stage()

    def trigger(self):
        super().trigger()
        print(f"I got the trigger!")
        acquire_status = SubscriptionStatus(
            self.cam.acquire,
            acquire_high_to_low
        )

        self.cam.acquire.set(PerkinElmerCamera.Acquire.ACQUIRE)

        return acquire_status

    def unstage(self):
        print(f"NewPerkinElmerDetector unstage")
        self.logger.debug("unstage")
        super().unstage()
