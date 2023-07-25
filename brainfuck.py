#!/usr/bin/python
#
# Brainfuck Interpreter
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
"""

import sys
import argparse


class Source(object):
  """
  Uses either a string or a file for an input.
  It can read one character after the other or parse one ASCII written integer after the other
  """
  def __init__(self,string=None,filename=None,readmode="raw"):
    """
    Set either string or filename. But not both. filename can also be a already opened file
    readmode should be raw (every byte/character is one int/character outputed) or int, where the
     input has a list of ASCII written integers.
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
        return
    c = getNumber(self)
    if c is None: return
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

class Band(object):
  """
  Object to store the data of a brainfuck program
  """
  def __init__(self,mode="infinit",bandlimit=0,initValue=0,celllimit=0):
    """
    mode should either be infinit, wrap, wait or error
    in infinit mode, new cells get added each time the pointer moves pass a border
    in wrap mode, the position is calculated modulo bandlimit
    in wait mode, the position stays at the border and doesn't move pass it
    in error mode, passing beyond the border causes a error

    the bandlimit set a maximum number of cells. Ignored in infinit mode
    The bandlimit 0 means in this modes:
    - inifinit: Ignore
    - wrap: going below 0 means wrap to the highest current used. Grow when go beyond the positive border
    - wait: going below 0 means wait at 0. Grow when go beyond the positive border
    - error: going below 0 means error. Grow when go beyond the positive border

    The celllimit gives a maximum value per cell
    """
    if mode not in ["infinit", "wrap", "wait", "error"]:
      raise Exception("Invalid bandmode "+mode)
    self.initValue= initValue%celllimit if celllimit else initValue

    self.mode=mode
    self.cells=[self.initValue]
    if mode=="infinit":
      self.ncells=[self.initValue]
    self.position=0
    self.bandlimit=bandlimit

    self.celllimit=celllimit

  def movePositive(self):
    self.position += 1
    if self.position==len(self.cells):
      if self.bandlimit==0 or self.mode=="inifinit":
        self.cells.append( self.initValue )
      elif self.bandlimit==self.position:
        if self.mode=="wrap": self.position = 0
        if self.mode=="wait": self.position = self.position-1
        if self.mode=="error": raise Exception("Reached out of bounds location")
  def moveNegative(self):
    self.position -= 1
    if self.mode=="inifinit":
      if self.position==-len(self.ncells)-1:
        self.ncells.append( self.initValue )
    elif self.position == -1:
      if self.mode=="wrap":
        if self.bandlimit==0:
          self.position = len(self.cells)-1
        else:
          if len(self.cells) < self.bandlimit:
            self.cells = self.cells + [ self.initValue for i in range(self.bandlimit-len(self.cells)) ]
          self.position = self.bandlimit-1
      if self.mode=="wait": self.position = 0
      if self.mode=="error": raise Exception("Reached out of bounds location")

  def add_substract(self,value):
    if self.position>=0:
      self.cells[self.position] = self.cells[self.position]+value
    else:
      self.ncells[-self.position-1] = self.cells[-self.position-1]+value
    if self.celllimit:
      self.cells[self.position] = self.cells[self.position] % self.celllimit

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
    r=str(self.position) + " :: "
    if self.mode=="infinit":
      r= r + str( self.ncells[::-1] ) + " :: "
    return r + str(self.cells)
    value = value % self.celllimit if self.celllimit else value
    if self.position>=0:
      self.cells[self.position] = value
    else:
      self.ncells[-self.position-1] = value

def execute(code,data,outputMode,band):
  if outputMode not in ["raw", "int"]:
    raise Exception("Invalid outmode "+readmode)

  code     = cleanup( list(code) )
  bracemap = buildbracemap(code)
  codeptr  = 0

  while codeptr < len(code):
    command = code[codeptr]

    if command == ">":   band.movePositive()
    if command == "<":   band.moveNegative()
    if command == "+":   band.add_substract( 1)
    if command == "-":   band.add_substract(-1)
    if command == "[" and band.getValue() == 0: codeptr = bracemap[codeptr]
    if command == "]" and band.getValue() != 0: codeptr = bracemap[codeptr]

    if command == ".":
      if outputMode=="raw":
        sys.stdout.write(chr(band.getValue()))
      if outputMode=="int":
        sys.stdout.write(str(band.getValue())+"\n")
    if command == ",":
      c = data.getC()
      if c is None: break
      band.setValue(c)

    codeptr += 1


def cleanup(code):
  return ''.join(filter(lambda x: x in ['.', ',', '[', ']', '<', '>', '+', '-'], code))


def buildbracemap(code):
  temp_bracestack, bracemap = [], {}

  for position, command in enumerate(code):
    if command == "[": temp_bracestack.append(position)
    if command == "]":
      start = temp_bracestack.pop()
      bracemap[start] = position
      bracemap[position] = start
  return bracemap


def main():
  parser=argparse.ArgumentParser(epilog=helptext,formatter_class=argparse.RawDescriptionHelpFormatter)
  h="Input source file, should contain the source code"
  parser.add_argument("--source",   action="store",type=str,required=False,default=None,dest="codeFile",       help=h)
  h="code, given as command line argument"
  parser.add_argument("--code",     action="store",type=str,required=False,default=None,dest="inputCode",      help=h)
  h="How the input is read. Either raw or int for ASCII written integers"
  parser.add_argument("--inmode",   action="store",type=str,required=False,default="raw",dest="inputMode",     help=h)
  h="input as argument. Read from it with the ',' command."
  parser.add_argument("--input",    action="store",type=str,required=False,dest="input",                       help=h)
  h="input as file. Read from it with the ',' command."
  parser.add_argument("--infile",   action="store",type=str,required=False,dest="inFile",                      help=h)
  h="How the values are outputed. Either raw or int for ASCII written integers"
  parser.add_argument("--outmode",  action="store",type=str,required=False,default="raw",    dest="outputMode",help=h)
  h="Maximum value of a cell A limit implies that there are no negative values. 0 means no limit and cell can get negative"
  parser.add_argument("--celllimit",action="store",type=int,required=False,default=0,        dest="celllimit", help=h)
  h=\
  """
    What happens when the data pointer moves 
    this mode should either be infinit, wrap, wait or error
    in infinit mode, new cells get added each time the pointer moves pass a border
    in wrap mode, the position is calculated modulo bandlimit
    in wait mode, the position stays at the border and doesn't move pass it
    in error mode, passing beyond the border causes a error

    the bandlimit set a maximum number of cells. Ignored in infinit mode
    The bandlimit 0 means in this modes:
    - inifinit: Ignore
    - wrap: going below 0 means wrap to the highest current used. Grow when go beyond the positive border
    - wait: going below 0 means wait at 0. Grow when go beyond the positive border
    - error: going below 0 means error. Grow when go beyond the positive border
  """
  parser.add_argument("--bandmode", action="store",type=str,required=False,default="infinit",dest="bandmode", help=h)
  h="How many cells are there at maximum. Interpretations Depends on bandmode"
  parser.add_argument("--bandlimit",action="store",type=int,required=False,default=0,dest="bandlimit",         help=h)
  h="Starting value of a cell"
  parser.add_argument("--initvalue",action="store",type=int,required=False,default=0,dest="initValue",         help=h)
  args=parser.parse_args(sys.argv[1:])

  if args.inFile is None and args.input is None:
    args.inFile = sys.stdin

  code = Source( args.inputCode, args.codeFile )
  data = Source( args.input,     args.inFile,  args.inputMode )
  band = Band( args.bandmode, args.bandlimit,  args.initValue, args.celllimit )
  execute( code, data, args.outputMode, band )

if __name__ == "__main__": main()

