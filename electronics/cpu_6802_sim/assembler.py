"""Tiny label-based assembler so jump/subroutine targets don't need hand-counted
byte offsets. Turns source lines into a flat list of bytes for CPU.memory."""

from isa import NAME_TO_OPCODE, HAS_OPERAND


def assemble(lines):
    """
    Each line is one of:
      "LABEL:"          -> marks the next byte's address (may share a line
                            with an instruction, e.g. "loop:   LDA counter")
      "OPCODE [arg]"    -> instruction (arg: number or label name)
      "DB value"        -> raw data byte (not an instruction)
    """
    entries = []  # ("instr", mnemonic, operand) | ("data", value)
    pending_labels = []
    label_addrs = {}
    addr = 0

    for line in lines:
        line = line.split(";", 1)[0].strip()  # strip comments
        if not line:
            continue
        if ":" in line:
            label, rest = line.split(":", 1)
            pending_labels.append(label.strip())
            line = rest.strip()
            if not line:
                continue

        for label in pending_labels:
            label_addrs[label] = addr
        pending_labels = []

        parts = line.split()
        mnemonic = parts[0]
        operand = parts[1] if len(parts) > 1 else None

        if mnemonic == "DB":
            entries.append(("data", int(operand)))
            addr += 1
        else:
            entries.append(("instr", mnemonic, operand))
            addr += 2 if NAME_TO_OPCODE[mnemonic] in HAS_OPERAND else 1

    program = []
    for entry in entries:
        if entry[0] == "data":
            program.append(entry[1] & 0xFF)
            continue
        _, mnemonic, operand = entry
        opcode = NAME_TO_OPCODE[mnemonic]
        program.append(opcode)
        if opcode in HAS_OPERAND:
            if operand is None:
                raise ValueError(f"{mnemonic} requires an operand")
            value = label_addrs.get(operand)
            if value is None:
                value = int(operand)
            program.append(value)
    return program
