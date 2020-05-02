import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import namedtuple


# Simple translation functions
fn_delay_on_off = lambda src, dest: 0 if src.delay_output_routing == 0 else 1
fn_str_pred = lambda src, dest: "PRED"
fn_str_sq = lambda src, dest: "SQ"
fn_target = lambda src, dest: 0 if src.lfo_eg == 2 else 1
fn_lfo_mode = lambda src, dest: 1 if src.lfo_bpm_sync == 0 else 2
fn_cutoff_velocity = lambda src, dest: (0, 63, 127)[src.cutoff_velocity]
fn_cutoff_kbd_track = lambda src, dest: 2 - src.cutoff_kbd_track
fn_multi_octave = lambda src, dest: 0 if src.vco_1_octave == 0 else src.vco_1_octave - 1
fn_voice_mode_type = lambda src, dest: {0: 4, 1: 4, 2: 3, 3: 2, 4: 2, 5: 4, 6: 1, 7: 4}[src.voice_mode]
fn_delay_time = lambda src, dest: int(src.delay_time * 350.0 / 654.0)


def fn_voice_mode_depth(src, dest):
    """
    -XD-
    *note P3 (VOICE MODE TYPE)
        1:ARP, 2:CHORD (Mono verified), 3:UNISON, 4:POLY
    *note P2 (VOICE MODE DEPTH)
        [POLY] 0~255:Poly, 256~1023:Duo 0~1023
        [UNISON] 0 ~ 1023: Detune 0 Cent
        [CHORD] 0~1:Mono, 2~73:5th, 74~146:sus2, 147~219:m, 220~292:Maj, 293~365:sus4,
            366~438:m7, 439~511:7, 512~585:7sus4, 586~658:Maj7, 659~731:aug,
            732~804:dim, 805~877:m7b5, 878~950:mMaj7, 951~1023:Maj7b5
        [ARP] unchanged

    -OG-
    *note P11 (VOICE MODE)
        0:POLY, 1:DUO, 2:UNISON, 3:MONO, 4:CHORD, 5:DELAY, 6:ARP, 7:SIDECHAIN

    *note P12 (VOICE MODE DEPTH)
        [POLY] 0~1023:Invert 0~8
        [DUO],[UNISON] 0~1023:Detune 0 Cent ~ 50 Cent
        [MONO] 0~1023:Sub 0~1023
        [CHORD] unchanged for non-mono mode
        [DELAY] N/A
        [ARP] unchanged
        [SIDECHAIN] N/A
    """
    if src.voice_mode == 1:
        # DUO; this handling could well be wrong
        return src.voice_mode_depth + 256
    elif src.voice_mode == 3:
        # MONO
        return 0
    else:
        return src.voice_mode_depth


patch_translation_value = namedtuple("Field", ["name", "type", "source"])

"""
A translation table for converting from minilogue OG patch data. Each tuple takes one of
the forms

('label', 'binary-format string', 'src1_name')
('label', 'binary-format string', p), where p is an integer
('label', 'binary-format string', f, arg1, ..., argN), where f is a function with optional args

"""
minilogue_xd_patch_struct = (
    # 0
    ("str_PROG", "4s", "str_PROG"),
    ("program_name", "12s", "program_name"),
    ("octave", "B", "keyboard_octave"),
    ("portamento", "B", "portamento_time"),
    ("key_trig", "B", 0),
    ("voice_mode_depth", "H", fn_voice_mode_depth),
    ("voice_mode_type", "B", fn_voice_mode_type),
    ("vco_1_wave", "B", "vco_1_wave"),
    ("vco_1_octave", "B", "vco_1_octave"),
    ("vco_1_pitch", "H", "vco_1_pitch"),
    ("vco_1_shape", "H", "vco_1_shape"),
    ("vco_2_wave", "B", "vco_2_wave"),
    ("vco_2_octave", "B", "vco_2_octave"),
    ("vco_2_pitch", "H", "vco_2_pitch"),
    ("vco_2_shape", "H", "vco_2_shape"),
    ("sync", "B", "sync"),
    ("ring", "B", "ring"),
    ("cross_mod_depth", "H", "cross_mod_depth"),
    ("multi_type", "B", 0),
    ("select_noise", "B", 1),
    ("select_vpm", "B", 6),
    ("select_user", "B", 0),
    ("shape_noise", "H", 1),
    ("shape_vpm", "H", 6),
    ("shape_user", "H", 0),
    ("shift_shape_noise", "H", 0),
    # 50
    ("shift_shape_vpm", "H", 0),
    ("shift_shape_user", "H", 0),
    ("vco1_level", "H", "vco_1_level"),
    ("vco2_level", "H", "vco_2_level"),
    ("multi_level", "H", "noise_level"),
    ("cutoff", "H", "cutoff"),
    ("resonance", "H", "resonance"),
    ("cutoff_drive", "B", 0),
    ("cutoff_keyboard_track", "B", fn_cutoff_kbd_track),
    ("amp_eg_attack", "H", "amp_eg_attack"),
    ("amp_eg_decay", "H", "amp_eg_decay"),
    ("amp_eg_sustain", "H", "amp_eg_sustain"),
    ("amp_eg_release", "H", "amp_eg_release"),
    ("eg_attack", "H", "amp_attack"),
    ("eg_decay", "H", "amp_decay"),
    ("eg_int", "H", "cutoff_eg_int"),
    ("eg_target", "B", fn_target),
    ("lfo_wave", "B", "lfo_wave"),
    ("lfo_mode", "B", fn_lfo_mode),
    ("lfo_rate", "H", "lfo_rate"),
    ("lfo_int", "H", "lfo_int"),
    ("lfo_target", "B", "lfo_target"),
    ("mod_fx_on_off", "B", 0),
    ("mod_fx_type", "B", 0),
    ("mod_fx_chorus", "B", 0),
    ("mod_fx_ensemble", "B", 0),
    ("mod_fx_phaser", "B", 0),
    ("mod_fx_flanger", "B", 0),
    ("mod_fx_user", "B", 0),
    ("mod_fx_time", "H", 0),
    ("mod_fx_depth", "H", 0),
    ("delay_on_off", "B", fn_delay_on_off),
    # 100
    ("delay_sub_type", "B", 3),
    ("delay_time", "H", fn_delay_time),
    ("delay_depth", "H", "delay_feedback"),
    ("reverb_on_off", "B", 0),
    ("reverb_sub_type", "B", 0),
    ("reverb_time", "H", 0),
    ("reverb_depth", "H", 0),
    ("bend_range_plus", "B", "bend_range_plus"),
    ("bend_range_minus", "B", "bend_range_minus"),
    ("joystick_assign_plus", "B", 22),
    ("joystick_range_plus", "B", 100),
    ("joystick_assign_minus", "B", 12),
    ("joystick_range_minus", "B", 100),
    ("cv_in_mode", "B", 0),
    ("cv_in_1_assign", "B", 0),
    ("cv_in_1_range", "B", 100),
    ("cv_in_2_assign", "B", 0),
    ("cv_in_2_range", "B", 100),
    ("micro_tuning", "B", 0),
    ("scale_key", "B", 12),
    ("program_tuning", "B", 50),
    ("lfo_key_sync", "B", "lfo_key_sync"),
    ("lfo_voice_sync", "B", "lfo_voice_sync"),
    ("lfo_target_osc", "B", 0),
    ("cutoff_velocity", "B", fn_cutoff_velocity),
    ("amp_velocity", "B", "amp_velocity"),
    ("multi_octave", "B", fn_multi_octave),
    ("multi_routing", "B", 0),
    ("eg_legato", "B", 0),
    ("portamento_mode", "B", "portamento_mode"),
    ("portamento_bpm_sync", "B", "portamento_bpm"),
    ("program_level", "B", 102),
    ("vpm_param1_feedback", "B", 199),
    ("vpm_param2_noise_depth", "B", 199),
    ("vpm_param3_shapemodint", "B", 199),
    ("vpm_param4_mod_attack", "B", 199),
    ("vpm_param5_mod_decay", "B", 199),
    ("vpm_param6_modkeytrack", "B", 199),
    ("user_param1", "B", 0),
    ("user_param2", "B", 0),
    ("user_param3", "B", 0),
    ("user_param4", "B", 0),
    ("user_param5", "B", 0),
    ("user_param6", "B", 0),
    ("user_param5_6_r_r_type", "B", 0),
    ("user_param1_2_3_4_type", "B", 0),
    # 150
    ("program_transpose", "B", 13),
    ("delay_dry_wet", "H", 512),  # 50% wet/dry
    ("reverb_dry_wet", "H", 512),  # 50% wet/dry
    ("midi_after_touch_assign", "B", 12),
    ("str_PRED", "4s", fn_str_pred),
    ("str_SQ", "2s", fn_str_sq),
    ("step_1_16_active_step", "<H", 65535),
    ("bpm", "H", "bpm"),
    ("step_length", "B", "step_length"),
    ("step_resolution", "B", "step_resolution"),
    ("swing", "B", "swing"),
    ("default_gate_time", "B", "default_gate_time"),
    ("step1_16", "<H", "step1_16"),
    ("step1_16_motion", "<H", 0),  # Fix this
    ("motion_slot_1_parameter", "<H", "motion_slot_1_parameter"),
    ("motion_slot_2_parameter", "<H", "motion_slot_2_parameter"),
    ("motion_slot_3_parameter", "<H", "motion_slot_3_parameter"),
    ("motion_slot_4_parameter", "<H", "motion_slot_4_parameter"),
    ("motion_slot_1_step1_16", "<H", "motion_slot_1_step1_16"),
    ("motion_slot_2_step1_16", "<H", "motion_slot_2_step1_16"),
    ("motion_slot_3_step1_16", "<H", "motion_slot_3_step1_16"),
    ("motion_slot_4_step1_16", "<H", "motion_slot_4_step1_16"),
    # 190
    ("step_1_event_data", "52p", 52 * b"\x00"),  # Fix/translate these
    ("step_2_event_data", "52p", 52 * b"\x00"),
    ("step_3_event_data", "52p", 52 * b"\x00"),
    ("step_4_event_data", "52p", 52 * b"\x00"),
    ("step_5_event_data", "52p", 52 * b"\x00"),
    ("step_6_event_data", "52p", 52 * b"\x00"),
    ("step_7_event_data", "52p", 52 * b"\x00"),
    ("step_8_event_data", "52p", 52 * b"\x00"),
    ("step_9_event_data", "52p", 52 * b"\x00"),
    ("step_10_event_data", "52p", 52 * b"\x00"),
    ("step_11_event_data", "52p", 52 * b"\x00"),
    ("step_12_event_data", "52p", 52 * b"\x00"),
    ("step_13_event_data", "52p", 52 * b"\x00"),
    ("step_14_event_data", "52p", 52 * b"\x00"),
    ("step_15_event_data", "52p", 52 * b"\x00"),
    ("step_16_event_data", "52p", 52 * b"\x00"),
    # 1022
    ("arp_gate_time", "B", "default_gate_time"),
    ("arp_rate", "B", 10),
)


prog_info_template = """\
<?xml version="1.0" encoding="UTF-8"?>

<xd_ProgramInformation>
  <Programmer></Programmer>
  <Comment></Comment>
</xd_ProgramInformation>
"""


favorite_template = """\
<?xml version="1.0" encoding="UTF-8"?>

<xd_Favorite>
  <Bank>
    <Data>0</Data>
    <Data>1</Data>
    <Data>2</Data>
    <Data>3</Data>
    <Data>4</Data>
    <Data>5</Data>
    <Data>6</Data>
    <Data>7</Data>
  </Bank>
  <Bank>
    <Data>8</Data>
    <Data>9</Data>
    <Data>10</Data>
    <Data>11</Data>
    <Data>12</Data>
    <Data>13</Data>
    <Data>14</Data>
    <Data>15</Data>
  </Bank>
</xd_Favorite>
"""


def fileinfo_xml(non_init_patch_ids):
    """Build FileInformation.xml metadata file.

    Args:
        non_init_patch_ids (list of ints): 0-based list of non-Init-Program patches

    Returns:
        str: formatted xml

    """
    # create the file structure
    root = ET.Element("KorgMSLibrarian_Data")
    product = ET.SubElement(root, "Product")
    product.text = "minilogue xd"
    contents = ET.SubElement(root, "Contents")

    contents.set("NumProgramData", str(len(non_init_patch_ids)))
    contents.set("NumPresetInformation", "0")
    contents.set("NumTuneScaleData", "0")
    contents.set("NumTuneOctData", "0")

    if len(non_init_patch_ids) == 0:
        contents.set("NumFavoriteData", "0")
    else:
        contents.set("NumFavoriteData", "1")
        fave = ET.SubElement(contents, "FavoriteData")
        fave_info = ET.SubElement(fave, "File")
        fave_info.text = "FavoriteData.fav_data"

    for i in non_init_patch_ids:
        prog = ET.SubElement(contents, "ProgramData")
        prog_info = ET.SubElement(prog, "Information")
        prog_info.text = f"Prog_{i:03d}.prog_info"
        prog_bin = ET.SubElement(prog, "ProgramBinary")
        prog_bin.text = f"Prog_{i:03d}.prog_bin"

    # https://stackoverflow.com/a/3095723
    formatted_xml = minidom.parseString(
        ET.tostring(root, encoding="utf-8", method="xml")
    ).toprettyxml(indent="  ")

    return formatted_xml


"""
Korg's program format tables for the minilogues XD.
Any personal notes are designated Gn.

Minilogue XD
+---------+-------+---------+---------------------------------------------+
|  Offset |  Bit  |  Range  |  Description                                |
+---------+-------+---------+---------------------------------------------+
|   0~3   |       |  ASCII  |  'PROG'                                     |
+---------+-------+---------+---------------------------------------------+
|   4~15  |       |  ASCII  |  PROGRAM NAME [12]                 *note P1 |
+---------+-------+---------+---------------------------------------------+
|   16    |       |  0~4    |  OCTAVE                           0~4=-2~+2 |
+---------+-------+---------+---------------------------------------------+
|   17    |       |  0,1    |  PORTAMENTO *note G1                  0~127 |
+---------+-------+---------+---------------------------------------------+
|   18    |       |  0,1    |  KEY TRIG                        0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   19    | H:0~7 |  0~1023 |  VOICE MODE DEPTH                  *note P2 |
|   20    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   21    |       |  1~4    |  VOICE MODE TYPE *note G2          *note P3 |
+---------+-------+---------+---------------------------------------------+
|   22    |       |  0~2    |  VCO 1 WAVE                        *note P4 |
+---------+-------+---------+---------------------------------------------+
|   23    |       |  0~3    |  VCO 1 OCTAVE              0~3=16',8',4',2' |
+---------+-------+---------+---------------------------------------------+
|   24    | H:0~7 |  0~1023 |  VCO 1 PITCH                       *note P5 |
|   25    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   26    | H:0~7 |  0~1023 |  VCO 1 SHAPE                                |
|   27    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   28    |       |  0~2    |  VCO 2 WAVE                        *note P4 |
+---------+-------+---------+---------------------------------------------+
|   29    |       |  0~3    |  VCO 2 OCTAVE              0~3=16',8',4',2' |
+---------+-------+---------+---------------------------------------------+
|   30    | H:0~7 |  0~1023 |  VCO 2 PITCH                       *note P5 |
|   31    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   32    | H:0~7 |  0~1023 |  VCO 2 SHAPE                                |
|   33    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   34    |       |  0,1    |  SYNC                 0,1=SYNC ON, SYNC OFF |
+---------+-------+---------+---------------------------------------------+
|   35    |       |  0,1    |  RING                 0,1=RING ON, RING OFF |
+---------+-------+---------+---------------------------------------------+
|   36    | H:0~7 |  0~1023 |  CROSS MOD DEPTH                            |
|   37    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   38    |       |  0~2    |  MULTI TYPE              0~2=NOISE,VPM,USER |
+---------+-------+---------+---------------------------------------------+
|   39    |       |  0~3    |  SELECT NOISE                      *note P6 |
+---------+-------+---------+---------------------------------------------+
|   40    |       |  0~15   |  SELECT VPM                        *note P7 |
+---------+-------+---------+---------------------------------------------+
|   41    |       |  0~15   |  SELECT USER                       *note P8 |
+---------+-------+---------+---------------------------------------------+
|   42    | H:0~7 |  0~1023 |  SHAPE NOISE                                |
|   43    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   44    | H:0~7 |  0~1023 |  SHAPE VPM                                  |
|   45    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   46    | H:0~7 |  0~1023 |  SHAPE USER                                 |
|   47    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   48    | H:0~7 |  0~1023 |  SHIFT SHAPE NOISE                          |
|   49    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   50    | H:0~7 |  0~1023 |  SHIFT SHAPE VPM                            |
|   51    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   52    | H:0~7 |  0~1023 |  SHIFT SHAPE USER                           |
|   53    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   54    | H:0~7 |  0~1023 |  VCO1 LEVEL                                 |
|   55    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   56    | H:0~7 |  0~1023 |  VCO2 LEVEL                                 |
|   57    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   58    | H:0~7 |  0~1023 |  MULTI LEVEL                                |
|   59    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   60    | H:0~7 |  0~1023 |  CUTOFF                                     |
|   61    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   62    | H:0~7 |  0~1023 |  RESONANCE                                  |
|   63    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   64    |       |  0~2    |  CUTOFF DRIVE                      *note P9 |
+---------+-------+---------+---------------------------------------------+
|   65    |       |  0~2    |  CUTOFF KEYBOARD TRACK             *note P9 |
+---------+-------+---------+---------------------------------------------+
|   66    | H:0~7 |  0~1023 |  AMP EG ATTACK                              |
|   67    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   68    | H:0~7 |  0~1023 |  AMP EG DECAY                               |
|   69    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   70    | H:0~7 |  0~1023 |  AMP EG SUSTAIN                             |
|   71    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   72    | H:0~7 |  0~1023 |  AMP EG RELEASE                             |
|   73    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   74    | H:0~7 |  0~1023 |  EG ATTACK                                  |
|   75    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   76    | H:0~7 |  0~1023 |  EG DECAY                                   |
|   77    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   78    | H:0~7 |  0~1023 |  EG INT                           *note P10 |
|   79    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   80    | H:0~7 |  0~2    |  EG TARGET        0~2=CUTOFF, PITCH2, PITCH |
+---------+-------+---------+---------------------------------------------+
|   81    |       |  0~2    |  LFO WAVE                          *note P4 |
+---------+-------+---------+---------------------------------------------+
|   82    |       |  0~2    |  LFO MODE             0~2=1-SHOT,NORMAL,BPM |
+---------+-------+---------+---------------------------------------------+
|   83    | H:0~7 |  0~1023 |  LFO RATE                         *note P11 |
|   84    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   85    | H:0~7 |  0~1023 |  LFO INT                                    |
|   86    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   87    |       |  0~2    |  LFO TARGET          0~2=CUTOFF,SHAPE,PITCH |
+---------+-------+---------+---------------------------------------------+
|   88    |       |  0,1    |  MOD FX ON/OFF                   0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   89    |       |  1~5    |  MOD FX TYPE                      *note P12 |
+---------+-------+---------+---------------------------------------------+
|   90    |       |  0~7    |  MOD FX CHORUS                    *note P13 |
+---------+-------+---------+---------------------------------------------+
|   91    |       |  0~2    |  MOD FX ENSEMBLE                  *note P14 |
+---------+-------+---------+---------------------------------------------+
|   92    |       |  0~7    |  MOD FX PHASER                    *note P15 |
+---------+-------+---------+---------------------------------------------+
|   93    |       |  0~7    |  MOD FX FLANGER                   *note P16 |
+---------+-------+---------+---------------------------------------------+
|   94    |       |  0~15   |  MOD FX USER                       *note P8 |
+---------+-------+---------+---------------------------------------------+
|   95    | H:0~7 |  0~1023 |  MOD FX TIME                                |
|   96    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   97    | H:0~7 |  0~1023 |  MOD FX DEPTH                               |
|   98    | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   99    |       |  0,1    |  DELAY ON/OFF                    0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   100   |       |  0~19   |  DELAY SUB TYPE                   *note P17 |
+---------+-------+---------+---------------------------------------------+
|   101   | H:0~7 |  0~1023 |  DELAY TIME                                 |
|   102   | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   103   | H:0~7 |  0~1023 |  DELAY DEPTH                                |
|   104   | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   105   |       |  0,1    |  REVERB ON/OFF                   0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   106   |       |  0~19   |  REVERB SUB TYPE                  *note P18 |
+---------+-------+---------+---------------------------------------------+
|   107   | H:0~7 |  0~1023 |  REVERB TIME                                |
|   108   | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   109   | H:0~7 |  0~1023 |  REVERB DEPTH                               |
|   110   | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   111   |       |  0~12   |  BEND RANGE (+)                 OFF~+12Note |
+---------+-------+---------+---------------------------------------------+
|   112   |       |  0~12   |  BEND RANGE (-)                 OFF~-12Note |
+---------+-------+---------+---------------------------------------------+
|   113   |       |  0~28   |  JOYSTICK ASSIGN (+)              *note P19 |
+---------+-------+---------+---------------------------------------------+
|   114   |       |  0~200  |  JOYSTICK RANGE (+)       0~200=-100%~+100% |
+---------+-------+---------+---------------------------------------------+
|   115   |       |  0~28   |  JOYSTICK ASSIGN (-)              *note P19 |
+---------+-------+---------+---------------------------------------------+
|   116   |       |  0~200  |  JOYSTICK RANGE (-)       0~200=-100%~+100% |
+---------+-------+---------+---------------------------------------------+
|   117   |       |  0~2    |  CV IN MODE                       *note P20 |
+---------+-------+---------+---------------------------------------------+
|   118   |       |  0~28   |  CV IN 1 ASSIGN (+)               *note P19 |
+---------+-------+---------+---------------------------------------------+
|   119   |       |  0~200  |  CV IN 1 RANGE (+)        0~200=-100%~+100% |
+---------+-------+---------+---------------------------------------------+
|   120   |       |  0~28   |  CV IN 2 ASSIGN (-)               *note P19 |
+---------+-------+---------+---------------------------------------------+
|   121   |       |  0~200  |  CV IN 2 RANGE (-)        0~200=-100%~+100% |
+---------+-------+---------+---------------------------------------------+
|   122   |       |  0~139  |  MICRO TUNING                     *note P21 |
+---------+-------+---------+---------------------------------------------+
|   123   |       |  0~24   |  SCALE KEY             0~24=-12Note~+12Note |
+---------+-------+---------+---------------------------------------------+
|   124   |       |  0~100  |  PROGRAM TUNING       0~100=-50Cent~+50Cent |
+---------+-------+---------+---------------------------------------------+
|   125   |       |  0,1    |  LFO KEY SYNC                    0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   126   |       |  0,1    |  LFO VOICE SYNC                  0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   127   |       |  0~3    |  LFO TARGET OSC                   *note P22 |
+---------+-------+---------+---------------------------------------------+
|   128   |       |  0~127  |  CUTOFF VELOCITY                            |
+---------+-------+---------+---------------------------------------------+
|   129   |       |  0~127  |  AMP VELOCITY                               |
+---------+-------+---------+---------------------------------------------+
|   130   |       |  0~3    |  MULTI OCTAVE              0~3=16',8',4',2' |
+---------+-------+---------+---------------------------------------------+
|   131   |       |  0,1    |  MULTI ROUTING        0,1=Pre VCF, Post VCF |
+---------+-------+---------+---------------------------------------------+
|   132   |       |  0,1    |  EG LEGATO                       0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   133   |       |  0,1    |  PORTAMENTO MODE                0,1=Auto,On |
+---------+-------+---------+---------------------------------------------+
|   134   |       |  0,1    |  PORTAMENTO BPM SYNC             0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   135   |       | 12~132  |  PROGRAM LEVEL            12~132=-18dB~+6dB |
+---------+-------+---------+---------------------------------------------+
|   136   |       |  0~200  |  VPM PARAM1 (Feedback)    0~200=-100%~+100% |
+---------+-------+---------+---------------------------------------------+
|   137   |       |  0~200  |  VPM PARAM2 (Noise Depth) 0~200=-100%~+100% |
+---------+-------+---------+---------------------------------------------+
|   138   |       |  0~200  |  VPM PARAM3 (ShapeModInt) 0~200=-100%~+100% |
+---------+-------+---------+---------------------------------------------+
|   139   |       |  0~200  |  VPM PARAM4 (Mod Attack)  0~200=-100%~+100% |
+---------+-------+---------+---------------------------------------------+
|   140   |       |  0~200  |  VPM PARAM5 (Mod Decay)   0~200=-100%~+100% |
+---------+-------+---------+---------------------------------------------+
|   141   |       |  0~200  |  VPM PARAM6 (ModKeyTrack) 0~200=-100%~+100% |
+---------+-------+---------+---------------------------------------------+
|   142   |       |         |  USER PARAM1                      *note P23 |
+---------+-------+---------+---------------------------------------------+
|   143   |       |         |  USER PARAM2                      *note P23 |
+---------+-------+---------+---------------------------------------------+
|   144   |       |         |  USER PARAM3                      *note P23 |
+---------+-------+---------+---------------------------------------------+
|   145   |       |         |  USER PARAM4                      *note P23 |
+---------+-------+---------+---------------------------------------------+
|   146   |       |         |  USER PARAM5                      *note P23 |
+---------+-------+---------+---------------------------------------------+
|   147   |       |         |  USER PARAM6                      *note P23 |
+---------+-------+---------+---------------------------------------------+
|   148   |  0~1  |         |  USER PARAM5 TYPE                 *note P24 |
|         |  2~3  |         |  USER PARAM6 TYPE                 *note P24 |
|         |  4~5  |         |  Reserved                                   |
|         |  6~7  |         |  Reserved                                   |
+---------+-------+---------+---------------------------------------------+
|   149   |  0~1  |         |  USER PARAM1 TYPE                 *note P24 |
|         |  2~3  |         |  USER PARAM2 TYPE                 *note P24 |
|         |  4~5  |         |  USER PARAM3 TYPE                 *note P24 |
|         |  6~7  |         |  USER PARAM4 TYPE                 *note P24 |
+---------+-------+---------+---------------------------------------------+
|   150   |       | 1~25    |  PROGRAM TRANSPOSE             -12~+12 Note |
+---------+-------+---------+---------------------------------------------+
|   151   | H:0~7 | 0~1024  |  DELAY DRY WET                              |
|   152   | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   153   | H:0~7 | 0~1024  |  REVERB DRY WET                             |
|   154   | L:0~7 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   155   |       |  0~28   |  MIDI AFTER TOUCH ASSIGN          *note P19 |
+---------+-------+---------+---------------------------------------------+
| 156~159 |       |  ASCII  |  'PRED'                                     |
+---------+-------+---------+---------------------------------------------+
| 160~161 |       |  ASCII  |  'SQ'                              *note S1 |
+---------+-------+---------+---------------------------------------------+
|   162   |   0   |   0,1   |  Step  1 Active Step Off/On      0,1=Off,On |
|   162   |   1   |   0,1   |  Step  2 Active Step Off/On      0,1=Off,On |
|   162   |   2   |   0,1   |  Step  3 Active Step Off/On      0,1=Off,On |
|   162   |   3   |   0,1   |  Step  4 Active Step Off/On      0,1=Off,On |
|   162   |   4   |   0,1   |  Step  5 Active Step Off/On      0,1=Off,On |
|   162   |   5   |   0,1   |  Step  6 Active Step Off/On      0,1=Off,On |
|   162   |   6   |   0,1   |  Step  7 Active Step Off/On      0,1=Off,On |
|   162   |   7   |   0,1   |  Step  8 Active Step Off/On      0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   163   |   0   |   0,1   |  Step  9 Active Step Off/On      0,1=Off,On |
|   163   |   1   |   0,1   |  Step 10 Active Step Off/On      0,1=Off,On |
|   163   |   2   |   0,1   |  Step 11 Active Step Off/On      0,1=Off,On |
|   163   |   3   |   0,1   |  Step 12 Active Step Off/On      0,1=Off,On |
|   163   |   4   |   0,1   |  Step 13 Active Step Off/On      0,1=Off,On |
|   163   |   5   |   0,1   |  Step 14 Active Step Off/On      0,1=Off,On |
|   163   |   6   |   0,1   |  Step 15 Active Step Off/On      0,1=Off,On |
|   163   |   7   |   0,1   |  Step 16 Active Step Off/On      0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   164   | L:0~7 |100~3000 |  BPM                    100~3000=10.0~300.0 |
|   165   | H:0~3 |         |                                             |
+---------+-------+---------+---------------------------------------------+
|   166   |       |  1~16   |  Step Length                                |
+---------+-------+---------+---------------------------------------------+
|   167   |       |  0~4    |  Step Resolution 0~4 = 1/16,1/8,1/4,1/2,1/1 |
+---------+-------+---------+---------------------------------------------+
|   168   |       | -75~+75 |  Swing                                      |
+---------+-------+---------+---------------------------------------------+
|   169   |       |  0~72   |  Default Gate Time             0~72=0%~100% |
+---------+-------+---------+---------------------------------------------+
|   170   |   0   |   0,1   |  Step  1 Off/On                  0,1=Off,On |
|   170   |   1   |   0,1   |  Step  2 Off/On                  0,1=Off,On |
|   170   |   2   |   0,1   |  Step  3 Off/On                  0,1=Off,On |
|   170   |   3   |   0,1   |  Step  4 Off/On                  0,1=Off,On |
|   170   |   4   |   0,1   |  Step  5 Off/On                  0,1=Off,On |
|   170   |   5   |   0,1   |  Step  6 Off/On                  0,1=Off,On |
|   170   |   6   |   0,1   |  Step  7 Off/On                  0,1=Off,On |
|   170   |   7   |   0,1   |  Step  8 Off/On                  0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   171   |   0   |   0,1   |  Step  9 Off/On                  0,1=Off,On |
|   171   |   1   |   0,1   |  Step 10 Off/On                  0,1=Off,On |
|   171   |   2   |   0,1   |  Step 11 Off/On                  0,1=Off,On |
|   171   |   3   |   0,1   |  Step 12 Off/On                  0,1=Off,On |
|   171   |   4   |   0,1   |  Step 13 Off/On                  0,1=Off,On |
|   171   |   5   |   0,1   |  Step 14 Off/On                  0,1=Off,On |
|   171   |   6   |   0,1   |  Step 15 Off/On                  0,1=Off,On |
|   171   |   7   |   0,1   |  Step 16 Off/On                  0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   172   |   0   |   0,1   |  Step  1 Motion Off/On           0,1=Off,On |
|   172   |   1   |   0,1   |  Step  2 Motion Off/On           0,1=Off,On |
|   172   |   2   |   0,1   |  Step  3 Motion Off/On           0,1=Off,On |
|   172   |   3   |   0,1   |  Step  4 Motion Off/On           0,1=Off,On |
|   172   |   4   |   0,1   |  Step  5 Motion Off/On           0,1=Off,On |
|   172   |   5   |   0,1   |  Step  6 Motion Off/On           0,1=Off,On |
|   172   |   6   |   0,1   |  Step  7 Motion Off/On           0,1=Off,On |
|   172   |   7   |   0,1   |  Step  8 Motion Off/On           0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   173   |   0   |   0,1   |  Step  9 Motion Off/On           0,1=Off,On |
|   173   |   1   |   0,1   |  Step 10 Motion Off/On           0,1=Off,On |
|   173   |   2   |   0,1   |  Step 11 Motion Off/On           0,1=Off,On |
|   173   |   3   |   0,1   |  Step 12 Motion Off/On           0,1=Off,On |
|   173   |   4   |   0,1   |  Step 13 Motion Off/On           0,1=Off,On |
|   173   |   5   |   0,1   |  Step 14 Motion Off/On           0,1=Off,On |
|   173   |   6   |   0,1   |  Step 15 Motion Off/On           0,1=Off,On |
|   173   |   7   |   0,1   |  Step 16 Motion Off/On           0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
| 174~175 |       |         |  Motion Slot 1 Parameter           *note S2 |
+---------+-------+---------+---------------------------------------------+
| 176~177 |       |         |  Motion Slot 2 Parameter           *note S2 |
+---------+-------+---------+---------------------------------------------+
| 178~179 |       |         |  Motion Slot 3 Parameter           *note S2 |
+---------+-------+---------+---------------------------------------------+
| 180~181 |       |         |  Motion Slot 4 Parameter           *note S2 |
+---------+-------+---------+---------------------------------------------+
|   182   |   0   |         |  Motion Slot 1 Step  1 Off/On    0,1=Off,On |
|   182   |   1   |         |  Motion Slot 1 Step  2 Off/On    0,1=Off,On |
|   182   |   2   |         |  Motion Slot 1 Step  3 Off/On    0,1=Off,On |
|   182   |   3   |         |  Motion Slot 1 Step  4 Off/On    0,1=Off,On |
|   182   |   4   |         |  Motion Slot 1 Step  5 Off/On    0,1=Off,On |
|   182   |   5   |         |  Motion Slot 1 Step  6 Off/On    0,1=Off,On |
|   182   |   6   |         |  Motion Slot 1 Step  7 Off/On    0,1=Off,On |
|   182   |   7   |         |  Motion Slot 1 Step  8 Off/On    0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
|   183   |   0   |         |  Motion Slot 1 Step  9 Off/On    0,1=Off,On |
|   183   |   1   |         |  Motion Slot 1 Step 10 Off/On    0,1=Off,On |
|   183   |   2   |         |  Motion Slot 1 Step 11 Off/On    0,1=Off,On |
|   183   |   3   |         |  Motion Slot 1 Step 12 Off/On    0,1=Off,On |
|   183   |   4   |         |  Motion Slot 1 Step 13 Off/On    0,1=Off,On |
|   183   |   5   |         |  Motion Slot 1 Step 14 Off/On    0,1=Off,On |
|   183   |   6   |         |  Motion Slot 1 Step 15 Off/On    0,1=Off,On |
|   183   |   7   |         |  Motion Slot 1 Step 16 Off/On    0,1=Off,On |
+---------+-------+---------+---------------------------------------------+
| 184~185 |       |         |  Motion Slot 2 Step Off/On (same as Slot 1) |
+---------+-------+---------+---------------------------------------------+
| 186~187 |       |         |  Motion Slot 3 Step Off/On (same as Slot 1) |
+---------+-------+---------+---------------------------------------------+
| 188~189 |       |         |  Motion Slot 4 Step Off/On (same as Slot 1) |
+---------+-------+---------+---------------------------------------------+
| 190~241 |       |         |  Step 1 Event Data                 *note S3 |
| 242~293 |       |         |  Step 2 Event Data                 *note S3 |
|   :     |       |         |                                             |
|   :     |       |         |                                             |
| 426~1021|       |         |  Step 16 Event Data                *note S3 |
+---------+-------+---------+---------------------------------------------+
|  1022   |       |  0~72   |  ARP Gate Time               0~72 = 0%~100% |
+---------+-------+---------+---------------------------------------------+
|  1023   |       |  0~10   |  ARP Rate                          *note S4 |
+---------+-------+---------+---------------------------------------------+

*Note G1
Korg's table shows
|   17    |       |  0,1    |  PORTAMENTO                           0~127 |
I assume this should be
|   17    |       |  0~127  |  PORTAMENTO                           0~127 |

*Note G2
Korg's note P3 table shows 1, 2, 2, 3 but should be 1, 2, 3, 4
Korg's note P2 shows 0~73:5th but it should be more like 0~1:Mono 2~73:5th
I don't know if the breakover is from 1 to 2 or greater, but I will assume that.

Tables say Sync and Ring settings are inverted but that isn't true.
Delay time needs scaling: og max delay=350ms, xd high-pass max delay=654ms
Tables say Filter cutoff keyboard tracking value is the same but I find 0->2 -> 2->0

"""