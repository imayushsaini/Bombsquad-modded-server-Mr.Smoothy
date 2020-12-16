

# ba_meta require api 6

from __future__ import annotations
import copy
import time
from typing import TYPE_CHECKING

import _ba
import ba
if TYPE_CHECKING:
    from typing import Any, Optional, Dict, List, Tuple,Type
    import ba


# discord @mr.smoothy#5824

import _ba
def hehe(brrrrrr)->bool:
	return True
# ba_meta export plugin
class enablee(ba.Plugin):
    
    def __init__(self):
        ba.screenmessage('Pro Unlock by Mr.Smoothy', color=(0, 1, 0))   #will not work on android client ..still ... aadat se majboor
        if _ba.env().get("build_number",0) >= 20124:
            _ba.get_purchased= hehe
            #now you are rich    F   
        else:print("pro unlocker only work on 1.5 ")
    