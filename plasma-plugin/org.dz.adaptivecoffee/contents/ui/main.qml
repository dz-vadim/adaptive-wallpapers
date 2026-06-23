import QtQuick

// Adaptive Coffee wallpaper: обирає кадр за поточними сезоном, часом доби
// і погодою. Сезон/час — з годинника (працює офлайн). Погода — з wttr.in;
// якщо мережі немає, погода обирається ВИПАДКОВО (реалістичний ухил).
Item {
    id: root

    // --- конфіг (із налаштувань плагіна; є дефолти) ---
    readonly property string folder:
        (wallpaper.configuration.Folder && wallpaper.configuration.Folder.length > 0)
        ? wallpaper.configuration.Folder
        : "/home/dz/Pictures/wallpapers_archive/wallpapers"
    readonly property string location: wallpaper.configuration.Location || ""
    readonly property int intervalMin:
        wallpaper.configuration.IntervalMinutes > 0 ? wallpaper.configuration.IntervalMinutes : 15

    property string weather: "clear"
    property string current: ""

    readonly property var seasons: ["winter", "spring", "summer", "autumn"]
    readonly property var times: ["morning", "day", "evening", "night"]
    readonly property var weathers: ["clear", "cloudy", "rain_snow"]

    function pad2(n) { return (n < 10 ? "0" : "") + n }

    function seasonIdx(month) {            // month 1..12
        if (month === 12 || month <= 2) return 0   // winter
        if (month <= 5) return 1                    // spring
        if (month <= 8) return 2                    // summer
        return 3                                    // autumn
    }
    function timeIdx(hour) {
        if (hour >= 6 && hour < 11) return 0   // morning
        if (hour >= 11 && hour < 17) return 1  // day
        if (hour >= 17 && hour < 21) return 2  // evening
        return 3                               // night
    }
    function fileFor(sI, tI, wI) {
        var num = sI * 12 + tI * 3 + wI + 1    // 1..48, як у генераторі
        return pad2(num) + "_" + seasons[sI] + "_" + times[tI] + "_" + weathers[wI] + ".png"
    }
    function mapWeatherCode(code) {
        if (code === 113) return "clear"
        if ([116, 119, 122, 143, 248, 260].indexOf(code) !== -1) return "cloudy"
        return "rain_snow"
    }
    // Офлайн-фолбек: випадкова погода з реалістичним ухилом.
    function randomWeather() {
        var r = Math.random()
        if (r < 0.50) return "clear"
        if (r < 0.85) return "cloudy"
        return "rain_snow"
    }

    // --- зображення + плавний crossfade ---
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
        if (base.source.toString() === "") {   // перший показ — без анімації
            base.source = url
            return
        }
        if (url === base.source.toString() && top.opacity === 0) return
        top.source = url
        fade.restart()
    }

    function update() {
        var now = new Date()
        var sI = seasonIdx(now.getMonth() + 1)
        var tI = timeIdx(now.getHours())
        var wI = weathers.indexOf(weather); if (wI < 0) wI = 0
        var path = folder + "/" + fileFor(sI, tI, wI)
        if (path !== current) { current = path; show(path) }
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
                    weather = mapWeatherCode(parseInt(j.current_condition[0].weatherCode))
                    ok = true
                }
            } catch (e) { ok = false }
            if (!ok) weather = randomWeather()   // немає мережі → випадково
            update()
        }
        try { xhr.open("GET", url); xhr.send() }
        catch (e) { weather = randomWeather(); update() }
    }

    Timer {
        interval: Math.max(1, intervalMin) * 60000
        running: true
        repeat: true
        onTriggered: fetchWeather()   // оновлюємо погоду + кадр щотакту
    }

    Component.onCompleted: { update(); fetchWeather() }
}
