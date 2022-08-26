################################################################################
# Factorization algorithms
################################################################################
from math import floor, ceil
from gmpy2 import mpz,mpq,mpfr,mpc
from gmpy2 import is_square, isqrt, sqrt, log2, gcd, is_prime, next_prime, primorial
from factordb_connector import *
from time import time
import sympy as sp
import os

MSIEVE_BIN = os.environ.get("MSIEVE_BIN", "NONE") 
YAFU_BIN   = os.environ.get("YAFU_BIN",   "NONE")
CADO_BIN   = os.environ.get("CADO_BIN",   "NONE")
YAFU_THREADS   = os.environ.get("YAFU_THREADS",   "2")
YAFU_LATHREADS = os.environ.get("YAFU_LATHREADS", "2")
TIMEOUT=600

#Factoring libraries
USE_PARI = True if ( (YAFU_BIN == "NONE") or (YAFU_BIN == "NONE")) else False

if USE_PARI:
  import cypari2 as cp
  cyp = cp.Pari()
  cyp.default("parisizemax", 1<<29 )
  cyp.default("threadsizemax", 1<<27 )
  pari_cfactor = cyp.factorint

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

def pollard(n, limit=1000):
    x = 2
    y = 2
    d = 1
    l = 0
    def g(x):
      return x*x + 1
    while d == 1 and l <= limit:
        x = g(x) 
        y = g(g(y)) 
        d = gcd(abs(x - y), n)
        #print(n,l)
        l += 1
    if n > d > 1:
      return n//d, d
    else:
      return []
    
    
def cadonfs_factor_driver(n):
  global CADO_BIN, TIMEOUT
  print("[*] Factoring %d with yafu..." % n)
  tmp = []
  proc = subprocess.Popen(["timeout", str(TIMEOUT), CADO_BIN, str(n)], stdout=subprocess.PIPE)
  for line in proc.stdout:
    line = line.rstrip().decode("utf8")
    if re.search("\d+",line):
      tmp += [int(x) for x in line.split(" ")]
  return tmp


def msieve_factor_driver(n):
  global MSIEVE_BIN
  print("[*] Factoring %d with msieve..." % n) 
  import subprocess, re, os
  tmp = []
  proc = subprocess.Popen([MSIEVE_BIN,"-s","/tmp/%d.dat" % n,"-t","8","-v",str(n)],stdout=subprocess.PIPE)
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
  proc = subprocess.Popen([YAFU_BIN,"-one","-threads",YAFU_THREADS,"-lathreads",YAFU_LATHREADS, str(n)],stdout=subprocess.PIPE)
  for line in proc.stdout:
    line = line.rstrip().decode("utf8")
    if re.search("P\d+ = \d+",line):
      tmp += [int(line.split("=")[1])]
    if re.search("C\d+ = \d+",line):
      tmp += [int(line.split("=")[1])]
  return tmp

def cfactor(n):
  print("[*] pari factoring: %d..." % n)
  f0 = pari_cfactor(n)
  factors  = [int(a) for a in f0[0]]
  return factors

def external_factorization(n):
  factors = []

  if USE_PARI:
      factors = cfactor(n)
  else:
      factors = yafu_factor_driver(n)

  #YAFU already uses msieve
  #if len(factors) == 0:
  #  factors = msieve_factor_driver(n)
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
    start = time()
    current       = primorial( 1 << level)
    level_n_sieve = current//prev
    prev          = current
    siever.append(  level_n_sieve )
    print("Level: %d primes: %d  ok Time: %f" % (level,(1 << level), time()-start ))
  return siever

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

def SDC(W, candidates):
  print("[*] square difference check...")
  if is_square(W):
    a = isqrt(W)
    for n in candidates:
      n2 = abs(n - W)
      b = isqrt(n2)
      if (b * b) == n2:
        if n > gcd(a + b, n) > 1:
          factors = []
          print("[+] Factored using square difference...")
          if is_prime(a + b):
            factors += [a + b]
          if is_prime(a - b):
            factors += [a - b]
          if len(factors) == 2:
            return factors, n
  return None
