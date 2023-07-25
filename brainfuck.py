#!/usr/bin/python
#
# Brainfuck Interpreter
# Orginal from 2011 Sebastian Kaspari
# Modified by others
#
# Public Domain licence

"""
Brainfuck interpreter.

It reads brainfuck code and
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

def execute(code,data,outputMode):
  if outputMode not in ["raw", "int"]:
    raise Exception("Invalid outmode "+readmode)

  code     =  cleanup( list(code) )
  bracemap = buildbracemap(code)
  cells, codeptr, cellptr = [0], 0, 0

  while codeptr < len(code):
    command = code[codeptr]

    if command == ">":
      cellptr += 1
      if cellptr == len(cells): cells.append(0)

    if command == "<":
      cellptr = 0 if cellptr <= 0 else cellptr - 1

    if command == "+":
      cells[cellptr] = cells[cellptr] + 1

    if command == "-":
      cells[cellptr] = cells[cellptr] - 1

    if command == "[" and cells[cellptr] == 0: codeptr = bracemap[codeptr]
    if command == "]" and cells[cellptr] != 0: codeptr = bracemap[codeptr]
    if command == ".":
      if outputMode=="raw":
        sys.stdout.write(chr(cells[cellptr]))
      if outputMode=="int":
        sys.stdout.write(str(cells[cellptr])+"\n")
    if command == ",":
      c = data.getC()
      if c is None: break
      cells[cellptr] = c

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
  epilog =\
  parser=argparse.ArgumentParser()
  parser.add_argument("--source",action="store",type=str,required=False,default=None,dest="codeFile",help="Input source file, should contain the source code")
  parser.add_argument("--code",action="store",type=str,required=False,default=None,dest="inputCode",help="Input source file, should contain the source code")
  parser.add_argument("--inmode",action="store",type=str,required=False,default="raw",dest="inputMode",help="How the input is read. Either raw or int for ASCII written integers")
  parser.add_argument("--input",action="store",type=str,required=False,dest="input",help="input as argument. Read from it with the ',' command.")
  parser.add_argument("--infile",action="store",type=str,required=False,dest="inFile",help="input as file. Read from it with the ',' command.")
  parser.add_argument("--outmode",action="store",type=str,required=False,default="raw",dest="outputMode",help="How the values are outputed. Either raw or int for ASCII written integers")
  args=parser.parse_args(sys.argv[1:])

  if args.inFile is None and args.input is None:
    args.inFile = sys.stdin

  code = Source( args.inputCode, args.codeFile )
  data = Source( args.input,     args.inFile,  args.inputMode )
  execute( code, data, args.outputMode )

if __name__ == "__main__": main()

