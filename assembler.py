#!/usr/bin/python

from __future__ import print_function
import sys,re

class AssemblerError(Exception):
    def __init__(self, msg,token):
        self.msg = msg
        self.token = token
    def __str__(self):
        return self.msg

class Arg(object):
    def __init__(self, data):
        self.data = data

    def get_bits(self):
        l = self.length
        return ('{:0'+ str(l) +'b}').format(self.data % 2**l);

    def __str__(self):
        return self.description

@classmethod
def decode_number(cls, num):
    try:
        i = 0
        if num[1] == 'x':
            i = int(num,16)
        elif num[1] == 'b':
            i = int(num,2)
        else:
            i = int(num)

        if i >= 2**cls.length:
            raise AssemblerError("Number %s exceeds bit length of %d" % \
                                 (num, cls.length), num)
        return cls(i)
    except ValueError:
        raise AssemblerError("%s is not a valid number. Expected %s" % \
                             (num, cls.description), num)

@classmethod
def decode_reg(cls,reg):
    if reg[0] in ['r','R']:
        return cls(int(reg[1]))
    else:
        raise AssemblerError("Invalid register format: %s" % reg, reg)

def create_arg_type(name,desc,length,decode_logic):
    NewArgType = type(name, (Arg,), {'length':length, 'decode':decode_logic,
                                     'description': desc})
    return NewArgType

# Argument types
Raw = create_arg_type('Raw', '16 bit value', 16, decode_number)
NineBitImm = create_arg_type('NineBitImm', '9 bit immediate value', 9, decode_number)
SixBitImm = create_arg_type('SixBitImm', '6 bit immediate value', 6, decode_number)
Register = create_arg_type('Register', 'register', 3, decode_reg)

class Instruction(object):
    def __init__(self, args):
        self.args = args

    def get_byte(self):
        argb = [self.opcode,]
        argb.extend([a.get_bits() for a in self.args])
        if self.flags:
            argb.append(self.flags)
        return int(self.byte_format.format(*argb),2);

    @classmethod
    def cast_args(cls,args):
        cast = []
        n_exp = len(cls.arg_format)
        if len(args) != n_exp:
            raise AssemblerError( \
                    "Number of arguments don't match. Expected %d" % n_exp, args[0])
        for i,a in enumerate(args):
            arg = cls.arg_format[i].decode(a)
            if not arg:
                raise AssemblerError("Incorrect format of argument %s. Expected %s" % \
                                      (a,cls.arg_format[i]), a)
            cast.append(arg)
        return cast

def create_instr_type(name,opcode,arg_format,byte_format,flags):
    NewInstrType = type(name, (Instruction,),
                        {'opcode':opcode,
                         'arg_format':arg_format,
                         'byte_format':byte_format,
                         'flags':flags
                        })
    return NewInstrType

# Instructon types

instr_add = create_instr_type("instr_add","0000",
                              (Register,Register,Register),
                              "{0:s}{2:s}{3:s}{1:s}0{4:s}","00")
instr_adc = create_instr_type("instr_adc","0000",
                              (Register,Register,Register),
                              "{0:s}{2:s}{3:s}{1:s}0{4:s}","10")
instr_adz = create_instr_type("instr_adz","0000",
                              (Register,Register,Register),
                              "{0:s}{2:s}{3:s}{1:s}0{4:s}","01")
instr_adi = create_instr_type("instr_adi","0001",
                              (Register,Register,SixBitImm),
                              "{0:s}{2:s}{1:s}{3:s}",None)

instr_ndu = create_instr_type("instr_ndu","0010",
                              (Register,Register,Register),
                              "{0:s}{2:s}{3:s}{1:s}0{4:s}","00")
instr_ndc = create_instr_type("instr_ndc","0010",
                              (Register,Register,Register),
                              "{0:s}{2:s}{3:s}{1:s}0{4:s}","10")
instr_ndz = create_instr_type("instr_ndz","0010",
                              (Register,Register,Register),
                              "{0:s}{2:s}{3:s}{1:s}0{4:s}","01")

instr_lhi = create_instr_type("instr_lhi","0011",
                              (Register,NineBitImm),"{:s}{:s}{:s}",None)
instr_lw = create_instr_type("instr_lw","0100",
                             (Register,Register,SixBitImm),"{:s}{:s}{:s}{:s}",None)
instr_sw = create_instr_type("instr_sw","0101",
                             (Register,Register,SixBitImm),"{:s}{:s}{:s}{:s}",None)

instr_lm = create_instr_type("instr_lm","0110",
                             (Register,NineBitImm),"{:s}{:s}{:s}",None)
instr_sm = create_instr_type("instr_sm","0111",
                             (Register,NineBitImm),"{:s}{:s}{:s}",None)

instr_beq = create_instr_type("instr_beq","1100",
                              (Register,Register,SixBitImm),"{:s}{:s}{:s}{:s}",None)
instr_jal = create_instr_type("instr_jal","1000",
                              (Register,NineBitImm),"{:s}{:s}{:s}",None)
instr_jlr = create_instr_type("instr_jlr","1001",
                              (Register,Register),"{:s}{:s}{:s}000000",None)

instr_db = create_instr_type("instr_db","",(Raw,),"{:s}{:s}",None)
instr_org = create_instr_type("instr_org","",(Raw,),"{:s}{:s}",None)
instr_test = create_instr_type("instr_test","",(Raw,Raw),"{:s}{:s}{:s}",None)
instr_rst = create_instr_type("instr_rst","",(),"{:s}1111111111111111",None)

# Execution starts

mif_header = '''DEPTH = 32768;                -- The size of memory in words
WIDTH = 16;                   -- The size of data in bits
ADDRESS_RADIX = BIN;          -- The radix for address values
DATA_RADIX = BIN;             -- The radix for data values
CONTENT                       -- start of (address : data pairs)
BEGIN
'''

help_text = '''IITB-RISC instruction set assembler

Usage: assembler.py <assembly_file> [output_mif]

assembly_file: path to file you want to assemble
output_mif: path to output mif file. If not passed, outputs to stdout
'''

def main():
    errored = False

    if len(sys.argv) == 1:
        print(help_text,file=sys.stderr)
        return

    asm = sys.argv[1];
    if len(sys.argv) > 2:
        output_file = open(sys.argv[2],'w')
    else:
        output_file = sys.stdout

    program = []
    testcases = []
    labels = {}

    curr_addr = 0
    with open(asm,'r') as asm_file:
        for line_no,line in enumerate(asm_file):
            line = line.strip()
            line = line.split(';')[0]
            if line:
                tokens = re.split(' |,',line);
                tokens = [t for t in tokens if t]

                # check for Label assignment
                if len(tokens) == 1 and tokens[0][-1] == ':':
                    labels[tokens[0][:-1]] = curr_addr
                    continue

                for i in range(1,len(tokens)):
                    t = tokens[i]
                    if t[0] == '#' and t[1:] in labels:
                        tokens[i] = str(labels[t[1:]]-curr_addr)

                # get the type of instruction
                try:
                    instr_type = eval('instr_'+tokens[0]);
                    args = instr_type.cast_args(tokens[1:]);
                except (AssemblerError,NameError) as e:
                    e_line = "Error in instruction at line %d: %s" % (line_no+1,line)
                    if type(e) == NameError:
                        e = AssemblerError("Invalid instruction: %s" % tokens[0],tokens[0])

                    t_ind = e_line.index(e.token)
                    print(e_line,file=sys.stderr)
                    print(" "*t_ind + "^",file=sys.stderr)
                    print("    %s" % e,file=sys.stderr)
                    errored = True
                    continue

                instr = instr_type(args)
                if instr_type == instr_org:
                    curr_addr = instr.args[0].data
                elif instr_type == instr_test:
                    testcases.append({'addr':instr.args[0].data,
                                      'byte':instr.args[1].data})
                else:
                    program.append({'addr':curr_addr,'byte':instr.get_byte()})
                    curr_addr += 1

    if not errored:
        print(mif_header, file=output_file)
        for p in program:
            print('{:015b} : {:016b};'.format(p['addr'],p['byte']), file=output_file)
        print('END;',file=output_file)
        print("Successfully assembled")

if __name__ == '__main__':
    main()
