#!/usr/bin/env python2

from __future__ import print_function
from pipe_processor import (StreamProcessor, Adder)
import math

class Sinusoid (object):
  def __init__(self, freq_radians = 0.1, phz = 0.0):
    self.freq = freq_radians
    self.phz  = phz
  def __iter__(self):
    try:
      while True:
	yield math.sin(self.phz)
	self.phz += self.freq
    except GeneratorExit : print('GeneratorExit(Sin)', ); return

def doubler (input): 
  try:
    for y in input: 
      yield y*2
  except GeneratorExit : print('GeneratorExit(doubler)', ); return

src = ( doubler( Sinusoid() ))
offset_src = Adder(src , addend = 0.5)

for i in range(60):
  print (next(offset_src), end= '\t')

print()
