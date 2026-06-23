import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    twinFormLayouts: parentLayout

    property alias cfg_Folder: folderField.text
    property alias cfg_Location: locationField.text
    property alias cfg_IntervalMinutes: intervalSpin.value

    TextField {
        id: folderField
        Kirigami.FormData.label: "Wallpapers folder:"
        Layout.fillWidth: true
    }

    TextField {
        id: locationField
        Kirigami.FormData.label: "Weather location:"
        placeholderText: "blank = auto by IP"
        Layout.fillWidth: true
    }

    SpinBox {
        id: intervalSpin
        Kirigami.FormData.label: "Update every (minutes):"
        from: 1
        to: 240
    }
}
