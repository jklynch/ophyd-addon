from pathlib import Path, PureWindowsPath
import uuid

from bluesky import Msg
import bluesky.plan_stubs as bps

from ophyd.status import SubscriptionStatus

from ophyd_addon.areadetector.document_builders import (
    PerkinElmerCamera,
    NewPerkinElmerDetector,
    NDFile,
)

# fast_shutter = SimulatedFastShutter(name="fast_shutter", prefix="XF:07BMB-CT{Enc02-DO:0}Dflt-Sel")


pe_detector = NewPerkinElmerDetector(
    name="perkin_elmer_det1", prefix="XF:07BM-ES[Det:PE1]:"
)

"XF:07BM-ES[Det:PE1]:TIFF1:FileNumber_RBV"
"XF:07BM-ES[Det:PE1]:TIFF1:FileNumber_RBV"


def high_to_low_pe_acquire_offset(value, old_value, **kwargs):
    print(f"high_to_low_pe_acquire_offset value={value} old_value={old_value}")
    return (
        old_value == PerkinElmerCamera.AcquireOffset.ACQUIRE
        and value == PerkinElmerCamera.AcquireOffset.DONE
    )
    #    return True

    #return False


def perkin_elmer_diffraction_plan():
    ...


def pe_count(
    filename="",
    exposure=1,
    num_images: int = 1,
    num_dark_images: int = 1,
    num_repetitions: int = 5,
    delay=60,
):

    year = "2020"  # RE.md["year"]
    cycle = "C2"  # RE.md["cycle"]
    proposal = "67890"  # RE.md["PROPOSAL"]

    # write_path_template = 'Z:\\data\\pe1_data\\%Y\\%m\\%d\\'
    # write_path_template = f"Z:\\users\\{year}\\{cycle}\\{proposal}XRD\\"
    # file_path = datetime.now().strftime(write_path_template)
    # filename = filename + str(uuid.uuid4())[:6]

    # this is an example of what would be used at the beamline
    pe_detector.tiff_writer.resource_root_path = PureWindowsPath(f"Z:\\users\\")
    pe_detector.tiff_writer.relative_write_path = PureWindowsPath(
        f"{year}\\{cycle}\\{proposal}XRD\\"
    )

    # for testing
    pe_detector.tiff_writer.resource_root_path = Path("/tmp/")
    pe_detector.tiff_writer.relative_write_path = Path(
        f"perkin_elmer/detector/{year}/{cycle}/XRD{proposal}"  # remove "XRD" from the end?
    )

    # start the run
    yield from bps.open_run()

    # stage the detector
    yield from bps.stage(pe_detector)

    yield from bps.mv(pe_detector.tiff_writer.file_number, 1)
    tiff_full_file_path = (
        pe_detector.tiff_writer.resource_root_path
        / pe_detector.tiff_writer.relative_write_path
    )

    print(f"tiff_full_file_path: {str(tiff_full_file_path)}")
    yield from bps.mv(pe_detector.tiff_writer.file_path, str(tiff_full_file_path))

    for repetition_index in range(int(num_repetitions)):

        print("\n")
        print(
            "<<<<<<<<<<<<<<<<< Doing repetition {} out of {} >>>>>>>>>>>>>>>>>".format(
                repetition_index + 1, num_repetitions
            )
        )

        # TiffWriter or similar plugin should do this
        yield from bps.mv(
            pe_detector.tiff_writer.file_name, filename + str(uuid.uuid4())
        )

        if num_dark_images > 0:
            # originally used pe_detector.num_dark_images
            # but this is really pe_num_offset_frames
            yield from bps.mv(pe_detector.cam.pe_num_offset_frames, num_dark_images)
            yield from bps.mv(
                pe_detector.cam.image_mode,
                PerkinElmerCamera.PerkinElmerImageMode.AVERAGE,
            )
            # yield from bps.mv(fast_shutter, "Close")
            yield from bps.sleep(0.5)
            yield from bps.mv(
                pe_detector.tiff_writer.file_write_mode, NDFile.FileWriteMode.SINGLE
            )

            # acquire a "dark frame"
            pe_acquire_offset_status = SubscriptionStatus(
                pe_detector.cam.pe_acquire_offset, high_to_low_pe_acquire_offset
            )
            yield from bps.abs_set(
                pe_detector.cam.pe_acquire_offset,
                PerkinElmerCamera.AcquireOffset.ACQUIRE,
                wait=False,
            )
            yield Msg("wait_for_status", None, pe_acquire_offset_status)

            yield from bps.mv(
                pe_detector.tiff_writer.write_file, NDFile.WriteFile.WRITE
            )

        # yield from bps.mv(
        #  pe1.cam.image_mode,
        #  NewPerkinElmerDetector.ImageMode.MULTIPLE
        # )
        yield from bps.mv(
            pe_detector.cam.image_mode,
            PerkinElmerCamera.PerkinElmerImageMode.AVERAGE,
        )
        yield from bps.mv(pe_detector.cam.acquire_time, exposure)
        yield from bps.mv(pe_detector.cam.num_images, num_images)

        # yield from bps.mv(fast_shutter, "Open")
        yield from bps.sleep(0.5)

        ## Below 'Capture' mode is used with 'Multiple' image_mode
        # yield from bps.mv(pe1.tiff_writer.file_write_mode, 'Capture')

        ## Below 'Single' mode is used with 'Average' image_mode
        yield from bps.mv(
            pe_detector.tiff_writer.file_write_mode,
            NDFile.FileWriteMode.SINGLE,  # "Single"
        )

        ## Uncomment 'capture' bit settings when used in 'Capture' mode
        # yield from bps.mv(pe1.tiff_writer.capture, 1)

        # this was the old way to initiate the acquisition
        # yield from bps.mv(pe_detector, "acquire_light")

        yield from bps.trigger_and_read([pe_detector], name="primary")

        # can TiffWriter or similar plugin do this?
        ##Below write_file is needed when used in 'Average' mode
        yield from bps.mv(
            pe_detector.tiff_writer.write_file, NDFile.WriteFile.WRITE  # 1
        )

        yield from bps.sleep(delay)

    # unstage the detector
    yield from bps.unstage(pe_detector)

    # end the run
    yield from bps.close_run()
