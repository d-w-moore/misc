#!/usr/bin/python2
from __future__ import print_function
from sys import stdout

class StreamProcessor (object):
  def __init__(self, f_other):
    self.f = iter( f_other )
    self.processor = self.process()
    next( self.processor ) # --> advance to initial yield
  def process( self ):
    raise NotImplementedError('use StreamProcessor only as a base class')
  def __iter__(self): return self
  def next(self): return self.__next__()
  def __next__(self):
    input_ = next( self.f )
    output_ = self.processor.send( input_ )
    return output_

class Adder (StreamProcessor):

  def __init__(self, *x, **kw):
    super(Adder,self).__init__(*x)
    self.addend = kw.pop('addend',1)
    
  def process( self ):                          # 'process' does the class-specific task
    x = yield 
    while 1: x = yield (x + self.addend)


class Negator(StreamProcessor):

  def process (self):
    x = None
    while 1: 
      if x is not None:
        y = -(x)
        x = yield y
      else:
        x = yield

if __name__ == '__main__':

  try:
    p = StreamProcessor ( x for x in [] )
  except Exception as e:
    print ( '**** {!r} ****'.format(e) )
    
  # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_
  #
  # -- demo #1 -- iterate on any simple generator as input

  g = ( i*i for i in range(1,10) )

  print([i for i in Negator(g)])

  # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_
  #
  # -- demo #2 -- cascale of two stream processors with a
  #               generator expression a as input

  a = (i for i in Adder([ 3,4,5 ],addend=5000))

  print([i for i in Adder(a,addend=100)])

  # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_
  #
  # -- demo #3 -- iterate on a function generator instance

  def mygen ():        # generate three cycling counts of zero to a million
    for j in range(3):
      i = 0
      while i < 10**6:
        yield i
        i += 1

  a = Adder ( mygen(), addend=10**9)  # --> Add a billion to the cycling count.

  try:                                 #     Loop over next(a) to iterate.
    while 1:
      print ('%2s%12d%c'%('',next(a),13),file=stdout,end='' )
      stdout.flush()
  except StopIteration:
    pass

  # -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_
