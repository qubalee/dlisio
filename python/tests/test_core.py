import pytest
import numpy as np
from datetime import datetime

import dlisio

@pytest.fixture(scope="module", name="f")
def load_default_file():
    with dlisio.load('data/206_05a-_3_DWL_DWL_WIRE_258276498.DLIS') as f:
        yield f

@pytest.fixture(scope="module", name="channels_f")
def load_only_channels_file():
    with dlisio.load('data/only-channels.dlis') as f:
        yield f

def test_sul(f):
    label = ''.join([
                '   1',
                'V1.00',
                'RECORD',
                ' 8192',
                'Default Storage Set                                         ',
            ])

    sul = dlisio.core.storage_label(label.encode('ascii'))
    d = {
        'sequence': 1,
        'version': '1.0',
        'maxlen': 8192,
        'layout': 'record',
        'id': 'Default Storage Set                                         ',
    }

    assert sul == d

    assert f.storage_label() == d


def test_sul_error_values():
    label = "too short"
    with pytest.raises(ValueError) as excinfo:
       dlisio.core.storage_label(label.encode('ascii'))
    assert 'buffer to small' in str(excinfo.value)

    label = ''.join([
                '   1',
                'V2.00',
                'RECORD',
                ' 8192',
                'Default Storage Set                                         ',
            ])

    with pytest.raises(ValueError) as excinfo:
        dlisio.core.storage_label(label.encode('ascii'))
    assert 'unable to parse' in str(excinfo.value)


    label = ''.join([
                '  2 ',
                'V1.00',
                'TRASH1',
                'ZZZZZ',
                'Default Storage Set                                         ',
    ])

    with pytest.warns(RuntimeWarning) as warninfo:
        sul = dlisio.core.storage_label(label.encode('ascii'))
    assert len(warninfo) == 1
    assert "label inconsistent" in warninfo[0].message.args[0]
    assert sul['layout'] == 'unknown'


# The example record from the specification
stdrecord = bytearray([
    # The eflr function assumes unsegmented record
    # # segment header #1
    # 0x00, 0x68, # length = 104
    # 0xA6,       # attributes
    # 0x03,       # type = CHANNL

    # channel set
    0xF8,       # SET:TN
    0x07, 0x43, 0x48, 0x41, 0x4E, 0x4E, 0x45, 0x4C, # "CHANNEL"
    0x01, 0x30, # "0"

    # template
    0x34,       # ATTRIB:LR
    # "LONG-NAME"
    0x09, 0x4C, 0x4F, 0x4E, 0x47, 0x2D, 0x4E, 0x41, 0x4D, 0x45,
    0x17,       # OBNAME

    0x35,       # ATTRIB:LRV
    # "ELEMENT-LIMIT"
    0x0D, 0x45, 0x4C, 0x45, 0x4D, 0x45, 0x4E, 0x54, 0x2D, 0x4C,
    0x49, 0x4D, 0x49, 0x54,
    0x12,       # UVARI
    0x01,       # 1

    0x35,       # ATTRIB: LRV
    # "REPRESENTATION-CODE
    0x13, 0x52, 0x45, 0x50, 0x52, 0x45, 0x53, 0x45, 0x4E, 0x54,
    0x41, 0x54, 0x49, 0x4F, 0x4E, 0x2D, 0x43, 0x4F, 0x44, 0x45,
    0x0F,       # USHORT
    0x02,       # FSINGL

    0x30,       # ATTRIB: L
    0x05, 0x55, 0x4E, 0x49, 0x54, 0x53, # "UNITS"

    0x35,       # ATTRIB: LRV
    # "DIMENSION"
    0x09, 0x44, 0x49, 0x4D, 0x45, 0x4E, 0x53, 0x49, 0x4F, 0x4E,
    0x12,       # UVARI
    0x01,       # 1

    # object #1
    0x70,       # OBJECT:N
    0x00, 0x00, 0x04, 0x54, 0x49, 0x4D, 0x45, # (0, 0, "TIME")
    0x21, 0x00, 0x00, 0x01, 0x31,             # "1"

    # # segment trailer #1
    # 0x00, 0x00, # CHECKSUM, not checked yet
    # 0x00, 0x68, # length = 104

    # # segment header #2
    # 0x00, 0x26, # length = 38
    # 0xE7,
    # 0x03,

    # ATTRIB: x2
    0x20,
    0x20,

    0x21,       # ATTRIB: V
    0x01, 0x73, # 1

    # object #2
    0x70,
    # (1, 0, "PRESSURE")
    0x01, 0x00, 0x08, 0x50, 0x52, 0x45, 0x53, 0x53, 0x55, 0x52, 0x45,

    0x21,   # 0,0, "2"
    0x00, 0x00, 0x01, 0x32,

    0x20,   # ATTRIB:

    0x21, 0x07,

    0x21,
    0x03, 0x70, 0x73, 0x69, # "psi"

    # # segment trailer #2
    # 0x00, 0x00, # CHECKSUM, not cheched yet
    # 0x00, 0x26, # length = 38

    # # segment header #3
    # 0x00, 0x26, # length = 38
    # 0xC7,
    # 0x03,

    0x70,
    # "PAD-ARRAY"
    0x00, 0x01, 0x09, 0x50, 0x41, 0x44, 0x2D, 0x41, 0x52, 0x52, 0x41, 0x59,

    0x21,
    0x00, 0x00, 0x01, 0x33, # 0, 0, "3"

    0x29,
    0x02,
    0x08, 0x14, # [8, 20]

    0x21,
    0x0D,       # UNORM

    0x00,       # ABSENT

    0x29,
    0x02,
    0x08, 0x0A, # [8, 10]

    # # segment trailer #3
    # 0x01, # pad-count
    # 0x00, 0x00,
    # 0x00, 0x26, # length = 38
])

def test_objects(f):
    objects = f.objects
    assert len(list(objects)) == 864

def test_fileheader(f):
    key = dlisio.core.fingerprint('FILE-HEADER', '5', 2, 0)
    fh = f._objects.objects[key]
    assert fh.name.id == "5"
    assert fh.name.origin == 2
    assert fh.name.copynumber == 0
    assert fh.id == "MSCT_197LTP"
    assert fh.sequencenr == "197"

def test_origin(f):
    key = dlisio.core.fingerprint('ORIGIN', 'DLIS_DEFINING_ORIGIN', 2, 0)
    origin = f._objects.objects[key]

    assert origin.name.id           == "DLIS_DEFINING_ORIGIN"
    assert origin.name.origin       == 2
    assert origin.name.copynumber   == 0
    assert origin.file_id           == "MSCT_197LTP"
    assert origin.file_set_name     == "FAROE_PETROLEUM/206_05A-3"
    assert origin.file_set_nr       == 41
    assert origin.file_nr           == 167
    assert origin.file_type         == "STATION LOG"
    assert origin.product           == "OP"
    assert origin.version           == "19C0-187"
    assert len(origin.programs)     == 4
    assert origin.creation_time     == datetime(2011, 8, 20, 22, 48, 50)
    assert origin.order_nr          == "BSAX-00003"
    assert origin.descent_nr        == ["-1"]
    assert origin.run_nr            == ["1"]
    assert origin.well_id           == ""
    assert origin.well_name         == "206/05a-3"
    assert origin.field_name        == "Fulla"
    assert origin.producer_code     == 440
    assert origin.producer_name     == "Schlumberger"
    assert origin.company           == "Faroe Petroleum"
    assert origin.namespace_name    == "SLB"
    assert origin.namespace_version == None

def test_channel(f):
    key = dlisio.core.fingerprint('CHANNEL', 'TDEP', 2, 0)
    channel = f._objects.objects[key]
    assert channel.name.id         == "TDEP"
    assert channel.name.origin     == 2
    assert channel.name.copynumber == 0
    assert channel.long_name       == "6-Inch Frame Depth"
    assert channel.type            == "CHANNEL"
    assert channel.reprc           == 2
    assert channel.properties      == ["440-BASIC"]
    assert channel.dimension       == [1]
    assert channel.axis            == []
    assert channel.element_limit   == [1]
    assert channel.units           == "0.1 in"
    assert channel.source is None

def test_frame(f):
    key = dlisio.core.fingerprint('FRAME', '2000T', 2, 0)
    frame = f._objects.objects[key]
    assert frame.name.id         == "2000T"
    assert frame.name.origin     == 2
    assert frame.name.copynumber == 0
    assert frame.type            == "FRAME"
    assert frame.direction       == "INCREASING"
    assert frame.spacing         == 2000
    assert frame.index_type      == "TIME"
    assert frame.index_min       == 33354518
    assert frame.index_max       == 35194520
    assert len(frame.channels)   == 4
    assert frame.encrypted == False
    assert frame.description is None

def test_channel_order(f):
    key800 = dlisio.core.fingerprint('FRAME', '800T', 2, 0)
    key2000 = dlisio.core.fingerprint('FRAME', '2000T', 2, 0)

    ref2000T = ["TIME", "TDEP", "TENS_SL", "DEPT_SL"]
    ref800T  = ["TIME", "TDEP", "ETIM", "LMVL", "UMVL", "CFLA", "OCD" , "RCMD",
                "RCPP", "CMRT", "RCNU", "DCFL", "DFS" , "DZER", "RHMD", "HMRT",
                "RHV" , "RLSW", "MNU" , "S1CY", "S2CY", "RSCU", "RSTS", "UCFL",
                "CARC", "CMDV", "CMPP", "CNU" , "HMDV", "HV"  , "LSWI", "SCUR",
                "SSTA", "RCMP", "RHPP", "RRPP", "CMPR", "HPPR", "RPPV", "SMSC",
                "CMCU", "HMCU", "CMLP"]

    for i, ch in enumerate(f._objects.objects[key800].channels):
        assert ch.name.id == ref800T[i]

    for i, ch in enumerate(f._objects.objects[key2000].channels):
        assert ch.name.id == ref2000T[i]

def test_tool(f):
    key = dlisio.core.fingerprint('TOOL', 'MSCT', 2, 0)
    tool = f._objects.objects[key]
    assert tool.name.id         == "MSCT"
    assert tool.name.origin     == 2
    assert tool.name.copynumber == 0
    assert tool.type            == "TOOL"
    assert tool.description     == "Mechanical Sidewall Coring Tool"
    assert tool.trademark_name  == "MSCT-AA"
    assert tool.generic_name    == "MSCT"
    assert tool.status          == 1
    assert len(tool.parameters) == 22
    assert len(tool.channels)   == 74
    assert len(tool.parts)      == 9

    assert len(list(f.tools)) == 2
    tools = [o for o in f.tools if o.name.id == "MSCT"]
    assert len(tools) == 1

def test_parameter(f):
    key = dlisio.core.fingerprint('PARAMETER', 'FLSHSTRM', 2, 0)
    param = f._objects.objects[key]
    assert param.name.id         == "FLSHSTRM"
    assert param.name.origin     == 2
    assert param.name.copynumber == 0
    assert param.type            == "PARAMETER"
    assert param.long_name       == "Flush depth-delayed streams to output at end"
    assert param.dimension is None
    assert param.axis      is None
    assert param.zones     is None
    assert len(list(f.parameters)) == 226
    param = [o for o in f.parameters if o.name.id == "FLSHSTRM"]
    assert len(param) == 1

def test_calibrations(f):
    key = dlisio.core.fingerprint('CALIBRATION', 'CNU', 2, 0)
    calibration = f._objects.objects[key]
    assert calibration.name.id           == "CNU"
    assert calibration.name.origin       == 2
    assert calibration.name.copynumber   == 0
    assert calibration.type              == "CALIBRATION"
    assert len(calibration.parameters)   == 0
    assert len(calibration.coefficients) == 2
    assert calibration.method is None
    assert len(list(calibration.calibrated_channel))   == 1
    assert len(list(calibration.uncalibrated_channel)) == 1

def test_Unknown(f):
    unknown = next(iter(f.unknowns))
    print(unknown)
    # should have all unknown should have attributes as a field
    # so this shouldn't be AttributeError
    _ = unknown.attributes
    assert len(list(f.unknowns)) == 501

def test_fmtstring(f):
    reference1 = "ffffffffffffffffffffffffffffffffffffffflfff"
    reference2 = "ffff"

    key800 = dlisio.core.fingerprint('FRAME', '800T', 2, 0)
    key2000 = dlisio.core.fingerprint('FRAME', '2000T', 2, 0)

    frame800 = f._objects.objects[key800]
    frame2000 = f._objects.objects[key2000]

    fmtstring1 = frame800.fmtstr()
    fmtstring2 = frame2000.fmtstr()

    assert fmtstring1 == reference1
    assert fmtstring2 == reference2

def test_dtype(f):
    key2000 = dlisio.core.fingerprint('FRAME', '2000T', 2, 0)
    frame2000 = f._objects.objects[key2000]
    dtype1 = frame2000.dtype
    assert dtype1 == np.dtype([('TIME', np.float32),
                               ('TDEP', np.float32),
                               ('TENS_SL', np.float32),
                               ('DEPT_SL', np.float32)])

def test_load_pre_sul_garbage(channels_f):
    with dlisio.load('data/pre-sul-garbage.dlis') as f:
        assert f.storage_label() == channels_f.storage_label()
        assert f.sul_offset == 12

def test_load_pre_vrl_garbage(channels_f):
    with dlisio.load('data/pre-sul-pre-vrl-garbage.dlis') as f:
        assert f.storage_label() == channels_f.storage_label()
        assert f.sul_offset == 12

def test_load_file_with_broken_utf8():
    with dlisio.load('data/broken-degree-symbol.dlis') as f:
        pass

def test_padbytes_as_large_as_record():
    # 180-byte long explicit record with padding, and padbytes are set to 180
    # (leaving the resulting len(data) == 0)
    f = dlisio.open('data/padbytes-large-as-record.dlis')
    f.reindex([0], [180])

    rec = f.extract([0])[0]
    assert rec.explicit
    assert len(memoryview(rec)) == 0
