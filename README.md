

Batcher is a simple, yet powerful, tool to batch tasks for simulation and testing purposes. The tool relies heavily on variable substitutions to simplify the task of parameter exploration. This is similar to for loops in shell scripts. However, batcher has a better representation and better synchronization than traditional shell scripts. It also allows for parallel execution on multiple machines (using rsh or ssh):

```
batcher --cmd "command line"
--post "command line"
--opt name val
--opt_range name start_val stop_val step_size
--opt_list name val1 val2 val3
--machines m1 m2 m3
--outfile filename
--break_on_first
--sync_machines
--check
```

The basic option is the (--cmd), which specifies the command to launch. For example:

```
$> batcher –-cmd "mysimulator"
```

is just the same as running (mysimulator) on your command shell. If multiple (--cmd)'s are specified then they are launched in parallel. This particularly useful if you want to run another application that monitors your simulation (e.g., tcpdump). Since in many cases you will want to terminate the parallel command as soon as the first one ends, you can use the option (--break_on_first) to do exactly that. For example:

```
$> batcher --cmd "mysimulator" \
--cmd "tcpdump > junk" \
--break_on_first
```

will kill tcpdump (by sending a kill 9 signal) once (mysimulator) is finished.

Batcher allows you to specify three types of variables (--opt), (--opt_range), and (--opt_list). In all variables, batcher will substitute any instance of variables (name) with the corresponding value. For example,

```
$> batcher --cmd "mysimulator –i some_input" \
--cmd "tcpdump > junk.some_input" \
--break_on_first \
--opt_list some_input 1 2 3
```

will run (mysimulator) three times, each time with a different (some_input) value. Also, notice that we are capturing the (tcpdump) output into different files. To do a sanity check before actually running the command, you can specify the ( --check) option. This way batcher will show you an example of what it will do and asks you to proceed or not.

One additional reserved variable is (outfile), which I recommended using for specifying the output file of the simulation. Batcher keeps track of all outfiles so that it checks if they exist with (- -check) and for post processing with (--post). For example:

```
$> batcher –-cmd "mysimulator –i some_input " \
--cmd "tcpdump > outfile" \
--break_on_first \
--opt_list some_input 1 2 3 \
--outfile junk.some_input
```

This brings us the (--post) option, which specifies what to do after all simulations are completed. In many cases, you may want to copy or do some clean up on the output files that you generated. In this case, you can use (o_files) or (m_files, which is explained later) variables to specify all the output files that were generated, or per machine files, respectively. For example:

```
$> batcher –-cmd "mysimulator –i some_input " \
--cmd "tcpdump > outfile" \
--post "cp o_files /tmp" \
--break_on_first \
--opt_list some_input 1 2 3 \
--outfile junk.some_input
```

will copy all the output files one all runs are completed to the /tmp directory.

Probably the most powerful feature of batcher is its ability to run the application on multiple machines (more precisely, it keeps track of the commands that it executes in parallel). This gives you the power to use all of your compute resources to speed your simulation. Unfortunately, you will need to use either ssh or rsh to execute the command remotely, but once that is set up then you can execute each simulation point on a separate machine. Also, it is probably helpful to use a network file system such as NFS to move files around. Otherwise, you will need to specify these in your (--cmd) using scp, for example.

Assuming that you do have ssh and NFS installed on all machines. It is very easy to run your simulation in parallel. The only thing you need to specify is the list of machines using the (--machines) option. For example:

```
$> batcher –-cmd "ssh machine \"mysimulator –i some_input\" " \
--cmd "ssh machine tcpdump > outfile" \
--post "cp /n/machine/jamjoom/m_files /n/orange/tmp" \
--break_on_first \
--opt_list some_input 1 2 3 \
--outfile junk.some_input \
--machines orange yellow blue
```

will execute the three simulation runs in parallel on the three specified hosts: ```orange```, ```yellow```, and ```blue```. Notice that we had to specify the actual method to connect to the machines in both (--cmd) options. As mentioned earlier, the (m_files) variable specifies what output files where specified on each machine. This way, I can post process the files from each machine after the simulation is completed (look at the --post option).

Batcher can be configured for two different modes of parallelism. In the default mode, it considers the listed machines as a "process poll" and executes the next command as soon as one is done. However, if you want to synchronize all machines so that all parallel commands are completed before the next one is executed, you can use the (--sync_machines) option. While we are on the topic, (--post) option executes command in series, one machine after the other.

