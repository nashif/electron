#!/usr/bin/env python

import argparse
import glob
import os
import shutil
import sys

from lib.config import PLATFORM, get_target_arch, s3_config
from lib.util import safe_mkdir, scoped_cwd, s3put, get_out_dir, get_dist_dir

# TODO: Update this entire file to point at the correct file names in the out
#       directory
SOURCE_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DIST_DIR    = get_dist_dir()
OUT_DIR     = get_out_dir()
GEN_DIR     = os.path.join(OUT_DIR, 'gen')

HEADER_TAR_NAMES = [
  'node-{0}.tar.gz',
  'node-{0}-headers.tar.gz',
  'iojs-{0}.tar.gz',
  'iojs-{0}-headers.tar.gz'
]

def main():
  args = parse_args()

  # Upload node's headers to S3.
  bucket, access_key, secret_key = s3_config()
  upload_node(bucket, access_key, secret_key, args.version)


def parse_args():
  parser = argparse.ArgumentParser(description='upload sumsha file')
  parser.add_argument('-v', '--version', help='Specify the version',
                      required=True)
  return parser.parse_args()


def upload_node(bucket, access_key, secret_key, version):
  with scoped_cwd(GEN_DIR):
    generated_tar = os.path.join(GEN_DIR, 'node_headers.tar.gz')
    for header_tar in HEADER_TAR_NAMES:
      versioned_header_tar = header_tar.format(version)
      shutil.copy2(generated_tar, os.path.join(GEN_DIR, versioned_header_tar))

    s3put(bucket, access_key, secret_key, GEN_DIR,
          'atom-shell/dist/{0}'.format(version), glob.glob('node-*.tar.gz'))
    s3put(bucket, access_key, secret_key, GEN_DIR,
          'atom-shell/dist/{0}'.format(version), glob.glob('iojs-*.tar.gz'))

  if PLATFORM == 'win32':
    if get_target_arch() == 'ia32':
      node_lib = os.path.join(DIST_DIR, 'node.lib')
      iojs_lib = os.path.join(DIST_DIR, 'win-x86', 'iojs.lib')
      v4_node_lib = os.path.join(DIST_DIR, 'win-x86', 'node.lib')
    else:
      node_lib = os.path.join(DIST_DIR, 'x64', 'node.lib')
      iojs_lib = os.path.join(DIST_DIR, 'win-x64', 'iojs.lib')
      v4_node_lib = os.path.join(DIST_DIR, 'win-x64', 'node.lib')
    safe_mkdir(os.path.dirname(node_lib))
    safe_mkdir(os.path.dirname(iojs_lib))

    # Copy atom.lib to node.lib, iojs.lib and v4 node.lib
    electron_lib = os.path.join(OUT_DIR, 'electron.lib')
    shutil.copy2(electron_lib, node_lib)
    shutil.copy2(electron_lib, iojs_lib)
    shutil.copy2(electron_lib, v4_node_lib)

    # Upload the node.lib.
    s3put(bucket, access_key, secret_key, DIST_DIR,
          'atom-shell/dist/{0}'.format(version), [node_lib])

    # Upload the iojs.lib.
    s3put(bucket, access_key, secret_key, DIST_DIR,
          'atom-shell/dist/{0}'.format(version), [iojs_lib])

    # Upload the v4 node.lib.
    s3put(bucket, access_key, secret_key, DIST_DIR,
          'atom-shell/dist/{0}'.format(version), [v4_node_lib])


if __name__ == '__main__':
  sys.exit(main())
