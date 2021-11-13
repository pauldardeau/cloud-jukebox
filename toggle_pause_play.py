import os
import os.path


def main():
    if os.path.isfile("jukebox.pid"):
        pid_text = ''
        with open("jukebox.pid", "r") as f:
            pid_text = f.read().strip()
        if len(pid_text) > 0:
            pid = int(pid_text)
            cmd_to_run = "kill -s USR1 %d" % pid
            os.system(cmd_to_run)
        else:
            print("no jukebox running")
    else:
        print("no jukebox running")


if __name__ == '__main__':
    main()
