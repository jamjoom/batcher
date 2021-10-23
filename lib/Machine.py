# Copyright 2021 Hani Jamjoom <jamjoom\@gmail.com>"
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys, itertools, time, os
import os.path
from multiprocessing import Process, Manager
import subprocess


class jxContainer(object):
    
    def __init__(self,name,manager=False,break_on_first=False):
        self.name = name
        self.manager = manager
        self.break_on_first = break_on_first
        self._processes = []		
        self.outfiles = {}
        self.start = time.time()
        self.state = 0
        self.runtime = 0
        self.share = []
    
    def add_outfile(self,name):
        self.outfiles[name] = True

    def new_share(self):
  		l = self.manager.list()
  		self.share.append(l)
  		return l

    def get_outfiles(self):
        return self.outfiles.keys()

    def proc_exec(self,cmd):
        share = self.new_share()
        p = Process(target=cmd_exec,args=(cmd,share))
        p.start()
        self._processes.append(p)
        
    def proc_status(self, merge = False):
  		running = 0
  		for p in self._processes:
 			if p.is_alive():
  				running += 1

  		if running == 0 or (self.break_on_first == True and running != len(self._processes)):
			self.state = 0
			self.update_runtime()
			
			for p in self._processes:
				if p.is_alive():
					p.terminate()

			if merge is False:
				for l in self.share:
					prefix = "\n" + self.name + ", "
					print self.name + ", " + prefix.join(l)
				self.reset_share()
			
			self._processes = []

		return running

    def new_job(self):
        self.start = time.time()
        self.state = 1

    def reset_share(self):
		for l in self.share:
			l = []
		self.share = []

    def update_runtime(self):
        self.runtime += time.time() - self.start

class jxMachine(object):

    def __init__(self):
        self._containers = []
        self._manager = Manager()   # Manager for sharing output of commands back to master process
        self._start_pos = 0
        
    # Merges the output of machines; must be combined with --sync
    def export_merge_shares(self):
        merge = []
        owner = {}
        for m in self._containers:
            for a_list in m.share:
                for a_line in a_list:
                    if a_line not in merge:
                        merge.append(a_line)
                        owner[a_line] = [m.name]
                    else:
                        owner[a_line].append(m.name)
            m.reset_share()

        print self.get_header() + "|"
        for l in merge:
            print self.get_vector(owner[l]) + "| " + l 


    # Find an idle machine to send the command to
    def find(self,sync):

        if sync is False:
            self._start_pos = 0

        for i in range(self._start_pos,len(self._containers),1):
            if self._containers[i].state == 0:
                self._start_pos = i
                return self._containers[i]

        return -1

    def get_header(self):
        return "|".join(self.get_names())

    def get_names(self):
        names = []
        for m in self._containers:
            names.append(m.name)
        return names

    def get_vector(self,marked_list):
        vector = []
        names = self.get_names()
        for n in names:
            if n in marked_list:
                vector.append("*".center(len(n))) # should be length of m.name
            else:
                vector.append(" ".center(len(n))) # should be length of m.name
        
        return "|".join(vector)

    def new(self, name, break_on_first = False):
        m = jxContainer(name,self._manager,break_on_first)
        self._containers.append(m)

    # Wait for a machine to be done. IF sync == True, wait for all machine to complete
    def wait(self, sync, merge = False):

        while True:
            finished_containers = 0
                
            for m in self._containers:
                if m.proc_status(merge) == 0:			
                    finished_containers += 1
                    done_machine = m

            if sync is True and finished_containers == len(self._containers):
                if merge is True:
                    self.export_merge_shares()
                return self._containers[0] # Return first one 

            if sync is False and finished_containers > 0:
                return done_machine

            time.sleep(1)
    
    def stats_total_runtime(self):
    	
        total_time = 0
        for m in self._containers:
			total_time += m.runtime
        
        return total_time


# Useful functions
def cmd_exec(cmd,share):
#	return_code = subprocess.call(cmd, shell=True)  
	p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	for line in iter(p.stdout.readline, b''):
		share.append(line.strip())

