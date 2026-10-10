/* =========================================================================
   deck.js · McWrapped 动效引擎（零依赖，原生 JS）
   不认识任何业务概念，只通过 DOM 的 data-* 契约工作。

   核心行为：**逐步演出（staged reveal）+ 点击加速**
   - 进入一屏后，把带 data-anim 的元素按 data-beat 顺序一段段播放；
   - 播放中「点击/滚轮/方向键/触摸」= 加速：立即显示本屏剩余内容；
   - 全部显示完后再触发 = 翻到下一屏。

   其余职责：数字滚动、图表描边/生长、转场、粒子、主题、省电模式、重播。
   ========================================================================= */
(function () {
  "use strict";

  var mqReduce = window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  var reduce = mqReduce ? mqReduce.matches : false;

  /* ------------------------------------------------------------ DOM */
  var stage = document.getElementById("stage");
  var track = document.getElementById("track");
  if (!stage || !track) return;
  var scenes = Array.prototype.slice.call(track.querySelectorAll(".scene"));
  var rail = document.getElementById("rail");
  var bar = document.getElementById("progressBar");
  var chapter = document.getElementById("chapterLabel");
  var hint = document.getElementById("hint");
  var cue = document.getElementById("advanceCue");
  var total = scenes.length;
  if (!total) return;

  var visited = new Array(total);
  var index = 0;
  var motionOn = !reduce;
  var hintTimer = null;

  /* 逐步演出的状态机 */
  var beats = [];        /* 本屏所有节拍（元素数组的数组） */
  var beatAt = 0;        /* 已播到第几拍 */
  var beatTimer = null;  /* 下一拍的定时器 */
  var playing = false;   /* 是否正在逐步播放 */

  var BEAT_GAP = 460;    /* 拍与拍之间间隔（ms），营造"一点一点" */
  var FIRST_GAP = 260;   /* 进屏到第一拍的延迟 */

  var THEMES = __THEMES__;
  var DEFAULT_THEME = "__DEFAULT_THEME__";

  /* ============================================================ 主题 */
  function applyTheme(name) {
    var t = THEMES[name] || THEMES[DEFAULT_THEME];
    var r = document.documentElement;
    for (var k in t) {
      if (Object.prototype.hasOwnProperty.call(t, k)) {
        r.style.setProperty("--" + k, t[k]);
      }
    }
    r.setAttribute("data-theme", name);
    try { localStorage.setItem("mcdwrapped.theme", name); } catch (e) {}
  }
  function toggleTheme() {
    var cur = document.documentElement.getAttribute("data-theme") || DEFAULT_THEME;
    applyTheme(cur === "dark" ? "light" : "dark");
  }

  /* ============================================================ 粒子 */
  function seedParticles(scene) {
    if (!motionOn || scene.dataset.seeded) return;
    scene.dataset.seeded = "1";
    var host = scene.querySelector(".aura");
    if (!host) return;
    var n = parseInt(scene.dataset.particles || "0", 10);
    if (!n) return;
    var frag = document.createDocumentFragment();
    for (var i = 0; i < n; i++) {
      var p = document.createElement("span");
      p.className = "particle";
      var size = 2 + Math.random() * 7;
      p.style.width = size + "px";
      p.style.height = size + "px";
      p.style.left = (Math.random() * 100) + "%";
      p.style.bottom = (-10 - Math.random() * 20) + "%";
      p.style.setProperty("--p-op", (0.16 + Math.random() * 0.42).toFixed(2));
      p.style.animationDuration = (11 + Math.random() * 16).toFixed(1) + "s";
      p.style.animationDelay = (-Math.random() * 20).toFixed(1) + "s";
      frag.appendChild(p);
    }
    host.appendChild(frag);
  }

  /* ============================================================ 数字滚动 */
  function countUp(el) {
    var target = parseFloat(el.getAttribute("data-count"));
    var prefix = el.getAttribute("data-prefix") || "";
    var suffix = el.getAttribute("data-suffix") || "";
    var dec = parseInt(el.getAttribute("data-decimals") || "0", 10);
    var group = el.getAttribute("data-group") !== "0";

    function render(v) {
      var s = dec > 0 ? v.toFixed(dec) : String(Math.round(v));
      if (group && dec === 0) s = s.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      el.textContent = prefix + s + suffix;
    }
    if (isNaN(target)) { render(0); return; }
    if (!motionOn) { render(target); return; }

    var dur = parseInt(el.getAttribute("data-count-dur") || "1250", 10);
    var t0 = null;
    el.textContent = prefix + (dec > 0 ? (0).toFixed(dec) : "0") + suffix;
    /* 保险：动画若因标签被节流而没跑完，2 秒后强制落到真值，
       避免用户长时间盯着一个 0。 */
    var guard = window.setTimeout(function () { render(target); }, dur + 900);
    function tick(ts) {
      if (t0 === null) t0 = ts;
      var p = Math.min(1, (ts - t0) / dur);
      var eased = 1 - Math.pow(1 - p, 4);
      render(target * eased);
      if (p < 1) requestAnimationFrame(tick);
      else { window.clearTimeout(guard); render(target); }
    }
    requestAnimationFrame(tick);
  }
  function countUpInstant(el) {
    if (motionOn) return;           /* 动效开启时留给动画 */
    el.textContent = (el.getAttribute("data-prefix") || "") +
      el.getAttribute("data-count") + (el.getAttribute("data-suffix") || "");
  }

  /* ============================================================ 图表准备 */
  function primePath(path) {
    try {
      var len = path.getTotalLength();
      if (len && isFinite(len)) {
        path.style.setProperty("--len", len);
        path.style.strokeDasharray = len;
        path.style.strokeDashoffset = len;
      }
    } catch (e) {}
  }
  function primeDonut(svg) {
    var segs = svg.querySelectorAll(".donut-seg");
    var sum = 0;
    Array.prototype.forEach.call(segs, function (s) {
      sum += parseFloat(s.getAttribute("data-len") || "0");
    });
    Array.prototype.forEach.call(segs, function (s) {
      var len = parseFloat(s.getAttribute("data-len") || "0");
      var circ = parseFloat(s.getAttribute("data-circ") || "0") || sum;
      s.style.setProperty("--circ", circ);
      s.style.setProperty("--offset", circ - len);
    });
  }
  function prepare(scene) {
    Array.prototype.forEach.call(
      scene.querySelectorAll('[data-anim="draw"]'), primePath);
    Array.prototype.forEach.call(
      scene.querySelectorAll("svg[data-donut]"), primeDonut);
  }

  /* ============================================================ 逐步演出 */

  /* 把一屏的元素按 data-beat 分组。没有 data-beat 的，按 data-anim-delay
     排序后每 2 个一组合并成一拍（兼容旧场景）。 */
  function buildBeats(scene) {
    var els = Array.prototype.slice.call(scene.querySelectorAll("[data-anim]"));
    var groups = {};
    var hasBeat = false;
    els.forEach(function (el) {
      var raw = el.getAttribute("data-beat");
      if (raw !== null) hasBeat = true;
    });
    if (hasBeat) {
      els.forEach(function (el) {
        var b = parseInt(el.getAttribute("data-beat") || "0", 10);
        (groups[b] = groups[b] || []).push(el);
      });
    } else {
      els.map(function (el, i) { return { el: el, i: i }; })
        .sort(function (a, b) {
          return (parseInt(a.el.getAttribute("data-anim-delay") || "0", 10) || a.i * 60)
            - (parseInt(b.el.getAttribute("data-anim-delay") || "0", 10) || b.i * 60);
        })
        .forEach(function (o, k) {
          var b = Math.floor(k / 2);
          (groups[b] = groups[b] || []).push(o.el);
        });
    }
    return Object.keys(groups)
      .map(function (k) { return parseInt(k, 10); })
      .sort(function (a, b) { return a - b; })
      .map(function (k) { return groups[k]; });
  }

  /* 播放一拍（数组里的元素同时入场） */
  function playBeat(list) {
    list.forEach(function (el) {
      el.classList.add("anim-in");
      var d = el.getAttribute("data-anim-delay");
      if (d) el.style.setProperty("--delay", d + "ms");
    });
    /* 这一拍里的数字与图表跟着启动 */
    list.forEach(function (el) {
      if (el.hasAttribute("data-count")) countUp(el);
      if (el.getAttribute("data-anim") === "draw") primePath(el);
      Array.prototype.forEach.call(
        el.querySelectorAll ? el.querySelectorAll("[data-count]") : [], countUp);
    });
    watchdog(list);
  }

  /* 看门狗：动画理应结束后若仍不可见（后台标签节流 / 动画被禁用 /
     浏览器卡顿导致 fill-mode 停在 0），强制补一次"硬显示"，
     保证内容永远不会白屏。 */
  function watchdog(list) {
    var ms = 1400;
    window.setTimeout(function () {
      list.forEach(function (el) {
        var op = parseFloat(window.getComputedStyle(el).opacity);
        if (!isNaN(op) && op < 0.02) {
          el.classList.add("anim-done");
        }
      });
    }, ms);
  }

  /* 一次性把本屏全部显示（跳过/加速/reduced-motion） */
  function revealAll(scene) {
    stopBeats();
    scene.classList.add("anim");
    Array.prototype.forEach.call(scene.querySelectorAll("[data-anim]"), function (el) {
      el.classList.add("anim-in");
    });
    Array.prototype.forEach.call(scene.querySelectorAll("[data-count]"), function (el) {
      if (motionOn) countUp(el);
      else {
        el.textContent = (el.getAttribute("data-prefix") || "") +
          el.getAttribute("data-count") + (el.getAttribute("data-suffix") || "");
      }
    });
    Array.prototype.forEach.call(scene.querySelectorAll(".donut-seg"), function (s) {
      s.style.strokeDashoffset = 0;
    });
    Array.prototype.forEach.call(
      scene.querySelectorAll('[data-anim="draw"]'), function (p) {
        p.style.strokeDashoffset = 0;
      });
  }

  function stopBeats() {
    if (beatTimer) { window.clearTimeout(beatTimer); beatTimer = null; }
    playing = false;
    if (cue) cue.classList.remove("show");
  }

  /* 启动本屏的逐步演出 */
  function startBeats(scene, delay) {
    stopBeats();
    prepare(scene);
    beats = buildBeats(scene);
    beatAt = 0;

    if (!motionOn || !beats.length) {
      revealAll(scene);
      return;
    }

    scene.classList.add("anim");
    playing = true;
    if (cue) cue.classList.add("show");

    function nextBeat() {
      if (beatAt >= beats.length) { finishBeats(); return; }
      playBeat(beats[beatAt]);
      beatAt += 1;
      beatTimer = window.setTimeout(nextBeat, BEAT_GAP);
    }
    beatTimer = window.setTimeout(nextBeat, delay == null ? FIRST_GAP : delay);
  }

  function finishBeats() {
    if (beatTimer) { window.clearTimeout(beatTimer); beatTimer = null; }
    playing = false;
    if (cue) cue.classList.remove("show");
  }

  /* 用户想「加速」：还有剩余节拍就全放出来；否则返回 false（可以翻页） */
  function accelerate() {
    var scene = scenes[index];
    if (!playing) return false;
    revealAll(scene);
    return true;
  }

  /* ============================================================ 转场 */
  function layout() {
    scenes.forEach(function (s, i) {
      s.style.transform = "translate3d(0," + (i * 100) + "%,0)";
    });
  }

  function goto(n, opts) {
    opts = opts || {};
    n = Math.max(0, Math.min(total - 1, n));
    if (n === index && !opts.force) return;

    stopBeats();
    index = n;
    track.style.transform = "translate3d(0," + (-index * 100) + "%,0)";
    paint();

    var scene = scenes[index];
    seedParticles(scene);
    if (!visited[index] || opts.replay) {
      visited[index] = true;
      /* 等位移开始后再播，观感上是「滑入即生长」 */
      var delay = motionOn ? (opts.replay ? 60 : 300) : 0;
      if (opts.replay) { resetAnimations(scene); }
      window.setTimeout(function () { startBeats(scene, FIRST_GAP); }, delay);
    }
  }

  function paint() {
    var i = index;
    scenes.forEach(function (s, k) {
      var on = (k === i);
      s.classList.toggle("active", on);
      s.setAttribute("aria-hidden", on ? "false" : "true");
    });
    if (bar) bar.style.width = ((i + 1) / total * 100) + "%";
    if (chapter && scenes[i].dataset.chapterName) {
      chapter.textContent = scenes[i].dataset.chapterName;
    }
    if (rail) {
      Array.prototype.forEach.call(rail.children, function (b, k) {
        b.classList.toggle("on", k === i);
        b.setAttribute("aria-current", k === i ? "true" : "false");
      });
    }
    if (hint) hint.classList.toggle("hide", i > 0);
  }

  /* 统一的「前进」：正在演出则加速，否则翻页 */
  function advance(dir) {
    dir = dir || 1;
    if (accelerate()) return;
    goto(index + dir);
  }

  function resetAnimations(scene) {
    scene.classList.remove("anim");
    Array.prototype.forEach.call(scene.querySelectorAll("[data-anim]"), function (el) {
      el.classList.remove("anim-in");
    });
    Array.prototype.forEach.call(
      scene.querySelectorAll('[data-anim="draw"]'), function (el) {
        var len = parseInt(el.getAttribute("--len") || 0, 10);
        if (!len) { try { len = el.getTotalLength(); } catch (e) { len = 0; } }
        if (len) el.style.strokeDashoffset = len;
      });
    Array.prototype.forEach.call(scene.querySelectorAll("[data-count]"), function (el) {
      el.textContent = (el.getAttribute("data-prefix") || "") + "0" +
        (el.getAttribute("data-suffix") || "");
    });
    Array.prototype.forEach.call(scene.querySelectorAll(".donut-seg"), function (s) {
      s.style.strokeDashoffset = s.style.getPropertyValue("--circ") || "";
    });
  }

  /* ============================================================ 输入 */
  /* 滚轮：累积阈值，避免触控板惯性一次跳多屏 */
  var wheelAcc = 0, wheelLock = false;
  stage.addEventListener("wheel", function (e) {
    var t = e.target;
    if (t && t.closest && t.closest("[data-scrollable]")) return;
    e.preventDefault();
    if (wheelLock) return;
    wheelAcc += e.deltaY;
    var TH = 46;
    if (wheelAcc > TH) {
      wheelAcc = 0; wheelLock = true; advance(1);
    } else if (wheelAcc < -TH) {
      wheelAcc = 0; wheelLock = true; advance(-1);
    }
    window.setTimeout(function () { wheelLock = false; }, 620);
  }, { passive: false });

  /* 点击空白处 = 加速 / 翻页 */
  stage.addEventListener("click", function (e) {
    var t = e.target;
    if (t && t.closest && t.closest("button,a,[data-scrollable]")) return;
    advance(1);
  });

  /* 键盘 */
  document.addEventListener("keydown", function (e) {
    var k = e.key;
    if (k === "ArrowDown" || k === "PageDown" || k === " ") {
      e.preventDefault(); advance(1);
    } else if (k === "ArrowUp" || k === "PageUp") {
      e.preventDefault(); advance(-1);
    } else if (k === "Home") { e.preventDefault(); goto(0); }
    else if (k === "End") { e.preventDefault(); goto(total - 1); }
    else if (k === "r" || k === "R") { replay(); }
  });

  /* 触摸滑动 */
  var ts = null;
  stage.addEventListener("touchstart", function (e) {
    if (e.touches.length !== 1) return;
    ts = { y: e.touches[0].clientY, x: e.touches[0].clientX };
  }, { passive: true });
  stage.addEventListener("touchend", function (e) {
    if (!ts) return;
    var t = e.changedTouches[0];
    var dy = ts.y - t.clientY;
    var dx = ts.x - t.clientX;
    /* 纵向意图明显才翻屏，横向留给浏览器 */
    if (Math.abs(dy) > 48 && Math.abs(dy) > Math.abs(dx) * 1.3) {
      advance(dy > 0 ? 1 : -1);
    } else if (Math.abs(dy) < 12 && Math.abs(dx) < 12) {
      advance(1);            /* 轻点 = 加速 */
    }
    ts = null;
  }, { passive: true });

  /* ============================================================ 控制 */
  function replay() {
    var scene = scenes[index];
    resetAnimations(scene);
    window.setTimeout(function () { startBeats(scene, 40); }, 40);
  }
  function toggleMotion() {
    motionOn = !motionOn;
    document.documentElement.classList.toggle("motion-off", !motionOn);
    var bm = document.getElementById("btnMotion");
    if (bm) bm.classList.toggle("off", !motionOn);
    if (motionOn) { replay(); }
    else { revealAll(scenes[index]); }
    try { localStorage.setItem("mcdwrapped.motion", motionOn ? "1" : "0"); } catch (e) {}
  }

  /* ============================================================ 绑定 */
  ["btnTheme", "btnThemeTop"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener("click", toggleTheme);
  });
  ["btnReplay", "btnReplayEnd"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener("click", replay);
  });
  var bm = document.getElementById("btnMotion");
  if (bm) bm.addEventListener("click", toggleMotion);
  var bt = document.getElementById("btnPrint");
  if (bt) bt.addEventListener("click", function () { window.print(); });

  /* 开始按钮 */
  var sb = document.getElementById("startBtn");
  if (sb) sb.addEventListener("click", function (e) {
    e.stopPropagation();
    goto(index + 1);
  });

  /* 标签回到前台：若本屏仍在"逐步"中，补一次硬显示，避免后台节流
     把动画冻在 opacity:0 的中间态。 */
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible" && playing) {
      var s = scenes[index];
      Array.prototype.forEach.call(
        s.querySelectorAll("[data-anim].anim-in"), function (el) {
          var op = parseFloat(window.getComputedStyle(el).opacity);
          if (!isNaN(op) && op < 0.02) el.classList.add("anim-done");
        });
    }
  });

  /* 侧边导轨 */
  if (rail) {
    scenes.forEach(function (s, i) {
      var b = document.createElement("button");
      b.className = "rail-btn";
      b.type = "button";
      b.setAttribute("aria-label",
        "第 " + (i + 1) + " 屏：" + (s.dataset.chapterName || ""));
      b.addEventListener("click", function () { goto(i); });
      rail.appendChild(b);
    });
  }

  if (mqReduce && mqReduce.addEventListener) {
    mqReduce.addEventListener("change", function (e) {
      if (e.matches) { motionOn = false;
        document.documentElement.classList.add("motion-off");
        var b2 = document.getElementById("btnMotion");
        if (b2) b2.classList.add("off");
        revealAll(scenes[index]);
      }
    });
  }

  /* ============================================================ 启动 */
  try {
    var savedTheme = localStorage.getItem("mcdwrapped.theme");
    if (savedTheme && THEMES[savedTheme]) applyTheme(savedTheme);
    var savedMotion = localStorage.getItem("mcdwrapped.motion");
    if (savedMotion === "0") motionOn = false;
    else if (savedMotion === "1") motionOn = true;
  } catch (e) {}
  if (!motionOn) {
    document.documentElement.classList.add("motion-off");
    var bmEl = document.getElementById("btnMotion");
    if (bmEl) bmEl.classList.add("off");
  }

  layout();
  paint();
  seedParticles(scenes[0]);
  visited[0] = true;
  window.setTimeout(function () { startBeats(scenes[0], motionOn ? 420 : 0); }, 60);

  hintTimer = window.setTimeout(function () {
    if (hint) hint.classList.add("hide");
  }, 6000);

  /* 对外 API（便于自动化与人机调试） */
  window.McWrapped = {
    goto: goto,
    next: function () { advance(1); },
    prev: function () { advance(-1); },
    replay: replay,
    reset: function () { goto(0); },
    revealAll: function () { revealAll(scenes[index]); },
    isPlaying: function () { return playing; },
    beat: function () { return { at: beatAt, of: beats.length }; }
  };
})();
