# All the default Omarchy aliases and functions
# (don't mess with these directly, just overwrite them here!)
source ~/.local/share/omarchy/default/bash/rc

# Add your own exports, aliases, and functions here.
#
# Make an alias for invoking commands you use constantly
# alias p='python'
#
# Use VSCode instead of neovim as your default editor
# export EDITOR="code"
#
# Set a custom prompt with the directory revealed (alternatively use https://starship.rs)
# PS1="\W \[\e]0;\w\a\]$PS1"
# Initialize zoxide for bash

# Initialize starship for bash
eval "$(starship init bash)"

# Set preferred editors
export EDITOR="nvim"
export VISUAL="nvim"

# Aliases
alias c="clear && fastfetch"
alias fastfetch="/home/chuckles/.local/bin/random_logo.sh"

# Bash has no `unsetopt correct_all` — skip or replace with 'shopt -u cdspell' if needed
# shopt -u cdspell

export PATH="$HOME/.cargo/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"
# Source your random logo script
source /home/chuckles/.local/bin/random_logo.sh
eval "$(zoxide init bash --cmd cd)"


