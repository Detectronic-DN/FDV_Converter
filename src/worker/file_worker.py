from PySide6.QtCore import QObject, Signal, Slot


class UploadWorker(QObject):
    upload_csv_file = Signal(str)
    logMessage = Signal(str)
    siteDetailsRetrieved = Signal(str, str, str, str)
    errorOccurred = Signal(str)
    busyChanged = Signal(bool)

    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self._connections_made = False
        self.upload_csv_file.connect(self.perform_upload_csv_file)

    @Slot(str)
    def perform_upload_csv_file(self, filepath):
        self.busyChanged.emit(True)
        try:
            self.connect_signals()
            self.backend.upload_csv_file(filepath)
        finally:
            self.busyChanged.emit(False)

    def _connect_signals(self):
        if not self._connections_made:
            self.backend.logMessage.connect(self.logMessage.emit)
            self.backend.siteDetailsRetrieved.connect(self.siteDetailsRetrieved.emit)
            self.backend.errorOccurred.connect(self.errorOccurred.emit)
            self._connections_made = True

    def connect_signals(self):
        if not self._connections_made:
            self.backend.logMessage.connect(self.logMessage.emit)
            self.backend.siteDetailsRetrieved.connect(self.siteDetailsRetrieved.emit)
            self.backend.errorOccurred.connect(self.errorOccurred.emit)
            self._connections_made = True
