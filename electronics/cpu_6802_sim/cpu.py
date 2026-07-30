"""
Toy 8-bit CPU: fetch-decode-execute simulation.

Not a real ISA (not 6502/x86/AVR) — simplified so the cycle logic stays visible.
Buses modeled as explicit variables (address_bus, data_bus, control_bus) even
though real electrical signaling collapses here into plain reads/writes.

Program and data share one 256-byte address space (von Neumann style, like this
toy CPU's addressing keeps things simple) — the stack lives at the TOP of that
same space (0xFF downward) with zero protection from the program below it. Real
MCUs usually still share address space this way; safety comes from the programmer
(or compiler) keeping the stack and data regions apart, not from hardware limits.
"""

from isa import MNEMONIC, HAS_OPERAND, HLT


class CPU:
    def __init__(self, program, mem_size=256, stack_top=0xFF):
        self.memory = bytearray(mem_size)
        self.memory[: len(program)] = program

        # registers
        self.pc = 0  # program counter — address of the NEXT instruction
        self.acc = 0  # accumulator — main ALU operand/result
        self.x = 0  # index register X — offsets for indexed addressing, loop counters
        self.y = 0  # index register Y — same role as X, a second one
        self.sp = stack_top  # stack pointer — next free stack slot, grows DOWN
        self.ir = 0  # instruction register — opcode currently being decoded
        self.zero_flag = 0  # set when last ADD/SUB result == 0

        # buses — kept explicit so each step shows how data actually moves
        self.address_bus = 0
        self.data_bus = 0
        self.control_bus = None  # "READ" or "WRITE"

        self.halted = False
        self.trace = True

    # --- bus-level memory access ---
    def mem_read(self, addr):
        self.address_bus = addr
        self.control_bus = "READ"
        self.data_bus = self.memory[addr]
        return self.data_bus

    def mem_write(self, addr, value):
        self.address_bus = addr
        self.data_bus = value & 0xFF
        self.control_bus = "WRITE"
        self.memory[addr] = self.data_bus

    def fetch(self):
        opcode = self.mem_read(self.pc)
        self.ir = opcode  # latch into the instruction register — decode reads THIS, not the bus
        self.pc += 1
        return opcode

    def decode(self, opcode):
        if opcode not in MNEMONIC:
            raise ValueError(f"unknown opcode 0x{opcode:02X} at PC={self.pc - 1}")
        operand = None
        if opcode in HAS_OPERAND:
            operand = self.mem_read(
                self.pc
            )  # operand fetch: its own bus cycle, next address
            self.pc += 1
        return opcode, operand

    def push(self, value):
        self.mem_write(self.sp, value)
        self.sp = (self.sp - 1) & 0xFF

    def pop(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.mem_read(self.sp)

    def execute(self, opcode, operand):
        if opcode == 0x01:  # LDI
            self.acc = operand
        elif opcode == 0x02:  # LDA
            self.acc = self.mem_read(operand)
        elif opcode == 0x03:  # STA
            self.mem_write(operand, self.acc)
        elif opcode == 0x04:  # ADD
            self.acc = (self.acc + self.mem_read(operand)) & 0xFF
            self.zero_flag = int(self.acc == 0)
        elif opcode == 0x05:  # SUB
            self.acc = (self.acc - self.mem_read(operand)) & 0xFF
            self.zero_flag = int(self.acc == 0)
        elif opcode == 0x06:  # JMP
            self.pc = operand
        elif opcode == 0x07:  # JZ
            if self.zero_flag:
                self.pc = operand
        elif opcode == 0x08:  # OUT
            print(f"OUT -> {self.acc}")
        elif opcode == 0x09:  # LDX
            self.x = operand
        elif opcode == 0x0A:  # LDY
            self.y = operand
        elif opcode == 0x0B:  # INX
            self.x = (self.x + 1) & 0xFF
        elif opcode == 0x0C:  # DEX
            self.x = (self.x - 1) & 0xFF
        elif opcode == 0x0D:  # INY
            self.y = (self.y + 1) & 0xFF
        elif opcode == 0x0E:  # DEY
            self.y = (self.y - 1) & 0xFF
        elif (
            opcode == 0x0F
        ):  # LDAX — indexed addressing: address is addr+X, computed then dereferenced
            self.acc = self.mem_read((operand + self.x) & 0xFF)
        elif opcode == 0x10:  # STAX
            self.mem_write((operand + self.x) & 0xFF, self.acc)
        elif opcode == 0x11:  # PUSH
            self.push(self.acc)
        elif opcode == 0x12:  # POP
            self.acc = self.pop()
        elif opcode == 0x13:  # JSR — push return address, then jump
            self.push(self.pc)
            self.pc = operand
        elif opcode == 0x14:  # RET — pop return address back into PC
            self.pc = self.pop()
        elif opcode == HLT:
            self.halted = True

    def step(self):
        pc_before = self.pc
        opcode = self.fetch()
        opcode, operand = self.decode(opcode)
        if self.trace:
            name = MNEMONIC[opcode]
            operand_str = f" {operand}" if operand is not None else ""
            print(
                f"PC={pc_before:3d}  IR=0x{self.ir:02X} {name}{operand_str:<6}"
                f"  ACC={self.acc:3d} X={self.x:3d} Y={self.y:3d} SP={self.sp:3d} Z={self.zero_flag}"
                f"  [bus] addr={self.address_bus} data={self.data_bus} ctrl={self.control_bus}"
            )
        self.execute(opcode, operand)

    def run(self, max_steps=1000):
        steps = 0
        while not self.halted and steps < max_steps:
            self.step()
            steps += 1
        if steps >= max_steps:
            print("stopped: max_steps reached (possible infinite loop)")
