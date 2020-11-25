from enum import IntEnum, unique
import logging

from textwrap import dedent

from caproto import ChannelType
from caproto._log import config_caproto_logging
from caproto.server import pvproperty, PVGroup, SubGroup, ioc_arg_parser, run

from ophyd_addon.ioc_util import no_reentry

config_caproto_logging(level=logging.INFO)


class PluginBasePVGroup(PVGroup):
    def __init__(self, *args, plugin_type_rbv=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._enable_callbacks = PluginBasePVGroup.EnableCallbacks.ENABLE
        self._blocking_callbacks = PluginBasePVGroup.BlockingCallbacks.NO
        self._port_name_rbv = "FileTIFF1"  # ?????
        self._nd_array_port = None
        self._plugin_type_rbv = plugin_type_rbv  # "NDFileTIFF"

    """
    PluginType
    """

    @pvproperty(
        name=":PluginType_RBV",
        dtype=ChannelType.STRING,
        value="uninitialized PluginType_RBV",
        read_only=True,
    )
    async def plugin_type_rbv(self, instance):
        return self._plugin_type_rbv

    """
    BlockingCallbacks (No, Yes)
    """

    class BlockingCallbacks:
        NO = "No"
        YES = "Yes"

    @pvproperty(
        name=":BlockingCallbacks",
        dtype=ChannelType.ENUM,
        enum_strings=(BlockingCallbacks.NO, BlockingCallbacks.YES),
        value=BlockingCallbacks.NO,
    )
    async def blocking_callbacks(self, instance):
        return self._blocking_callbacks

    @blocking_callbacks.putter
    async def blocking_callbacks(self, instance, value):
        self._blocking_callbacks = value
        return value

    @pvproperty(
        name=":BlockingCallbacks_RBV",
        dtype=ChannelType.ENUM,
        enum_strings=(BlockingCallbacks.NO, BlockingCallbacks.YES),
        value=BlockingCallbacks.NO,
        read_only=True,
    )
    async def blocking_callbacks_rbv(self, instance):
        return self._blocking_callbacks

    """
    EnableCallbacks (0 - Disable, 1 - Enable)
    """

    class EnableCallbacks:
        DISABLE = "Disable"
        ENABLE = "Enable"

    @pvproperty(
        name=":EnableCallbacks",
        dtype=ChannelType.ENUM,
        enum_strings=(EnableCallbacks.DISABLE, EnableCallbacks.ENABLE),
        value=EnableCallbacks.ENABLE,
    )
    async def enable_callbacks(self, instance):
        return self._enable_callbacks

    @enable_callbacks.putter
    async def enable_callbacks(self, instance, value):
        self._enable_callbacks = value
        return value

    @pvproperty(
        name=":EnableCallbacks_RBV",
        dtype=ChannelType.ENUM,
        enum_strings=(EnableCallbacks.DISABLE, EnableCallbacks.ENABLE),
        value=EnableCallbacks.ENABLE,
        read_only=True,
    )
    async def enable_callbacks_rbv(self, instance):
        return self._enable_callbacks


class FilePluginPVGroup(PluginBasePVGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_name = None
        self._file_number = None
        self._file_path = None
        self._file_path_exists = None
        self._file_template = None
        self._file_write_mode = None
        self._write_file = None

        self._array_counter = None
        self._auto_increment = None
        self._auto_save = None
        self._capture = None
        self._num_capture = None

    # FileWriteMode = enum(SINGLE=0, CAPTURE=1, STREAM=2)
    #
    # auto_increment = Cpt(SignalWithRBV, 'AutoIncrement', kind='config')
    class AutoIncrement:
        NO = "No"
        YES = "Yes"

    @pvproperty(
        name=":AutoIncrement",
        dtype=ChannelType.ENUM,
        enum_strings=(AutoIncrement.NO, AutoIncrement.YES),
        value=AutoIncrement.NO,
    )
    async def auto_increment(self, instance):
        return self._auto_increment

    @auto_increment.putter
    async def auto_increment(self, instance, value):
        self._auto_increment = value
        return value

    @pvproperty(
        name=":AutoIncrement_RBV",
        dtype=ChannelType.ENUM,
        enum_strings=(AutoIncrement.NO, AutoIncrement.YES),
        value=AutoIncrement.NO,
        read_only=True,
    )
    async def auto_increment_rbv(self, instance):
        return self._auto_increment

    # auto_save = Cpt(SignalWithRBV, 'AutoSave', kind='config')
    class AutoSave:
        NO = "No"
        YES = "Yes"

    @pvproperty(
        name=":AutoSave",
        dtype=ChannelType.ENUM,
        enum_strings=(AutoSave.NO, AutoSave.YES),
        value=AutoSave.NO,
    )
    async def auto_save(self, instance):
        return self._auto_save

    @auto_save.putter
    async def auto_save(self, instance, value):
        self._auto_save = value
        return value

    @pvproperty(
        name=":AutoSave_RBV",
        dtype=ChannelType.ENUM,
        enum_strings=(AutoSave.NO, AutoSave.YES),
        value=AutoSave.NO,
        read_only=True,
    )
    async def auto_save_rbv(self, instance):
        return self._auto_save

    # capture = Cpt(SignalWithRBV, 'Capture')
    class Capture:
        DONE = "Done"
        CAPTURING = "Capturing"

    @pvproperty(
        name=":Capture",
        dtype=ChannelType.ENUM,
        enum_strings=(Capture.DONE, Capture.CAPTURING),
        value=Capture.DONE,
    )
    async def capture(self, instance):
        return self._capture

    @capture.putter
    async def capture(self, instance, value):
        self._capture = value
        return value

    @pvproperty(
        name=":Capture_RBV",
        dtype=ChannelType.ENUM,
        enum_strings=(Capture.DONE, Capture.CAPTURING),
        value=Capture.DONE,
        read_only=True,
    )
    async def capture_rbv(self, instance):
        return self._capture

    # delete_driver_file = Cpt(SignalWithRBV, 'DeleteDriverFile', kind='config')
    # file_format = Cpt(SignalWithRBV, 'FileFormat', kind='config')
    # file_name = Cpt(SignalWithRBV, 'FileName', string=True, kind='config')
    # file_number = Cpt(SignalWithRBV, 'FileNumber')
    # file_number_sync = Cpt(EpicsSignal, 'FileNumber_Sync')
    # file_number_write = Cpt(EpicsSignal, 'FileNumber_write')
    # file_path = Cpt(SignalWithRBV, 'FilePath', string=True, kind='config')
    # file_path_exists = Cpt(EpicsSignalRO, 'FilePathExists_RBV', kind='config')
    class FilePathExists:
        NO = "No"
        YES = "Yes"

    @pvproperty(
        name=":FilePathExists",
        dtype=ChannelType.ENUM,
        enum_strings=(FilePathExists.NO, FilePathExists.YES),
        value=FilePathExists.NO,
    )
    async def file_path_exists(self, instance):
        return self._file_path_exists

    @file_path_exists.putter
    async def file_path_exists(self, instance, value):
        self._file_path_exists = value
        return value

    @pvproperty(
        name=":FilePathExists_RBV",
        dtype=ChannelType.ENUM,
        enum_strings=(FilePathExists.NO, FilePathExists.YES),
        value=FilePathExists.NO,
        read_only=True,
    )
    async def file_path_exists_rbv(self, instance):
        return self._file_path_exists

    # file_template = Cpt(SignalWithRBV, 'FileTemplate', string=True, kind='config')
    @pvproperty(
        name=":FileTemplate",
        dtype=ChannelType.STRING,
        value="",
    )
    async def file_template(self, instance):
        return self._file_template

    @file_template.putter
    async def file_template(self, instance, value):
        self._file_template = value
        return value

    @pvproperty(
        name=":FileTemplate_RBV",
        dtype=ChannelType.STRING,
        value="",
        read_only=True,
    )
    async def file_template_rbv(self, instance):
        return self._file_template

    # file_write_mode = Cpt(SignalWithRBV, 'FileWriteMode', kind='config')
    # full_file_name = Cpt(EpicsSignalRO, 'FullFileName_RBV', string=True, kind='config')
    # num_capture = Cpt(SignalWithRBV, 'NumCapture', kind='config')
    @pvproperty(
        name=":NumCapture",
        dtype=ChannelType.INT,
        value=1,
    )
    async def num_capture(self, instance):
        return self._num_capture

    @num_capture.putter
    async def num_capture(self, instance, value):
        self._num_capture = value
        return value

    @pvproperty(
        name=":NumCapture_RBV",
        dtype=ChannelType.INT,
        value=1,
        read_only=True,
    )
    async def num_capture_rbv(self, instance):
        return self._num_capture

    # num_captured = Cpt(EpicsSignalRO, 'NumCaptured_RBV')
    # read_file = Cpt(SignalWithRBV, 'ReadFile')

    """
    WriteFile
        0 - Done
        1 - Write
    WriteFile_RBV
        0 - Done
        1 - Writing
    """

    @pvproperty(
        name=":WriteFile",
        dtype=ChannelType.INT,
        value=0,
    )
    async def write_file(self, instance):
        return self._write_file

    @write_file.putter
    async def write_file(self, instance, value):
        self._write_file = value
        return value

    @pvproperty(name=":WriteFile_RBV", dtype=ChannelType.INT, value=0, read_only=True)
    async def write_file_rbv(self, instance):
        return self._write_file

    # write_message = Cpt(EpicsSignal, 'WriteMessage', string=True)
    # write_status = Cpt(EpicsSignal, 'WriteStatus')

    """
    FileName 
    """

    @pvproperty(
        name=":FileName",
        dtype=ChannelType.CHAR,
        max_length=1024,
        value="file_name at file_name definition",
    )
    async def file_name(self, instance):
        print(f"pvpropety file_name {instance}")
        return self._file_name

    @file_name.putter
    async def file_name(self, instance, value):
        print(f"file_name.putter {instance} {value}")
        self._file_name = value
        return value

    @pvproperty(
        name=":FileName_RBV",
        dtype=ChannelType.CHAR,
        max_length=1024,
        value="file_name at file_name_rbv definition",
        read_only=True,
    )
    async def file_name_rbv(self, instance):
        return self._file_name

    """
    FileNumber 
    """

    @pvproperty(
        name=":FileNumber",
        dtype=ChannelType.INT,
        value=0,
    )
    async def file_number(self, instance):
        return self._file_number

    @file_number.putter
    async def file_number(self, instance, value):
        self._file_number = value
        return value

    @pvproperty(name=":FileNumber_RBV", dtype=ChannelType.INT, value=0, read_only=True)
    async def file_number_rbv(self, instance):
        return self._file_number

    """
    FilePath 
    """

    @pvproperty(
        name=":FilePath",
        dtype=ChannelType.CHAR,
        max_length=1024,
        # value="file_path pvproperty",
    )
    async def file_path(self, instance):
        return self._file_path

    @file_path.putter
    async def file_path(self, instance, value):
        print(f"file_path.putter value: {value}")
        self._file_path = value
        return value

    @pvproperty(
        name=":FilePath_RBV",
        dtype=ChannelType.CHAR,
        max_length=1024,
        # value="file_path_rbv pvproperty",
        read_only=True,
    )
    async def file_path_rbv(self, instance):
        return self._file_path

    """
    FileWriteMode (Single, Capture, Stream)
    """

    @pvproperty(
        name=":FileWriteMode",
        dtype=ChannelType.ENUM,
        enum_strings=("Single", "Capture", "Stream"),
        value="Single",
    )
    async def file_write_mode(self, instance):
        return self._file_write_mode

    @file_write_mode.putter
    async def file_write_mode(self, instance, value):
        self._file_write_mode = value
        return value

    @pvproperty(
        name=":FileWriteMode_RBV",
        dtype=ChannelType.ENUM,
        enum_strings=("Single", "Capture", "Stream"),
        value="Single",
        read_only=True,
    )
    async def file_write_mode_rbv(self, instance):
        return self._file_write_mode

    """
    PortName_RBV
    """

    @pvproperty(
        name=":PortName_RBV",
        dtype=ChannelType.CHAR,
        max_length=1024,
        value=None,
        read_only=True,
    )
    async def port_name_rbv(self, instance):
        return self._port_name_rbv

    """
    NDArrayPort
        Configure correctly or get this:
        RuntimeError: The asyn ports ['uninitialized NDArrayPort'] are used by plugins
        that ophyd is aware of but the source plugin is not.  Please reconfigure your 
        device to include the source plugin or reconfigure to not use these ports.
    """

    @pvproperty(name=":NDArrayPort", dtype=ChannelType.STRING, value=None)
    async def nd_array_port(self, instance):
        return self._nd_array_port

    @nd_array_port.putter
    async def nd_array_port(self, instance, value):
        self._nd_array_port = value
        return value

    @pvproperty(
        name=":NDArrayPort_RBV",
        dtype=ChannelType.STRING,
        # max_length=1024,
        value=None,
        read_only=True,
    )
    async def nd_array_port_rbv(self, instance):
        return self._nd_array_port

    # array_counter = ADCpt(SignalWithRBV, 'ArrayCounter')
    @pvproperty(
        name=":ArrayCounter",
        dtype=ChannelType.INT,
        value=0,
    )
    async def array_counter(self, instance):
        return self._array_counter

    @array_counter.putter
    async def array_counter(self, instance, value):
        self._array_counter = value
        return value

    @pvproperty(
        name=":ArrayCounter_RBV",
        dtype=ChannelType.INT,
        value=0,
        read_only=True,
    )
    async def array_counter_rbv(self, instance):
        return self._array_counter


class FileTiffPluginPVGroup(FilePluginPVGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, plugin_type_rbv="NDFileTIFF", **kwargs)


class ArrayBasePVGroup(PVGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._array_callbacks = ArrayBasePVGroup.ArrayCallbacks.DISABLE

    """
    ArrayCallbacks - this is really in NDPluginDriverBlockingCallbacks
       0 - queue and execute callback functions in the callback thread
       1 - execute callback functions in the driver thread
    """

    class ArrayCallbacks(IntEnum):
        DISABLE = int(0)
        ENABLE = int(1)

    array_callbacks = pvproperty(
        name=":{camera}:ArrayCallbacks",
        dtype=ChannelType.INT,
        value=ArrayCallbacks.DISABLE,
    )

    @array_callbacks.putter
    async def array_callbacks(self, instance, value):
        await self.array_callbacks_rbv.write(value)
        return value

    array_callbacks_rbv = pvproperty(
        name=":{camera}:ArrayCallbacks_RBV",
        dtype=ChannelType.INT,
        value=ArrayCallbacks.DISABLE,
        read_only=True,
    )

    """
    Acquire 
        0 - Done
        1 - Acquire
    """

    class Acquire:
        DONE = int(0)
        ACQUIRE = int(1)

    acquire = pvproperty(
        name=":{camera}:Acquire",
        dtype=ChannelType.INT,
        value=Acquire.DONE,
    )

    @acquire.putter
    @no_reentry
    async def acquire(self, instance, value):
        print(f"acquire putter called with instance {instance} and value {value}")
        if not instance.async_event.is_set():

            await instance.async_event.wait()
            return ArrayBasePVGroup.Acquire.DONE

        if value == ArrayBasePVGroup.Acquire.ACQUIRE:
            instance.async_event.clear()
            try:

                await instance.write(ArrayBasePVGroup.Acquire.ACQUIRE)
                await self.acquire_rbv.write(ArrayBasePVGroup.Acquire.ACQUIRE)

                # await instance.async_lib.library.sleep(self.exposure_time.value)
                await instance.async_lib.library.sleep(2)

                # await self.reading.write(np.random.rand())

            finally:
                instance.async_event.set()

        await self.acquire_rbv.write(ArrayBasePVGroup.Acquire.DONE)
        return ArrayBasePVGroup.Acquire.DONE

    @acquire.startup
    async def acquire(self, instance, async_lib):
        instance.async_lib = async_lib
        instance.async_event = async_lib.Event()
        instance.async_event.set()

    acquire_rbv = pvproperty(
        name=":{camera}:Acquire_RBV",
        dtype=ChannelType.INT,
        value=Acquire.DONE,
        read_only=True,
    )
    # async def acquire_rbv(self, instance):
    #     return self._acquire


class SimulatedPerkinElmerDetectorIoc(ArrayBasePVGroup):
    """
    Try to simulate the Perkin-Elmer IOC.

    """

    @unique
    class TriggerMode(IntEnum):
        INTERNAL = 0
        EXTERNAL = 1
        FREE_RUNNING = 2
        SOFT_TRIGGER = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._acquire_period = 1.0
        self._acquire_time = 1.0
        self._array_counter = None

        self._num_images = 0

        self._port_name_rbv = None

        self._image_mode = 0  # Single

        self._trigger_mode = SimulatedPerkinElmerDetectorIoc.TriggerMode.INTERNAL

        self._pe_num_offset_frames = 0

        self._pe_acquire_offset = 0  # Done

    tiff_plugin = SubGroup(FileTiffPluginPVGroup, prefix=":TIFF1")

    # Shared among all cams and plugins
    """
    array_rate = ADCpt(EpicsSignalRO, 'ArrayRate_RBV')
    asyn_io = ADCpt(EpicsSignal, 'AsynIO')

    nd_attributes_file = ADCpt(EpicsSignal, 'NDAttributesFile', string=True)
    pool_alloc_buffers = ADCpt(EpicsSignalRO, 'PoolAllocBuffers')
    pool_free_buffers = ADCpt(EpicsSignalRO, 'PoolFreeBuffers')
    pool_max_buffers = ADCpt(EpicsSignalRO, 'PoolMaxBuffers')
    pool_max_mem = ADCpt(EpicsSignalRO, 'PoolMaxMem')
    pool_used_buffers = ADCpt(EpicsSignalRO, 'PoolUsedBuffers')
    pool_used_mem = ADCpt(EpicsSignalRO, 'PoolUsedMem')
    """

    """
    PortName_RBV
    """

    @pvproperty(
        name=":{camera}:PortName_RBV",
        dtype=ChannelType.STRING,
        value=None,
        read_only=True,
    )
    async def port_name_rbv(self, instance):
        return self._port_name_rbv

    """
    # Cam-specific
    acquire = ADCpt(SignalWithRBV, 'Acquire')
    acquire_period = ADCpt(SignalWithRBV, 'AcquirePeriod')
    acquire_time = ADCpt(SignalWithRBV, 'AcquireTime')
    """

    """
    AcquirePeriod
    """

    @pvproperty(
        name=":{camera}:AcquirePeriod",
        dtype=ChannelType.FLOAT,
        value=1.0,
    )
    async def acquire_period(self, instance):
        return self._acquire_period

    @acquire_period.putter
    async def acquire_period(self, instance, value):
        self._acquire_period = value
        return value

    @pvproperty(
        name=":{camera}:AcquirePeriod_RBV",
        dtype=ChannelType.FLOAT,
        value=1.0,
        read_only=True,
    )
    async def acquire_period_rbv(self, instance):
        return self._acquire_period

    """
    AcquireTime
    """

    @pvproperty(
        name=":{camera}:AcquireTime",
        dtype=ChannelType.FLOAT,
        value=1.0,
    )
    async def acquire_time(self, instance):
        return self._acquire_time

    @acquire_time.putter
    async def acquire_time(self, instance, value):
        self._acquire_time = value
        return value

    @pvproperty(
        name=":{camera}:AcquireTime_RBV",
        dtype=ChannelType.FLOAT,
        value=1.0,
        read_only=True,
    )
    async def acquire_time_rbv(self, instance):
        return self._acquire_time

    """
    array_size = DDC(ad_group(EpicsSignalRO,
                              (('array_size_x', 'ArraySizeX_RBV'),
                               ('array_size_y', 'ArraySizeY_RBV'),
                               ('array_size_z', 'ArraySizeZ_RBV'))),
                     doc='Size of the array in the XYZ dimensions')

    array_size_bytes = ADCpt(EpicsSignalRO, 'ArraySize_RBV')
    bin_x = ADCpt(SignalWithRBV, 'BinX')
    bin_y = ADCpt(SignalWithRBV, 'BinY')
    color_mode = ADCpt(SignalWithRBV, 'ColorMode')
    data_type = ADCpt(SignalWithRBV, 'DataType')
    detector_state = ADCpt(EpicsSignalRO, 'DetectorState_RBV')
    frame_type = ADCpt(SignalWithRBV, 'FrameType')
    gain = ADCpt(SignalWithRBV, 'Gain')

    image_mode = ADCpt(SignalWithRBV, 'ImageMode')
    """

    """
    ImageMode
        0 - Single
        1 - Multiple
        2 - Continuous
        3 - Average  (specific to the Perkin-Elmer detector)
    """

    @pvproperty(
        name=":{camera}:ImageMode",
        dtype=ChannelType.INT,
        value=0,
    )
    async def image_mode(self, instance):
        return self._image_mode

    @image_mode.putter
    async def image_mode(self, instance, value):
        self._image_mode = value
        return value

    @pvproperty(
        name=":{camera}:ImageMode_RBV",
        dtype=ChannelType.INT,
        value=0,
        read_only=True,
    )
    async def image_mode_rbv(self, instance):
        return self._image_mode

    # using dtype=ChannelType.CHAR and max_length=1024 results in un-JSON-able
    # data in the start document
    manufacturer_rbv = pvproperty(
        name=":{camera}:Manufacturer_RBV",
        dtype=ChannelType.STRING,
        read_only=True,
        value="PerkinElmer",
    )

    model_rbv = pvproperty(
        name=":{camera}:Model_RBV",
        dtype=ChannelType.STRING,
        read_only=True,
        value="Simulated",
    )

    """
    max_size = DDC(ad_group(EpicsSignalRO,
                            (('max_size_x', 'MaxSizeX_RBV'),
                             ('max_size_y', 'MaxSizeY_RBV'))),
                   doc='Maximum sensor size in the XY directions')

    min_x = ADCpt(SignalWithRBV, 'MinX')
    min_y = ADCpt(SignalWithRBV, 'MinY')

    """

    num_exposures = pvproperty(name=":{camera}:NumExposures", value=1)
    num_exposures_rbv = pvproperty(
        name=":{camera}:NumExposures_RBV", read_only=True, value=1
    )

    """
    num_exposures_counter = ADCpt(EpicsSignalRO, 'NumExposuresCounter_RBV')

    """

    """
    NumImages
    """

    @pvproperty(
        name=":{camera}:NumImages",
        dtype=ChannelType.INT,
        value=0,
    )
    async def num_images(self, instance):
        return self._num_images

    @num_images.putter
    async def num_images(self, instance, value):
        self._num_images = value
        return value

    @pvproperty(
        name=":{camera}:NumImages_RBV", dtype=ChannelType.INT, value=0, read_only=True
    )
    async def num_images_rbv(self, instance):
        return self._num_images

    num_images_counter = pvproperty(
        name=":{camera}:NumImagesCounter_RBV", read_only=True, value=0
    )

    """
    read_status = ADCpt(EpicsSignal, 'ReadStatus')
    reverse = DDC(ad_group(SignalWithRBV,
                           (('reverse_x', 'ReverseX'),
                            ('reverse_y', 'ReverseY'))
                           ))

    shutter_close_delay = ADCpt(SignalWithRBV, 'ShutterCloseDelay')
    shutter_close_epics = ADCpt(EpicsSignal, 'ShutterCloseEPICS')
    shutter_control = ADCpt(SignalWithRBV, 'ShutterControl')
    shutter_control_epics = ADCpt(EpicsSignal, 'ShutterControlEPICS')
    shutter_fanout = ADCpt(EpicsSignal, 'ShutterFanout')
    shutter_mode = ADCpt(SignalWithRBV, 'ShutterMode')
    shutter_open_delay = ADCpt(SignalWithRBV, 'ShutterOpenDelay')
    shutter_open_epics = ADCpt(EpicsSignal, 'ShutterOpenEPICS')
    shutter_status_epics = ADCpt(EpicsSignalRO, 'ShutterStatusEPICS_RBV')
    shutter_status = ADCpt(EpicsSignalRO, 'ShutterStatus_RBV')

    size = DDC(ad_group(SignalWithRBV,
                        (('size_x', 'SizeX'),
                         ('size_y', 'SizeY'))
                        ))

    status_message = ADCpt(EpicsSignalRO, 'StatusMessage_RBV', string=True)
    string_from_server = ADCpt(EpicsSignalRO, 'StringFromServer_RBV', string=True)
    string_to_server = ADCpt(EpicsSignalRO, 'StringToServer_RBV', string=True)
    temperature = ADCpt(SignalWithRBV, 'Temperature')
    temperature_actual = ADCpt(EpicsSignal, 'TemperatureActual')
    time_remaining = ADCpt(EpicsSignalRO, 'TimeRemaining_RBV')
    """

    """
    TriggerMode (Internal, External, Free Running, Soft Trigger)
    """

    @pvproperty(
        name=":{camera}:TriggerMode", dtype=ChannelType.INT, value=TriggerMode.INTERNAL
    )
    async def trigger_mode(self, instance):
        return self._trigger_mode

    @trigger_mode.putter
    async def trigger_mode(self, instance, value):
        self._trigger_mode = value
        return value

    @pvproperty(
        name=":{camera}:TriggerMode_RBV",
        dtype=ChannelType.INT,
        value=TriggerMode.INTERNAL,
        read_only=True,
    )
    async def trigger_mode_rbv(self, instance):
        return self._trigger_mode

    # pe_acquire_gain = ADCpt(EpicsSignal, 'PEAcquireGain')

    """
    PEAcquireOffset 
        0 - Done
        1 - Acquire
    """

    class PEAcquireOffset:
        DONE = int(0)
        ACQUIRE = int(1)

    pe_acquire_offset = pvproperty(
        name=":{camera}:PEAcquireOffset",
        dtype=ChannelType.INT,
        value=PEAcquireOffset.DONE,
    )

    @pe_acquire_offset.putter
    @no_reentry
    async def pe_acquire_offset(self, instance, value):
        print(f"pe_acquire_offset putter called with instance {instance} and value {value}")
        if not instance.async_event.is_set():

            await instance.async_event.wait()
            return SimulatedPerkinElmerDetectorIoc.PEAcquireOffset.DONE

        if value == SimulatedPerkinElmerDetectorIoc.PEAcquireOffset.ACQUIRE:
            instance.async_event.clear()
            try:

                await instance.write(SimulatedPerkinElmerDetectorIoc.PEAcquireOffset.ACQUIRE)
                await self.acquire_rbv.write(SimulatedPerkinElmerDetectorIoc.PEAcquireOffset.ACQUIRE)

                # await instance.async_lib.library.sleep(self.exposure_time.value)
                await instance.async_lib.library.sleep(2)

            finally:
                instance.async_event.set()

        await self.acquire_rbv.write(SimulatedPerkinElmerDetectorIoc.PEAcquireOffset.DONE)
        return SimulatedPerkinElmerDetectorIoc.PEAcquireOffset.DONE

    @pe_acquire_offset.startup
    async def pe_acquire_offset(self, instance, async_lib):
        instance.async_lib = async_lib
        instance.async_event = async_lib.Event()
        instance.async_event.set()

    pe_acquire_offset_rbv = pvproperty(
        name=":{camera}:PEAcquireOffset_RBV",
        dtype=ChannelType.INT,
        value=PEAcquireOffset.DONE,
        read_only=True,
    )
    # @pvproperty(
    #     name=":{camera}:PEAcquireOffset",
    #     dtype=ChannelType.INT,
    #     value=PEAcquireOffset.DONE,
    # )
    # async def pe_acquire_offset(self, instance):
    #     return self._pe_acquire_offset
    #
    # @pe_acquire_offset.putter
    # async def pe_acquire_offset(self, instance, value):
    #     self._pe_acquire_offset = value
    #     return value
    #
    # @pvproperty(
    #     name=":{camera}:PEAcquireOffset_RBV",
    #     dtype=ChannelType.INT,
    #     value=0,
    #     read_only=True,
    # )
    # async def pe_acquire_offset_rbv(self, instance):
    #     return self._pe_acquire_offset

    # pe_corrections_dir = ADCpt(EpicsSignal, 'PECorrectionsDir')
    # pe_current_gain_frame = ADCpt(EpicsSignal, 'PECurrentGainFrame')
    # pe_current_offset_frame = ADCpt(EpicsSignal, 'PECurrentOffsetFrame')
    # pe_dwell_time = ADCpt(SignalWithRBV, 'PEDwellTime')
    # pe_frame_buff_index = ADCpt(EpicsSignal, 'PEFrameBuffIndex')
    # pe_gain = ADCpt(SignalWithRBV, 'PEGain')
    # pe_gain_available = ADCpt(EpicsSignal, 'PEGainAvailable')
    # pe_gain_file = ADCpt(EpicsSignal, 'PEGainFile')
    # pe_image_number = ADCpt(EpicsSignal, 'PEImageNumber')
    # pe_initialize = ADCpt(EpicsSignal, 'PEInitialize')
    # pe_load_gain_file = ADCpt(EpicsSignal, 'PELoadGainFile')
    # pe_load_pixel_correction = ADCpt(EpicsSignal, 'PELoadPixelCorrection')
    # pe_num_frame_buffers = ADCpt(SignalWithRBV, 'PENumFrameBuffers')
    # pe_num_frames_to_skip = ADCpt(SignalWithRBV, 'PENumFramesToSkip')
    # pe_num_gain_frames = ADCpt(EpicsSignal, 'PENumGainFrames')

    """
    PENumOffsetFrames
    limits 1-500?
    pe_num_offset_frames = ADCpt(EpicsSignal, 'PENumOffsetFrames')
    """

    @pvproperty(
        name=":{camera}:PENumOffsetFrames",
        dtype=ChannelType.INT,
        value=1,
    )
    async def pe_num_offset_frames(self, instance):
        return self._pe_num_offset_frames

    @pe_num_offset_frames.putter
    async def pe_num_offset_frames(self, instance, value):
        self._pe_num_offset_frames = value
        return value

    # pe_offset_available = ADCpt(EpicsSignal, 'PEOffsetAvailable')
    # pe_pixel_correction_available = ADCpt(EpicsSignal,
    #                                       'PEPixelCorrectionAvailable')
    # pe_pixel_correction_file = ADCpt(EpicsSignal, 'PEPixelCorrectionFile')
    # pe_save_gain_file = ADCpt(EpicsSignal, 'PESaveGainFile')
    # pe_skip_frames = ADCpt(SignalWithRBV, 'PESkipFrames')
    # pe_sync_time = ADCpt(SignalWithRBV, 'PESyncTime')
    # pe_system_id = ADCpt(EpicsSignal, 'PESystemID')
    # pe_trigger = ADCpt(EpicsSignal, 'PETrigger')
    # pe_use_gain = ADCpt(EpicsSignal, 'PEUseGain')
    # pe_use_offset = ADCpt(EpicsSignal, 'PEUseOffset')
    # pe_use_pixel_correction = ADCpt(EpicsSignal, 'PEUsePixelCorrection')


if __name__ == "__main__":
    """
        python ophyd_addon/simulated_perkin_elmer_detector_ioc.py --list-pvs --prefix="XF:07BM-ES[Det:PE1]"
    """
    ioc_options, run_options = ioc_arg_parser(
        # default_prefix="simple:",
        default_prefix="XF:07BM-ES[Det:PE12]",
        desc=dedent(SimulatedPerkinElmerDetectorIoc.__doc__),
        macros=dict(
            camera="cam1",
        ),
    )
    ioc = SimulatedPerkinElmerDetectorIoc(**ioc_options)
    run(ioc.pvdb, **run_options)
