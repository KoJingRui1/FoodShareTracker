from src.gui.main_dashboard import launch
# TODO: Import the new admin utilities.
from src.app.utils import init_logger, backup_data

if __name__ == "__main__":
    # Initialize the logger as the very first step.
    init_logger()

    # Perform a data backup before starting the application session.
    backup_data()

    # Launch the GUI as before.
    launch()