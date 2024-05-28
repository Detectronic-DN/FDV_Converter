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

        # Connect the download_csv_file signal to the appropriate method
        self.download_csv_file.connect(self.perform_download_csv_file)

    @Slot(str, str)
    def perform_download_csv_file(self, site_id, folderpath):
        self.busyChanged.emit(True)
        try:
            self._connect_signals()
            self.backend.download_csv_file(site_id, folderpath)
        finally:
            self.busyChanged.emit(False)
            self._disconnect_signals()

    def _connect_signals(self):
        self.backend.logMessage.connect(self.logMessage.emit)
        self.backend.siteDetailsRetrieved.connect(self.siteDetailsRetrieved.emit)
        self.backend.errorOccurred.connect(self.errorOccurred.emit)

    def _disconnect_signals(self):
        try:
            self.backend.logMessage.disconnect(self.logMessage.emit)
        except RuntimeError:
            pass
        try:
            self.backend.siteDetailsRetrieved.disconnect(self.siteDetailsRetrieved.emit)
        except RuntimeError:
            pass
        try:
            self.backend.errorOccurred.disconnect(self.errorOccurred.emit)
        except RuntimeError:
            pass
