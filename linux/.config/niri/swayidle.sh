#!/bin/bash
exec swayidle -w \
    timeout 300 'qs ipc call globalIPC toggleLock' \
    timeout 600 'systemctl suspend' \
    before-sleep 'qs ipc call globalIPC toggleLock' \
    lock 'qs ipc call globalIPC toggleLock'
