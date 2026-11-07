/* ==========================================================================
   Логика панели водителя такси
   - статус и профиль авто
   - карта Leaflet (Москва) и GPS-трек через watchPosition
   - пробег: восстанавливается с сервера, точки каждые 75 м
   - деньги: заказы, расходы, чистая прибыль
   - завершение смены с сохранением итогов в историю
   ========================================================================== */

"use strict";

const STATUS_META = {
  free: { label: "Свободен" },
  busy: { label: "На заказе" },
  offline: { label: "Не на линии" },
};

const EXPENSE_LABELS = {
  fuel: "Бензин",
  wash: "Мойка",
  food: "Еда",
  fine: "Штраф",
};

const MOSCOW_CENTER = [55.7558, 37.6173];

const WEATHER_URL =
  "https://api.open-meteo.com/v1/forecast?latitude=55.7558&longitude=37.6173&current=temperature_2m,precipitation,weather_code,wind_speed_10m&timezone=Europe/Moscow";
const WEATHER_REFRESH_MS = 15 * 60 * 1000;

const WMO_WEATHER = Object.freeze({
  0: { icon: "☀️", label: "Ясно" },
  1: { icon: "🌤️", label: "Малооблачно" },
  2: { icon: "⛅", label: "Переменная облачность" },
  3: { icon: "☁️", label: "Пасмурно" },
  45: { icon: "🌫️", label: "Туман" },
  48: { icon: "🌫️", label: "Иней, туман" },
  51: { icon: "🌦️", label: "Слабая морось" },
  53: { icon: "🌦️", label: "Морось" },
  55: { icon: "🌧️", label: "Сильная морось" },
  56: { icon: "🌧️", label: "Ледяная морось" },
  57: { icon: "🌧️", label: "Сильная ледяная морось" },
  61: { icon: "🌦️", label: "Небольшой дождь" },
  63: { icon: "🌧️", label: "Дождь" },
  65: { icon: "🌧️", label: "Сильный дождь" },
  66: { icon: "🌧️", label: "Ледяной дождь" },
  67: { icon: "🌧️", label: "Сильный ледяной дождь" },
  71: { icon: "🌨️", label: "Небольшой снег" },
  73: { icon: "❄️", label: "Снег" },
  75: { icon: "❄️", label: "Сильный снег" },
  77: { icon: "🌨️", label: "Снежная крупа" },
  80: { icon: "🌦️", label: "Ливень" },
  81: { icon: "🌧️", label: "Сильный ливень" },
  82: { icon: "⛈️", label: "Очень сильный ливень" },
  85: { icon: "🌨️", label: "Снегопад" },
  86: { icon: "❄️", label: "Сильный снегопад" },
  95: { icon: "⛈️", label: "Гроза" },
  96: { icon: "⛈️", label: "Гроза с градом" },
  99: { icon: "⛈️", label: "Сильная гроза с градом" },
});

const els = {
  body: document.body,
  chip: document.getElementById("status-chip"),
  chipLabel: document.getElementById("status-chip-label"),
  carForm: document.getElementById("car-form"),
  brand: document.getElementById("car-brand"),
  plate: document.getElementById("car-plate"),
  saveButton: document.getElementById("car-save"),
  statusButtons: Array.from(document.querySelectorAll(".status-btn")),
  toast: document.getElementById("toast"),
  map: document.getElementById("map"),
  trackButton: document.getElementById("track-btn"),
  geoStatus: document.getElementById("geo-status"),
  geoAlert: document.getElementById("geo-alert"),
  geoHelp: document.getElementById("geo-help"),
  resetMileageButton: document.getElementById("reset-mileage"),
  totalDistance: document.getElementById("total-distance"),
  lastDistance: document.getElementById("last-distance"),
  markerCount: document.getElementById("marker-count"),
  mileageHint: document.getElementById("mileage-hint"),
  shiftStarted: document.getElementById("shift-started"),
  revenue: document.getElementById("revenue"),
  expensesTotal: document.getElementById("expenses-total"),
  profit: document.getElementById("profit"),
  addOrderButton: document.getElementById("add-order-btn"),
  addExpenseButton: document.getElementById("add-expense-btn"),
  orderForm: document.getElementById("order-form"),
  orderAmount: document.getElementById("order-amount"),
  expenseForm: document.getElementById("expense-form"),
  expenseAmount: document.getElementById("expense-amount"),
  expenseCategory: document.getElementById("expense-category"),
  finishShiftButton: document.getElementById("finish-shift"),
  historyButton: document.getElementById("history-btn"),
  historyScreen: document.getElementById("history-screen"),
  historyClose: document.getElementById("history-close"),
  historyList: document.getElementById("history-list"),
  historyEmpty: document.getElementById("history-empty"),
  historyLoading: document.getElementById("history-loading"),
  weather: document.getElementById("weather"),
  weatherIcon: document.getElementById("weather-icon"),
  weatherTemp: document.getElementById("weather-temp"),
  weatherDesc: document.getElementById("weather-desc"),
  weatherWind: document.getElementById("weather-wind"),
  driveToggle: document.getElementById("drive-toggle"),
  driveExit: document.getElementById("drive-exit"),
  statusCard: document.querySelector(".status-card"),
  fabOrder: document.getElementById("fab-order"),
  fabExpense: document.getElementById("fab-expense"),
  moneyModal: document.getElementById("money-modal"),
  moneyModalTitle: document.getElementById("money-modal-title"),
  moneyModalSubtitle: document.getElementById("money-modal-subtitle"),
  moneyModalClose: document.getElementById("money-modal-close"),
  expenseCategories: document.getElementById("expense-categories"),
  amountDisplay: document.getElementById("amount-display"),
  amountHint: document.getElementById("amount-hint"),
  keypad: document.getElementById("keypad"),
  moneySubmit: document.getElementById("money-submit"),
};

const emptyShift = () => ({
  started_at: null,
  total_meters: 0,
  markers: [],
  revenue: 0,
  orders: [],
  expenses: [],
});

const current = {
  shift: emptyShift(),
};

const TRACK_MIN_METERS = 75;
const TRACK_MAX_ACCURACY_M = 80;

const geo = {
  watchId: null,
  watching: false,
  lastStored: null,
  pendingBreak: false,
  sending: false,
  accuracy: null,
  currentDot: null,
  accuracyCircle: null,
  centered: false,
};

let map = null;
let routeLayers = [];
const weatherState = {
  loading: false,
  loaded: false,
  updatedAt: 0,
};

let wakeLock = null;
let weatherTimer = null;
let carSaving = false;
let statusSaving = false;
let moneySaving = false;
let shiftFinishing = false;
let toastTimer = null;

/* --------------------------------------------------------------------------
   Форматирование и запросы
   -------------------------------------------------------------------------- */

const moneyFormatter = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "RUB",
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

function formatMoney(value) {
  const amount = Number(value);
  return moneyFormatter.format(Number.isFinite(amount) ? amount : 0);
}

function formatKilometers(meters) {
  return `${(Number(meters) / 1000).toFixed(2).replace(".", ",")} км`;
}

function formatSegment(meters) {
  if (meters === null || meters === undefined) return "—";
  if (meters < 1000) return `${Math.round(meters)} м`;
  return formatKilometers(meters);
}

function formatStarted(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return `Смена с ${date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}`;
}

function showToast(message, kind = "info") {
  if (!els.toast) return;

  els.toast.textContent = message;
  els.toast.dataset.kind = kind;
  els.toast.hidden = false;

  if (toastTimer !== null) {
    window.clearTimeout(toastTimer);
  }
  toastTimer = window.setTimeout(() => {
    els.toast.hidden = true;
    toastTimer = null;
  }, 3400);
}

async function requestJSON(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    ...options,
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const message = data && data.error ? data.error : `Ошибка сервера (${response.status})`;
    throw new Error(message);
  }

  return data;
}

/* --------------------------------------------------------------------------
   Погода (Open-Meteo)
   -------------------------------------------------------------------------- */

function describeWeather(code) {
  const numeric = Number(code);
  if (Number.isFinite(numeric) && WMO_WEATHER[numeric]) {
    return WMO_WEATHER[numeric];
  }
  return { icon: "🌡️", label: "Нет данных" };
}

function isDemandWeather(code) {
  const numeric = Number(code);
  if (!Number.isFinite(numeric)) return false;

  return (
    (numeric >= 51 && numeric <= 67) ||
    (numeric >= 71 && numeric <= 77) ||
    (numeric >= 80 && numeric <= 86) ||
    (numeric >= 95 && numeric <= 99)
  );
}

function renderWeather(current) {
  if (!els.weather) return;

  const code = Number(current.weather_code);
  const temperature = Number(current.temperature_2m);
  const wind = Number(current.wind_speed_10m);

  if (!Number.isFinite(temperature) || !Number.isFinite(wind)) {
    throw new Error("Open-Meteo: нет температуры или ветра");
  }

  const info = describeWeather(code);
  const alert = isDemandWeather(code);
  const tempText = `${Math.round(temperature)}°C`;
  const windText = `Ветер ${Math.round(wind)} км/ч`;
  const updated = new Date().toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });

  els.weatherIcon.textContent = info.icon;
  els.weatherTemp.textContent = tempText;
  els.weatherDesc.textContent = info.label;
  els.weatherWind.textContent = windText;
  els.weather.dataset.state = "ready";
  els.weather.classList.remove("is-error", "is-stale");
  els.weather.classList.toggle("is-alert", alert);
  els.weather.title =
    `Погода в Москве: ${info.label}, ${tempText}, ${windText.toLowerCase()}. ` +
    `Обновлено в ${updated}.` +
    (alert ? " Дождь или снег — возможен повышенный спрос." : "");

  weatherState.loaded = true;
  weatherState.updatedAt = Date.now();
}

function renderWeatherError() {
  if (!els.weather) return;

  if (weatherState.loaded) {
    // Последние успешные данные остаются на экране.
    els.weather.classList.add("is-stale");
    els.weather.title =
      "Не удалось обновить погоду. Показаны последние полученные данные.";
    return;
  }

  els.weather.dataset.state = "error";
  els.weather.classList.remove("is-alert");
  els.weather.classList.add("is-error");
  els.weatherIcon.textContent = "🌐";
  els.weatherTemp.textContent = "—";
  els.weatherDesc.textContent = "Погода недоступна";
  els.weatherWind.textContent = "Нет связи";
  els.weather.title =
    "Не удалось загрузить погоду. Приложение продолжит работать без неё.";
}

async function loadWeather() {
  if (weatherState.loading) return;

  weatherState.loading = true;
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(WEATHER_URL, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Open-Meteo ответил HTTP ${response.status}`);
    }

    const data = await response.json();
    if (!data || !data.current) {
      throw new Error("Open-Meteo: в ответе нет блока current");
    }

    renderWeather(data.current);
  } catch (error) {
    console.warn("Не удалось загрузить погоду Open-Meteo:", error);
    renderWeatherError();
  } finally {
    window.clearTimeout(timeoutId);
    weatherState.loading = false;
  }
}

function startWeatherUpdates() {
  loadWeather();
  if (weatherTimer !== null) {
    window.clearInterval(weatherTimer);
  }
  weatherTimer = window.setInterval(loadWeather, WEATHER_REFRESH_MS);
}

/* --------------------------------------------------------------------------
   Статус
   -------------------------------------------------------------------------- */

function applyStatus(status) {
  const meta = STATUS_META[status] || STATUS_META.offline;
  const normalized = STATUS_META[status] ? status : "offline";

  els.body.dataset.status = normalized;

  if (els.chip) {
    els.chip.dataset.status = normalized;
  }
  if (els.chipLabel) {
    els.chipLabel.textContent = meta.label;
  }

  for (const button of els.statusButtons) {
    const isActive = button.dataset.status === normalized;
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  }

  document.title = `${meta.label} · Такси — панель водителя`;
}

function setStatusButtonsDisabled(disabled) {
  for (const button of els.statusButtons) {
    button.disabled = disabled;
  }
}

async function saveStatus(status) {
  if (statusSaving || !STATUS_META[status]) return;

  statusSaving = true;
  setStatusButtonsDisabled(true);

  try {
    const state = await requestJSON("/api/status", {
      method: "POST",
      body: JSON.stringify({ status }),
    });
    applyStatus(state.status);
    showToast(`Статус обновлён: ${STATUS_META[state.status].label}`);
  } catch (error) {
    showToast(error instanceof Error ? error.message : "Не удалось сохранить статус", "error");
  } finally {
    statusSaving = false;
    setStatusButtonsDisabled(false);
  }
}

/* --------------------------------------------------------------------------
   Профиль авто
   -------------------------------------------------------------------------- */

function applyCar(state) {
  if (!state) return;
  if (els.brand && typeof state.car_brand === "string") {
    els.brand.value = state.car_brand;
  }
  if (els.plate && typeof state.car_plate === "string") {
    els.plate.value = state.car_plate;
  }
}

async function saveCar(event) {
  event.preventDefault();
  if (carSaving) return;

  const carBrand = els.brand ? els.brand.value.trim() : "";
  const carPlate = els.plate ? els.plate.value.trim() : "";

  carSaving = true;
  if (els.saveButton) {
    els.saveButton.disabled = true;
    els.saveButton.textContent = "Сохраняем…";
  }

  try {
    const state = await requestJSON("/api/car", {
      method: "POST",
      body: JSON.stringify({ car_brand: carBrand, car_plate: carPlate }),
    });
    applyCar(state);
    showToast("Данные автомобиля сохранены");
  } catch (error) {
    showToast(error instanceof Error ? error.message : "Не удалось сохранить данные авто", "error");
  } finally {
    carSaving = false;
    if (els.saveButton) {
      els.saveButton.disabled = false;
      els.saveButton.textContent = "Сохранить";
    }
  }
}

/* --------------------------------------------------------------------------
   Пробег и GPS-трек
   -------------------------------------------------------------------------- */

function haversineMeters(from, to) {
  const radius = 6371000;
  const toRadians = (degrees) => (degrees * Math.PI) / 180;
  const dLat = toRadians(to.lat - from.lat);
  const dLng = toRadians(to.lng - from.lng);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(from.lat)) *
      Math.cos(toRadians(to.lat)) *
      Math.sin(dLng / 2) ** 2;

  return 2 * radius * Math.asin(Math.min(1, Math.sqrt(a)));
}

function drawRoute(fitToRoute = false) {
  if (map === null) return;

  for (const layer of routeLayers) {
    layer.remove();
  }
  routeLayers = [];

  const markers = current.shift.markers;
  const segments = [];
  let segment = [];

  for (const point of markers) {
    if (point.break && segment.length > 0) {
      segments.push(segment);
      segment = [];
    }
    segment.push([point.lat, point.lng]);
  }
  if (segment.length > 0) segments.push(segment);

  for (const points of segments) {
    if (points.length < 2) continue;
    const line = window.L.polyline(points, {
      color: "#3b82f6",
      weight: 4,
      opacity: 0.9,
      lineCap: "round",
      lineJoin: "round",
    }).addTo(map);
    routeLayers.push(line);
  }

  if (markers.length > 0) {
    const startMarker = window.L.circleMarker([markers[0].lat, markers[0].lng], {
      radius: 7,
      color: "#ffffff",
      weight: 3,
      fillColor: "#22c55e",
      fillOpacity: 1,
    })
      .addTo(map)
      .bindPopup("Старт маршрута");
    routeLayers.push(startMarker);
  }

  if (fitToRoute && markers.length > 0) {
    const latlngs = markers.map((point) => [point.lat, point.lng]);
    if (latlngs.length === 1) {
      map.setView(latlngs[0], 15);
    } else {
      map.fitBounds(latlngs, { padding: [40, 40], maxZoom: 16 });
    }
  }
}

function updateMileageUI() {
  const markers = current.shift.markers;
  const hasPoints = markers.length > 0;
  const lastPoint = markers[markers.length - 1];
  const lastSegment =
    lastPoint && Number(lastPoint.segment_m) > 0 ? lastPoint.segment_m : null;

  if (els.totalDistance) {
    els.totalDistance.textContent = formatKilometers(current.shift.total_meters);
  }
  if (els.lastDistance) {
    els.lastDistance.textContent = formatSegment(lastSegment);
  }
  if (els.markerCount) {
    els.markerCount.textContent = String(markers.length);
  }
  if (els.resetMileageButton) {
    els.resetMileageButton.disabled =
      !hasPoints && Number(current.shift.total_meters) === 0;
  }
  if (els.trackButton) {
    els.trackButton.classList.toggle("is-active", geo.watching);
    els.trackButton.setAttribute("aria-pressed", geo.watching ? "true" : "false");
    els.trackButton.textContent = geo.watching
      ? "Остановить отслеживание"
      : "Начать отслеживание";
  }
  if (els.mileageHint) {
    if (map === null) {
      els.mileageHint.textContent =
        "Карта недоступна: проверьте подключение к CDN Leaflet.";
    } else if (geo.watching) {
      els.mileageHint.textContent = "Маршрут пишется автоматически: точка каждые 75 м.";
    } else if (hasPoints) {
      els.mileageHint.textContent =
        "Отслеживание остановлено. Продолжите, чтобы дописать маршрут.";
    } else {
      els.mileageHint.textContent =
        "Нажмите «Начать отслеживание» и разрешите доступ к геолокации.";
    }
  }
}

function setGeoStatus(text, kind = "") {
  if (!els.geoStatus) return;
  els.geoStatus.textContent = text;
  els.geoStatus.classList.toggle("is-error", kind === "error");
  els.geoStatus.classList.toggle("is-active", kind === "active");
}

function showGeoAlert(message, openHelp = false) {
  if (els.geoAlert) {
    els.geoAlert.textContent = message;
    els.geoAlert.hidden = false;
  }
  if (openHelp && els.geoHelp) {
    els.geoHelp.open = true;
  }
}

function hideGeoAlert() {
  if (els.geoAlert) {
    els.geoAlert.hidden = true;
    els.geoAlert.textContent = "";
  }
}

async function requestWakeLock() {
  if (
    !("wakeLock" in navigator) ||
    !navigator.wakeLock ||
    typeof navigator.wakeLock.request !== "function"
  ) {
    console.warn(
      "Screen Wake Lock API не поддерживается: экран планшета может погаснуть во время отслеживания."
    );
    return;
  }

  if (wakeLock !== null && !wakeLock.released) return;

  try {
    const sentinel = await navigator.wakeLock.request("screen");

    if (!geo.watching) {
      await sentinel.release();
      return;
    }

    wakeLock = sentinel;
    wakeLock.addEventListener("release", () => {
      if (wakeLock === sentinel) {
        wakeLock = null;
      }
      if (geo.watching) {
        console.warn(
          "Screen Wake Lock снят браузером. Блокировка будет запрошена снова при возврате на вкладку."
        );
      }
    });
  } catch (error) {
    wakeLock = null;
    console.warn("Не удалось включить Screen Wake Lock:", error);
  }
}

async function releaseWakeLock() {
  const sentinel = wakeLock;
  wakeLock = null;

  if (sentinel === null) return;

  try {
    await sentinel.release();
  } catch (error) {
    console.warn("Не удалось освободить Screen Wake Lock:", error);
  }
}

function updateCurrentPosition(latlng, accuracy) {
  if (map === null) return;

  const point = [latlng.lat, latlng.lng];
  const radius = Math.max(Number(accuracy) || 0, 5);

  if (geo.currentDot === null) {
    geo.currentDot = window.L.circleMarker(point, {
      radius: 8,
      color: "#ffffff",
      weight: 3,
      fillColor: "#3b82f6",
      fillOpacity: 1,
      zIndexOffset: 1000,
    }).addTo(map);
  } else {
    geo.currentDot.setLatLng(point);
  }

  if (geo.accuracyCircle === null) {
    geo.accuracyCircle = window.L.circle(point, {
      radius,
      color: "#3b82f6",
      weight: 1,
      opacity: 0.5,
      fillColor: "#3b82f6",
      fillOpacity: 0.08,
      interactive: false,
    }).addTo(map);
  } else {
    geo.accuracyCircle.setLatLng(point);
    geo.accuracyCircle.setRadius(radius);
  }
}

async function sendTrackPoint(latlng, newSegment) {
  geo.sending = true;
  setGeoStatus("Сохраняем точку маршрута…", "active");

  try {
    const data = await requestJSON("/api/track", {
      method: "POST",
      body: JSON.stringify({
        lat: latlng.lat,
        lng: latlng.lng,
        new_segment: newSegment,
      }),
    });

    geo.pendingBreak = false;
    renderShift(data.state.shift);

    const total = Number(data.state.shift.total_meters) || 0;
    const accuracyText = Number.isFinite(geo.accuracy)
      ? ` ±${Math.round(geo.accuracy)} м`
      : "";
    setGeoStatus(
      `GPS активен${accuracyText} · ${formatKilometers(total)}`,
      "active"
    );
    hideGeoAlert();
  } catch (error) {
    setGeoStatus("Не удалось сохранить точку маршрута", "error");
    showGeoAlert(
      "Точка не сохранилась на сервере. Проверьте, что приложение запущено, и продолжите движение."
    );
  } finally {
    geo.sending = false;
  }
}

function onGeoSuccess(position) {
  if (!geo.watching) return;

  const accuracy = Number(position.coords.accuracy) || 0;
  const latlng = {
    lat: position.coords.latitude,
    lng: position.coords.longitude,
  };

  geo.accuracy = accuracy;
  updateCurrentPosition(latlng, accuracy);
  hideGeoAlert();

  if (!geo.centered && map !== null) {
    map.setView([latlng.lat, latlng.lng], 16);
    geo.centered = true;
  }

  if (accuracy > TRACK_MAX_ACCURACY_M) {
    setGeoStatus(
      `GPS: точность ±${Math.round(accuracy)} м — ждём улучшения сигнала`,
      "active"
    );
    return;
  }

  if (geo.sending) return;

  const last = geo.lastStored;
  const firstInSession = last === null || geo.pendingBreak;

  if (!firstInSession) {
    const distance = haversineMeters(last, latlng);
    if (distance < TRACK_MIN_METERS) {
      const left = Math.max(0, Math.ceil(TRACK_MIN_METERS - distance));
      setGeoStatus(
        `GPS активен · ±${Math.round(accuracy)} м · до точки ${left} м`,
        "active"
      );
      return;
    }
  }

  const hasRoute = current.shift.markers.length > 0;
  sendTrackPoint(latlng, firstInSession && hasRoute);
}

function onGeoError(error) {
  if (error && error.code === 1) {
    stopTracking(true);
    setGeoStatus("Доступ к геолокации запрещён", "error");
    showGeoAlert(
      "Браузер запретил доступ к геолокации. Разрешите его в настройках сайта и нажмите «Начать отслеживание» снова.",
      true
    );
    return;
  }

  if (error && error.code === 2) {
    setGeoStatus("GPS недоступен: включите геолокацию на устройстве", "error");
    showGeoAlert(
      "Не удалось определить местоположение. Включите GPS/геолокацию на планшете и проверьте, что приложение открыто по HTTPS или localhost."
    );
    return;
  }

  setGeoStatus("Не удалось получить координаты. Ждём сигнал GPS…", "error");
}

async function startTracking() {
  if (geo.watching) return;

  hideGeoAlert();

  if (map === null) {
    setGeoStatus("Карта недоступна — отслеживание не запустить", "error");
    return;
  }

  if (!window.isSecureContext) {
    setGeoStatus("Геолокация заблокирована браузером", "error");
    showGeoAlert(
      "Геолокация работает только по HTTPS или на localhost. По локальному IP браузер её блокирует — откройте приложение по http://127.0.0.1:5000 или настройте HTTPS.",
      true
    );
    return;
  }

  if (!("geolocation" in navigator)) {
    setGeoStatus("Браузер не поддерживает геолокацию", "error");
    showGeoAlert(
      "Этот браузер не поддерживает HTML5 Geolocation. Откройте приложение в Chrome или Safari.",
      true
    );
    return;
  }

  if (navigator.permissions && navigator.permissions.query) {
    try {
      const permission = await navigator.permissions.query({ name: "geolocation" });
      if (permission.state === "denied") {
        setGeoStatus("Доступ к геолокации запрещён", "error");
        showGeoAlert(
          "Браузер уже запретил доступ к геолокации для этого сайта. Разрешите его в настройках сайта и нажмите «Начать отслеживание» снова.",
          true
        );
        return;
      }
    } catch {
      // Permissions API может быть недоступен — просто продолжаем.
    }
  }

  geo.watching = true;
  geo.pendingBreak = current.shift.markers.length > 0;
  geo.accuracy = null;
  geo.centered = false;

  setGeoStatus("Ожидаем разрешение и сигнал GPS…", "active");
  updateMileageUI();
  await requestWakeLock();

  try {
    geo.watchId = navigator.geolocation.watchPosition(
      onGeoSuccess,
      onGeoError,
      {
        enableHighAccuracy: true,
        timeout: 20000,
        maximumAge: 5000,
      }
    );
  } catch (error) {
    geo.watching = false;
    await releaseWakeLock();
    setGeoStatus("Не удалось запустить GPS", "error");
    showGeoAlert("Не удалось запустить отслеживание. Проверьте разрешения браузера.");
    updateMileageUI();
  }
}

function stopTracking(silent = false) {
  if (geo.watchId !== null && "geolocation" in navigator) {
    navigator.geolocation.clearWatch(geo.watchId);
  }

  geo.watchId = null;
  geo.watching = false;
  geo.pendingBreak = false;
  releaseWakeLock();

  if (geo.accuracyCircle !== null) {
    geo.accuracyCircle.remove();
    geo.accuracyCircle = null;
  }

  setGeoStatus(silent ? "Отслеживание выключено" : "Отслеживание остановлено");
  updateMileageUI();
}

function toggleTracking() {
  if (geo.watching) {
    stopTracking();
    showToast("Отслеживание остановлено");
  } else {
    startTracking();
  }
}

async function resetMileage() {
  try {
    const data = await requestJSON("/api/mileage/reset", { method: "POST" });
    renderShift(data.state.shift);
    geo.lastStored = null;
    geo.pendingBreak = false;

    if (!geo.watching && geo.currentDot !== null) {
      geo.currentDot.remove();
      geo.currentDot = null;
    }
    if (geo.accuracyCircle !== null) {
      geo.accuracyCircle.remove();
      geo.accuracyCircle = null;
    }

    showToast("Пробег сброшен, маршрут очищен");
  } catch (error) {
    showToast(
      error instanceof Error ? error.message : "Не удалось сбросить пробег",
      "error"
    );
  }
}

/* --------------------------------------------------------------------------
   Деньги
   -------------------------------------------------------------------------- */

function updateMoneyUI() {
  const revenue = Number(current.shift.revenue) || 0;
  const expensesTotal = current.shift.expenses.reduce(
    (sum, expense) => sum + (Number(expense.amount) || 0),
    0
  );
  const profit = revenue - expensesTotal;

  if (els.revenue) {
    els.revenue.textContent = formatMoney(revenue);
  }
  if (els.expensesTotal) {
    els.expensesTotal.textContent = formatMoney(expensesTotal);
  }
  if (els.profit) {
    els.profit.textContent = formatMoney(profit);
    els.profit.classList.toggle("is-negative", profit < 0);
  }
  if (els.shiftStarted) {
    els.shiftStarted.textContent = formatStarted(current.shift.started_at);
  }
}

function renderShift(shift, options = {}) {
  const data = shift || {};

  current.shift = {
    started_at: data.started_at || null,
    total_meters: Number(data.total_meters) || 0,
    markers: Array.isArray(data.markers) ? data.markers : [],
    revenue: Number(data.revenue) || 0,
    orders: Array.isArray(data.orders) ? data.orders : [],
    expenses: Array.isArray(data.expenses) ? data.expenses : [],
  };

  drawRoute(Boolean(options.fitToRoute));
  updateMileageUI();
  updateMoneyUI();

  const lastPoint = current.shift.markers[current.shift.markers.length - 1];
  geo.lastStored = lastPoint ? { lat: lastPoint.lat, lng: lastPoint.lng } : null;
}

function setFormOpen(formName) {
  const forms = [els.orderForm, els.expenseForm].filter(Boolean);

  for (const form of forms) {
    const isTarget = form.id === formName;
    form.hidden = !isTarget;
    if (isTarget) {
      form.reset();
      const input = form.querySelector('input[type="number"]');
      if (input) {
        input.focus();
        input.select();
      }
    }
  }

  if (els.addOrderButton) {
    els.addOrderButton.setAttribute(
      "aria-expanded",
      formName === "order-form" ? "true" : "false"
    );
  }
  if (els.addExpenseButton) {
    els.addExpenseButton.setAttribute(
      "aria-expanded",
      formName === "expense-form" ? "true" : "false"
    );
  }
}

function closeMoneyForms() {
  setFormOpen(null);
}

function readAmountInput(input) {
  if (!input) return null;
  const value = Number(input.value.replace(",", "."));
  if (!Number.isFinite(value) || value <= 0 || value > 10_000_000) return null;
  return Math.round(value * 100) / 100;
}

function setMoneySaving(saving) {
  moneySaving = saving;
  for (const button of document.querySelectorAll(
    '#order-form button[type="submit"], #expense-form button[type="submit"]'
  )) {
    button.disabled = saving;
  }
}

async function submitOrder(event) {
  event.preventDefault();
  if (moneySaving) return;

  const amount = readAmountInput(els.orderAmount);
  if (amount === null) {
    showToast("Введите сумму заказа больше нуля", "error");
    return;
  }

  setMoneySaving(true);

  try {
    const data = await requestJSON("/api/orders", {
      method: "POST",
      body: JSON.stringify({ amount }),
    });
    renderShift(data.state.shift);
    closeMoneyForms();
    showToast(`Заказ добавлен: ${formatMoney(amount)}`);
  } catch (error) {
    showToast(error instanceof Error ? error.message : "Не удалось добавить заказ", "error");
  } finally {
    setMoneySaving(false);
  }
}

async function submitExpense(event) {
  event.preventDefault();
  if (moneySaving) return;

  const amount = readAmountInput(els.expenseAmount);
  if (amount === null) {
    showToast("Введите сумму расхода больше нуля", "error");
    return;
  }

  const category = els.expenseCategory ? els.expenseCategory.value : "fuel";
  const label = EXPENSE_LABELS[category] || "Расход";

  setMoneySaving(true);

  try {
    const data = await requestJSON("/api/expenses", {
      method: "POST",
      body: JSON.stringify({ amount, category }),
    });
    renderShift(data.state.shift);
    closeMoneyForms();
    showToast(`Расход добавлен: ${label} — ${formatMoney(amount)}`);
  } catch (error) {
    showToast(error instanceof Error ? error.message : "Не удалось добавить расход", "error");
  } finally {
    setMoneySaving(false);
  }
}

/* --------------------------------------------------------------------------
   Завершение смены
   -------------------------------------------------------------------------- */

async function finishShift() {
  if (shiftFinishing) return;

  const confirmed = window.confirm(
    "Завершить смену? Итоги сохранятся в историю, а карта и счётчики очистятся."
  );
  if (!confirmed) return;

  shiftFinishing = true;
  if (els.finishShiftButton) {
    els.finishShiftButton.disabled = true;
    els.finishShiftButton.textContent = "Завершаем…";
  }

  try {
    const data = await requestJSON("/api/shift/finish", { method: "POST" });
    const archived = data.archived || {};

    if (geo.watching) stopTracking(true);
    releaseWakeLock();
    geo.lastStored = null;
    geo.pendingBreak = false;
    closeMoneyForms();
    renderShift(data.state.shift);

    const distance = Number(archived.distance_km) || 0;
    const profit = Number(archived.profit) || 0;
    showToast(
      `Смена завершена: ${distance.toFixed(2).replace(".", ",")} км, прибыль ${formatMoney(profit)}`
    );
  } catch (error) {
    showToast(error instanceof Error ? error.message : "Не удалось завершить смену", "error");
  } finally {
    shiftFinishing = false;
    if (els.finishShiftButton) {
      els.finishShiftButton.disabled = false;
      els.finishShiftButton.textContent = "Завершить смену";
    }
  }
}

/* --------------------------------------------------------------------------
   Режим за рулем
   -------------------------------------------------------------------------- */

function setDrivingMode(enabled) {
  if (document.body.classList.contains("driving-mode") === enabled) return;

  if (enabled) {
    closeHistory();
    closeMoneyForms();
  }

  if (!enabled) {
    document.body.style.removeProperty("--drive-bar-height");
  }

  document.body.classList.toggle("driving-mode", enabled);

  if (els.driveToggle) {
    els.driveToggle.setAttribute("aria-pressed", enabled ? "true" : "false");
  }

  const refreshMapSize = () => {
    if (map) map.invalidateSize();
    updateDriveBarHeight();
  };
  window.requestAnimationFrame(refreshMapSize);
  window.setTimeout(refreshMapSize, 150);

  if (enabled) {
    if (els.driveExit) els.driveExit.focus({ preventScroll: true });
  } else if (els.driveToggle) {
    els.driveToggle.focus({ preventScroll: true });
  }
}

/* --------------------------------------------------------------------------
   Быстрое добавление заказа / расхода
   -------------------------------------------------------------------------- */

const QUICK_MAX_AMOUNT = 10_000_000;

const quickEntry = {
  mode: "order",
  amount: 0,
  category: "fuel",
  saving: false,
};

let quickEntryReturnFocus = null;

function quickEntryIsOpen() {
  return Boolean(els.moneyModal && !els.moneyModal.hidden);
}

function updateDriveBarHeight() {
  if (!document.body.classList.contains("driving-mode")) return;
  if (!els.statusCard) return;

  const height = Math.ceil(els.statusCard.getBoundingClientRect().height);
  if (height > 0) {
    document.body.style.setProperty("--drive-bar-height", `${height}px`);
  }
}

function updateQuickEntryUI() {
  if (!els.moneyModal) return;

  const isExpense = quickEntry.mode === "expense";

  if (els.moneyModalTitle) {
    els.moneyModalTitle.textContent = isExpense ? "Новый расход" : "Новый заказ";
  }
  if (els.moneyModalSubtitle) {
    els.moneyModalSubtitle.textContent = isExpense
      ? "Сумма и категория расхода"
      : "Сумма чека";
  }
  if (els.expenseCategories) {
    els.expenseCategories.hidden = !isExpense;
  }
  if (els.amountDisplay) {
    els.amountDisplay.textContent = formatMoney(quickEntry.amount);
  }
  if (els.amountHint) {
    els.amountHint.textContent = isExpense ? "Введите сумму расхода" : "Введите сумму чека";
  }

  if (els.keypad) {
    for (const button of els.keypad.querySelectorAll("button")) {
      if (button === els.moneySubmit) continue;
      button.disabled = quickEntry.saving;
    }
  }

  if (els.moneySubmit) {
    els.moneySubmit.disabled = quickEntry.saving || quickEntry.amount <= 0;
    els.moneySubmit.textContent = quickEntry.saving ? "Сохраняем…" : "ОК";
  }

  if (els.moneyModalClose) {
    els.moneyModalClose.disabled = quickEntry.saving;
  }

  if (els.expenseCategories) {
    for (const chip of els.expenseCategories.querySelectorAll("[data-category]")) {
      chip.setAttribute(
        "aria-pressed",
        chip.dataset.category === quickEntry.category ? "true" : "false"
      );
      chip.disabled = quickEntry.saving;
    }
  }
}

function openQuickEntry(mode) {
  if (!els.moneyModal || !document.body.classList.contains("driving-mode")) return;

  quickEntry.mode = mode === "expense" ? "expense" : "order";
  quickEntry.amount = 0;
  quickEntry.category = "fuel";
  quickEntry.saving = false;
  quickEntryReturnFocus = quickEntry.mode === "expense" ? els.fabExpense : els.fabOrder;

  updateQuickEntryUI();
  els.moneyModal.hidden = false;

  if (els.moneyModalClose) {
    els.moneyModalClose.focus({ preventScroll: true });
  }
}

function closeQuickEntry() {
  if (!els.moneyModal || els.moneyModal.hidden || quickEntry.saving) return;

  els.moneyModal.hidden = true;
  const target = quickEntryReturnFocus;
  quickEntryReturnFocus = null;

  if (target && document.body.classList.contains("driving-mode")) {
    target.focus({ preventScroll: true });
  }
}

function appendQuickDigit(digit) {
  if (quickEntry.saving || !quickEntryIsOpen()) return;

  const next = quickEntry.amount * 10 + digit;
  if (next > QUICK_MAX_AMOUNT) return;

  quickEntry.amount = next;
  updateQuickEntryUI();
}

function backspaceQuickDigit() {
  if (quickEntry.saving || !quickEntryIsOpen()) return;
  quickEntry.amount = Math.floor(quickEntry.amount / 10);
  updateQuickEntryUI();
}

function clearQuickAmount() {
  if (quickEntry.saving || !quickEntryIsOpen()) return;
  quickEntry.amount = 0;
  updateQuickEntryUI();
}

function selectQuickCategory(category) {
  if (quickEntry.saving || !quickEntryIsOpen()) return;
  if (!Object.prototype.hasOwnProperty.call(EXPENSE_LABELS, category)) return;

  quickEntry.category = category;
  updateQuickEntryUI();
}

async function submitQuickEntry() {
  if (quickEntry.saving || quickEntry.amount <= 0) return;

  const mode = quickEntry.mode;
  const amount = quickEntry.amount;
  const category = quickEntry.category;

  quickEntry.saving = true;
  updateQuickEntryUI();

  try {
    const data =
      mode === "expense"
        ? await requestJSON("/api/expenses", {
            method: "POST",
            body: JSON.stringify({ amount, category }),
          })
        : await requestJSON("/api/orders", {
            method: "POST",
            body: JSON.stringify({ amount }),
          });

    renderShift(data.state.shift);
    quickEntry.saving = false;
    closeQuickEntry();

    if (mode === "expense") {
      showToast(`Расход добавлен: ${EXPENSE_LABELS[category]} — ${formatMoney(amount)}`);
    } else {
      showToast(`Заказ добавлен: ${formatMoney(amount)}`);
    }
  } catch (error) {
    showToast(
      error instanceof Error ? error.message : "Не удалось сохранить операцию",
      "error"
    );
  } finally {
    quickEntry.saving = false;
    updateQuickEntryUI();
  }
}

/* --------------------------------------------------------------------------
   История смен
   -------------------------------------------------------------------------- */

const HISTORY_EMPTY_TEXT = "Пока нет завершённых смен. Завершите смену — она появится здесь.";

let historyReturnFocus = null;

function makeEl(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function formatHistoryDate(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "Дата неизвестна";
  return date.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function formatClock(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "--:--";
  return date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}

function formatDuration(minutes) {
  const total = Math.max(0, Math.round(Number(minutes) || 0));
  if (total < 60) return `${total} мин`;
  const hours = Math.floor(total / 60);
  const rest = total % 60;
  return rest > 0 ? `${hours} ч ${rest} мин` : `${hours} ч`;
}

function buildOperation(item) {
  const isOrder = item.kind === "order";
  const row = makeEl("li", `operation operation--${isOrder ? "order" : "expense"}`);

  const time = document.createElement("time");
  time.className = "operation__time";
  if (item.created_at) time.dateTime = item.created_at;
  time.textContent = formatClock(item.created_at);

  const label = isOrder
    ? "Заказ"
    : `Расход · ${EXPENSE_LABELS[item.category] || "Другое"}`;

  const amount = Number(item.amount) || 0;

  row.append(time);
  row.append(makeEl("span", "operation__label", label));
  row.append(makeEl("span", "operation__amount", `${isOrder ? "+" : "−"}${formatMoney(amount)}`));

  return row;
}

function buildShiftCard(record) {
  const card = makeEl("article", "shift-card");

  const head = makeEl("div", "shift-card__head");
  const when = makeEl("div", "shift-card__when");

  when.append(makeEl("p", "shift-card__date", formatHistoryDate(record.started_at)));
  when.append(
    makeEl(
      "p",
      "shift-card__times",
      `${formatClock(record.started_at)} — ${formatClock(record.finished_at)}`
    )
  );

  const car = [record.car_brand, record.car_plate].filter(Boolean).join(" · ");
  if (car) {
    when.append(makeEl("p", "shift-card__car", car));
  }
  head.append(when);

  const profit = Number(record.profit) || 0;
  const profitBox = makeEl("div", "shift-card__profit");
  profitBox.append(makeEl("span", "shift-card__profit-label", "Чистая прибыль"));
  profitBox.append(
    makeEl(
      "strong",
      `shift-card__profit-value${profit < 0 ? " is-negative" : ""}`,
      formatMoney(profit)
    )
  );
  head.append(profitBox);
  card.append(head);

  const metrics = makeEl("div", "shift-card__metrics");
  const addMetric = (label, value) => {
    const item = makeEl("div", "shift-card__metric");
    item.append(makeEl("span", "shift-card__metric-label", label));
    item.append(makeEl("span", "shift-card__metric-value", value));
    metrics.append(item);
  };

  addMetric("В пути", formatDuration(record.duration_minutes));
  addMetric(
    "Пробег",
    `${(Number(record.distance_km) || 0).toFixed(2).replace(".", ",")} км`
  );
  addMetric("Выручка", formatMoney(record.revenue));
  addMetric("Расходы", formatMoney(record.expenses_total));
  card.append(metrics);

  const orders = Array.isArray(record.orders) ? record.orders : [];
  const expenses = Array.isArray(record.expenses) ? record.expenses : [];

  const operations = [
    ...orders.map((order) => ({ ...order, kind: "order" })),
    ...expenses.map((expense) => ({ ...expense, kind: "expense" })),
  ].sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));

  if (operations.length > 0) {
    const details = makeEl("details", "shift-card__details");
    details.append(
      makeEl("summary", "shift-card__summary", `Журнал операций · ${operations.length}`)
    );

    const list = makeEl("ul", "operations");
    for (const operation of operations) {
      list.append(buildOperation(operation));
    }

    details.append(list);
    card.append(details);
  }

  return card;
}

function renderHistory(shifts) {
  if (!els.historyList) return;

  els.historyList.replaceChildren();
  if (els.historyLoading) els.historyLoading.hidden = true;

  if (!Array.isArray(shifts) || shifts.length === 0) {
    if (els.historyEmpty) {
      els.historyEmpty.textContent = HISTORY_EMPTY_TEXT;
      els.historyEmpty.hidden = false;
    }
    return;
  }

  if (els.historyEmpty) els.historyEmpty.hidden = true;

  for (const shift of shifts) {
    els.historyList.append(buildShiftCard(shift));
  }
}

async function openHistory() {
  if (!els.historyScreen) return;

  historyReturnFocus = document.activeElement;
  els.historyScreen.hidden = false;
  document.body.classList.add("is-history-open");

  if (els.historyList) els.historyList.replaceChildren();
  if (els.historyLoading) els.historyLoading.hidden = false;
  if (els.historyEmpty) els.historyEmpty.hidden = true;

  if (els.historyClose) els.historyClose.focus();

  try {
    const data = await requestJSON("/api/history");
    renderHistory(data && data.shifts);
  } catch (error) {
    if (els.historyLoading) els.historyLoading.hidden = true;
    if (els.historyEmpty) {
      els.historyEmpty.textContent = "Не удалось загрузить историю. Попробуйте ещё раз.";
      els.historyEmpty.hidden = false;
    }
  }
}

function closeHistory() {
  if (!els.historyScreen || els.historyScreen.hidden) return;

  els.historyScreen.hidden = true;
  document.body.classList.remove("is-history-open");

  const target = historyReturnFocus || els.historyButton;
  historyReturnFocus = null;
  if (target && typeof target.focus === "function") target.focus();
}

/* --------------------------------------------------------------------------
   Карта
   -------------------------------------------------------------------------- */

function initMap() {
  if (!els.map) return;

  if (typeof window.L === "undefined") {
    els.map.innerHTML =
      '<p style="padding:24px;color:#93a3b5;font-family:sans-serif;text-align:center;">' +
      "Не удалось загрузить карту: проверьте подключение к интернету (CDN Leaflet)." +
      "</p>";
    if (els.trackButton) {
      els.trackButton.disabled = true;
    }
    updateMileageUI();
    return;
  }

  map = window.L.map(els.map, {
    center: MOSCOW_CENTER,
    zoom: 12,
    zoomControl: true,
    scrollWheelZoom: true,
  });

  window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
  }).addTo(map);

  let resizeTimer = null;
  window.addEventListener("resize", () => {
    if (resizeTimer !== null) {
      window.clearTimeout(resizeTimer);
    }
    resizeTimer = window.setTimeout(() => {
      if (map) map.invalidateSize();
      updateDriveBarHeight();
      resizeTimer = null;
    }, 150);
  });
}

/* --------------------------------------------------------------------------
   Инициализация
   -------------------------------------------------------------------------- */

function bindEvents() {
  if (els.carForm) {
    els.carForm.addEventListener("submit", saveCar);
  }

  for (const button of els.statusButtons) {
    button.addEventListener("click", () => {
      saveStatus(button.dataset.status);
    });
  }

  if (els.trackButton) {
    els.trackButton.addEventListener("click", toggleTracking);
  }

  if (els.resetMileageButton) {
    els.resetMileageButton.addEventListener("click", resetMileage);
  }

  if (els.addOrderButton) {
    els.addOrderButton.addEventListener("click", () => {
      setFormOpen(els.orderForm && els.orderForm.hidden ? "order-form" : null);
    });
  }

  if (els.addExpenseButton) {
    els.addExpenseButton.addEventListener("click", () => {
      setFormOpen(els.expenseForm && els.expenseForm.hidden ? "expense-form" : null);
    });
  }

  for (const button of document.querySelectorAll("[data-close-form]")) {
    button.addEventListener("click", closeMoneyForms);
  }

  if (els.orderForm) {
    els.orderForm.addEventListener("submit", submitOrder);
  }

  if (els.expenseForm) {
    els.expenseForm.addEventListener("submit", submitExpense);
  }

  if (els.finishShiftButton) {
    els.finishShiftButton.addEventListener("click", finishShift);
  }

  if (els.historyButton) {
    els.historyButton.addEventListener("click", openHistory);
  }

  if (els.driveToggle) {
    els.driveToggle.addEventListener("click", () => setDrivingMode(true));
  }

  if (els.driveExit) {
    els.driveExit.addEventListener("click", () => setDrivingMode(false));
  }

  if (els.fabOrder) {
    els.fabOrder.addEventListener("click", () => openQuickEntry("order"));
  }

  if (els.fabExpense) {
    els.fabExpense.addEventListener("click", () => openQuickEntry("expense"));
  }

  if (els.moneyModalClose) {
    els.moneyModalClose.addEventListener("click", closeQuickEntry);
  }

  if (els.moneyModal) {
    els.moneyModal.addEventListener("click", (event) => {
      if (event.target === els.moneyModal) closeQuickEntry();
    });
  }

  if (els.keypad) {
    els.keypad.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-key]");
      if (!button) return;

      const key = button.dataset.key;
      if (key === "clear") {
        clearQuickAmount();
      } else if (key === "backspace") {
        backspaceQuickDigit();
      } else if (/^\d$/.test(key)) {
        appendQuickDigit(Number(key));
      }
    });
  }

  if (els.expenseCategories) {
    els.expenseCategories.addEventListener("click", (event) => {
      const chip = event.target.closest("[data-category]");
      if (chip) selectQuickCategory(chip.dataset.category);
    });
  }

  if (els.moneySubmit) {
    els.moneySubmit.addEventListener("click", submitQuickEntry);
  }

  if (els.historyClose) {
    els.historyClose.addEventListener("click", closeHistory);
  }

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState !== "visible") return;

    if (geo.watching) {
      requestWakeLock();
    }
    if (
      !weatherState.loading &&
      Date.now() - weatherState.updatedAt >= WEATHER_REFRESH_MS
    ) {
      loadWeather();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (els.moneyModal && !els.moneyModal.hidden) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeQuickEntry();
        return;
      }
      if (event.key === "Backspace") {
        event.preventDefault();
        backspaceQuickDigit();
        return;
      }
      if (/^\d$/.test(event.key)) {
        event.preventDefault();
        appendQuickDigit(Number(event.key));
        return;
      }
      return;
    }

    if (event.key !== "Escape") return;
    if (document.body.classList.contains("driving-mode")) {
      setDrivingMode(false);
      return;
    }
    if (els.historyScreen && !els.historyScreen.hidden) {
      closeHistory();
      return;
    }
    closeMoneyForms();
  });
}

async function loadState() {
  try {
    const state = await requestJSON("/api/state");
    applyCar(state);
    applyStatus(state.status);
    renderShift(state.shift, { fitToRoute: true });
  } catch (error) {
    showToast("Не удалось загрузить состояние. Проверьте, что сервер запущен.", "error");
  }
}

function init() {
  initMap();
  bindEvents();

  applyStatus(els.body.dataset.status || "offline");
  updateMileageUI();
  updateMoneyUI();

  startWeatherUpdates();
  loadState();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
