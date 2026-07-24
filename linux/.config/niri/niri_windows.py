import subprocess
import json
import select

def track_niri_windows():
    # Start the niri event stream
    cmd = ["niri", "msg", "--json", "event-stream"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)

    print("--- Monitoring Niri Window Events ---")
    print("Watching for creations and title changes...")
    
    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            
            try:
                event_data = json.loads(line)
                
                # Check for Window Opened
                if "WindowOpened" in event_data:
                    win = event_data["WindowOpened"]["window"]
                    print(f"\n[NEW WINDOW]")
                    print(f"  ID:     {win['id']}")
                    print(f"  App ID: {win['app_id']}")
                    print(f"  Title:  {win['title']}")

                # Check for Window Property Changes (like Title)
                elif "WindowPropertyChanged" in event_data:
                    change = event_data["WindowPropertyChanged"]
                    win = change["window"]
                    print(f"\n[PROPERTY CHANGE] Window ID: {win['id']}")
                    print(f"  Current App ID: {win['app_id']}")
                    print(f"  Current Title:  {win['title']}")

            except json.JSONDecodeError:
                continue
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        proc.terminate()

if __name__ == "__main__":
    track_niri_windows()
