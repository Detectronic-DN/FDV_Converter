from PySide6.QtCore import QObject, Signal, Slot


class Worker(QObject):
    download_csv_file = Signal(str, str)
    logMessage = Signal(str)
    siteDetailsRetrieved = Signal(str, str, str, str)
    errorOccurred = Signal(str)
    busyChanged = Signal(bool)

    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self._connections_made = False

        # Connect the download_csv_file signal to the appropriate method
        self.download_csv_file.connect(self.perform_download_csv_file)

    @Slot(str, str)
    def perform_download_csv_file(self, site_id, folder_path):
        self.busyChanged.emit(True)
        try:
            self._connect_signals()
            print(folder_path)
            self.backend.download_csv_file(site_id, folder_path)
        finally:
            self.busyChanged.emit(False)

    def _connect_signals(self):
        if not self._connections_made:
            self.backend.logMessage.connect(self.logMessage.emit)
            self.backend.siteDetailsRetrieved.connect(self.siteDetailsRetrieved.emit)
            self.backend.errorOccurred.connect(self.errorOccurred.emit)
            self._connections_made = True
