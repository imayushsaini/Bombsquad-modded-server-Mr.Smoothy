from __future__ import division
import threading
import json
import os     
import urllib2
import bs

#original credit to MythB for collecting stats 
#updated as mystat.py by sobydamn add rank system
#large part of code is by MythB  so giving file name credit to him. 

# where our stats file and pretty html output will go

#change path according to you 
#if you already using mystats.py or same 



statsfile = 'stats2.json'
htmlfile = 'index.html'


#path to parent directories if you want to share stats with multiple servers 
#or in same folder ..if want to have different stats for different server on same instance

def update(score_set):
     """
    Given a Session's ScoreSet, tallies per-account kills
    and passes them to a background thread to process and
    store.
    """ 
    # look at score-set entries to tally per-account kills for this round
     account_kills = {}
     account_killed = {}
     account_scores = {}
     account_played = {}
     account_name = {}
     account_localname = {}
     for p_entry in score_set.getValidPlayers().values():
        account_id = p_entry.getPlayer().get_account_id()
        if account_id is not None:
            account_kills.setdefault(account_id, 0)
            account_kills[account_id] += p_entry.accumKillCount
            account_killed.setdefault(account_id, 0)
            account_killed[account_id] += p_entry.accumKilledCount
            account_scores.setdefault(account_id, 0)
            account_scores[account_id] += p_entry.accumScore
            account_played.setdefault(account_id, 0)
            account_played[account_id] += 1
            account_localname.setdefault(account_id, p_entry.name)
            account_localname[account_id] = p_entry.name
    # Ok; now we've got a dict of account-ids and kills.
    # Now lets kick off a background thread to load existing scores
    # from disk, do display-string lookups for accounts that need them,
    # and write everything back to disk (along with a pretty html version)
    # We use a background thread so our server doesn't hitch while doing this.
     UpdateThread(account_kills,account_killed,account_scores,account_played,account_name, account_localname).start()
class UpdateThread(threading.Thread):
    def __init__(self, account_kills, account_killed, account_scores, account_played, account_name, account_localname):
        threading.Thread.__init__(self)
        self._account_kills = account_kills
        self._account_killed = account_killed
        self._account_scores = account_scores
        self._account_played = account_played
        self._account_name = account_name
        self._account_localname = account_localname
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
                stats[account_id] = {'kills': 0, 'killed': 0, 'scores': 0, 'played': 0, 'name_html': name_html, 'account_id': account_id}
            # now increment their kills whether they were already there or not
            stats[account_id]['kills'] += kill_count
        for account_id, killed_count in self._account_killed.items():
            stats[account_id]['killed'] += killed_count
        for account_id, scores_count in self._account_scores.items():
            stats[account_id]['scores'] += scores_count
        for account_id, played_count in self._account_played.items():
            stats[account_id]['played'] += played_count
        for account_id, name in self._account_localname.items():
            stats[account_id]['name_full'] = name
        # dump our stats back to disk
        with open(statsfile, 'w') as f:
            f.write(json.dumps(stats))
        # lastly, write a pretty html version.
        # our stats url could point at something like this...
        entries = [(a['scores'], a['kills'], a['killed'], a['played'], a['name_html'], a['name_full'], a['account_id']) for a in stats.values()]
        # this gives us a list of kills/names sorted high-to-low
        entries.sort(reverse=True)
        with open(htmlfile, 'w') as f:
            f.write('<head><meta charset="UTF-8"></head><body>')
            for entry in entries:
                scores = str(entry[0])
                kills = str(entry[1])
                killed = str(entry[2])
                gameplayed = str(entry[3])
                if int(entry[2]) <= 0:
                    kill_death_ratio = str(entry[1])
                else:
                    x = str(round(int(entry[1]) / int(entry[2]), 2))
                    kill_death_ratio = x
                num_scores = int(entry[0])
                num_played = int(entry[3])
                x = str(round(num_scores / num_played, 2))
                avgScore = x
                account_id = entry[6].encode('utf-8')
                name = entry[4].encode('utf-8')
                localname = entry[5].encode('utf-8')
                f.write(kills + ' kills ' + killed + ' deaths ' + scores + ' score ' + gameplayed + ' games : ' + name +'kd:'+kill_death_ratio+'accountid:'+account_id+ '<br>')
            f.write('</body>') 
            
        print 'Scores and Data Updated!'
        with open(bs.getEnvironment()['systemScriptsDirectory'] + "/rank.py",mode='w') as f:
            f.write("player = [")
            for entry in entries:
                a = str(entry[6])
                f.write(" '" + a + "',")
            f.write("]\n")
            
            
        print 'Ranks Updated'