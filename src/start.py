# -*- coding: utf-8 -*-
"""Launcher script with encoding fix and crash protection."""
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

if __name__ == '__main__':
    try:
        import main
        import threading

        scanner_thread = threading.Thread(target=main.run_loop, daemon=True)
        scanner_thread.start()

        port = int(os.environ.get('PORT', 8080))
        main.add_bot_log("Dashboard: http://localhost:{}".format(port), 'INFO')
        main.app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\nBot arrete.")
    except Exception as e:
        print("ERREUR FATALE: {}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
