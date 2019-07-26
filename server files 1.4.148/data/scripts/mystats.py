"""
mystats module for BombSquad version 1.4.143
Provides functionality for dumping player stats to disk between rounds.
To use this, add the following 2 lines to bsGame.ScoreScreenActivity.onBegin():
import mystats
mystats.update(self.scoreSet) 
"""

import threading
import json
import os
import urllib2


# where our stats file and pretty html output will go
statsfile = '/path/to/my/stats.json'
htmlfile = '/path/to/my/statspage.html'

def update(score_set):
     """
    Given a Session's ScoreSet, tallies per-account kills
    and passes them to a background thread to process and
    store.
    """ 
    # look at score-set entries to tally per-account kills for this round
    
    for p_entry in score_set.getValidPlayers().values():
        account_id = p_entry.getPlayer().get_account_id()
        if account_id is not None:
            account_kills.setdefault(account_id, 0)  # make sure exists
            account_kills[account_id] += p_entry.accumKillCount

    # Ok; now we've got a dict of account-ids and kills.
    # Now lets kick off a background thread to load existing scores
    # from disk, do display-string lookups for accounts that need them,
    # and write everything back to disk (along with a pretty html version)
    # We use a background thread so our server doesn't hitch while doing this.
    UpdateThread(account_kills).start()


class UpdateThread(threading.Thread):
    def __init__(self, account_kills):
        threading.Thread.__init__(self)
        self._account_kills = account_kills

    def run(self):
        # pull our existing stats from disk
        if os.path.exists(statsfile):
            with open(statsfile) as f:
                stats = json.loads(f.read())
        else:
            stats = {}
            
        # now add this batch of kills to our persistant stats
        for account_id, kill_count in self._account_kills.items():
            # add a new entry for any accounts that dont have one
            if account_id not in stats:
                # also lets ask the master-server for their account-display-str.
                # (we only do this when first creating the entry to save time,
                # though it may be smart to refresh it periodically since
                # it may change)
                url = 'http://bombsquadgame.com/accountquery?id=' + account_id
                response = json.loads(
                    urllib2.urlopen(urllib2.Request(url)).read())
                name_html = response['name_html']
                stats[account_id] = {'kills': 0, 'name_html': name_html}
            # now increment their kills whether they were already there or not
            stats[account_id]['kills'] += kill_count
            
        # dump our stats back to disk
        with open(statsfile, 'w') as f:
            f.write(json.dumps(stats))
            
        # lastly, write a pretty html version.
        # our stats url could point at something like this...
        entries = [(a['kills'], a['name_html']) for a in stats.values()]
        # this gives us a list of kills/names sorted high-to-low
        entries.sort(reverse=True)
        with open(htmlfile, 'w') as f:
            f.write('<head><meta charset="UTF-8"></head><body>')
            for entry in entries:
                kills = str(entry[0])
                name = entry[1].encode('utf-8')
                f.write(kills + ' kills : ' + name + '<br>')
            f.write('</body>')
            
        # aaand that's it!  There IS no step 27!
        print 'Added', len(self._account_kills), 'kill entries.'