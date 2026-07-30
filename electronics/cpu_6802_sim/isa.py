"""Instruction set for the toy CPU: opcode constants + metadata tables."""

LDI = 0x01  # LDI val        -> ACC = val                          (immediate)
LDA = 0x02  # LDA addr       -> ACC = MEM[addr]                    (absolute)
STA = 0x03  # STA addr       -> MEM[addr] = ACC                    (absolute)
ADD = 0x04  # ADD addr       -> ACC = ACC + MEM[addr]              (absolute)
SUB = 0x05  # SUB addr       -> ACC = ACC - MEM[addr]              (absolute)
JMP = 0x06  # JMP addr       -> PC = addr
JZ = 0x07  # JZ addr        -> if Z flag: PC = addr
OUT = 0x08  # OUT            -> print ACC
LDX = 0x09  # LDX val        -> X = val                            (immediate)
LDY = 0x0A  # LDY val        -> Y = val                            (immediate)
INX = 0x0B  # INX            -> X = X + 1
DEX = 0x0C  # DEX            -> X = X - 1
INY = 0x0D  # INY            -> Y = Y + 1
DEY = 0x0E  # DEY            -> Y = Y - 1
LDAX = 0x0F  # LDAX addr      -> ACC = MEM[addr + X]                (indexed)
STAX = 0x10  # STAX addr      -> MEM[addr + X] = ACC                (indexed)
PUSH = 0x11  # PUSH           -> MEM[SP] = ACC; SP -= 1
POP = 0x12  # POP            -> SP += 1; ACC = MEM[SP]
JSR = 0x13  # JSR addr       -> push return addr (PC); PC = addr   (subroutine call)
RET = 0x14  # RET            -> pop addr into PC                  (subroutine return)
HLT = 0xFF  # HLT            -> stop

MNEMONIC = {
    LDI: "LDI",
    LDA: "LDA",
    STA: "STA",
    ADD: "ADD",
    SUB: "SUB",
    JMP: "JMP",
    JZ: "JZ",
    OUT: "OUT",
    LDX: "LDX",
    LDY: "LDY",
    INX: "INX",
    DEX: "DEX",
    INY: "INY",
    DEY: "DEY",
    LDAX: "LDAX",
    STAX: "STAX",
    PUSH: "PUSH",
    POP: "POP",
    JSR: "JSR",
    RET: "RET",
    HLT: "HLT",
}

# opcodes whose encoding is [opcode][operand] (one extra byte fetched in decode)
HAS_OPERAND = {LDI, LDA, STA, ADD, SUB, JMP, JZ, LDX, LDY, LDAX, STAX, JSR}

NAME_TO_OPCODE = {v: k for k, v in MNEMONIC.items()}
