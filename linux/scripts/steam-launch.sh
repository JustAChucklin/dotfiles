#!/bin/bash
source ~/.bash_profile 2>/dev/null || source ~/.profile 2>/dev/null
exec /usr/bin/steam "$@"
