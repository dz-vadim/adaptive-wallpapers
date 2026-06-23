import QtQuick
import org.kde.plasma.plasmoid
import "logic.js" as L

// Adaptive Coffee wallpaper (Plasma 6): кадр за сезоном, часом доби і погодою.
// Сезон/час — з годинника (офлайн), або примусово з налаштувань. Погода — з
// wttr.in; без мережі обирається ВИПАДКОВО. Якщо файл відсутній — фолбек на
// найближчий доступний (без чорного екрана).
WallpaperItem {
    id: root

    readonly property string folder:
        (configuration.Folder && configuration.Folder.length > 0)
        ? configuration.Folder
        : "/home/dz/Pictures/wallpapers_archive/wallpapers"
    readonly property string location: configuration.Location || ""
    readonly property int intervalMin:
        configuration.IntervalMinutes > 0 ? configuration.IntervalMinutes : 15

    property string weather: "clear"
    property string current: ""        // активний файл (для прев'ю/діагностики)

    // черга кандидатів для фолбеку
    property var _cands: []
    property int _idx: 0
    property string _pending: ""

    // --- вибір і завантаження з фолбеком ---
    function update() {
        var sName = L.resolveSeason(configuration.SeasonMode)
        var tName = L.resolveTime(configuration.TimeMode)
        var names = L.candidates(sName, tName, weather)
        _cands = names.map(function (n) { return folder + "/" + n })
        _idx = 0
        tryNext()
    }
    function tryNext() {
        if (_idx >= _cands.length) return         // нічого не знайшли — лишаємо як є
        _pending = _cands[_idx]
        if ("file://" + _pending === base.source.toString()) return  // вже показано
        probe.source = "file://" + _pending
    }

    // прихований лоадер: перевіряє, чи файл вантажиться, перш ніж показати
    Image {
        id: probe
        visible: false
        asynchronous: true
        cache: false
        onStatusChanged: {
            if (status === Image.Ready) {
                current = _pending
                show(_pending)
            } else if (status === Image.Error) {
                _idx += 1
                tryNext()
            }
        }
    }

    // --- зображення + плавний crossfade ---
    Rectangle { anchors.fill: parent; color: "#101418" }   // фон, поки нема картинки
    Image {
        id: base
        anchors.fill: parent
        fillMode: Image.PreserveAspectCrop
        cache: false
        asynchronous: true
    }
    Image {
        id: top
        anchors.fill: parent
        fillMode: Image.PreserveAspectCrop
        cache: false
        asynchronous: true
        opacity: 0
    }
    NumberAnimation {
        id: fade
        target: top; property: "opacity"
        from: 0; to: 1; duration: 1200; easing.type: Easing.InOutQuad
        onFinished: { base.source = top.source; top.opacity = 0 }
    }
    function show(path) {
        var url = "file://" + path
        if (base.source.toString() === "") { base.source = url; return }
        if (url === base.source.toString() && top.opacity === 0) return
        top.source = url
        fade.restart()
    }

    // --- погода ---
    function refresh() {
        var mode = configuration.WeatherMode || "auto"
        if (mode !== "auto") { weather = mode; update(); return }
        fetchWeather()
    }
    function fetchWeather() {
        var url = "https://wttr.in/" + encodeURIComponent(location) + "?format=j1"
        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== XMLHttpRequest.DONE) return
            var ok = false
            try {
                if (xhr.status === 200) {
                    var j = JSON.parse(xhr.responseText)
                    weather = L.mapWeatherCode(parseInt(j.current_condition[0].weatherCode))
                    ok = true
                }
            } catch (e) { ok = false }
            if (!ok) weather = L.randomWeather()
            update()
        }
        try { xhr.open("GET", url); xhr.send() }
        catch (e) { weather = L.randomWeather(); update() }
    }

    Timer {
        interval: Math.max(1, intervalMin) * 60000
        running: true
        repeat: true
        onTriggered: refresh()
    }
    // реагуємо на зміну примусових налаштувань одразу
    Connections {
        target: root.configuration
        function onSeasonModeChanged() { update() }
        function onTimeModeChanged() { update() }
        function onWeatherModeChanged() { refresh() }
        function onFolderChanged() { update() }
    }

    Component.onCompleted: { update(); refresh() }
}
