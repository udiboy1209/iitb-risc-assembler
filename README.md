Assembler for IITB-RISC
=====================

Assembler for IITB-RISC written in Python. Compiles assembly instructions
into MIF file to be loaded by Quartus into memory block.

Usage
-----

```
python assembler.py <assembly file> <output file>
```

Syntax
------------

Each line is a single instruction, all characters lower case.

 - Instruction starts with operator followed by `<SPACE>` followed by 
   comma-separated list of operands.
 - Operands are either register name `r<NUM>` (eg. `r1`, `r2`)
   or hex values (eg. `0xa1`)
 - Optionally followed by `;` and comment

 In below table `r` represents register operand. Both 6bit and 9bit hex can
 be specified using normal hex representation, it will be truncated to 6bit
 and 9bit.


| Instruction              | Operands        | 
|:-------------------------|----------------:|
| add/adc/adz/ndu/ndc/ndz  | `r,r,r`         |
| adi/lw/sw/beq            | `r,r,6bit hex`  |
| lhi/jal/lm/sm            | `r,9bit hex`    |
| jlr                      | `r,r`           |

There are some additional instructions for assembler preprocessing


| Instruction   | Operands        | Function  |
|:--------------|----------------:|-----------|
| db            | `16bit hex`     | insert data byte at this mem location |
| org           | `16bit hex`     | All further instructions will be inserted from this location. Similar to 8085 ORG instruction |
| rst           | None            | Stop program special instruction `0xffff` |


Example
----------

test.txt 

```
lhi r0,0x2
lhi r1,0x1
adi r1,r1,0x32
adi r1,r1,0x32 ; this is a comment

; Store something
sw r1,r0,0x0

rst

; Should store 0x00e4 at 0x100 location
```

test.mif

```
DEPTH = 32768;                -- The size of memory in words
WIDTH = 16;                   -- The size of data in bits
ADDRESS_RADIX = BIN;          -- The radix for address values
DATA_RADIX = BIN;             -- The radix for data values
CONTENT                       -- start of (address : data pairs)
BEGIN

000000000000000 : 0011000000000010;
000000000000001 : 0011001000000001;
000000000000010 : 0001001001110010;
000000000000011 : 0001001001110010;
000000000000100 : 0101001000000000;
000000000000101 : 1111111111111111;
END;
```
