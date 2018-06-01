
import os
import sys
import readline
import threading
from splcmds import exitme, chdir

"""
    1. to support backgorund process
    2. history of commands ( up or down commands )
    3. support pipelining of processes - d
    4. special commands - p
    5. readline - d
    6. add support for alias
"""

CAPY_VERSION = '0.5c'
PATH = os.environ['PATH'].split(':')
SPL_CMDS = {'exit':exitme,
            'quit':exitme,
            'cd': chdir}

def get_input():
    cmd = ''
    while cmd == '':
        prompt = "capy_{} {}# ".format(CAPY_VERSION,os.getcwd().split('/')[-1])
        try:
            cmd = input(prompt).strip()
        except (KeyboardInterrupt, EOFError) as e:
            print ("Thanks "+str(e))
            sys.exit(0)
    return cmd

def process_cmd(cmd, pin=None):
    cmd = cmd.split(" ")
    cpid = os.fork()
    if cpid == 0:
        try:
            if pin:
                os.dup2(pin, 0)
            os.execvp(cmd[0],cmd)
        except FileNotFoundError:
            print ("{}: not found".format(''.join(cmd)))
            sys.exit(-1)
    pid, status = os.waitpid(cpid,0)
    print ("\nProcess {} pid {}, exited with status {}".format(cmd[0], pid, status))

def spawn_proc(pin, pout, cmd):
    pid = os.fork()
    if pid == 0:
        #child
        if pin != 0:
            os.dup2(pin, 0)
            os.close(pin)
        if pout != 1:
            os.dup2(pout, 1)
            os.close(pout)
        os.execvp(cmd[0],cmd)
    return pid

def process_bg ( cmd ):
    print ( "process cmd ", cmd)
    if '|' in cmd:
        target  = process_pipeline
    else:
        target = process_cmd
    t = threading.Thread(target=target, args=(cmd,))
    print ("Child process started, pid {}".format("l"))
    t.start()
    t.join()
    print ("Child process exited, pid {}, status ".format("l"))

def process_pipeline(cmd,thread=False):
    cmds = [x.strip() for x in cmd.split('|')]
    pin = pout = pip = 0
    pidlist = []
    for i in range(len(cmds)-1):
        cmd = cmds[i].split(' ')
        pin, pout = os.pipe()
        # child is handled inside spawn proc
        try:
            pid = spawn_proc( pip , pout, cmd)
        except FileNotFoundError:
            sys.exit(-1)
            #break
        if pid:
            pidlist.append(pid)
        os.close(pout)
        pip = pin
    # handle last stage
    cmd = cmds[-1].split(' ')
    process_cmd (cmd,pin=pip)

def main():
    os.system('clear')
    print ( "Welcome capy {}".format(CAPY_VERSION))
    print ( "To exit the shell enter 'exit' or 'quit'")
    while True:
        cmd = get_input()
        # handle background process
        if cmd[-1] == '&':
            process_bg(cmd[:-1])
            continue
        # handle pipeline
        if '|' in cmd:
            process_pipeline(cmd)
            continue
        ncmd = cmd.split(" ")
        if ncmd[0] in SPL_CMDS:
            SPL_CMDS[ncmd[0]](ncmd[1:])
            continue
        process_cmd(cmd)


if __name__ == '__main__':
    main()
