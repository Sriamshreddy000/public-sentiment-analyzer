import sys
import time
import subprocess

def spinner_run(script_name: str, label: str):
    proc = subprocess.Popen(
        [sys.executable, script_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    spin = "|/-\\"
    i = 0
    while True:
        ret = proc.poll()
        if ret is not None:
            break
        ch = spin[i % len(spin)]
        print(f"\r{label} {ch}", end="", flush=True)
        time.sleep(0.12)
        i += 1

    print(f"\r{label} ✅", flush=True)

    if ret != 0:
        print(f"(Error) {script_name} failed. Run it directly to see logs:\n  {sys.executable} {script_name}")
        raise SystemExit(ret)

def run_visible(script_name: str):
    subprocess.run([sys.executable, script_name], check=True)

def prompt_int(msg: str):
    raw = input(msg).strip()
    if not raw:
        return None
    if not raw.isdigit():
        return None
    return int(raw)

def menu():
    while True:
        print("\n==============================")
        print("Public Sentiment CLI")
        print("==============================")
        print("1) View trending topics + analyze one")
        print("2) Refresh trending topics (reset + refetch + analyze)")
        print("3) About")
        print("4) Exit (and clear cached data)")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            run_visible("list_topics.py")
            n = prompt_int("\nEnter topic number to analyze (or press Enter to go back): ")
            if n is None:
                continue
            subprocess.run([sys.executable, "topic_detail.py", str(n)], check=True)

        elif choice == "2":
            print("\nRefreshing (fresh start)...\n")
            steps = [
                ("reset_db.py", "Resetting DB"),
                ("fetch_rising.py", "Fetching trending posts"),
                ("fetch_comments.py", "Fetching comments"),
                ("extract_post_entities.py", "Extracting topic entities"),
                ("clear_entity_stance.py", "Clearing stance table"),
                ("analyze_entity_stance_auto.py", "Analyzing stance"),
            ]
            for script, label in steps:
                spinner_run(script, label)

            print("\nDone ✅\n")
            run_visible("list_topics.py")
            n = prompt_int("\nEnter topic number to analyze now (or press Enter to skip): ")
            if n is not None:
                subprocess.run([sys.executable, "topic_detail.py", str(n)], check=True)

        elif choice == "3":
            run_visible("about.py")

        elif choice == "4":
            spinner_run("reset_db.py", "Clearing cached data")
            print("\nBye 👋")
            break

        else:
            print("Invalid choice. Pick 1, 2, 3, or 4.")

if __name__ == "__main__":
    menu()