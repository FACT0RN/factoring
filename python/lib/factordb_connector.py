# reports factors to factordb
import re
import urllib3
import logging

http = urllib3.PoolManager()

logger = logging.getLogger("global_logger")


def _send2fdb(composite, factors):
    factors = map(str, factors)
    payload = {"report": str(composite) + "=" + "*".join(factors)}
    url = "http://factordb.com/report.php"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = http.request(
        "POST", url, encode_multipart=False, headers=headers, fields=payload
    )
    webpage = str(response.data.decode("utf-8"))

    msg = re.findall("Found [0-9] factors and [0-9] ECM", webpage)[0]
    print("[+] FactorDB: " + msg)
    #if msg != "":
    #    if msg == "Found 0 factors and 0 ECM":
    #        logger.info("[!] All the factors we found are already known to factordb")
    #    else:
    #        msg = "[+] Factordb: " + re.findall("Found [0-9] factors and [0-9] ECM", webpage)[0]
    #        print(msg)
    #        logger.info(msg)

def send2fdb(composite, factors):
    try:
        _send2fdb(composite,factors)
    except:
        print("[!] some error reporting factors to fdb")
        
        
        
from factordb.factordb import FactorDB

def _getfdb(n):
  print("[*] FactorDB: Checking composite: %d..." % n)
  f = FactorDB(n)
  r = f.connect()
  if str(r) == "<Response [200]>":
    tmp = [int(x[0]) for x in f.get_factor_from_api()]
    #print("debug:",tmp)
    #print(r.text)
    if tmp[0] != n:
      return tmp
    else:
      return []
  else:
    return []
    
    
def getfdb(n):
    try:
        return _getfdb(n)
    except:
        print("[!] Some error fetching from FactorDB...")
        return []
