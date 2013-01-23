#!/usr/bin/env python2.7

from driver import *
import sys

def generate_output_fn(in_fn, remove=False):
    if (remove == False):
        return '%s.png' % (in_fn,)

    assert(in_fn.lower().endswith('.png'))

    return in_fn[:-4]


def opener(in_fn, write=False):
    if (in_fn == '-'):
        if (write):
            return sys.stdout
        else:
            return sys.stdin

    mode = 'w' if write else 'r'
    return open(in_fn, mode)


def encode(in_fn, out_fn=None):
    from PIL import Image
    import math

    assert(in_fn != '-' or out_fn is not None)
    if (out_fn is None):
        out_fn = generate_output_fn(in_fn)

    data = v0_driver.encode(opener(in_fn))
    dimension = int(math.sqrt(len(data) / 4))
    img = Image.fromstring('RGBA', (dimension, dimension), data)
    img.save(opener(out_fn, True), 'png')


def decode(in_fn, out_fn=None):
    from PIL import Image
    import math
    import StringIO

    assert(in_fn != '-' or out_fn is not None)
    if (out_fn is None):
        out_fn = generate_output_fn(in_fn, True)

    img = Image.open(opener(in_fn))
    decoded = versioned_driver.infer_and_decode(img.tostring())

    out_fh = opener(out_fn, True)
    out_fh.write(decoded[1])
    out_fh.close()


def usage(exename):
    sys.stderr.write('Usage:\n')
    sys.stderr.write('  %s encode <file> [<output>]\n' % (exename,))
    sys.stderr.write('  %s decode <file> [<output>]\n' % (exename,))
    sys.exit(1)

if (__name__ == '__main__'):
    args = sys.argv

    if (len(args) < 2):
        usage(args[0])

    if (args[1] == 'encode'):
        encode(*args[2:])
    elif (args[1] == 'decode'):
        decode(*args[2:])
    else:
        usage(args[0])
