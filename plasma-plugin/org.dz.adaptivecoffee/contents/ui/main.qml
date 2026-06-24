import QtQuick
import org.kde.plasma.plasmoid
import "logic.js" as L

// Adaptive Coffee wallpaper (Plasma 6).
// Режим "adaptive": кадр за сезоном + часом доби (за реальним сонцем) + погодою
//   (wttr.in з кешем; офлайн — випадково). Якщо файл відсутній — фолбек.
// Режим "carousel": циклічно міняє відмічені кадри (або всі 48) із заданим
//   інтервалом. Обидва режими — з плавним crossfade.
WallpaperItem {
    id: root

    // Фолбек, якщо Folder не задано: тека wallpapers/ у корені репо,
    // обчислена відносно цього файлу (працює при symlink-встановленні).
    readonly property string defaultFolder: {
        var u = Qt.resolvedUrl("../../../../wallpapers").toString()
        return u.replace(/^file:\/\//, "").replace(/\/+$/, "")
    }
    readonly property string folder:
        (configuration.Folder && configuration.Folder.length > 0)
        ? configuration.Folder
        : defaultFolder
    readonly property string location: configuration.Location || ""
    readonly property string mode: configuration.Mode || "adaptive"

    property string weather: "clear"
    property string current: ""
    property int sunrise: -1
    property int sunset: -1
    property double weatherTs: 0
    readonly property int weatherTtlMs: 30 * 60000

    // --- карусель ---
    readonly property var carouselList: {
        var sel = configuration.CarouselImages
        return (sel && sel.length > 0) ? sel : L.allFiles()
    }
    property int carouselPos: 0

    // черга кандидатів для adaptive-фолбеку
    property var _cands: []
    property int _idx: 0
    property string _pending: ""

    // === спільне: показ із crossfade ===
    Rectangle { anchors.fill: parent; color: "#101418" }
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

    // === ADAPTIVE: вибір із фолбеком ===
    Image {
        id: probe
        visible: false
        asynchronous: true
        cache: false
        onStatusChanged: {
            if (status === Image.Ready) { current = _pending; show(_pending) }
            else if (status === Image.Error) { _idx += 1; tryNext() }
        }
    }
    // Читаємо режим напряму з конфіга — щоб не залежати від порядку
    // оновлення біндингу `mode` під час сигналів зміни конфігу.
    function curMode() { return configuration.Mode || "adaptive" }

    function update() {
        if (curMode() === "carousel") return
        var sName = L.resolveSeason(configuration.SeasonMode)
        var tName = L.resolveTime(configuration.TimeMode, sunrise, sunset)
        var names = L.candidates(sName, tName, weather)
        _cands = names.map(function (n) { return folder + "/" + n })
        _idx = 0
        tryNext()
    }
    function tryNext() {
        if (_idx >= _cands.length) return
        _pending = _cands[_idx]
        if ("file://" + _pending === base.source.toString()) return
        probe.source = "file://" + _pending
    }

    // погода з кешем
    function maybeRefresh() {
        if (curMode() === "carousel") return
        var wmode = configuration.WeatherMode || "auto"
        if (wmode !== "auto") { weather = wmode; update(); return }
        if (Date.now() - weatherTs > weatherTtlMs || sunrise < 0) fetchWeather()
        else update()
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
                    var astro = j.weather[0].astronomy[0]
                    sunrise = L.parseClock(astro.sunrise)
                    sunset = L.parseClock(astro.sunset)
                    ok = true
                }
            } catch (e) { ok = false }
            if (!ok) weather = L.randomWeather()
            weatherTs = Date.now()
            update()
        }
        try { xhr.open("GET", url); xhr.send() }
        catch (e) { weather = L.randomWeather(); weatherTs = Date.now(); update() }
    }

    // === CAROUSEL ===
    function carouselShowAt(i) {
        var list = carouselList
        if (!list || list.length === 0) return
        carouselPos = ((i % list.length) + list.length) % list.length
        var name = list[carouselPos]
        current = name
        show(folder + "/" + name)
    }
    function carouselStep() { carouselShowAt(carouselPos + 1) }

    // === диспетчер ===
    function apply() {
        if (curMode() === "carousel") {
            carouselShowAt(0)
        } else {
            update()        // показати кадр ОДРАЗУ (з відомою/дефолтною погодою)
            maybeRefresh()  // потім уточнити погоду й перемалювати за потреби
        }
    }

    Timer {                        // adaptive: перевірка меж щохвилини
        interval: 60000
        running: root.mode !== "carousel"
        repeat: true
        onTriggered: maybeRefresh()
    }
    Timer {                        // carousel: зміна кадру за інтервалом
        interval: Math.max(1, configuration.CarouselIntervalMinutes || 30) * 60000
        running: root.mode === "carousel"
        repeat: true
        onTriggered: carouselStep()
    }

    Connections {
        target: root.configuration
        function onModeChanged() { apply() }
        function onSeasonModeChanged() { if (root.mode !== "carousel") update() }
        function onTimeModeChanged() { if (root.mode !== "carousel") update() }
        function onWeatherModeChanged() { if (root.mode !== "carousel") { weatherTs = 0; maybeRefresh() } }
        function onFolderChanged() { apply() }
        function onLocationChanged() { if (root.mode !== "carousel") { weatherTs = 0; maybeRefresh() } }
        function onCarouselImagesChanged() { if (root.mode === "carousel") carouselShowAt(0) }
    }

    Component.onCompleted: apply()
}
