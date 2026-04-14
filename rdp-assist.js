/**
 * Mobile RDP Assist — Injectable Panel
 * Tap the bookmarklet on remotedesktop.google.com to toggle this overlay.
 *
 * Features:
 *   • Sticky modifier keys  (Ctrl / Alt / Shift / Win)
 *   • Right-click arming    (next tap becomes a right-click)
 *   • Common shortcuts      (Copy, Paste, Undo, Redo, Save …)
 *   • Special keys          (Esc, Tab, Enter, arrows, Home/End, PgUp/Dn …)
 *   • Text relay            (type on phone keyboard, send to remote desktop)
 *   • Scroll buttons        (Up / Down / Left / Right)
 *   • Draggable + minimisable panel
 */
(function () {
  'use strict';

  var ID = 'mrdpa';

  /* ── Toggle off if already injected ── */
  var prev = document.getElementById(ID + '-panel');
  if (prev) {
    prev.remove();
    var ps = document.getElementById(ID + '-style');
    if (ps) ps.remove();
    return;
  }

  /* ── State ── */
  var mod      = { ctrl: false, alt: false, shift: false, meta: false };
  var rcArmed  = false;
  var minimized = false;
  var drag     = { on: false, ox: 0, oy: 0, pl: 8, pt: 70 };

  /* ── Helpers ── */
  function rdpTarget() {
    return document.querySelector('canvas') || document.body;
  }

  function updateModBtns() {
    ['ctrl', 'alt', 'shift', 'meta'].forEach(function (k) {
      var el = document.getElementById(ID + '-m-' + k);
      if (!el) return;
      el.style.background  = mod[k] ? '#1d4ed8' : '#1f2937';
      el.style.borderColor = mod[k] ? '#3b82f6' : '#374151';
      el.style.color       = mod[k] ? '#fff'    : '#d1d5db';
    });
  }

  function clearMods() {
    mod.ctrl = mod.alt = mod.shift = mod.meta = false;
    updateModBtns();
  }

  function sendKey(key, code) {
    var el = rdpTarget();
    try { el.focus(); } catch (e) {}
    var opts = {
      key:      key,
      code:     code || ('Key' + key.toUpperCase()),
      ctrlKey:  mod.ctrl,
      altKey:   mod.alt,
      shiftKey: mod.shift,
      metaKey:  mod.meta,
      bubbles:    true,
      cancelable: true
    };
    el.dispatchEvent(new KeyboardEvent('keydown', opts));
    setTimeout(function () {
      el.dispatchEvent(new KeyboardEvent('keyup', opts));
      clearMods();
    }, 60);
  }

  function typeText(text) {
    var el = rdpTarget();
    try { el.focus(); } catch (e) {}
    for (var i = 0; i < text.length; i++) {
      var ch = text[i];
      var o  = { key: ch, bubbles: true, cancelable: true };
      el.dispatchEvent(new KeyboardEvent('keydown',  o));
      el.dispatchEvent(new KeyboardEvent('keypress', o));
      el.dispatchEvent(new KeyboardEvent('keyup',    o));
    }
  }

  function sendScroll(dx, dy) {
    var el = rdpTarget();
    var r  = el.getBoundingClientRect
      ? el.getBoundingClientRect()
      : { left: 0, top: 0, width: window.innerWidth, height: window.innerHeight };
    el.dispatchEvent(new WheelEvent('wheel', {
      clientX:   r.left + r.width  / 2,
      clientY:   r.top  + r.height / 2,
      deltaX:    dx,
      deltaY:    dy,
      deltaMode: 0,
      bubbles:    true,
      cancelable: true
    }));
  }

  /* ── CSS ── */
  var styleEl = document.createElement('style');
  styleEl.id  = ID + '-style';
  styleEl.textContent = [
    '#' + ID + '-panel {',
      'position:fixed!important; z-index:2147483647!important;',
      'top:70px; left:8px; width:316px;',
      'background:#0f172a; border:1px solid #1e293b; border-radius:18px;',
      'color:#f1f5f9;',
      'font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text",sans-serif;',
      'font-size:14px;',
      'box-shadow:0 24px 64px rgba(0,0,0,.85);',
      'touch-action:none; -webkit-user-select:none; user-select:none;',
    '}',
    '#' + ID + '-panel * { box-sizing:border-box; }',
    '#' + ID + '-panel button {',
      'font-family:inherit; cursor:pointer;',
      '-webkit-tap-highlight-color:transparent;',
    '}',

    /* Header */
    '#' + ID + '-hdr {',
      'display:flex; align-items:center; justify-content:space-between;',
      'padding:13px 14px 11px; border-bottom:1px solid #1e293b; cursor:grab;',
    '}',
    '#' + ID + '-hdr:active { cursor:grabbing; }',
    '#' + ID + '-htitle {',
      'font-size:11px; font-weight:700; letter-spacing:.1em;',
      'color:#475569; text-transform:uppercase;',
    '}',
    '#' + ID + '-hbtns { display:flex; gap:6px; }',
    '.' + ID + '-hbtn {',
      'background:#1e293b; border:1px solid #334155; color:#94a3b8;',
      'border-radius:8px; width:28px; height:28px; padding:0; font-size:13px;',
      'display:flex; align-items:center; justify-content:center;',
    '}',

    /* Body */
    '#' + ID + '-body { padding:12px 12px 14px; }',
    '.' + ID + '-sec  { margin-bottom:11px; }',
    '.' + ID + '-lbl  {',
      'font-size:10px; font-weight:700; letter-spacing:.1em;',
      'color:#334155; text-transform:uppercase; margin-bottom:6px;',
    '}',
    '.' + ID + '-row { display:flex; gap:5px; }',

    /* Modifier buttons */
    '.' + ID + '-mbtn {',
      'flex:1; padding:9px 2px; font-size:12px; font-weight:700;',
      'background:#1f2937; border:1px solid #374151; color:#d1d5db;',
      'border-radius:9px;',
    '}',
    '.' + ID + '-mbtn:active { opacity:.7; }',

    /* Right-click button */
    '.' + ID + '-rcbtn {',
      'width:100%; padding:9px; font-size:13px; font-weight:600;',
      'text-align:center; background:#1e293b; border:1px solid #334155;',
      'color:#cbd5e1; border-radius:9px;',
    '}',

    /* Grids */
    '.' + ID + '-g4 { display:grid; grid-template-columns:repeat(4,1fr); gap:4px; }',
    '.' + ID + '-g5 { display:grid; grid-template-columns:repeat(5,1fr); gap:4px; }',

    /* Key buttons */
    '.' + ID + '-key {',
      'padding:8px 2px; font-size:11px; font-weight:500; text-align:center;',
      'background:#1e293b; border:1px solid #334155; color:#e2e8f0;',
      'border-radius:8px;',
    '}',
    '.' + ID + '-key:active { background:#334155; transform:scale(.93); }',

    /* Shortcut buttons */
    '.' + ID + '-sc {',
      'padding:8px 2px; font-size:11px; font-weight:700; text-align:center;',
      'background:#1e293b; border:1px solid #334155; color:#93c5fd;',
      'border-radius:8px;',
    '}',
    '.' + ID + '-sc:active { background:#1e3a5f; transform:scale(.93); }',

    /* Text input row */
    '.' + ID + '-trow { display:flex; gap:5px; }',
    '#' + ID + '-txt {',
      'flex:1; background:#1e293b; border:1px solid #334155; color:#f1f5f9;',
      'border-radius:9px; padding:9px 10px; font-size:14px;',
      'font-family:inherit; outline:none;',
    '}',
    '#' + ID + '-send {',
      'background:#2563eb; border:none; color:#fff;',
      'border-radius:9px; padding:9px 14px; font-size:13px; font-weight:700;',
    '}',
    '#' + ID + '-send:active { background:#1d4ed8; }',

    /* Scroll buttons */
    '.' + ID + '-srow { display:flex; gap:5px; margin-bottom:4px; }',
    '.' + ID + '-sbtn {',
      'flex:1; padding:8px; font-size:12px; text-align:center;',
      'background:#1e293b; border:1px solid #334155; color:#e2e8f0;',
      'border-radius:8px;',
    '}',
    '.' + ID + '-sbtn:active { background:#334155; }'
  ].join('\n');

  document.head.appendChild(styleEl);

  /* ── Panel HTML ── */
  var panel = document.createElement('div');
  panel.id = ID + '-panel';

  function btn(cls, id, key, code, ctrl, label) {
    var attrs = ' class="' + ID + '-' + cls + '"';
    if (id)   attrs += ' id="' + ID + '-' + id + '"';
    if (key)  attrs += ' data-key="' + key + '"';
    if (code) attrs += ' data-code="' + code + '"';
    if (ctrl) attrs += ' data-ctrl="1"';
    return '<button' + attrs + '>' + label + '</button>';
  }

  panel.innerHTML = [
    '<div id="' + ID + '-hdr">',
      '<span id="' + ID + '-htitle">\uD83D\uDCF1 RDP Assist</span>',
      '<div id="' + ID + '-hbtns">',
        '<button class="' + ID + '-hbtn" id="' + ID + '-min">\u2014</button>',
        '<button class="' + ID + '-hbtn" id="' + ID + '-cls">\u00D7</button>',
      '</div>',
    '</div>',

    '<div id="' + ID + '-body">',

      /* Modifier keys */
      '<div class="' + ID + '-sec">',
        '<div class="' + ID + '-lbl">Modifier Keys</div>',
        '<div class="' + ID + '-row">',
          btn('mbtn', 'm-ctrl',  null, null, false, 'Ctrl'),
          btn('mbtn', 'm-alt',   null, null, false, 'Alt'),
          btn('mbtn', 'm-shift', null, null, false, 'Shift'),
          btn('mbtn', 'm-meta',  null, null, false, '\u229E&nbsp;Win'),
        '</div>',
      '</div>',

      /* Right-click arm */
      '<div class="' + ID + '-sec">',
        '<button class="' + ID + '-rcbtn" id="' + ID + '-rc">',
          '\uD83D\uDDB1 Right-Click Next Tap: OFF',
        '</button>',
      '</div>',

      /* Shortcuts */
      '<div class="' + ID + '-sec">',
        '<div class="' + ID + '-lbl">Shortcuts</div>',
        '<div class="' + ID + '-g4">',
          btn('sc', null, 'c', null, true,  'Copy'),
          btn('sc', null, 'v', null, true,  'Paste'),
          btn('sc', null, 'z', null, true,  'Undo'),
          btn('sc', null, 'y', null, true,  'Redo'),
          btn('sc', null, 'a', null, true,  'Sel&nbsp;All'),
          btn('sc', null, 'x', null, true,  'Cut'),
          btn('sc', null, 's', null, true,  'Save'),
          btn('sc', null, 'f', null, true,  'Find'),
          btn('sc', null, 't', null, true,  'New&nbsp;Tab'),
          btn('sc', null, 'w', null, true,  'Close'),
          btn('sc', null, 'F5',  'F5',  false, 'F5&nbsp;\u21BA'),
          btn('sc', null, 'F11', 'F11', false, 'F11&nbsp;\u26F6'),
        '</div>',
      '</div>',

      /* Special keys */
      '<div class="' + ID + '-sec">',
        '<div class="' + ID + '-lbl">Keys</div>',
        '<div class="' + ID + '-g5">',
          btn('key', null, 'Escape',     'Escape',     false, 'Esc'),
          btn('key', null, 'Tab',        'Tab',        false, 'Tab'),
          btn('key', null, 'Enter',      'Enter',      false, '\u21B5'),
          btn('key', null, 'Backspace',  'Backspace',  false, '\u232B'),
          btn('key', null, 'Delete',     'Delete',     false, 'Del'),
          btn('key', null, 'Home',       'Home',       false, 'Home'),
          btn('key', null, 'End',        'End',        false, 'End'),
          btn('key', null, 'PageUp',     'PageUp',     false, 'PgUp'),
          btn('key', null, 'PageDown',   'PageDown',   false, 'PgDn'),
          btn('key', null, ' ',          'Space',      false, 'Spc'),
          btn('key', null, 'ArrowUp',    'ArrowUp',    false, '\u25B2'),
          btn('key', null, 'ArrowLeft',  'ArrowLeft',  false, '\u25C4'),
          btn('key', null, 'ArrowDown',  'ArrowDown',  false, '\u25BC'),
          btn('key', null, 'ArrowRight', 'ArrowRight', false, '\u25BA'),
          btn('key', null, 'PrintScreen','PrintScreen',false, 'PrtSc'),
        '</div>',
      '</div>',

      /* Text input */
      '<div class="' + ID + '-sec">',
        '<div class="' + ID + '-lbl">Type Text</div>',
        '<div class="' + ID + '-trow">',
          '<input id="' + ID + '-txt" type="text" placeholder="Type &amp; send to desktop\u2026">',
          '<button id="' + ID + '-send">Send</button>',
        '</div>',
      '</div>',

      /* Scroll */
      '<div class="' + ID + '-sec">',
        '<div class="' + ID + '-lbl">Scroll</div>',
        '<div class="' + ID + '-srow">',
          '<button class="' + ID + '-sbtn" id="' + ID + '-su">\u2191 Up</button>',
          '<button class="' + ID + '-sbtn" id="' + ID + '-sd">\u2193 Down</button>',
        '</div>',
        '<div class="' + ID + '-srow">',
          '<button class="' + ID + '-sbtn" id="' + ID + '-sl">\u2190 Left</button>',
          '<button class="' + ID + '-sbtn" id="' + ID + '-sr">\u2192 Right</button>',
        '</div>',
      '</div>',

    '</div>'
  ].join('');

  document.body.appendChild(panel);

  /* ── Drag ── */
  function startDrag(cx, cy) {
    drag.on = true;
    drag.ox = cx; drag.oy = cy;
    drag.pl = parseInt(panel.style.left) || 8;
    drag.pt = parseInt(panel.style.top)  || 70;
  }
  function moveDrag(cx, cy) {
    if (!drag.on) return;
    panel.style.left = Math.max(0, drag.pl + cx - drag.ox) + 'px';
    panel.style.top  = Math.max(0, drag.pt + cy - drag.oy) + 'px';
  }
  function endDrag() { drag.on = false; }

  var hdr = document.getElementById(ID + '-hdr');
  hdr.addEventListener('touchstart', function (e) {
    if (e.target.closest('.' + ID + '-hbtn')) return;
    startDrag(e.touches[0].clientX, e.touches[0].clientY);
    e.preventDefault();
  }, { passive: false });
  document.addEventListener('touchmove', function (e) {
    if (!drag.on) return;
    moveDrag(e.touches[0].clientX, e.touches[0].clientY);
    e.preventDefault();
  }, { passive: false });
  document.addEventListener('touchend', endDrag);

  /* Also support mouse drag for desktop testing */
  hdr.addEventListener('mousedown', function (e) {
    if (e.target.closest('.' + ID + '-hbtn')) return;
    startDrag(e.clientX, e.clientY);
  });
  document.addEventListener('mousemove', function (e) { moveDrag(e.clientX, e.clientY); });
  document.addEventListener('mouseup', endDrag);

  /* ── Minimise / Close ── */
  document.getElementById(ID + '-min').addEventListener('click', function () {
    minimized = !minimized;
    document.getElementById(ID + '-body').style.display = minimized ? 'none' : '';
    this.textContent = minimized ? '\u25A1' : '\u2014';
  });
  document.getElementById(ID + '-cls').addEventListener('click', function () {
    panel.remove();
    styleEl.remove();
  });

  /* ── Modifier key toggles ── */
  ['ctrl', 'alt', 'shift', 'meta'].forEach(function (k) {
    document.getElementById(ID + '-m-' + k).addEventListener('click', function () {
      mod[k] = !mod[k];
      updateModBtns();
    });
  });

  /* ── Right-click mode ── */
  var rcBtn = document.getElementById(ID + '-rc');

  function setRc(on) {
    rcArmed = on;
    rcBtn.style.background  = on ? '#7f1d1d' : '#1e293b';
    rcBtn.style.borderColor = on ? '#ef4444' : '#334155';
    rcBtn.style.color       = on ? '#fca5a5' : '#cbd5e1';
    rcBtn.textContent       = '\uD83D\uDDB1 Right-Click Next Tap: ' + (on ? 'ON' : 'OFF');
    if (on) document.addEventListener('click', rcIntercept, { once: true, capture: true });
    else    document.removeEventListener('click', rcIntercept, true);
  }

  rcBtn.addEventListener('click', function () { setRc(!rcArmed); });

  function rcIntercept(e) {
    if (panel.contains(e.target)) {
      /* Click was on our panel — re-arm and wait for the next one */
      document.addEventListener('click', rcIntercept, { once: true, capture: true });
      return;
    }
    e.preventDefault();
    e.stopImmediatePropagation();
    var el = e.target;
    var o2 = {
      clientX: e.clientX, clientY: e.clientY,
      button: 2, buttons: 2,
      bubbles: true, cancelable: true
    };
    el.dispatchEvent(new MouseEvent('mousedown', o2));
    setTimeout(function () {
      el.dispatchEvent(new MouseEvent('mouseup', o2));
      el.dispatchEvent(new MouseEvent('contextmenu', {
        clientX: e.clientX, clientY: e.clientY,
        bubbles: true, cancelable: true
      }));
    }, 60);
    setRc(false);
  }

  /* ── Key / shortcut buttons ── */
  panel.addEventListener('click', function (e) {
    var b = e.target.closest('[data-key]');
    if (!b) return;
    if (b.dataset.ctrl === '1') { mod.ctrl = true; updateModBtns(); }
    sendKey(b.dataset.key, b.dataset.code);
  });

  /* ── Text send ── */
  document.getElementById(ID + '-send').addEventListener('click', function () {
    var inp = document.getElementById(ID + '-txt');
    if (inp.value) { typeText(inp.value); inp.value = ''; }
  });
  document.getElementById(ID + '-txt').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      e.stopPropagation();
      if (this.value) { typeText(this.value); this.value = ''; }
    }
  });

  /* ── Scroll ── */
  document.getElementById(ID + '-su').addEventListener('click', function () { sendScroll(0,    -400); });
  document.getElementById(ID + '-sd').addEventListener('click', function () { sendScroll(0,     400); });
  document.getElementById(ID + '-sl').addEventListener('click', function () { sendScroll(-400,    0); });
  document.getElementById(ID + '-sr').addEventListener('click', function () { sendScroll( 400,    0); });

}());
