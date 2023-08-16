#!/usr/bin/python
#
# Not so small anymore Brainfuck Interpreter
# Orginal from 2011 Sebastian Kaspari
# Modified by others
#
# Public Domain licence

helptext=\
"""
Brainfuck interpreter.

Brainfuck commands:
+ Increment current cell
- Decrement current cell
> Move to next cell
< Move to previous cell (here: stay at cell 0 if we are already at cell 0)
[ if cell value is 0, move to next command after the corresponding ]. If value is not 0, continue with command after [
] jump to corresponding [
, read value
. output value

This is a slow but more flexible version of a brainfuck interpreter.
"""

import sys
import argparse

class Code(object):
  """
  Class to hold code.
  We use it in a class to be able to store line and column information
  """
  def __init__(self,source):
    def buildbracemap(code):
      "Create a set with the indexes to jump from one [ to the other ]"
      temp_bracestack, bracemap = [], {}

      for position, command in enumerate(code):
        if command == "[": temp_bracestack.append(position)
        if command == "]":
          start = temp_bracestack.pop()
          bracemap[start] = position
          bracemap[position] = start
      return bracemap
    self.position=[]
    l=[]
    line=1
    column=1
    for i in source:
      if i=='\n':
        line=line+1
        column=0
      elif i in ['.', ',', '[', ']', '<', '>', '+', '-']:
        l.append(i)
        self.position.append((line,column))
      column=column+1;
    self.code=''.join(l)
    self.bracemap = buildbracemap( self.code )
  def jumpBrace(self,codepointer):
    return self.bracemap[codepointer]
  def getPosition(self,codepointer):
    return self.position[codepointer]
  def __getitem__(self,codepointer):
    return self.code[codepointer]
  def __len__(self):
    return len(self.code)


class Source(object):
  """
  Uses either a string or a file for an input.
  It can read one character after the other or parse one ASCII written integer after the other
  """
  def __init__(self,string=None,filename=None,readmode="raw",eof=None):
    """
    Set either string or filename. But not both. filename can also be a already opened file
    readmode should be raw (every byte/character is one int/character outputed) or int, where the
     input has a list of ASCII written integers.
    eof is the character that is read when there is no more input left
    """
    if string is not None and filename is not None:
      raise Exception("Can not use a string and a file for input at the same time")
    if string is None and filename is None:
      raise Exception("Need at least one input source, either a file or a string (argument)")
    if string is not None:
      self.s=string
      self.type="s"
    if filename is not None:
      if type(filename)==type(""):
        self.s=open(filename,"r");
      else:
        self.s=filename
      self.type="f"
    self.readmode=readmode
    if type(eof)==type(0) or eof is None:
      self.eof = eof
    else:
      self.eof = ord( eof )
    self.position=0
    if readmode not in ["raw", "int"]:
      raise Exception("Invalid readmode "+readmode)
  def _getCSub(self):
    """
    Return the next character from the input.
    Return None if there are no more characters to read
    """
    if self.type=='s':
      if len(self.s)==self.position:
        return None
      c = self.s[self.position]
      self.position=self.position+1
      return c
    if self.type=='f':
      c = self.s.read(1)
      if len(c): return c
      return None
  def getC(self,ascii=0):
    """
    Return the integer or character from the input.
    Return None if there are no more characters to read
    """
    def getNumber(self):
      if self.readmode=="raw":
        c = self._getCSub()
        if c is None: return None
        return ord( c )
      if self.readmode=="int":
        c=' '
        while c is not None and not c.isdigit():
          c = self._getCSub()
        s=""
        while c is not None and c.isdigit():
          s = s+c
          c = self._getCSub()
        if len(s):
          return int(s)
        return None
    c = getNumber(self)
    if c is None: c = self.eof
    if c is None: return None
    if ascii:     return chr(c)
    else:         return c

  def __next__(self):
    c = self.getC(ascii=1)
    if type(c)==type(""): return c
    if type(c)==type(0):  return c
    raise StopIteration #stop iteration when c is None
  def __iter__(self):
    self.position=0
    return self

class Tape(object):
  """
  Object to store the data of a brainfuck program
  """
  def __init__(self,mode="infinit",tapelimit=0,initValue=0,celllimit=0):
    """
    mode should either be infinit, wrap, wait or error
    in infinit mode, new cells get added each time the pointer moves pass a border
    in wrap mode, the position is calculated modulo tapelimit
    in wait mode, the position stays at the border and doesn't move pass it
    in error mode, passing beyond the border causes a error

    the tapelimit set a maximum number of cells. Ignored in infinit mode
    The tapelimit 0 means in this modes:
    - inifinit: Ignore
    - wrap: going below 0 means wrap to the highest current used. Grow when go beyond the positive border
    - wait: going below 0 means wait at 0. Grow when go beyond the positive border
    - error: going below 0 means error. Grow when go beyond the positive border

    The celllimit gives a maximum value + 1 per cell
    """
    if mode not in ["infinit", "wrap", "wait", "error"]:
      raise Exception("Invalid tapemode "+mode)
    self.initValue= initValue%celllimit if celllimit else initValue

    self.mode=mode
    self.cells=[self.initValue]
    if mode=="infinit":
      self.ncells=[self.initValue]
    self.position=0
    self.tapelimit=tapelimit

    self.celllimit=celllimit

  def movePositive(self):
    self.position += 1
    if self.position==len(self.cells):
      if self.tapelimit==0 or self.mode=="inifinit":
        self.cells.append( self.initValue )
      elif self.tapelimit==self.position:
        if self.mode=="wrap": self.position = 0
        if self.mode=="wait": self.position = self.position-1
        if self.mode=="error": raise Exception("Reached out of bounds location")
  def moveNegative(self):
    self.position -= 1
    if self.mode=="infinit":
      if self.position==-len(self.ncells)-1:
        self.ncells.append( self.initValue )
    elif self.position == -1:
      if self.mode=="wrap":
        if self.tapelimit==0:
          self.position = len(self.cells)-1
        else:
          if len(self.cells) < self.tapelimit:
            self.cells = self.cells + [ self.initValue for i in range(self.tapelimit-len(self.cells)) ]
          self.position = self.tapelimit-1
      if self.mode=="wait": self.position = 0
      if self.mode=="error": raise Exception("Reached out of bounds location")

  def add_substract(self,value):
    v = self.getValue()+value
    if self.celllimit:
      v = v % self.celllimit
    self.setValue(v)

  def getValue(self):
    if self.position>=0:
      return self.cells[self.position]
    else:
      return self.ncells[-self.position-1]
  def setValue(self,value):
    value = value % self.celllimit if self.celllimit else value
    if self.position>=0:
      self.cells[self.position] = value
    else:
      self.ncells[-self.position-1] = value

  def __str__(self):
    r= "{:3} ::".format(self.position)
    if self.mode=="infinit":
      r= r + str( self.ncells[::-1] ) + " :: "
    return r + ''.join( '{:02X} '.format(a) for a in self.cells )
    value = value % self.celllimit if self.celllimit else value
    if self.position>=0:
      self.cells[self.position] = value
    else:
      self.ncells[-self.position-1] = value

def execute(code,data,outputMode,tape,debug=0,output=sys.stdout):
  if outputMode not in ["raw", "int"]:
    raise Exception("Invalid outmode "+readmode)

  code     = Code( code )
  codeptr  = 0

  i=debug

  while codeptr < len(code):
    command = code[codeptr]
    i=i-1
    if i==0:
      i=debug
      print("{} {:3} {:9}".format(command,codeptr,str(code.getPosition(codeptr)))+str(tape),file=sys.stderr)

    if command == ">":  tape.movePositive()
    if command == "<":  tape.moveNegative()
    if command == "+":  tape.add_substract( 1)
    if command == "-":  tape.add_substract(-1)
    if command == "[" and tape.getValue() == 0: codeptr = code.jumpBrace(codeptr)
    if command == "]" and tape.getValue() != 0: codeptr = code.jumpBrace(codeptr)

    if command == ".":
      if outputMode=="raw":
        output.write(chr(tape.getValue()))
      if outputMode=="int":
        output.write(str(tape.getValue())+"\n")
    if command == ",":
      c = data.getC()
      if c is None: break
      tape.setValue(c)

    codeptr += 1




def main():
  parser=argparse.ArgumentParser(epilog=helptext,formatter_class=argparse.RawDescriptionHelpFormatter)
  h="Input source file, should contain the source code"
  parser.add_argument("--source",   action="store",type=str,required=False,default=None,  dest="codeFile",  help=h)
  h="code, given as command line argument"
  parser.add_argument("--code",     action="store",type=str,required=False,default=None,  dest="inputCode", help=h)
  h="How the input is read. Either raw or int for ASCII written integers"
  parser.add_argument("--inmode",   action="store",type=str,required=False,default="raw", dest="inputMode", help=h)
  h="input as argument. Read from it with the ',' command."
  parser.add_argument("--input",    action="store",type=str,required=False,default=None,  dest="input",     help=h)
  h="input as file. Read from it with the ',' command."
  parser.add_argument("--infile",   action="store",type=str,required=False,default=None,  dest="inFile",    help=h)
  h="How the values are outputed. Either raw or int for ASCII written integers"
  parser.add_argument("--outmode",  action="store",type=str,required=False,default="raw", dest="outputMode",help=h)
  h="Maximum value of a cell + 1 A limit implies that there are no negative values. 0 means no limit and cell can get negative. Set to 256 for 8 bit cells"
  parser.add_argument("--celllimit",action="store",type=int,required=False,default=0,     dest="celllimit", help=h)
  h="Which value is read when the input ends. AKA EOF character. If not set, the program stops when reading past the last input character"
  parser.add_argument("--eof",      action="store",type=int,required=False,default=None,  dest="eof",       help=h)
  h=\
  """
    What happens when the data pointer moves
    this mode should either be infinit, wrap, wait or error
    in infinit mode, new cells get added each time the pointer moves pass a border
    in wrap mode, the position is calculated modulo tapelimit
    in wait mode, the position stays at the border and doesn't move pass it
    in error mode, passing beyond the border causes a error

    the tapelimit set a maximum number of cells. Ignored in infinit mode
    The tapelimit 0 means in this modes:
    - inifinit: Ignore
    - wrap: going below 0 means wrap to the highest current used. Grow when go beyond the positive border
    - wait: going below 0 means wait at 0. Grow when go beyond the positive border
    - error: going below 0 means error. Grow when go beyond the positive border
  """
  parser.add_argument("--tapemode", action="store",type=str,required=False,default="infinit",dest="tapemode",help=h)
  h="How many cells are there at maximum. Interpretations Depends on tapemode"
  parser.add_argument("--tapelimit",action="store",type=int,required=False,default=0,     dest="tapelimit", help=h)
  h="Starting value of a cell"
  parser.add_argument("--initvalue",action="store",type=int,required=False,default=0,     dest="initValue", help=h)
  h=\
  "Print Debug output each nth command execution. 0 means no debug output, 1 is highest possible debug output "
  "It has this columns: \n"
  "<current command> <codepointer> <line and column in source file> <tape position> :: <tape to the left> :: <tape to the right> "
  parser.add_argument("--debug",    action="store",type=int,required=False,default=0,     dest="debug",     help=h)
  args=parser.parse_args(sys.argv[1:])

  if args.inFile is None and args.input is None:
    args.inFile = sys.stdin

  code = Source( args.inputCode, args.codeFile )
  data = Source( args.input,     args.inFile,    args.inputMode, args.eof       )
  tape = Tape  ( args.tapemode,  args.tapelimit, args.initValue, args.celllimit )
  execute( code, data, args.outputMode, tape, args.debug )

if __name__ == "__main__": main()

def evaluate\
  (
    code,
    data=None,inputMode="raw",eof=None,
    outputMode="raw", output=sys.stdout,
    tape=None,tapemode="infinit",tapelimit=0,initValue=0,celllimit=0,
    debug=0
  ):
  """
  Function to execute brainfuck code from python.
  code should be a code string
  data should either be string containing the input data, a instance of Source or None In case it
   is None, data is read from sys.stdin
  inputMode should either be "raw" or "int".
  eof indicates the character read when there are no input character left
  outputMode should either be "raw" or "int"
  output should be a output file.
  tape can be a instance of tape, a new instance will be created when tape is None
  tapemode, tapelimit, initValue and celllimit are parameters for the new tape instance.
  debug set how often we debug something to sys.stderr, 0 for no debugging.
  """
  code = Source( code )
  if type(data)==type(""):
    data = Source(string=data,filename=None,readmode=inputMode,eof=eof)
  elif data==None:
    data = Source(string=None,filename=sys.stdin,readmode=inputMode,eof=eof)
  if tape==None:
    tape = Tape( tapemode, tapelimit, initValue, celllimit )

  execute( code, data, outputMode, tape, debug, output )
