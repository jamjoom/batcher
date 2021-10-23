#!/usr/bin/python

# batcher -- the ultimate batching program
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


import sys, time, os, itertools
import os.path

os.chdir( os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, '.')

from lib.Machine import *

# Usage
if len(sys.argv) < 2:
	print "USUAGE: batcher --cmd 'command line'" 
	print "                --post 'command line'"
	print "                --opt       name val"
	print "                --opt_range name start_val stop_val step_size"
	print "                --opt_list  name val_or_string_between_quotes ..."
	print "                --machines m1 m2 m3 ... (can be set in env variable JX_MACHINES: export JX_MACHINES=pi1,pi2,pi3)"
	print "                --outfile filename"
	print "                --break_on_first"
	print "                --sync" 
	print "                --mirror"
	print "                --check"
	print "                --show_all_in_check"
	print "                --verbose"
	print "                --merge 'command line' (or -m)"

	sys.exit()

# Some Classes
def dict_product(dicts):
    return [dict(itertools.izip(dicts, x)) for x in itertools.product(*dicts.itervalues())]

# Perform option parameter substitution
def get_cur_cmd(opts,machine):
	
	cur_outfile = in_outfile
   	cur_cmds = in_cmds[:]

   	cur_outfile = cur_outfile.replace('machine',machine.name)

   	for key in opts:
	   	for i,cmd in enumerate(cur_cmds):
   			cur_cmds[i] = cmd.replace(key,opts[key])
   		cur_outfile = cur_outfile.replace(key,opts[key])

   	for i,cmd in enumerate(cur_cmds):
   		cmd = cmd.replace('outfile',cur_outfile)
   		cur_cmds[i] = cmd.replace('machine',machine.name)

   		if machine.name != 'localhost' and not cur_cmds[i].startswith('ssh'):
   			cur_cmds[i] = "ssh {} {}".format(machine.name,cur_cmds[i])

	return (cur_cmds,cur_outfile)


# Variables 
config_break_on_first = False
config_sync = False
config_check = False
config_mirror = False
config_show_all_in_check = False
config_verbose = False
config_merge = False

in_cmds = []
in_machines = []
in_posts = []
in_outfile = ''
opt_list = {}
machines = []
outfiles = {}

total_time = 0
cur_run   = 0
cur_machine = -1
sample_flag = False

# Parse input
in_arg = sys.argv.pop(0) 

while len(sys.argv) > 0: 

	in_arg = sys.argv.pop(0) 

	if in_arg == "--cmd":
		in_cmds.append( sys.argv.pop(0) )

	elif in_arg == "--opt":
		name = sys.argv.pop(0)
		opt_list[name] = [ sys.argv.pop(0) ]

	elif in_arg == "--opt_range":
		name = sys.argv.pop(0)
		x = int(sys.argv.pop(0))
		stop = int(sys.argv.pop(0))
		step = int(sys.argv.pop(0))
		opt_list[name] = []
		while x <= stop:
			opt_list[name].append(str(x))
			x = x + step

	elif in_arg == "--opt_list":
		name = sys.argv.pop(0)
		opt_list[name] = []

		while len(sys.argv) > 0 and sys.argv[0].startswith('-') == False:
			opt_list[name].append(sys.argv.pop(0))

	elif in_arg == "--outfile":
		in_outfile = sys.argv.pop(0)

	elif in_arg == "--break_on_first":
		config_break_on_first = True

	elif in_arg == "--check":
		config_check = True

	elif in_arg == "--show_all_in_check":
		config_show_all_in_check = True

	elif in_arg == "--sync":
		config_sync = True

	elif in_arg == "--mirror":
		config_mirror = True

	elif in_arg == "--merge" or in_arg == "-m":
		in_cmds.append( sys.argv.pop(0) )
		config_merge = True

	elif in_arg == "--post":
		in_posts.append( sys.argv.pop(0) )

	elif in_arg == "--machines":
		while len(sys.argv) > 0 and sys.argv[0].startswith('-') == False:
			in_machines.append(sys.argv.pop(0))

	elif in_arg == "--verbose":
		config_verbose = True

	else:
		print "SYNTAX ERROR: Dude, you wrote somethig ({}) that is not supported".format(in_arg)
		sys.exit()

opts_product = dict_product(opt_list)

# Init machines
if len(in_machines) == 0 and os.getenv('JX_MACHINES',False) != False:
	in_machines = os.getenv('JX_MACHINES',False).split(",") 

if len(in_machines) == 0:
	in_machines.append('localhost')

if config_merge:
	config_mirror = True

if config_mirror:
	config_sync = True
	mirrors = in_machines[:]
else:
	mirrors = [':']

total_runs = len(opts_product) * len(mirrors)

machines = jxMachine()

for name in in_machines:
	machines.new(name, config_break_on_first)

cur_machine = machines.find(config_sync)

# config_check for review
if config_check == True:
	print "    -- PLEASE REVIEW WHAT I AM ABOUT TO DO --"
	for opts in opts_product:
		for mirror in mirrors:
		    
			(cur_cmds,cur_outfile) = get_cur_cmd(opts,cur_machine)

			# Print Sample 
			if sample_flag == False:
				if config_show_all_in_check == False:
					sample_flag = True
				print " > " + "\n > ".join(cur_cmds)
			
			if os.path.exists(cur_outfile):
				print "WARNING: {} exists".format(cur_outfile)
		
	if raw_input("Do you want to me to proceed (y/n)?") != 'y':
		print "... Goodbye!"
		sys.exit()

# REAL WORK STARTS HERE...

for opts in opts_product:
	for mirror in mirrors:

		# Find a machine
		cur_machine = machines.find(config_sync)
		if cur_machine == -1:
		   	cur_machine = machines.wait(config_sync,config_merge)

		# Compute some averages
		if config_verbose:
			cur_run += 1
			total_time = machines.stats_total_runtime()
			average_time = float(total_time / cur_run)
			TTF = float((average_time) * (total_runs - cur_run))
			print "Executing ({}/{}) on {}:".format(cur_run,total_runs,cur_machine.name)
			print "   + Average time = {:0.2f} sec, Time remaining = {:0.2}f sec".format(average_time,TTF)

		(cur_cmds,cur_outfile) = get_cur_cmd(opts,cur_machine)

		# Track outfiles 
		outfiles[cur_outfile] = True
		cur_machine.add_outfile(cur_outfile)
		
		cur_machine.new_job()

	    #Start Running
		for cmd in cur_cmds:
			if config_verbose:
				print "   + $> " + cmd	
			cur_machine.proc_exec(cmd)


# final wait
machines.wait(True,config_merge)

if config_verbose:
	print "... Post processing"

o_files = " ".join(outfiles.keys())

for m in machines._containers:

	cur_posts = in_posts[:]
	m_files = " ".join(m.get_outfiles())

	for i,post in enumerate(cur_posts):
		cur_posts[i] = post.replace('o_files',o_files)
		cur_posts[i] = post.replace('m_files',m_files) 
		cur_posts[i] = post.replace('machine',m.name)

	for p in cur_posts:
		pexec(p)

if config_verbose:
	print "... Goodbye!"
