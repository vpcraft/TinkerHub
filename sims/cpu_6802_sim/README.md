# Fetch-Decode-Execute Simulation

8-bit CPU in Python. Not a real ISA — built to make fetch-decode-execute
mechanics visible in code, not to be an accurate 6502/AVR/x86 clone.

- `isa.py` — opcode constants, mnemonics, which opcodes carry an operand byte
- `assembler.py` — tiny label-based assembler (source text → byte list)
- `cpu.py` — the `CPU` class: registers, buses, fetch/decode/execute
- `sim.py` — entry point, assembles + runs the demo programs

```
python3 sim.py
```

Prints one line per CPU step: PC, IR, instruction, ACC/X/Y/SP, zero flag, bus state.

---

## Microprocessor vs Microcontroller

**Microprocessor (MPU)** — just the CPU core (ALU, registers, control unit). No RAM,
ROM, or I/O on the same chip. Needs external chips for memory and peripherals,
connected via buses on a board. Example: old x86 CPUs needed separate RAM chips,
BIOS ROM, I/O controllers.

**Microcontroller (MCU)** — CPU + RAM + Flash/ROM + I/O peripherals (GPIO, timers,
UART, ADC) all on one chip. Self-contained, cheap, made for embedded control tasks.
Example: ATmega328P (the chip on an Arduino Uno) — CPU, 32KB flash, 2KB SRAM,
digital/analog pins, timers, all in one package.

Arduino course context: the Uno's ATmega328P is an MCU. Everything below applies to
its CPU core same as to a standalone MPU — the fetch-decode-execute cycle doesn't
care whether memory is on-chip or off-chip, only the wiring differs.

---

## The Three Buses

A bus is a shared set of wires. CPU talks to memory/peripherals over three of them:

- **Address bus** — CPU puts a memory address here. Says "I want to talk to *this*
  location." Width determines addressable memory: 16-bit address bus = 65536
  locations (64KB), which is why old 8-bit CPUs like the 6502 topped out at 64KB.
  One-directional: only CPU drives it.

- **Data bus** — the actual byte (or word) moves here. Bidirectional: CPU writes to
  memory (data flows CPU→memory) or reads from memory (data flows memory→CPU).
  Width often matches word size — 8-bit CPU, 8-bit data bus, one byte per transfer.

- **Control bus** — carries signals that say what kind of operation is happening:
  READ or WRITE, clock signal, interrupt lines, reset line. Without this, memory
  wouldn't know whether the address+data on the bus mean "store this" or "give me
  what's there."

In `sim.py`, `CPU.mem_read()` / `CPU.mem_write()` set `self.address_bus`,
`self.data_bus`, `self.control_bus` explicitly before touching `self.memory[]` —
real hardware has no `self.memory[addr]` shortcut, every access is bus traffic.
Each traced step prints the bus state so you see it fire.

---

## Registers

Small, fast storage inside the CPU itself (not memory — no bus transfer needed to
access them, which is why they're faster).

- **PC (Program Counter)** — address of the *next* instruction to fetch. Incremented
  after each fetch; overwritten directly by JMP/branch instructions.
- **ACC (Accumulator)** — general-purpose register holding the "current" value most
  ALU ops work on. Early CPUs centered everything around one accumulator; 
  modern CPUs have many general-purpose registers instead.
- **Flags/Status register** — bits set by the ALU as side effects: Zero (result was
  0), Carry (arithmetic overflowed), Negative, etc. Branches like `JZ` read these
  instead of recomputing conditions.
- **IR (Instruction Register)** — holds the opcode currently being decoded, separate
  from the data bus. `CPU.fetch()` latches the fetched byte into `self.ir` before
  decode runs — decode logic reads from IR, not straight off the bus, since the bus
  gets reused immediately after for the operand fetch.
- **SP (Stack Pointer)** — address of the next free stack slot. Grows *down*:
  `PUSH` writes to `MEM[SP]` then decrements SP; `POP` increments SP then reads
  `MEM[SP]`. Used implicitly by `JSR`/`RET` to stash/restore a return address —
  see [Addressing Modes](#addressing-modes) demo below.
- **X, Y (Index Registers)** — general-purpose, but their main job is *indexed
  addressing*: `LDAX addr` reads `MEM[addr + X]`, so incrementing X in a loop walks
  through consecutive memory (an array) without rewriting the instruction's address
  operand each time.

---

## Fetch → Decode → Execute

One instruction cycle, repeated forever until halted:

1. **Fetch** — put PC on the address bus, assert READ on the control bus, read the
   byte that comes back on the data bus. That byte is the opcode. Increment PC.
   (`CPU.fetch()`)

2. **Decode** — figure out what the opcode means: which operation, which addressing
   mode, how many more bytes to fetch as operands. In real CPUs this is done by
   dedicated decode logic (a ROM lookup table or hardwired logic gates translating
   opcode bits into control signals). In `sim.py`, `MNEMONIC` + `HAS_OPERAND` dicts
   play that role — if the opcode needs an operand, fetch one more byte from PC (this
   is itself a bus cycle, same as instruction fetch). (`CPU.decode()`)

3. **Execute** — actually perform the operation: ALU computation, register update,
   or memory read/write via the buses again. Flags update as a side effect.
   (`CPU.execute()`)

Then PC (already advanced past the instruction) points to the next opcode, and the
cycle repeats. This is literally what a clock signal on the control bus is pacing —
each tick nudges the CPU through fetch/decode/execute stages.

---

## Addressing Modes

How an instruction says *where* its data is. `cpu.py` implements three:

- **Immediate** — operand IS the value. `LDI 5` → ACC = 5. Fetching the `5` byte
  from program memory is still a bus read (program and data share one address
  space here — von Neumann style) — the only difference from absolute mode is
  what's *done* with the fetched byte: used directly, no second lookup.
- **Direct/absolute** — operand is an address; CPU dereferences it. `LDA 34` →
  fetch `34` from the instruction stream (1st bus read), then read `MEM[34]`
  (2nd bus read) to get the actual value.
- **Indexed** — operand is a *base* address, offset by a register at execute time.
  `LDAX arr` (with X=1) → reads `MEM[arr + 1]`. Same two-bus-read shape as
  absolute, but the effective address isn't fixed at assembly time — bump X in a
  loop and the same instruction walks through consecutive memory. See `sim.py`'s
  `INDEXED_AND_STACK` demo: X counts 0,1,2 to visit three array elements with one
  `LDAX arr` instruction reused three times.

Real CPUs add more: indirect (address stored at another address), relative (offset
from PC, used for short jumps). More addressing modes = more flexible instructions,
but more decode complexity — one reason CISC (6502, x86) vs RISC (ARM, MIPS) differ
so much in decode-stage complexity.

---

## Register Transfer Logic

The idea that every CPU operation, reduced to its lowest level, is just:

> read a register or memory location onto a bus → write bus contents into another
> register or memory location, possibly through the ALU on the way.

`ACC = ACC + MEM[addr]` (the `ADD` instruction) is really: address bus ← addr,
memory drives data bus ← MEM[addr], ALU takes data bus + ACC as inputs, ALU output
writes back into ACC. Every line in `CPU.execute()` is a stand-in for a sequence
of these micro-transfers — real CPUs implement them as literal wired data paths
between registers, ALU, and buses, sequenced by the control unit.

This is the layer beneath assembly language: assembly instructions are just names
for pre-built sequences of register transfers.

---

## Mapping to `sim.py`

| Concept            | In code |
|---------------------|---------|
| Address bus          | `CPU.address_bus` |
| Data bus             | `CPU.data_bus` |
| Control bus           | `CPU.control_bus` ("READ"/"WRITE") |
| PC                   | `CPU.pc` |
| ACC                  | `CPU.acc` |
| IR                   | `CPU.ir` |
| SP                   | `CPU.sp` |
| X, Y                 | `CPU.x`, `CPU.y` |
| Status flags          | `CPU.zero_flag` |
| Fetch stage           | `CPU.fetch()` |
| Decode stage          | `CPU.decode()` |
| Execute stage         | `CPU.execute()` |
| Main loop / clock tick | `CPU.step()`, called repeatedly by `CPU.run()` |
| RAM                  | `CPU.memory` (bytearray, stands in for the whole address space) |

## Opcodes

| Mnemonic | Operand | Effect |
|----------|---------|--------|
| LDI val  | immediate | ACC = val |
| LDA addr | address | ACC = MEM[addr] |
| STA addr | address | MEM[addr] = ACC |
| ADD addr | address | ACC = ACC + MEM[addr], updates Z flag |
| SUB addr | address | ACC = ACC - MEM[addr], updates Z flag |
| JMP addr | address | PC = addr |
| JZ addr  | address | if Z flag set: PC = addr |
| OUT      | — | print ACC |
| LDX val  | immediate | X = val |
| LDY val  | immediate | Y = val |
| INX/DEX  | — | X += 1 / X -= 1 |
| INY/DEY  | — | Y += 1 / Y -= 1 |
| LDAX addr | address | ACC = MEM[addr + X] (indexed) |
| STAX addr | address | MEM[addr + X] = ACC (indexed) |
| PUSH     | — | MEM[SP] = ACC; SP -= 1 |
| POP      | — | SP += 1; ACC = MEM[SP] |
| JSR addr | address | push PC (return addr); PC = addr |
| RET      | — | pop addr into PC |
| HLT      | — | stop |

`sim.py` runs two demos:
- `SUM_LOOP` — sums 1..5 via direct/absolute addressing, prints 15. Exercises the
  base loop/branch opcodes.
- `INDEXED_AND_STACK` — walks a 3-element array with X (indexed addressing),
  calling a `print_it` subroutine via `JSR`/`RET` for each element. Watch SP dip
  from 255→254 on `JSR` (return address pushed) and climb back to 255 on `RET`
  (popped) in the trace output.

## Next steps

- Add indirect and relative addressing modes to feel decode complexity grow further.
- Add an interrupt line on the control bus and a simple ISR jump.
- Compare this trace output against a real 6502 emulator's cycle trace side by side.
