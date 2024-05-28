from PySide6.QtCore import QObject, Signal, Slot


class Worker(QObject):
    logMessage = Signal(str)
    siteDetailsRetrieved = Signal(str, str, str, str)
    errorOccurred = Signal(str)
    busyChanged = Signal(bool)

    def __init__(self, backend):
        super().__init__()
        self.backend = backend

    @Slot(str, str)
    def download_csv_file(self, site_id, folderpath):
        self.busyChanged.emit(True)
        try:
            self.backend.logMessage.connect(self.logMessage.emit)
            self.backend.siteDetailsRetrieved.connect(self.siteDetailsRetrieved.emit)
            self.backend.errorOccurred.connect(self.errorOccurred.emit)
            self.backend.download_csv_file(site_id, folderpath)
        finally:
            self.busyChanged.emit(False)
            self.backend.logMessage.disconnect(self.logMessage.emit)
            self.backend.siteDetailsRetrieved.disconnect(self.siteDetailsRetrieved.emit)
            self.backend.errorOccurred.disconnect(self.errorOccurred.emit)
