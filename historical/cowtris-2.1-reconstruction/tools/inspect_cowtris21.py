#!/usr/bin/env python3
"""Inspect the Cowtris 2.1 VB6 executable using only the Python standard library.

This is deliberately a narrow evidence collector, not a general VB6 decompiler. It
reports executable identity, VB object/method metadata, calls to the PlaySound
wrapper that use byte-sized resource IDs, and embedded WAVE resources.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path


KNOWN_WAVE_NAMES = {
    101: "madcow.wav",
    102: "Zap.wav",
    103: "Zap2.wav",
    104: "Cow.wav",
    105: "game-over sound",
    106: "Mad2back.wav",
    107: "monks cow 2.wav",
    108: "purple.wav",
    109: "EXPLODE.WAV",
    110: "violence.wav",
    111: "lavache.wav",
    112: "ni.wav",
    113: "represd.wav",
    114: "bitelegs.wav",
    115: "hamster.wav",
}

EXPECTED_EXE_SHA256 = "4b74269713b7e70b6280a179d1a00399e4b345d92d1fa99db80e6b5e00cbf1df"

# Names are recovered with help from the published 2.0 source. Addresses are
# identities of p-code procedure descriptors, not native-code entry points.
KNOWN_PROCEDURES = {
    0x00412584: "Sub Main",
    0x00411E50: "EndProgram",
    0x00412C48: "PlaySound",
    0x00412698: "random-breed helper (name inferred)",
    0x00414D84: "TransPiece / special landing effects",
    0x004158A8: "CheckForRowCompletion",
    0x00416A48: "BeginPiece",
}


@dataclass(frozen=True)
class Section:
    name: str
    virtual_address: int
    virtual_size: int
    raw_offset: int
    raw_size: int


@dataclass(frozen=True)
class Method:
    object_name: str
    index: int
    descriptor: int
    start: int
    end: int
    constant_pool: int


class PortableExecutable:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        self.pe_offset = self.u32_offset(0x3C)
        if self.data[self.pe_offset : self.pe_offset + 4] != b"PE\0\0":
            raise ValueError("not a PE executable")

        coff = self.pe_offset + 4
        section_count = self.u16_offset(coff + 2)
        self.timestamp = self.u32_offset(coff + 4)
        optional_size = self.u16_offset(coff + 16)
        self.optional_offset = coff + 20
        self.image_base = self.u32_offset(self.optional_offset + 28)
        self.entry_rva = self.u32_offset(self.optional_offset + 16)
        self.resource_rva = self.u32_offset(self.optional_offset + 112)

        section_table = self.optional_offset + optional_size
        sections = []
        for index in range(section_count):
            offset = section_table + index * 40
            name = self.data[offset : offset + 8].rstrip(b"\0").decode("ascii")
            virtual_size = self.u32_offset(offset + 8)
            virtual_address = self.u32_offset(offset + 12)
            raw_size = self.u32_offset(offset + 16)
            raw_offset = self.u32_offset(offset + 20)
            sections.append(
                Section(name, virtual_address, virtual_size, raw_offset, raw_size)
            )
        self.sections = tuple(sections)

    def u16_offset(self, offset: int) -> int:
        return struct.unpack_from("<H", self.data, offset)[0]

    def s16_offset(self, offset: int) -> int:
        return struct.unpack_from("<h", self.data, offset)[0]

    def u32_offset(self, offset: int) -> int:
        return struct.unpack_from("<I", self.data, offset)[0]

    def rva_to_offset(self, rva: int) -> int:
        for section in self.sections:
            size = max(section.virtual_size, section.raw_size)
            if section.virtual_address <= rva < section.virtual_address + size:
                return section.raw_offset + rva - section.virtual_address
        raise ValueError(f"unmapped RVA {rva:#x}")

    def va_to_offset(self, va: int) -> int:
        return self.rva_to_offset(va - self.image_base)

    def offset_to_va(self, offset: int) -> int:
        for section in self.sections:
            if section.raw_offset <= offset < section.raw_offset + section.raw_size:
                return self.image_base + section.virtual_address + offset - section.raw_offset
        raise ValueError(f"unmapped file offset {offset:#x}")

    def bytes_at_va(self, va: int, size: int) -> bytes:
        offset = self.va_to_offset(va)
        return self.data[offset : offset + size]

    def u16_va(self, va: int) -> int:
        return self.u16_offset(self.va_to_offset(va))

    def s16_va(self, va: int) -> int:
        return self.s16_offset(self.va_to_offset(va))

    def u32_va(self, va: int) -> int:
        return self.u32_offset(self.va_to_offset(va))

    def c_string(self, va: int) -> str:
        offset = self.va_to_offset(va)
        end = self.data.index(0, offset)
        return self.data[offset:end].decode("cp1252", "replace")

    def mapped_va(self, va: int) -> bool:
        try:
            self.va_to_offset(va)
            return True
        except ValueError:
            return False


def parse_vb_methods(pe: PortableExecutable) -> tuple[int, list[Method]]:
    entry_va = pe.image_base + pe.entry_rva
    if pe.bytes_at_va(entry_va, 1) != b"\x68":
        raise ValueError("entry point does not begin with the expected VB header push")
    vb_header = pe.u32_va(entry_va + 1)
    if pe.bytes_at_va(vb_header, 4) != b"VB5!":
        raise ValueError("VB5!/VB6 project header not found")

    project_info = pe.u32_va(vb_header + 0x30)
    object_table = pe.u32_va(project_info + 4)
    object_count = pe.u16_va(object_table + 0x2A)
    object_array = pe.u32_va(object_table + 0x30)
    methods = []

    for object_index in range(object_count):
        public_descriptor = object_array + object_index * 0x30
        object_info = pe.u32_va(public_descriptor)
        object_name = pe.c_string(pe.u32_va(public_descriptor + 0x18))
        method_count = pe.u16_va(object_info + 0x20)
        method_table = pe.u32_va(object_info + 0x24)
        constant_pool = pe.u32_va(object_info + 0x34)

        for method_index in range(method_count):
            descriptor = pe.u32_va(method_table + method_index * 4)
            if not pe.mapped_va(descriptor):
                continue
            # A p-code descriptor begins with a back-pointer to its object info.
            if pe.u32_va(descriptor) != object_info:
                continue
            procedure_size = pe.u16_va(descriptor + 8)
            start = descriptor - procedure_size
            if procedure_size == 0 or not pe.mapped_va(start):
                continue
            methods.append(
                Method(
                    object_name,
                    method_index,
                    descriptor,
                    start,
                    descriptor,
                    constant_pool,
                )
            )
    return vb_header, methods


def find_thunk(pe: PortableExecutable, descriptor: int) -> int:
    needle = b"\xBA" + struct.pack("<I", descriptor)
    text = next(section for section in pe.sections if section.name == ".text")
    start = text.raw_offset
    end = start + text.raw_size
    offset = pe.data.find(needle, start, end)
    while offset >= 0:
        if pe.data[offset + 10 : offset + 12] == b"\xFF\xE1":
            return pe.offset_to_va(offset)
        offset = pe.data.find(needle, offset + 1, end)
    raise ValueError(f"thunk for descriptor {descriptor:#x} not found")


def scan_sound_calls(
    pe: PortableExecutable, methods: list[Method], play_sound_thunk: int
) -> list[dict[str, int | str]]:
    calls = []
    for method in methods:
        code = pe.bytes_at_va(method.start, method.end - method.start)
        # In this build, calls with a byte-sized resource ID compile as:
        #   F4 <id>       push integer literal
        #   0A <pool> 08 00   call constant-pool target with 8 bytes of args
        for offset in range(0, len(code) - 6):
            if code[offset] != 0xF4 or code[offset + 2] != 0x0A:
                continue
            pool_index = struct.unpack_from("<h", code, offset + 3)[0]
            try:
                target = pe.u32_va(method.constant_pool + pool_index * 4)
            except ValueError:
                continue
            if target != play_sound_thunk:
                continue
            resource_id = code[offset + 1]
            calls.append(
                {
                    "address": method.start + offset,
                    "resource_id": resource_id,
                    "object": method.object_name,
                    "method_index": method.index,
                    "descriptor": method.descriptor,
                    "procedure": KNOWN_PROCEDURES.get(method.descriptor, "unidentified"),
                }
            )
    return calls


def walk_resources(pe: PortableExecutable) -> list[dict[str, int | str | bytes]]:
    resource_base = pe.rva_to_offset(pe.resource_rva)
    resources = []

    def resource_name(value: int) -> int | str:
        if not value & 0x80000000:
            return value
        offset = resource_base + (value & 0x7FFFFFFF)
        length = pe.u16_offset(offset)
        start = offset + 2
        return pe.data[start : start + length * 2].decode("utf-16le")

    def walk(directory_offset: int, path: tuple[int | str, ...] = ()) -> None:
        directory = resource_base + directory_offset
        count = pe.u16_offset(directory + 12) + pe.u16_offset(directory + 14)
        for index in range(count):
            entry = directory + 16 + index * 8
            name = resource_name(pe.u32_offset(entry))
            target = pe.u32_offset(entry + 4)
            next_path = path + (name,)
            if target & 0x80000000:
                walk(target & 0x7FFFFFFF, next_path)
                continue
            leaf = resource_base + target
            payload_offset = pe.rva_to_offset(pe.u32_offset(leaf))
            payload_size = pe.u32_offset(leaf + 4)
            payload = pe.data[payload_offset : payload_offset + payload_size]
            resources.append(
                {
                    "type": str(next_path[0]),
                    "id": int(next_path[1]),
                    "size": payload_size,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "payload": payload,
                }
            )

    walk(0)
    return resources


def sound_match(payload: bytes, sounds_dir: Path | None) -> str:
    if sounds_dir is None or not sounds_dir.is_dir():
        return ""
    digest = hashlib.sha256(payload).hexdigest()
    for candidate in sounds_dir.iterdir():
        if not candidate.is_file() or candidate.suffix.lower() != ".wav":
            continue
        candidate_data = candidate.read_bytes()
        if hashlib.sha256(candidate_data).hexdigest() == digest:
            return candidate.name + " (exact)"
        if payload.startswith(candidate_data) and len(payload) - len(candidate_data) <= 2:
            return candidate.name + " (plus resource padding)"
    return ""


def report(exe: Path, sounds_dir: Path | None) -> str:
    pe = PortableExecutable(exe)
    digest = hashlib.sha256(pe.data).hexdigest()
    if digest != EXPECTED_EXE_SHA256:
        raise ValueError(
            f"unexpected Cowtris.exe SHA-256: {digest}; expected {EXPECTED_EXE_SHA256}"
        )
    vb_header, methods = parse_vb_methods(pe)
    audio_methods = [m for m in methods if m.object_name == "modAudio"]
    play_sound = next(m for m in audio_methods if m.index == 3)
    play_sound_thunk = find_thunk(pe, play_sound.descriptor)
    sound_calls = scan_sound_calls(pe, methods, play_sound_thunk)
    resources = walk_resources(pe)

    lines = [
        "Cowtris 2.1 binary inspection report",
        "=====================================",
        f"file: {exe.name}",
        f"size: {len(pe.data)} bytes",
        f"sha256: {digest}",
        "PE timestamp: "
        + datetime.datetime.fromtimestamp(pe.timestamp, datetime.timezone.utc).isoformat(),
        f"image base: 0x{pe.image_base:08x}",
        f"entry point: 0x{pe.image_base + pe.entry_rva:08x}",
        f"VB header: 0x{vb_header:08x}",
        f"valid p-code procedures found: {len(methods)}",
        f"PlaySound descriptor: 0x{play_sound.descriptor:08x}",
        f"PlaySound thunk: 0x{play_sound_thunk:08x}",
        "",
        "Calls to PlaySound with literal resource IDs",
        "--------------------------------------------",
    ]
    for call in sound_calls:
        resource_id = int(call["resource_id"])
        lines.append(
            f"0x{int(call['address']):08x}  resource {resource_id:3d}  "
            f"{call['object']}.method[{call['method_index']}]  "
            f"descriptor=0x{int(call['descriptor']):08x}  {call['procedure']}"
        )

    lines.extend(["", "Embedded WAVE resources", "-----------------------"])
    wave_resources = sorted(
        (resource for resource in resources if resource["type"] == "WAVE"),
        key=lambda resource: int(resource["id"]),
    )
    for resource in wave_resources:
        resource_id = int(resource["id"])
        # Locate the payload again only for optional archive matching.
        # The resource walker intentionally keeps its public report compact.
        known = KNOWN_WAVE_NAMES.get(resource_id, "")
        match = sound_match(bytes(resource["payload"]), sounds_dir)
        labels = match or known
        if known and match and not match.lower().startswith(known.lower()):
            labels = f"{known}; {match}"
        lines.append(
            f"{resource_id:3d}  {int(resource['size']):6d} bytes  "
            f"{resource['sha256']}  {labels}"
        )

    lines.extend(
        [
            "",
            "Special-cow selection procedure",
            "-------------------------------",
        ]
    )
    selection = next(m for m in methods if m.descriptor == 0x00412698)
    lines.append(
        f"descriptor=0x{selection.descriptor:08x} "
        f"p-code=0x{selection.start:08x}..0x{selection.end:08x}"
    )
    lines.append(pe.bytes_at_va(selection.start, selection.end - selection.start).hex(" "))

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path, help="path to the extracted Cowtris.exe")
    parser.add_argument(
        "--sounds-dir",
        type=Path,
        help="optional directory containing archived WAV files",
    )
    args = parser.parse_args()
    print(report(args.exe, args.sounds_dir), end="")


if __name__ == "__main__":
    main()
