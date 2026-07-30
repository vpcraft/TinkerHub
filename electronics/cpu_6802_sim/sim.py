"""Entry point: assembles and runs the demo programs. See README.md."""

from assembler import assemble
from cpu import CPU

# ---- demo 1: sum 1..5 via a loop, direct/absolute addressing, print result ----
SUM_LOOP = """
        LDI 5           ; counter = 5
        STA counter
        LDI 0           ; total = 0
        STA total
        LDI 1
        STA one

loop:   LDA counter
        JZ  end
        LDA total
        ADD counter
        STA total
        LDA counter
        SUB one
        STA counter
        JMP loop

end:    LDA total
        OUT
        HLT

counter: DB 0
total:   DB 0
one:     DB 0
"""

# ---- demo 2: walk an array with the X index register (indexed addressing),
# printing each element via a subroutine call — exercises JSR/RET/PUSH/POP,
# which use the stack pointer (SP) under the hood ----
INDEXED_AND_STACK = """
        LDX 0
        LDAX arr        ; ACC = MEM[arr + X]
        JSR print_it
        INX
        LDAX arr
        JSR print_it
        INX
        LDAX arr
        JSR print_it
        HLT

print_it:
        OUT
        RET

arr:    DB 10
        DB 20
        DB 30
"""

if __name__ == "__main__":
    print("=== demo 1: sum loop (direct addressing) ===")
    cpu1 = CPU(assemble(SUM_LOOP.strip().splitlines()))
    cpu1.run()

    print("\n=== demo 2: indexed addressing + subroutine call (stack) ===")
    cpu2 = CPU(assemble(INDEXED_AND_STACK.strip().splitlines()))
    cpu2.run()
