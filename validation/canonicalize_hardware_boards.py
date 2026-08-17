#!/usr/bin/env python3
"""Canonicalize the private PCB references with KiCad's official libraries.

Run this inside the verifier image after generate_hardware_fixtures.py.  Using
pcbnew here keeps the checked-in reference footprints byte-for-byte aligned
with the KiCad version that scores submissions instead of maintaining partial
hand-written footprint copies.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SOLUTIONS = ROOT / "validation" / "solutions"
FOOTPRINT_ROOT = Path("/usr/share/kicad/footprints")


def _mm(value: float) -> int:
    return pcbnew.FromMM(value)


def _point(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(_mm(x), _mm(y))


def _net(board: pcbnew.BOARD, name: str):
    net = board.FindNet(name)
    if net is None:
        raise RuntimeError(f"Board is missing net {name!r}")
    return net


def _footprint_records(board: pcbnew.BOARD) -> list[dict]:
    records = []
    for footprint in board.GetFootprints():
        fpid = footprint.GetFPID()
        position = footprint.GetPosition()
        records.append(
            {
                "library": str(fpid.GetLibNickname()),
                "name": str(fpid.GetLibItemName()),
                "position": (position.x, position.y),
                "orientation": footprint.GetOrientation().AsDegrees(),
                "reference": footprint.GetReference(),
                "value": footprint.GetValue(),
                "pad_nets": {pad.GetNumber(): pad.GetNetname() for pad in footprint.Pads()},
            }
        )
    return records


def _build_replacements(
    board: pcbnew.BOARD,
    records: list[dict],
    position_overrides: dict[str, tuple[float, float]] | None = None,
) -> list:
    replacements = []
    position_overrides = position_overrides or {}
    for record in records:
        library = record["library"]
        name = record["name"]
        replacement = pcbnew.FootprintLoad(str(FOOTPRINT_ROOT / f"{library}.pretty"), name)
        if replacement is None:
            raise RuntimeError(f"Unable to load {library}:{name}")

        replacement.SetFPID(pcbnew.LIB_ID(library, name))
        if record["reference"] in position_overrides:
            replacement.SetPosition(_point(*position_overrides[record["reference"]]))
        else:
            replacement.SetPosition(pcbnew.VECTOR2I(*record["position"]))
        replacement.SetOrientationDegrees(record["orientation"])
        replacement.SetReference(record["reference"])
        replacement.SetValue(record["value"])
        replacement.Reference().SetVisible(False)
        for pad in replacement.Pads():
            net_name = record["pad_nets"].get(pad.GetNumber())
            if net_name:
                pad.SetNet(_net(board, net_name))
        replacements.append(replacement)
    return replacements


def _replace_footprints(board: pcbnew.BOARD, replacements: list) -> None:
    board.DeleteAllFootprints()
    for replacement in replacements:
        board.Add(replacement)


def _clear_tracks(board: pcbnew.BOARD) -> None:
    for track in board.GetTracks():
        board.Remove(track)


def _segment(board: pcbnew.BOARD, net_name: str, layer: int, start: tuple[float, float], end: tuple[float, float]) -> None:
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(_point(*start))
    track.SetEnd(_point(*end))
    track.SetWidth(_mm(0.25))
    track.SetLayer(layer)
    track.SetNet(_net(board, net_name))
    board.Add(track)


def _path(board: pcbnew.BOARD, net_name: str, layer: int, points: list[tuple[float, float]]) -> None:
    for start, end in zip(points, points[1:]):
        _segment(board, net_name, layer, start, end)


def _via(board: pcbnew.BOARD, net_name: str, point: tuple[float, float]) -> None:
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(_point(*point))
    via.SetWidth(_mm(0.8))
    via.SetDrill(_mm(0.4))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(_net(board, net_name))
    board.Add(via)


def canonicalize_adapter() -> None:
    path = SOLUTIONS / "deepee-pcb-001/artifacts/nrf24-adapter.kicad_pcb"
    board = pcbnew.LoadBoard(str(path))
    footprint_records = _footprint_records(board)
    replacements = _build_replacements(
        board,
        footprint_records,
        {"C1": (115, 101.5), "C2": (110.5, 101.5)},
    )
    _clear_tracks(board)
    _replace_footprints(board, replacements)

    # Power rails and the two decoupling capacitors.
    _path(board, "GND", pcbnew.B_Cu, [(103, 102), (105, 100.7), (111.275, 100.7), (115.95, 100.7), (122, 104)])
    for pad, via in [((111.275, 101.5), (111.275, 100.7)), ((115.95, 101.5), (115.95, 100.7))]:
        _path(board, "GND", pcbnew.F_Cu, [pad, via])
        _via(board, "GND", via)

    _path(board, "+3V3", pcbnew.F_Cu, [(103, 104.54), (105, 104.54), (105, 102.7), (109.725, 102.7), (109.725, 101.5)])
    _path(board, "+3V3", pcbnew.F_Cu, [(109.725, 102.7), (114.05, 102.7), (114.05, 101.5)])
    _path(board, "+3V3", pcbnew.F_Cu, [(114.05, 102.7), (117, 102.7), (119.46, 104)])

    # Odd connector pins can be routed directly without changing ordering.
    _path(board, "CE", pcbnew.F_Cu, [(103, 107.08), (106, 107.81), (124.5, 107.81), (124.5, 106.54), (122, 106.54)])
    _path(board, "SCK", pcbnew.F_Cu, [(103, 112.16), (106, 110.35), (124.5, 110.35), (124.5, 109.08), (122, 109.08)])
    _path(board, "MISO", pcbnew.F_Cu, [(103, 117.24), (106, 113.2), (124.5, 113.2), (124.5, 111.62), (122, 111.62)])

    # The official 2x04 socket footprint puts the even column to the left.
    # Alternating layers keeps each ordered set of routes planar.
    _path(board, "CSN", pcbnew.B_Cu, [(103, 109.62), (119.46, 106.54)])
    _path(board, "MOSI", pcbnew.B_Cu, [(103, 114.7), (119.46, 109.08)])
    _path(board, "IRQ", pcbnew.B_Cu, [(103, 119.78), (119.46, 111.62)])

    board.BuildListOfNets()
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(path), board)


def canonicalize_breakout() -> None:
    path = SOLUTIONS / "deepee-pcb-002/artifacts/mcp9808-breakout.kicad_pcb"
    board = pcbnew.LoadBoard(str(path))
    footprint_records = _footprint_records(board)
    replacements = _build_replacements(board, footprint_records)
    _clear_tracks(board)
    _replace_footprints(board, replacements)

    # Keep the top edge clear so the F.Cu ground pour cannot form an orphaned
    # strip above this rail.
    _path(board, "3V3", pcbnew.F_Cu, [(101.225, 105), (101.225, 100.8), (116, 100.8), (116, 102)])
    for pad in [(103.175, 102), (106.375, 102), (109.575, 102)]:
        _path(board, "3V3", pcbnew.F_Cu, [pad, (pad[0], 100.8)])
    _path(board, "3V3", pcbnew.F_Cu, [(109.1125, 106.525), (109.575, 102)])

    # SDA: R1 and U1 on F.Cu, then a B.Cu branch to the connector.
    _path(board, "SDA", pcbnew.F_Cu, [(104.825, 102), (104.825, 106.525), (104.8875, 106.525)])
    _via(board, "SDA", (104.825, 105))
    _path(board, "SDA", pcbnew.B_Cu, [(104.825, 105), (116, 107.08)])

    # SCL uses B.Cu between two local F.Cu fan-outs.  A short F.Cu bridge at
    # x=113 crosses the SDA route on the opposite layer.
    _path(board, "SCL", pcbnew.F_Cu, [(108.025, 102), (108.025, 103.2)])
    _via(board, "SCL", (108.025, 103.2))
    _path(board, "SCL", pcbnew.B_Cu, [(108.025, 103.2), (102, 103.2), (102, 107.175)])
    _via(board, "SCL", (102, 107.175))
    _path(board, "SCL", pcbnew.F_Cu, [(102, 107.175), (104.8875, 107.175)])
    _path(board, "SCL", pcbnew.B_Cu, [(108.025, 103.2), (113, 103.2)])
    _via(board, "SCL", (113, 103.2))
    _path(board, "SCL", pcbnew.F_Cu, [(113, 103.2), (113, 109.62)])
    _via(board, "SCL", (113, 109.62))
    _path(board, "SCL", pcbnew.B_Cu, [(113, 109.62), (116, 109.62)])

    # ALERT remains on F.Cu and stays below the SCL bridge.
    _path(board, "ALERT", pcbnew.F_Cu, [(111.225, 102), (111.7, 102), (111.7, 111.2), (103.2, 111.2), (103.2, 107.825), (104.8875, 107.825)])
    _path(board, "ALERT", pcbnew.F_Cu, [(111.7, 111.2), (114, 111.2), (114, 112.16), (116, 112.16)])

    # The B.Cu ground pour connects these fan-out vias and J1.2 while all
    # signal routing remains clear of the dense U1 ground-pad cluster.
    _path(board, "GND", pcbnew.F_Cu, [(102.775, 105), (102.775, 104.2)])
    _via(board, "GND", (102.775, 104.2))
    _path(board, "GND", pcbnew.F_Cu, [(104.8875, 108.475), (109.1125, 108.475)])
    _path(board, "GND", pcbnew.F_Cu, [(109.1125, 107.175), (110.5, 107.175), (110.5, 108.475)])
    _path(board, "GND", pcbnew.F_Cu, [(109.1125, 107.825), (110.5, 107.825)])
    _path(board, "GND", pcbnew.F_Cu, [(109.1125, 108.475), (110.5, 108.475)])
    _via(board, "GND", (110.5, 108.475))

    board.BuildListOfNets()
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(path), board)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", choices=["adapter", "breakout"])
    args = parser.parse_args()
    if args.board == "adapter":
        canonicalize_adapter()
    else:
        canonicalize_breakout()
    return 0


if __name__ == "__main__":
    # KiCad 10.0.4's SWIG bindings can fault while Python tears down objects
    # created by pcbnew after SaveBoard has completed.  Exit without invoking
    # those broken destructors; all writes above are synchronous.
    os._exit(main())
