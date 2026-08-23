#!/bin/bash

# Better Random Logo Fastfetch Script
# Uses multiple randomization methods to ensure variety

# Configuration
LOGO_DIR="$HOME/.config/fastfetch/logos"
DEBUG=false  # Set to false to disable debug output
HISTORY_FILE="$HOME/.config/fastfetch/logo_history"

# Create directories
mkdir -p "$HOME/.config/fastfetch"
mkdir -p "$LOGO_DIR"

# Debug function
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo "DEBUG: $1" >&2
    fi
}

# Check if fastfetch is installed
if ! command -v fastfetch &> /dev/null; then
    echo "fastfetch is not installed. Please install it first."
    exit 1
fi

# Find all PNG and TXT files
logos=($(find "$LOGO_DIR" -type f \( -iname "*.png" -o -iname "*.txt" \) 2>/dev/null))

# Check if any logos were found
if [ ${#logos[@]} -eq 0 ]; then
    echo "No logos found in $LOGO_DIR"
    fastfetch --pipe false
    exit 0
fi

# List all available logos for debugging
debug_log "Available logos:"
for i in "${!logos[@]}"; do
    debug_log "  [$i] $(basename "${logos[$i]}")"
done

# Better randomization using multiple entropy sources
get_random_logo() {
    local num_logos=${#logos[@]}
    
    # Method 1: Use /dev/urandom if available
    if [ -r /dev/urandom ]; then
        local random_bytes=$(od -An -N4 -tu4 < /dev/urandom | tr -d ' ')
        local index=$((random_bytes % num_logos))
        debug_log "Method 1 (/dev/urandom): index=$index"
        echo "$index"
        return
    fi
    
    # Method 2: Use current time with microseconds + PID
    local time_seed=$(date +%s%N 2>/dev/null || date +%s)
    local pid_seed=$$
    local combined_seed=$((time_seed + pid_seed))
    RANDOM=$combined_seed
    local index=$((RANDOM % num_logos))
    debug_log "Method 2 (time+PID): seed=$combined_seed, index=$index"
    echo "$index"
}

# Avoid repeating the last few logos
avoid_recent_logos() {
    local selected_index=$1
    local selected_logo="${logos[$selected_index]}"
    
    # Create history file if it doesn't exist
    touch "$HISTORY_FILE"
    
    # Read recent logos (last 3)
    local recent_logos=($(tail -3 "$HISTORY_FILE" 2>/dev/null))
    
    # Check if current selection is in recent history
    local logo_basename=$(basename "$selected_logo")
    for recent in "${recent_logos[@]}"; do
        if [ "$logo_basename" = "$recent" ]; then
            debug_log "Logo $logo_basename was used recently, trying another..."
            # Try up to 5 times to get a different logo
            for attempt in {1..5}; do
                local new_index=$(get_random_logo)
                local new_logo="${logos[$new_index]}"
                local new_basename=$(basename "$new_logo")
                
                # Check if this new logo is also recent
                local is_recent=false
                for recent in "${recent_logos[@]}"; do
                    if [ "$new_basename" = "$recent" ]; then
                        is_recent=true
                        break
                    fi
                done
                
                if [ "$is_recent" = false ]; then
                    debug_log "Found non-recent logo: $new_basename (attempt $attempt)"
                    echo "$new_index"
                    return
                fi
            done
            # If we couldn't find a non-recent logo after 5 attempts, just use the original
            debug_log "Couldn't avoid recent logos after 5 attempts, using original selection"
            break
        fi
    done
    
    echo "$selected_index"
}

# Get random logo with better entropy
random_index=$(get_random_logo)

# Try to avoid recently used logos (only if we have more than 3 logos)
if [ ${#logos[@]} -gt 3 ]; then
    random_index=$(avoid_recent_logos $random_index)
fi

selected_logo="${logos[$random_index]}"
extension="${selected_logo##*.}"

debug_log "Final selection: index=$random_index, logo=$(basename "$selected_logo")"

# Update history
echo "$(basename "$selected_logo")" >> "$HISTORY_FILE"
# Keep only last 5 entries
tail -5 "$HISTORY_FILE" > "${HISTORY_FILE}.tmp" && mv "${HISTORY_FILE}.tmp" "$HISTORY_FILE"

# Function to display PNG properly in Kitty
display_png_kitty() {
    local logo_file="$1"
    
    # We set a hard limit of 35 characters wide and 18 lines tall.
    # Fastfetch will scale the PNG down to fit inside this box.
    fastfetch --logo "$logo_file" \
              --logo-type kitty \
              --logo-width 45 \
              --logo-height 18 \
              --logo-preserve-aspect-ratio true \
              --logo-padding-right 4 \
              --pipe false
}
# display_png_kitty() {
#     local logo_file="$1"
#
#     debug_log "Displaying PNG: $(basename "$logo_file")"
#
#     # Check if image exists and is readable
#     if [ ! -r "$logo_file" ]; then
#         debug_log "Cannot read logo file: $logo_file"
#         return 1
#     fi
#
#     # Try different methods for Kitty
#     if [[ "$TERM" == "xterm-kitty" ]]; then
#         debug_log "Using Kitty terminal, trying kitty protocol"
#         if fastfetch --logo "$logo_file" --logo-type kitty --logo-width  --logo-padding-bottom 0 --pipe false 2>/dev/null; then
#             return 0
#         fi
#
#         debug_log "Kitty protocol failed, trying iterm protocol"
#         if fastfetch --logo "$logo_file" --logo-type iterm --logo-width 10 --logo-padding-bottom 0 --pipe false 2>/dev/null; then
#             return 0
#         fi
#     fi
#
#     # Fallback methods
#     debug_log "Trying auto detection"
#     if fastfetch --logo "$logo_file" --logo-type auto --pipe false 2>/dev/null; then
#         return 0
#     fi
#
#     debug_log "All PNG display methods failed"
#     return 1
# }

# Main execution
case "${extension,,}" in
    "png")
        debug_log "Processing PNG file"
        if ! display_png_kitty "$selected_logo"; then
            echo "Could not display PNG logo: $(basename "$selected_logo")"
            fastfetch --pipe false
        fi
        ;;
    "txt")
        debug_log "Processing TXT file"
        if ! fastfetch --logo-type file --logo "$selected_logo" --pipe false 2>/dev/null; then
            if ! fastfetch --logo "$selected_logo" --pipe false 2>/dev/null; then
                echo "Could not display TXT logo: $(basename "$selected_logo")"
                fastfetch --pipe false
            fi
        fi
        ;;
    *)
        debug_log "Unknown file type, using default"
        fastfetch --pipe false
        ;;
esac
