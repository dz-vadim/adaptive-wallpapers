.pragma library
// Спільна логіка для main.qml (фон) і config.qml (прев'ю) — щоб вибір кадру
// був однаковий в обох місцях.

var SEASONS = ["winter", "spring", "summer", "autumn"]
var TIMES = ["morning", "day", "evening", "night"]
var WEATHERS = ["clear", "cloudy", "rain_snow"]

function pad2(n) { return (n < 10 ? "0" : "") + n }

function seasonIdx(month) {            // month 1..12
    if (month === 12 || month <= 2) return 0   // winter
    if (month <= 5) return 1                    // spring
    if (month <= 8) return 2                    // summer
    return 3                                    // autumn
}

// Фіксовані межі (фолбек, коли немає даних про сонце / офлайн).
function timeIdxFixed(hour) {
    if (hour >= 6 && hour < 11) return 0   // morning
    if (hour >= 11 && hour < 17) return 1  // day
    if (hour >= 17 && hour < 21) return 2  // evening
    return 3                               // night
}

// Межі за реальним сонцем: srMin/ssMin — схід/захід у хвилинах від півночі.
function timeIdxSun(nowMin, srMin, ssMin) {
    if (srMin < 0 || ssMin < 0 || ssMin <= srMin) return -1   // невалідні дані
    var span = ssMin - srMin
    var morningEnd = srMin + span * 0.35      // ранок ~перша третина дня
    var dayEnd = ssMin - 90                    // день до ~1.5 год перед заходом
    var eveningEnd = ssMin + 45                // вечір ~золота година навколо заходу
    if (nowMin >= srMin && nowMin < morningEnd) return 0
    if (nowMin >= morningEnd && nowMin < dayEnd) return 1
    if (nowMin >= dayEnd && nowMin < eveningEnd) return 2
    return 3                                   // ніч
}

// "06:13 AM" / "20:47" → хвилини від півночі; -1 при невдачі.
function parseClock(s) {
    if (!s) return -1
    var m = ("" + s).match(/(\d{1,2}):(\d{2})\s*(AM|PM)?/i)
    if (!m) return -1
    var h = parseInt(m[1]), min = parseInt(m[2])
    var ap = m[3] ? m[3].toUpperCase() : ""
    if (ap === "PM" && h < 12) h += 12
    if (ap === "AM" && h === 12) h = 0
    return h * 60 + min
}

function fileName(sI, tI, wI) {
    var num = sI * 12 + tI * 3 + wI + 1    // 1..48, як у генераторі
    return pad2(num) + "_" + SEASONS[sI] + "_" + TIMES[tI] + "_" + WEATHERS[wI] + ".png"
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

// "auto" → з годинника; інакше — задане користувачем.
function resolveSeason(mode) {
    if (mode && mode !== "auto") return mode
    return SEASONS[seasonIdx(new Date().getMonth() + 1)]
}
// Час доби: примусовий → за сонцем (якщо є дані) → фіксовані межі.
function resolveTime(mode, srMin, ssMin) {
    if (mode && mode !== "auto") return mode
    var now = new Date()
    var nowMin = now.getHours() * 60 + now.getMinutes()
    var i = -1
    if (srMin !== undefined && ssMin !== undefined)
        i = timeIdxSun(nowMin, srMin, ssMin)
    if (i < 0) i = timeIdxFixed(now.getHours())
    return TIMES[i]
}

// Усі 48 імен файлів у порядку нумерації (для каруселі/чеклиста).
function allFiles() {
    var out = []
    for (var s = 0; s < SEASONS.length; s++)
        for (var t = 0; t < TIMES.length; t++)
            for (var w = 0; w < WEATHERS.length; w++)
                out.push(fileName(s, t, w))
    return out
}

// Впорядкований список кандидатів (імена файлів) з фолбеком:
// точний → той самий сезон+час, інша погода → будь-що в межах сезону.
function candidates(sName, tName, wName) {
    var sI = SEASONS.indexOf(sName)
    var tI = TIMES.indexOf(tName)
    var wI = WEATHERS.indexOf(wName)
    if (sI < 0) sI = 0
    if (tI < 0) tI = 0
    if (wI < 0) wI = 0
    var list = []
    function add(s, t, w) {
        var f = fileName(s, t, w)
        if (list.indexOf(f) < 0) list.push(f)
    }
    add(sI, tI, wI)
    for (var w = 0; w < WEATHERS.length; w++) add(sI, tI, w)
    for (var t = 0; t < TIMES.length; t++)
        for (var w2 = 0; w2 < WEATHERS.length; w2++) add(sI, t, w2)
    return list
}
