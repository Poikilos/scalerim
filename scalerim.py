#!/usr/bin/env python3
import sys
import os

from PIL import Image
import tempfile
import shutil
import subprocess
resize_bin = "scalerx"
help_s = """
This program uses {resize_bin}, but fixes the edge by padding before
scaling then un-padding the edge after scaling. This allows {resize_bin}
to accurately detect the edge of the sprite, rather than leaving large
pixelated parts where the sprite touches the edge.

Options:
-f (or --force)           Overwrite destination file if present.
-c (or --command)         Specify what command to use (default scalerx).
-e=<value>
(or --extend=<value>)     Specify how many extra pixels to keep after
                          the scale command succeeds.

Examples:
{cmd} <source> <destination>
{cmd} <source> <destination> -k4
{cmd} <source> <destination>

""".format(cmd=sys.argv[0], resize_bin=resize_bin)

def customDie(msg, exit_code=1):
    print("")
    print("ERROR:")
    print(msg)
    print("")
    print("")
    exit(exit_code)

def usage():
    print(help_s)

name_alts = {}
name_alts["force"] = "f"
name_alts["command"] = "c"
name_alts["extend"] = "e"

delay_args = ['k']

arg_alts = {}
for k, v in name_alts.items():
    arg_alts[v] = k  # Create a reverse lookup.

options = {}

def add_option(s, value):
    result = False
    if len(s) == 1:
        name = arg_alts.get(s)
        if name is None:
            usage()
            print("passing along unknown option: {}".format(s))
            return False
        options[name] = value
        print("* set {} to {}".format(name, value))
    else:
        c = name_alts.get(s)
        if c is None:
            usage()
            print("passing along unknown option: {}".format(s))
            return False
        else:
            options[s] = value
            print("* set {} to {}".format(s, value))

    return True

def main():
    global resize_bin
    if len(sys.argv) < 3:
        usage()
        customDie("You must supply a source and destination.")

    src = None
    dst = None
    scale = None
    name = None
    value = None

    passthroughs = []
    delayed = None
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if arg.startswith("-"):
            skip = 1
            if arg.startswith("--"):
                skip = 2
                sign_i = arg.find("=")

                if sign_i > -1:
                    name = arg[skip:sign_i]
                    value = arg[sign_i+1:]
                else:
                    name = arg[skip:]
                    value = True
                delayed = None
                result = add_option(name, value)
                if not result:
                    passthroughs.append(arg)
            else:
                if arg[1:] in delay_args:
                    delayed = arg
                else:
                    sign_i = arg.find("=")
                    if sign_i > -1:
                        c = arg[skip:sign_i]
                        value = arg[sign_i+1:]
                        name = arg_alts.get(c)
                        if not add_option(name, value):
                            print("* passing along unknown option"
                                  " '{}'".format(arg))
                            passthroughs.append(arg)
                    else:
                        for i in range(1, len(arg)):
                            if not add_option(arg[i], True):
                                passthroughs.append(arg)
                                break
                        delayed = None
        else:
            if delayed is not None:
                passthroughs.extend([delayed, arg])
                name = delayed[1:]
                if name == 'k':
                    scale = int(arg)
                name = None
                delayed = None
            elif src is None:
                src = arg
            elif dst is None:
                dst = arg
            else:
                usage()
                print("* You supplied extra unnamed arguments.\n"
                      "  The next program will get the"
                      " {} option.".format(arg))
                passthroughs.append(arg)
    # if scale is None:
    #     customDie("You must specify -k or the subcommand scale will"
    #               " not be understood. Knowing the scale is"
    #               " necessary")
    if src is None:
        customDie("You didn't supply a source file (a first unnamed"
                  " argument)")
    if dst is None:
        customDie("You didn't supply a destination file (a second unnamed"
                  " argument)")

    if not os.path.isfile(src):
        customDie("'{}' does not exist.".format(src))

    force = False
    force_why = None
    if options.get("force") is True:
        force = True
        force_why = "--force"
    elif options.get("f") is True:
        force = True
        force_why = "-f"

    if os.path.isfile(dst):
        if not force:
            customDie("'{}' already exists, and you didn't specify --force or -f.".format(src))
        else:
            print("* overwriting '{}' due to {}.".format(dst, force_why))
    #     dest_dir = os.path.dirname(os.path.realpath(dst))
    # else:
    #     dest_dir = os.path.dirname(dst)
    temps = tempfile.mkdtemp()
    ext = os.path.splitext(src)[1]
    tmp = os.path.join(temps, "tmp"+ext)
    big = os.path.join(temps, "big"+ext)
    src_img = Image.open(src, 'r')
    src_w, src_h = src_img.size
    # src_img = src_img.convert('RGBA')  # not necessary?
    # See https://stackoverflow.com/a/2563883/4541104
    # supercedes border_cmd = ["mogrify", "-path", dest_dir, "-bordercolor", "transparent", "-border", "20", "-format", "png", src]
    big_img = Image.new('RGBA', (src_w*2, src_h*2), (0, 0, 0, 0))
    src_w, src_h = src_img.size
    big_w, big_h = big_img.size
    offset = ((big_w - src_w) // 2, (big_h - src_h) // 2)
    big_img.paste(src_img, offset)
    print("* saving extended image for input: '{}'".format(big))
    big_img.save(big)
    did_exist = False
    if os.path.isfile(dst):
        did_exist = True
    resize_bin = options.get("command")
    if resize_bin is None:
        resize_bin = "scalerx"
    scale_cmd = [resize_bin]
    if len(passthroughs) > 0:
        scale_cmd.extend(passthroughs)
    scale_cmd.extend([big, tmp])
    cmd_s = " ".join(scale_cmd)
    print("* running '{}'...".format(cmd_s))
    ok = False
    try:
        # Examples:
        # scalerx -k 4 input.png output.png
        # scalerx -k 2 input.png output.png
        # scalerx or scalex
        # proc = subprocess.Popen(scale_cmd, stdout=subprocess.PIPE,
        #                         stderr=subprocess.PIPE)
        completedprocess = subprocess.run(scale_cmd)
        ok = True
    except Exception as e:
        print("  ERROR: {}".format(e))
        print("* Trying the command with os.system...")
        try:
            os.system(cmd_s)
            ok = True
        except Exception as e:
            print("  ERROR: {}".format(e))
    if not os.path.isfile(tmp):
        print("  ERROR: The command did not result in '{}'".format(tmp))
        ok = False
    if ok:
        tmp_img = Image.open(tmp, 'r')
        tmp_w, tmp_h = tmp_img.size
        delta_w = tmp_w - big_w
        delta_h = tmp_h - big_h
        ratio = tmp_w / big_w  # usually 2 or 4
        extend = options.get("extend")
        # Now remove the margin (except "extend" amount specified)
        if extend is None:
            extend = 0
        else:
            extend = int(extend)
        new_w = int(src_w * ratio) + extend*2
        new_h = int(src_h * ratio) + extend*2
        print("* source size: {}".format((src_w, src_h)))
        # print("* new size: {}".format((new_w, new_h)))
        # dst_img = Image.new('RGBA', (new_w, new_h), (0, 0, 0, 0))
        left = (tmp_w - new_w) // 2
        top = (tmp_w - new_h) // 2
        right = left + new_w
        bottom = top + new_h
        print("* temp size: {}x{}".format(tmp_w, tmp_h))
        print("* cropped at: {},{}".format(left, top))
        print("* new size: {}x{}".format(new_w, new_h))
        dst_img = tmp_img.crop((left, top, right, bottom))
        dst_w, dst_h = dst_img.size
        print("* saving destination '{}'".format(dst))
        dst_img.save(dst)
        if os.path.isfile(dst):
            # dst_w, dst_h = dst_img.size
            if not did_exist:
                print("* '{}' was created.".format(dst))
            else:
                print("* check '{}' (was already present;"
                      " It is overwritten if the command"
                      " succeeded).".format(dst))
        else:
            print("  ERROR: the command did not result in"
                  " '{}'".format(dst))

    if os.path.isfile(tmp):
        os.remove(tmp)
    if os.path.isfile(big):
        os.remove(big)
    if os.path.isdir(temps):
        os.rmdir(temps)


if __name__ == "__main__":
    main()
