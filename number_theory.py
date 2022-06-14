################################################################################
# Factorization algorithms
################################################################################
from math import floor, ceil
from gmpy2 import mpz,mpq,mpfr,mpc
from gmpy2 import is_square, isqrt, sqrt, log2, gcd, is_prime, next_prime, primorial
from factordb_connector import *

MSIEVE_BIN = "/home/dclavijo/code/FACTORING/msieve/msieve"
YAFU_BIN = "/home/dclavijo/code/FACTORING/yafu/yafu"
USE_PARI = None

#Factoring libraries
if USE_PARI:
  import cypari2 as cp
  cyp = cp.Pari()
  cyp.default("parisizemax", 1<<29 )
  cyp.default("threadsizemax", 1<<27 )
  pari_cfactor = cyp.factorint

  def cfactor(n):
    print("[*] pari factoring: %d..." % n)
    f0 = pari_cfactor(n)
    factors  = [int(a) for a in f0[0]]
    return factors

# This gives direct access to the integer factoring engine called by most arithmetical functions. flag is optional; its binary digits mean 
# 1: avoid MPQS, 
# 2: skip first stage ECM (we may still fall back to it later), 
# 4: avoid Rho and SQUFOF, 
# 8: don’t run final ECM (as a result, a huge composite may be declared to be prime). 
#    Note that a (strong) probabilistic primality test is used, thus composites might not be detected, although no example is known.

#Flags
SKIP_MPQS          = 1
SKIP_ECM_STAGE_ONE = 2
SKIP_RO_SQUFOF     = 4
SKIP_ECM_STAGE_TWO = 8


        
def msieve_factor_driver(n):
  global MSIEVE_BIN
  print("[*] Factoring %d with msieve..." % n) 
  import subprocess, re, os
  tmp = []
  proc = subprocess.Popen([MSIEVE_BIN,"-s","%d.dat" % n,"-t","8","-v",str(n)],stdout=subprocess.PIPE)
  for line in proc.stdout:
    line = line.rstrip().decode("utf8")
    if re.search("factor: ",line):
      tmp += [int(line.split()[2])]
  os.system("rm %d.dat" % n)
  return tmp


def yafu_factor_driver(n):
  global YAFU_BIN
  print("[*] Factoring %d with yafu..." % n)
  import subprocess, re, os
  tmp = []
  proc = subprocess.Popen([YAFU_BIN,str(n),"-session",str(n),"-qssave","qs_%s.dat" % str(n)],stdout=subprocess.PIPE)
  for line in proc.stdout:
    line = line.rstrip().decode("utf8")
    if re.search("P\d+ = \d+",line):
      tmp += [int(line.split("=")[1])]
  os.system("rm qs_%d.dat" % n)
  return tmp


def external_factorization(n):
  global USE_PARI
  factors = yafu_factor_driver(n)
  if len(factors) == 0:
    factors = msieve_factor_driver(n)
    if len(factors) == 0 and USE_PARI:
      factors = cfactor(n)
  return factors


def factorization_handler(n):
  print("[*] Factoring:",n)
  F = getfdb(n)
  if len(F) == 0:
    factors = external_factorization(n)
    print("[+] factors: %s" % str(factors))
  else:
    print("fdb got: %d factors: %s" % (len(F),str(F)))
    factors = []
    for f in F:
      if is_prime(f):
        factors += [f]
      else:
        factors += external_factorization(f)
  factors = sorted(factors)
  send2fdb(n,factors)
  return factors


def ranged_primorial(L, p = 2):
  #print("pre sieving...",end="")
  tmp = 2
  c = 0
  while c < L:
    p = next_prime(p)
    tmp *= p
    c += 1
  #print("ok")
  return tmp, p


def prime_levels_load0(s,e):
  siever = [ 0, 1, 6, 5005 ]
  prev, last_p = ranged_primorial(8)
  for level in range(s,e):
    siever.append(ranged_primorial(1 << level, p = last_p))
    print("Level %d ok" % level)
  return siever


import sympy as sp
def prime_levels_load1(s,e):
  siever = [ 0, 1, 6, 5005 ]
  prev = sp.primorial( 1<<3, False)
  for level in range(s,e):
    current       = sp.primorial( 1 << level, False)
    level_n_sieve = current//prev
    prev          = current
    siever.append(  level_n_sieve )
    print("Level %d ok" % level)
  return siever
  

def prime_levels_load2(s,e):
  siever = [ 0, 1, 6, 5005 ]
  prev = primorial( 1<<3)
  for level in range(s,e):
    current       = primorial( 1 << level)
    level_n_sieve = current//prev
    prev          = current
    siever.append(  level_n_sieve )
    print("Level: %d primes: %d  ok" % (level,(1 << level)))
  return siever
  
  
        #Sieving primes by levels, where a level corresponds to all primes with that many bits.
        #So sieving at level n means removing all numbers with any n-bit prime.
        #Here's a table of what percentage of all candidates are removed at every level:
        #
        #Level      Removed candidates as a percentage
        #2          0.6666666666666666
        #3          0.7714285714285714
        #4          0.8081918081918081
        #5          0.8471478486110139
        #6          0.8684126481497298
        #7          0.8861336590826278
        #8          0.8996467037376545
        #9          0.9107441143245115
        #10         0.9193531905796095
        #11         0.9265468468966381
        #12         0.932643270281829
        #13         0.9377500251662417
        #14         0.9421954718030565
        #15         0.9460195709571103
        #16         0.9493867455534085
        #17         0.952363027338504
        #18         0.9550042678652465
        #19         0.9573729617185134
        #20         0.9595015390721805
        #21         0.9614296619957499
        #22         0.9631823298937472
        #23         0.9647826123705192
        #24         0.9662497561067234
        #25         0.9675998287565128
        #
        #The higher the sieve, the more time it takes to sieve any one candidate, 
        #so at some point it is cheaper to factor each number directly
        #than it is to use a sieve level. This sweet spot is likely to be 
        #under 2^26 for CPUs based on heuristics. 
        #GPUs might be able to handle higher levels, unclear at the moment.


def prime_levels_load_timing():
  t0 = time.time()
  prime_levels_load0(4,16)
  t1 = time.time()
  print(t1-t0)
  prime_levels_load1(4,16)
  t2 = time.time()
  print(t2-t1)
  prime_levels_load2(4,16)
  t3 = time.time()
  print(t3-t2)

prime_levels_load = prime_levels_load2
