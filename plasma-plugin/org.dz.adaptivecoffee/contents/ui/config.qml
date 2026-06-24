import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.kirigami as Kirigami
import "logic.js" as L

ColumnLayout {
    id: root

    property var configDialog
    property var wallpaperConfiguration: wallpaper.configuration
    property var parentLayout

    // cfg_<Key> ↔ config/main.xml
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
    property string cfg_Mode: "adaptive"
    property string cfg_ModeDefault: "adaptive"
    property alias cfg_CarouselIntervalMinutes: carouselSpin.value
    property int cfg_CarouselIntervalMinutesDefault: 30
    property list<string> cfg_CarouselImages: []
    property list<string> cfg_CarouselImagesDefault: []

    readonly property bool carousel: cfg_Mode === "carousel"
    property string previewWeather: "clear"

    readonly property string defaultFolder: {
        var u = Qt.resolvedUrl("../../../../wallpapers").toString()
        return u.replace(/^file:\/\//, "").replace(/\/+$/, "")
    }
    readonly property string previewFolder:
        (cfg_Folder && cfg_Folder.length > 0) ? cfg_Folder : defaultFolder

    function previewName() {
        var sName = L.resolveSeason(cfg_SeasonMode)
        var tName = L.resolveTime(cfg_TimeMode)
        var wName = (cfg_WeatherMode && cfg_WeatherMode !== "auto") ? cfg_WeatherMode : previewWeather
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
            } catch (e) {}
        }
        try { xhr.open("GET", url); xhr.send() } catch (e) {}
    }
    function toggleCarousel(name, on) {
        var arr = cfg_CarouselImages.slice()
        var i = arr.indexOf(name)
        if (on && i < 0) arr.push(name)
        else if (!on && i >= 0) arr.splice(i, 1)
        cfg_CarouselImages = arr
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

        ComboBox {
            id: modeCombo
            Kirigami.FormData.label: "Mode:"
            textRole: "text"; valueRole: "value"
            model: [
                { text: "Adaptive (season · time · weather)", value: "adaptive" },
                { text: "Carousel (cycle chosen images)", value: "carousel" }
            ]
            currentIndex: Math.max(0, indexOfValue(cfg_Mode))
            onActivated: cfg_Mode = currentValue
        }

        RowLayout {
            Kirigami.FormData.label: "Wallpapers folder:"
            TextField { id: folderField; Layout.fillWidth: true; Layout.minimumWidth: 280 }
            Button { text: "Browse…"; icon.name: "document-open-folder"; onClicked: folderDialog.open() }
        }

        // ---------- ADAPTIVE ----------
        TextField {
            id: locationField
            Kirigami.FormData.label: "Weather location:"
            placeholderText: "blank = auto by IP"
            Layout.fillWidth: true
            visible: !root.carousel
            onEditingFinished: if (cfg_WeatherMode === "auto") root.fetchPreviewWeather()
        }
        SpinBox {
            id: intervalSpin
            Kirigami.FormData.label: "Update every (minutes):"
            from: 1; to: 240
            visible: !root.carousel
        }
        ComboBox {
            id: weatherCombo
            Kirigami.FormData.label: "Weather:"
            visible: !root.carousel
            textRole: "text"; valueRole: "value"
            model: [
                { text: "Auto (live)", value: "auto" },
                { text: "Clear", value: "clear" },
                { text: "Cloudy", value: "cloudy" },
                { text: "Rain / Snow", value: "rain_snow" }
            ]
            currentIndex: Math.max(0, indexOfValue(cfg_WeatherMode))
            onActivated: { cfg_WeatherMode = currentValue; if (currentValue === "auto") root.fetchPreviewWeather() }
        }
        ComboBox {
            id: seasonCombo
            Kirigami.FormData.label: "Season:"
            visible: !root.carousel
            textRole: "text"; valueRole: "value"
            model: [
                { text: "Auto (by date)", value: "auto" },
                { text: "Winter", value: "winter" }, { text: "Spring", value: "spring" },
                { text: "Summer", value: "summer" }, { text: "Autumn", value: "autumn" }
            ]
            currentIndex: Math.max(0, indexOfValue(cfg_SeasonMode))
            onActivated: cfg_SeasonMode = currentValue
        }
        ComboBox {
            id: timeCombo
            Kirigami.FormData.label: "Time of day:"
            visible: !root.carousel
            textRole: "text"; valueRole: "value"
            model: [
                { text: "Auto (sun-based)", value: "auto" },
                { text: "Morning", value: "morning" }, { text: "Day", value: "day" },
                { text: "Evening", value: "evening" }, { text: "Night", value: "night" }
            ]
            currentIndex: Math.max(0, indexOfValue(cfg_TimeMode))
            onActivated: cfg_TimeMode = currentValue
        }
        ColumnLayout {
            Kirigami.FormData.label: "Now showing:"
            visible: !root.carousel
            Image {
                Layout.preferredWidth: 256; Layout.preferredHeight: 144
                fillMode: Image.PreserveAspectCrop; asynchronous: true; cache: false
                source: "file://" + root.previewFolder + "/" + root.previewName()
                Rectangle {
                    anchors.fill: parent; color: "transparent"
                    border.color: Kirigami.Theme.disabledTextColor; border.width: 1
                    visible: parent.status !== Image.Ready
                    Label {
                        anchors.centerIn: parent
                        text: parent.parent.status === Image.Error ? "немає файлу" : "…"
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
            }
            Label { text: root.previewName(); font: Kirigami.Theme.smallFont; opacity: 0.8 }
        }

        // ---------- CAROUSEL ----------
        SpinBox {
            id: carouselSpin
            Kirigami.FormData.label: "Change every (minutes):"
            from: 1; to: 1440
            visible: root.carousel
        }
    }

    // чеклист кадрів для каруселі
    ColumnLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: root.carousel
        spacing: Kirigami.Units.smallSpacing

        RowLayout {
            Label { text: "Pick images (none = all 48):"; Layout.fillWidth: true }
            Button { text: "All"; onClicked: cfg_CarouselImages = L.allFiles() }
            Button { text: "None"; onClicked: cfg_CarouselImages = [] }
        }

        GridView {
            id: grid
            Layout.fillWidth: true
            Layout.preferredHeight: 320
            clip: true
            cellWidth: 150; cellHeight: 100
            model: L.allFiles()
            ScrollBar.vertical: ScrollBar {}
            delegate: Item {
                width: grid.cellWidth; height: grid.cellHeight
                required property string modelData
                Image {
                    anchors { fill: parent; margins: 3 }
                    fillMode: Image.PreserveAspectCrop; asynchronous: true; cache: false
                    source: "file://" + root.previewFolder + "/" + parent.modelData
                    Rectangle {
                        anchors.fill: parent
                        color: checkBox.checked ? "transparent" : "#99000000"
                        border.color: checkBox.checked ? Kirigami.Theme.highlightColor : "transparent"
                        border.width: 2
                    }
                }
                CheckBox {
                    id: checkBox
                    anchors { top: parent.top; right: parent.right; margins: 4 }
                    checked: cfg_CarouselImages.indexOf(parent.modelData) >= 0
                    onToggled: root.toggleCarousel(parent.modelData, checked)
                }
            }
        }
    }
}
