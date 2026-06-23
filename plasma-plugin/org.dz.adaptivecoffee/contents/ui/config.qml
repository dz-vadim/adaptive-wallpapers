import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami
import "logic.js" as L

ColumnLayout {
    id: root

    // властивості, які передає KCM шпалер у Plasma 6
    property var configDialog
    property var wallpaperConfiguration: wallpaper.configuration
    property var parentLayout

    // cfg_<Key> мають збігатися з ключами у config/main.xml
    property alias cfg_Folder: folderField.text
    property string cfg_FolderDefault
    property alias cfg_Location: locationField.text
    property string cfg_LocationDefault
    property alias cfg_IntervalMinutes: intervalSpin.value
    property int cfg_IntervalMinutesDefault: 15
    property string cfg_SeasonMode: "auto"
    property string cfg_SeasonModeDefault: "auto"
    property string cfg_TimeMode: "auto"
    property string cfg_TimeModeDefault: "auto"
    property string cfg_WeatherMode: "auto"
    property string cfg_WeatherModeDefault: "auto"

    // погода для прев'ю (коли режим Auto — підтягуємо реальну)
    property string previewWeather: "clear"

    readonly property string previewFolder:
        (cfg_Folder && cfg_Folder.length > 0) ? cfg_Folder
        : "/home/dz/Pictures/wallpapers_archive/wallpapers"

    function previewName() {
        var sName = L.resolveSeason(cfg_SeasonMode)
        var tName = L.resolveTime(cfg_TimeMode)
        var wName = (cfg_WeatherMode && cfg_WeatherMode !== "auto")
                    ? cfg_WeatherMode : previewWeather
        return L.candidates(sName, tName, wName)[0]
    }

    function fetchPreviewWeather() {
        var url = "https://wttr.in/" + encodeURIComponent(cfg_Location) + "?format=j1"
        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== XMLHttpRequest.DONE) return
            try {
                if (xhr.status === 200) {
                    var j = JSON.parse(xhr.responseText)
                    previewWeather = L.mapWeatherCode(parseInt(j.current_condition[0].weatherCode))
                }
            } catch (e) { /* лишаємо як є */ }
        }
        try { xhr.open("GET", url); xhr.send() } catch (e) {}
    }

    Component.onCompleted: if (cfg_WeatherMode === "auto") fetchPreviewWeather()

    FolderDialog {
        id: folderDialog
        title: "Choose wallpapers folder"
        onAccepted: folderField.text = selectedFolder.toString().replace(/^file:\/\//, "")
    }

    Kirigami.FormLayout {
        twinFormLayouts: parentLayout
        Layout.fillWidth: true

        RowLayout {
            Kirigami.FormData.label: "Wallpapers folder:"
            TextField {
                id: folderField
                Layout.fillWidth: true
                Layout.minimumWidth: 280
            }
            Button {
                text: "Browse…"
                icon.name: "document-open-folder"
                onClicked: folderDialog.open()
            }
        }

        TextField {
            id: locationField
            Kirigami.FormData.label: "Weather location:"
            placeholderText: "blank = auto by IP"
            Layout.fillWidth: true
            onEditingFinished: if (cfg_WeatherMode === "auto") root.fetchPreviewWeather()
        }

        SpinBox {
            id: intervalSpin
            Kirigami.FormData.label: "Update every (minutes):"
            from: 1
            to: 240
        }

        Item { Kirigami.FormData.isSection: true }

        ComboBox {
            id: weatherCombo
            Kirigami.FormData.label: "Weather:"
            textRole: "text"
            valueRole: "value"
            model: [
                { text: "Auto (live)", value: "auto" },
                { text: "Clear", value: "clear" },
                { text: "Cloudy", value: "cloudy" },
                { text: "Rain / Snow", value: "rain_snow" }
            ]
            currentIndex: indexOfValue(cfg_WeatherMode)
            onActivated: {
                cfg_WeatherMode = currentValue
                if (currentValue === "auto") root.fetchPreviewWeather()
            }
        }

        ComboBox {
            id: seasonCombo
            Kirigami.FormData.label: "Season:"
            textRole: "text"
            valueRole: "value"
            model: [
                { text: "Auto (by date)", value: "auto" },
                { text: "Winter", value: "winter" },
                { text: "Spring", value: "spring" },
                { text: "Summer", value: "summer" },
                { text: "Autumn", value: "autumn" }
            ]
            currentIndex: indexOfValue(cfg_SeasonMode)
            onActivated: cfg_SeasonMode = currentValue
        }

        ComboBox {
            id: timeCombo
            Kirigami.FormData.label: "Time of day:"
            textRole: "text"
            valueRole: "value"
            model: [
                { text: "Auto (by clock)", value: "auto" },
                { text: "Morning", value: "morning" },
                { text: "Day", value: "day" },
                { text: "Evening", value: "evening" },
                { text: "Night", value: "night" }
            ]
            currentIndex: indexOfValue(cfg_TimeMode)
            onActivated: cfg_TimeMode = currentValue
        }

        Item { Kirigami.FormData.isSection: true }

        ColumnLayout {
            Kirigami.FormData.label: "Now showing:"
            spacing: Kirigami.Units.smallSpacing
            Image {
                Layout.preferredWidth: 256
                Layout.preferredHeight: 144
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                cache: false
                source: "file://" + root.previewFolder + "/" + root.previewName()
                Rectangle {   // рамка/заглушка, якщо файлу нема
                    anchors.fill: parent
                    color: "transparent"
                    border.color: Kirigami.Theme.disabledTextColor
                    border.width: 1
                    visible: parent.status !== Image.Ready
                    Label {
                        anchors.centerIn: parent
                        text: parent.parent.status === Image.Error ? "немає файлу" : "…"
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
            }
            Label {
                text: root.previewName()
                font: Kirigami.Theme.smallFont
                opacity: 0.8
            }
        }
    }
}
