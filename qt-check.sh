#!/bin/sh

if [ -x /usr/lib/x86_64-linux-gnu/libQt5Core.so.5 ]; then
  (set -x; strip --remove-section=.note.ABI-tag /usr/lib/x86_64-linux-gnu/libQt5Core.so.5)
fi