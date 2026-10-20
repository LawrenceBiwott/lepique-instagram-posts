/**
 * Lepique Fashions — AI Era Enhancement Suite
 * Includes: AI Style Assistant · Scroll Reveals · Smart Search · Smart Size Finder · Hero Typing
 */
(function () {
  'use strict';

  /* ─── INJECT STYLES ─────────────────────────────────────────── */
  const css = `
    /* ── SCROLL REVEAL ── */
    [data-reveal]{opacity:0;transform:translateY(28px);transition:opacity .65s cubic-bezier(.22,1,.36,1),transform .65s cubic-bezier(.22,1,.36,1);}
    [data-reveal].revealed{opacity:1;transform:none;}
    [data-reveal][data-delay="1"]{transition-delay:.1s;}
    [data-reveal][data-delay="2"]{transition-delay:.2s;}
    [data-reveal][data-delay="3"]{transition-delay:.3s;}
    [data-reveal][data-delay="4"]{transition-delay:.4s;}
    [data-reveal][data-delay="5"]{transition-delay:.5s;}

    /* ── AI STYLE ASSISTANT ── */
    .lpq-ai-btn{position:fixed;bottom:6.5rem;right:2rem;z-index:198;background:linear-gradient(135deg,#111111 0%,#2b1f22 100%);color:#fff;border:1px solid rgba(192,96,112,.55);border-radius:28px;padding:.72rem 1.1rem;font-family:'Inter',sans-serif;font-size:.7rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;display:flex;align-items:center;gap:.48rem;box-shadow:0 4px 22px rgba(192,96,112,.28);transition:all .2s;white-space:nowrap;}
    .lpq-ai-btn:hover{box-shadow:0 6px 30px rgba(192,96,112,.45);transform:translateY(-2px);}
    .lpq-ai-btn-icon{font-size:.95rem;animation:lpq-sparkle 2.4s ease-in-out infinite;}
    @keyframes lpq-sparkle{0%,100%{opacity:1;transform:scale(1) rotate(0deg);}50%{opacity:.75;transform:scale(1.15) rotate(18deg);}}
    @media(max-width:768px){.lpq-ai-btn{bottom:5.2rem;right:1rem;}}

    .lpq-ai-panel{position:fixed;bottom:10.5rem;right:2rem;z-index:350;width:334px;max-width:calc(100vw - 2.4rem);background:#0f0f0f;border:1px solid rgba(192,96,112,.3);border-radius:14px;box-shadow:0 24px 64px rgba(0,0,0,.6);display:none;flex-direction:column;overflow:hidden;font-family:'Inter',sans-serif;}
    .lpq-ai-panel.open{display:flex;animation:lpq-panel-in .25s cubic-bezier(.22,1,.36,1);}
    @keyframes lpq-panel-in{from{opacity:0;transform:translateY(14px) scale(.97);}to{opacity:1;transform:none;}}
    @media(max-width:768px){.lpq-ai-panel{right:1rem;bottom:9.5rem;width:calc(100vw - 2rem);}}

    .lpq-ai-head{background:linear-gradient(135deg,#111 0%,#2b1f22 100%);padding:.9rem 1rem;display:flex;align-items:center;gap:.7rem;border-bottom:1px solid rgba(192,96,112,.18);}
    .lpq-ai-avatar{width:34px;height:34px;background:rgba(192,96,112,.18);border:1px solid rgba(192,96,112,.4);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.95rem;flex-shrink:0;}
    .lpq-ai-hname{font-size:.82rem;font-weight:800;color:#fff;letter-spacing:.03em;}
    .lpq-ai-hsub{font-size:.62rem;color:rgba(192,96,112,.85);letter-spacing:.1em;text-transform:uppercase;margin-top:.05rem;}
    .lpq-ai-x{margin-left:auto;background:none;border:none;color:rgba(255,255,255,.4);font-size:1.2rem;cursor:pointer;padding:0 .15rem;line-height:1;transition:color .15s;}
    .lpq-ai-x:hover{color:#fff;}

    .lpq-ai-chat{padding:.9rem;max-height:262px;overflow-y:auto;display:flex;flex-direction:column;gap:.65rem;scroll-behavior:smooth;}
    .lpq-ai-chat::-webkit-scrollbar{width:4px;}
    .lpq-ai-chat::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:4px;}

    .lpq-msg-ai{background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.08);border-radius:8px 8px 8px 2px;padding:.65rem .85rem;font-size:.8rem;color:rgba(255,255,255,.9);line-height:1.55;max-width:90%;white-space:pre-line;animation:lpq-fadein .3s ease;}
    .lpq-msg-user{background:rgba(192,96,112,.22);border:1px solid rgba(192,96,112,.35);border-radius:8px 8px 2px 8px;padding:.55rem .85rem;font-size:.78rem;color:rgba(255,255,255,.9);align-self:flex-end;max-width:82%;animation:lpq-fadein .2s ease;}
    @keyframes lpq-fadein{from{opacity:0;transform:translateY(5px);}to{opacity:1;transform:none;}}

    .lpq-typing{display:flex;gap:4px;padding:.35rem .1rem;align-items:center;}
    .lpq-typing span{width:6px;height:6px;background:rgba(192,96,112,.7);border-radius:50%;animation:lpq-dot 1.2s ease-in-out infinite;}
    .lpq-typing span:nth-child(2){animation-delay:.2s;}
    .lpq-typing span:nth-child(3){animation-delay:.4s;}
    @keyframes lpq-dot{0%,100%{opacity:.3;transform:scale(.8);}50%{opacity:1;transform:scale(1.2);}}

    .lpq-chips{padding:.75rem .9rem;display:flex;flex-wrap:wrap;gap:.45rem;border-top:1px solid rgba(255,255,255,.06);background:rgba(0,0,0,.18);}
    .lpq-chip{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);color:rgba(255,255,255,.85);padding:.38rem .7rem;border-radius:20px;font-size:.74rem;font-weight:600;cursor:pointer;transition:all .18s;font-family:'Inter',sans-serif;}
    .lpq-chip:hover{background:rgba(192,96,112,.25);border-color:rgba(192,96,112,.55);color:#fff;}

    .lpq-rec{background:rgba(255,255,255,.04);border:1px solid rgba(192,96,112,.22);border-radius:9px;padding:.75rem;text-decoration:none;display:block;transition:all .18s;margin-top:.35rem;}
    .lpq-rec:hover{background:rgba(192,96,112,.1);border-color:rgba(192,96,112,.55);}
    .lpq-rec-emoji{font-size:1.05rem;margin-bottom:.22rem;display:block;}
    .lpq-rec-name{font-size:.8rem;font-weight:800;color:#fff;margin-bottom:.18rem;}
    .lpq-rec-desc{font-size:.7rem;color:rgba(255,255,255,.55);margin-bottom:.3rem;}
    .lpq-rec-price{font-size:.73rem;color:#c06070;font-weight:700;}
    .lpq-rec-arrow{float:right;color:rgba(192,96,112,.7);font-size:.9rem;margin-top:.1rem;}

    .lpq-wa-btn{display:block;background:#25d366;color:#fff;text-align:center;text-decoration:none;padding:.6rem 1rem;font-size:.75rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase;margin:.5rem .9rem .9rem;border-radius:6px;transition:background .18s;}
    .lpq-wa-btn:hover{background:#128c50;}
    .lpq-restart{width:100%;background:none;border:none;border-top:1px solid rgba(255,255,255,.06);color:rgba(255,255,255,.35);font-size:.68rem;padding:.6rem;cursor:pointer;font-family:'Inter',sans-serif;letter-spacing:.06em;transition:color .15s;}
    .lpq-restart:hover{color:rgba(255,255,255,.65);}

    /* ── AI SEARCH BAR ── */
    .lpq-search-wrap{position:relative;max-width:640px;margin:0 auto 2rem;}
    .lpq-search-input{width:100%;padding:.9rem 3.5rem .9rem 1.2rem;border:1.5px solid rgba(192,96,112,.3);border-radius:8px;font-family:'Inter',sans-serif;font-size:.9rem;color:#111;background:#fff;outline:none;transition:border-color .2s,box-shadow .2s;}
    .lpq-search-input:focus{border-color:#c06070;box-shadow:0 0 0 3px rgba(192,96,112,.1);}
    .lpq-search-input::placeholder{color:#9ca3af;}
    .lpq-search-icon{position:absolute;right:1rem;top:50%;transform:translateY(-50%);font-size:1.1rem;cursor:pointer;color:#c06070;transition:transform .2s;}
    .lpq-search-icon:hover{transform:translateY(-50%) scale(1.15);}
    .lpq-search-result{font-size:.8rem;color:#6b7280;text-align:center;margin-top:-.5rem;margin-bottom:1rem;min-height:1.2rem;font-family:'Inter',sans-serif;}
    .lpq-search-result strong{color:#c06070;}

    /* ── SMART SIZE FINDER ── */
    .lpq-size-finder{background:#fff;border:1.5px solid rgba(192,96,112,.25);border-radius:10px;padding:1.4rem 1.6rem;margin-top:1.5rem;max-width:480px;}
    .lpq-sf-title{font-family:'Inter',sans-serif;font-size:.82rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#c06070;margin-bottom:1rem;}
    .lpq-sf-row{display:flex;align-items:center;gap:.8rem;margin-bottom:.9rem;flex-wrap:wrap;}
    .lpq-sf-label{font-size:.82rem;font-weight:600;color:#6b7280;white-space:nowrap;font-family:'Inter',sans-serif;}
    .lpq-sf-input{flex:1;min-width:80px;padding:.5rem .75rem;border:1px solid #ece0e3;border-radius:6px;font-size:.9rem;color:#111;font-family:'Inter',sans-serif;outline:none;transition:border-color .2s;}
    .lpq-sf-input:focus{border-color:#c06070;}
    .lpq-sf-unit{display:flex;gap:.4rem;}
    .lpq-sf-unit button{padding:.38rem .65rem;border:1px solid #ece0e3;border-radius:6px;font-size:.75rem;font-weight:700;cursor:pointer;background:#fff;color:#6b7280;font-family:'Inter',sans-serif;transition:all .15s;}
    .lpq-sf-unit button.active{background:#111;color:#fff;border-color:#111;}
    .lpq-sf-result{background:linear-gradient(135deg,#111,#2b1f22);color:#fff;border-radius:8px;padding:1rem 1.2rem;text-align:center;margin-top:.8rem;display:none;}
    .lpq-sf-result.show{display:block;animation:lpq-fadein .3s ease;}
    .lpq-sf-size{font-family:'Playfair Display',serif;font-size:2.2rem;font-weight:800;color:#c06070;line-height:1;}
    .lpq-sf-sizelabel{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-top:.3rem;}
    .lpq-sf-note{font-size:.78rem;color:rgba(255,255,255,.7);margin-top:.5rem;line-height:1.5;}
    .lpq-sf-btn{display:inline-block;margin-top:.75rem;background:#c06070;color:#111;padding:.5rem 1.2rem;border-radius:6px;font-size:.75rem;font-weight:800;text-decoration:none;letter-spacing:.07em;text-transform:uppercase;}
    .lpq-sf-error{background:rgba(229,62,62,.1);border:1px solid rgba(229,62,62,.3);color:#e53e3e;border-radius:6px;padding:.65rem 1rem;font-size:.8rem;margin-top:.8rem;display:none;text-align:center;}
    .lpq-sf-error.show{display:block;}

    /* ── HERO AI BADGE ── */
    .lpq-ai-hero-badge{display:inline-flex;align-items:center;gap:.4rem;background:rgba(192,96,112,.1);border:1px solid rgba(192,96,112,.3);color:#c06070;font-size:.62rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;padding:.28rem .75rem;border-radius:20px;margin-bottom:.6rem;}
    .lpq-ai-hero-badge::before{content:'✦';font-size:.7rem;}

    /* ── TYPING CURSOR ── */
    .lpq-typing-word{color:#c06070;}
    .lpq-cursor{display:inline-block;width:2px;height:.9em;background:#c06070;margin-left:2px;vertical-align:middle;animation:lpq-blink .7s step-end infinite;}
    @keyframes lpq-blink{0%,100%{opacity:1;}50%{opacity:0;}}

    /* ── AI SECTION ── */
    .lpq-ai-section{background:linear-gradient(135deg,#111111 0%,#1a1015 50%,#111111 100%);padding:5rem 5%;text-align:center;position:relative;overflow:hidden;}
    .lpq-ai-section::before{content:'';position:absolute;top:-50%;left:-20%;width:700px;height:700px;border-radius:50%;background:radial-gradient(circle,rgba(192,96,112,.07) 0%,transparent 70%);pointer-events:none;}
    .lpq-ai-section::after{content:'';position:absolute;bottom:-30%;right:-10%;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(192,96,112,.05) 0%,transparent 70%);pointer-events:none;}
    .lpq-ai-section .section-tag{color:#c06070;}
    .lpq-ai-section .section-title{color:#fff;}
    .lpq-ai-section .section-sub{color:rgba(255,255,255,.6);margin:0 auto 2.5rem;}
    .lpq-ai-features{display:grid;grid-template-columns:repeat(3,1fr);gap:1.25rem;max-width:900px;margin:0 auto 2.5rem;}
    @media(max-width:768px){.lpq-ai-features{grid-template-columns:1fr;}}
    .lpq-ai-feat{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:1.5rem 1.2rem;text-align:left;transition:border-color .2s,background .2s;}
    .lpq-ai-feat:hover{background:rgba(192,96,112,.07);border-color:rgba(192,96,112,.3);}
    .lpq-ai-feat-icon{font-size:1.6rem;margin-bottom:.8rem;display:block;}
    .lpq-ai-feat-title{font-family:'Inter',sans-serif;font-size:.9rem;font-weight:800;color:#fff;margin-bottom:.4rem;}
    .lpq-ai-feat-desc{font-family:'Inter',sans-serif;font-size:.8rem;color:rgba(255,255,255,.5);line-height:1.6;}
    .lpq-ai-launch-btn{background:#c06070;color:#111;padding:.85rem 2rem;font-family:'Inter',sans-serif;font-weight:900;font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;border:none;border-radius:6px;cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;gap:.5rem;}
    .lpq-ai-launch-btn:hover{background:#d46a82;transform:translateY(-2px);box-shadow:0 8px 28px rgba(192,96,112,.4);}

    /* ── GRID DOTS BG for AI section ── */
    .lpq-dots-bg{position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.04) 1px,transparent 1px);background-size:28px 28px;pointer-events:none;}
  `;

  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  /* ─── SCROLL REVEAL ─────────────────────────────────────────── */
  function initScrollReveal() {
    const targets = document.querySelectorAll('section, .trust-item, .cat-card, .need-card, .tops-card, .look-card, .step, .review-card');
    targets.forEach((el, i) => {
      if (!el.hasAttribute('data-reveal')) {
        el.setAttribute('data-reveal', '');
        if (i % 4 === 1) el.setAttribute('data-delay', '1');
        else if (i % 4 === 2) el.setAttribute('data-delay', '2');
        else if (i % 4 === 3) el.setAttribute('data-delay', '3');
      }
    });
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); obs.unobserve(e.target); } });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
    document.querySelectorAll('[data-reveal]').forEach(el => obs.observe(el));
  }

  /* ─── HERO TYPING EFFECT ────────────────────────────────────── */
  function initHeroTyping() {
    const hero = document.querySelector('.hero h1 em');
    if (!hero) return;
    const words = ['Quality Ladies\' Jeans', 'Flare Jeans', 'Wide Leg Jeans', 'Skinny Jeans', 'Mom Jeans', 'Crop Tops', 'Denim Jackets'];
    let wi = 0, ci = 0, deleting = false;
    const cursor = document.createElement('span');
    cursor.className = 'lpq-cursor';
    hero.parentNode.insertBefore(cursor, hero.nextSibling);
    hero.classList.add('lpq-typing-word');

    function tick() {
      const word = words[wi];
      if (!deleting) {
        hero.textContent = word.slice(0, ci + 1);
        ci++;
        if (ci === word.length) { deleting = true; setTimeout(tick, 1800); return; }
        setTimeout(tick, 58);
      } else {
        hero.textContent = word.slice(0, ci - 1);
        ci--;
        if (ci === 0) { deleting = false; wi = (wi + 1) % words.length; setTimeout(tick, 380); return; }
        setTimeout(tick, 36);
      }
    }
    setTimeout(tick, 1200);
  }

  /* ─── AI STYLE ASSISTANT ────────────────────────────────────── */
  const questions = [
    { id: 'style', q: 'Hi! 👋 I\'m your Lepique Style AI.\n\nWhat\'s your everyday style?', opts: ['Casual & Relaxed 🌿', 'Trendy & Chic ✨', 'Smart & Polished 💼', 'Sporty & Active ⚡'] },
    { id: 'fit',   q: 'Love it! What fit works best for you?', opts: ['Slim & Fitted', 'Regular / Standard', 'Curvy & Relaxed', 'Plus Size (XL+)'] },
    { id: 'budget',q: 'What\'s your budget?', opts: ['Under Ksh 1,500', 'Ksh 1,500–2,500', 'Ksh 2,500+', 'Open to anything'] },
    { id: 'occ',   q: 'Last one — what\'s the occasion?', opts: ['Everyday / Casual 🏡', 'Work / Office 💼', 'Going out 🌙', 'Special event 🎉'] }
  ];
  let aiStep = 0, aiAnswers = {};

  function getRecs() {
    const s = aiAnswers.style || ''; const f = aiAnswers.fit || ''; const b = aiAnswers.budget || '';
    const recs = [];
    if (s.includes('Casual')) {
      if (f.includes('Slim') || f.includes('Regular')) {
        recs.push({ n:'Wide Leg Jeans', d:'Relaxed, on-trend & effortlessly cool', u:'wide-leg-jeans-nairobi.html', p:'from Ksh 2,500', e:'👖' });
        recs.push({ n:'Flare Jeans', d:'Classic casual with a feminine flare', u:'flare-jeans-nairobi.html', p:'from Ksh 2,500', e:'✨' });
      } else {
        recs.push({ n:'Mom Jeans', d:'Relaxed, flattering & super comfortable', u:'mom-jeans-nairobi.html', p:'from Ksh 2,500', e:'💛' });
        recs.push({ n:'High Waist Jeans', d:'Curvy-friendly & always on point', u:'high-waist-jeans-nairobi.html', p:'from Ksh 2,500', e:'💪' });
      }
    } else if (s.includes('Trendy')) {
      recs.push({ n:'New Arrivals ✦', d:'First to get the latest drops', u:'new-arrivals-nairobi.html', p:'from Ksh 1,500', e:'🔥' });
      recs.push({ n:'Wide Leg Jeans', d:'#1 trending style in Nairobi right now', u:'wide-leg-jeans-nairobi.html', p:'from Ksh 2,500', e:'✨' });
    } else if (s.includes('Smart')) {
      recs.push({ n:'Skinny Jeans', d:'Sleek, versatile & always polished', u:'skinny-jeans-nairobi.html', p:'from Ksh 1,500', e:'💼' });
      recs.push({ n:'Straight Jeans', d:'Clean silhouette for the office', u:'catalogue.html', p:'from Ksh 2,000', e:'🎯' });
    } else {
      recs.push({ n:'Three-Quarter Jeans', d:'Freedom of movement all day', u:'three-quarter-jeans-nairobi.html', p:'from Ksh 1,500', e:'⚡' });
      recs.push({ n:'Skinny Jeans', d:'Flexible & sleek for active days', u:'skinny-jeans-nairobi.html', p:'from Ksh 1,500', e:'🏃‍♀️' });
    }
    if (b.includes('1,500') && !b.includes('2,500')) {
      recs.push({ n:'Tops & Bodysuits', d:'Complete your look affordably', u:'bodysuits-nairobi.html', p:'from Ksh 1,000', e:'👚' });
    } else if (b.includes('2,500+')) {
      recs.push({ n:'Denim Jackets', d:'Premium statement piece', u:'denim-jackets-nairobi.html', p:'from Ksh 2,500', e:'🧥' });
    }
    return recs.slice(0, 3);
  }

  function buildWAMsg() {
    const clean = s => (s || '').replace(/[🌿✨💼⚡🏡🌙🎉💛💪🔥🎯⚡🏃‍♀️👚🧥]/gu, '').trim();
    const recs = getRecs().map(r => r.n.replace(' ✦','')).join(', ');
    return encodeURIComponent(`Hi Lepique Fashions! 👋\n\nI used your Style AI and I'm looking for:\n• Style: ${clean(aiAnswers.style)}\n• Fit: ${clean(aiAnswers.fit)}\n• Budget: ${aiAnswers.budget}\n• Occasion: ${clean(aiAnswers.occ)}\n\nRecommended: ${recs}\n\nCan you help me order?`);
  }

  function aiAddMsg(text, cls) {
    const chat = document.getElementById('lpq-ai-chat');
    if (!chat) return;
    const d = document.createElement('div');
    d.className = cls; d.textContent = text;
    chat.appendChild(d);
    chat.scrollTop = chat.scrollHeight;
    return d;
  }

  function aiTyping(cb) {
    const chat = document.getElementById('lpq-ai-chat');
    if (!chat) { cb(); return; }
    const d = document.createElement('div');
    d.className = 'lpq-msg-ai';
    d.innerHTML = '<div class="lpq-typing"><span></span><span></span><span></span></div>';
    chat.appendChild(d);
    chat.scrollTop = chat.scrollHeight;
    setTimeout(() => { d.remove(); cb(); }, 700);
  }

  function aiSetChips(opts, onClick) {
    const c = document.getElementById('lpq-ai-chips');
    if (!c) return;
    c.innerHTML = '';
    opts.forEach(opt => {
      const b = document.createElement('button');
      b.className = 'lpq-chip'; b.textContent = opt;
      b.onclick = () => onClick(opt);
      c.appendChild(b);
    });
  }

  function aiAsk(step) {
    const chips = document.getElementById('lpq-ai-chips');
    if (chips) chips.innerHTML = '';
    aiTyping(() => {
      aiAddMsg(questions[step].q, 'lpq-msg-ai');
      aiSetChips(questions[step].opts, (answer) => {
        aiAnswers[questions[step].id] = answer;
        aiAddMsg(answer.replace(/[🌿✨💼⚡🏡🌙🎉]/gu,'').trim(), 'lpq-msg-user');
        if (step < questions.length - 1) {
          aiAsk(step + 1);
        } else {
          aiShowRecs();
        }
      });
    });
  }

  function aiShowRecs() {
    const chips = document.getElementById('lpq-ai-chips');
    if (chips) chips.innerHTML = '';
    aiTyping(() => {
      aiAddMsg('✦ Perfect! Based on your answers, here are my top picks for you:', 'lpq-msg-ai');
      const chat = document.getElementById('lpq-ai-chat');
      if (!chat) return;
      getRecs().forEach(r => {
        const a = document.createElement('a');
        a.className = 'lpq-rec'; a.href = r.u;
        a.innerHTML = `<span class="lpq-rec-emoji">${r.e}</span><div class="lpq-rec-name">${r.n} <span class="lpq-rec-arrow">→</span></div><div class="lpq-rec-desc">${r.d}</div><div class="lpq-rec-price">${r.p}</div>`;
        chat.appendChild(a);
      });
      // WA button
      const wa = document.createElement('a');
      wa.href = `https://wa.me/254721672900?text=${buildWAMsg()}`;
      wa.target = '_blank';
      wa.className = 'lpq-wa-btn';
      wa.textContent = '📱 Order These on WhatsApp';
      chat.appendChild(wa);
      chat.scrollTop = chat.scrollHeight;
      // restart
      const panel = document.getElementById('lpq-ai-panel');
      if (panel) {
        const rb = document.createElement('button');
        rb.className = 'lpq-restart'; rb.textContent = '↺ Start over';
        rb.onclick = aiReset;
        panel.appendChild(rb);
      }
    });
  }

  function aiReset() {
    aiStep = 0; aiAnswers = {};
    const chat = document.getElementById('lpq-ai-chat');
    if (chat) chat.innerHTML = '';
    const chips = document.getElementById('lpq-ai-chips');
    if (chips) chips.innerHTML = '';
    const panel = document.getElementById('lpq-ai-panel');
    if (panel) { const r = panel.querySelector('.lpq-restart'); if (r) r.remove(); }
    aiAsk(0);
  }

  function toggleAI() {
    const panel = document.getElementById('lpq-ai-panel');
    if (!panel) return;
    const isOpen = panel.classList.contains('open');
    panel.classList.toggle('open', !isOpen);
    if (!isOpen && !aiAnswers.style) aiAsk(0);
  }

  function injectAIWidget() {
    // Trigger button
    const btn = document.createElement('button');
    btn.id = 'lpq-ai-btn';
    btn.className = 'lpq-ai-btn';
    btn.setAttribute('aria-label', 'AI Style Assistant');
    btn.onclick = toggleAI;
    btn.innerHTML = '<span class="lpq-ai-btn-icon">✦</span><span>Style AI</span>';
    document.body.appendChild(btn);

    // Panel
    const panel = document.createElement('div');
    panel.id = 'lpq-ai-panel';
    panel.className = 'lpq-ai-panel';
    panel.innerHTML = `
      <div class="lpq-ai-head">
        <div class="lpq-ai-avatar">✦</div>
        <div><div class="lpq-ai-hname">Lepique Style AI</div><div class="lpq-ai-hsub">Smart Recommendations · Free</div></div>
        <button class="lpq-ai-x" onclick="document.getElementById('lpq-ai-panel').classList.remove('open')" aria-label="Close">×</button>
      </div>
      <div class="lpq-ai-chat" id="lpq-ai-chat"></div>
      <div class="lpq-ai-chips" id="lpq-ai-chips"></div>
    `;
    document.body.appendChild(panel);
  }

  /* ─── SMART SEARCH (catalogue.html only) ───────────────────── */
  function initSmartSearch() {
    const filterBar = document.querySelector('.filter-bar');
    if (!filterBar) return;

    const wrap = document.createElement('div');
    wrap.className = 'lpq-search-wrap';
    wrap.innerHTML = `
      <input type="text" class="lpq-search-input" id="lpqSearch"
        placeholder="e.g. 'blue wide leg jeans under 2500' or 'black bodysuit'…"
        aria-label="Smart search" />
      <span class="lpq-search-icon" onclick="lpqRunSearch()" title="Search">✦</span>
      <div class="lpq-search-result" id="lpqResult"></div>
    `;
    filterBar.parentNode.insertBefore(wrap, filterBar);

    const inp = document.getElementById('lpqSearch');
    if (inp) inp.addEventListener('keydown', e => { if (e.key === 'Enter') lpqRunSearch(); });

    window.lpqRunSearch = function () {
      const q = (document.getElementById('lpqSearch')?.value || '').toLowerCase();
      if (!q.trim()) { clearSearch(); return; }

      const colors = ['blue','navy','black','white','grey','gray','green','red','pink','camel','light','dark','medium'];
      const cats   = { 'wide leg':'wide-leg','wide-leg':'wide-leg','mom':'mom','skinny':'skinny','flare':'flare',
                       'high waist':'high-waist','high-waist':'high-waist','printed':'printed','cargo':'cargo',
                       'three quarter':'three-quarter','jacket':'jacket','bodysuit':'bodysuit','top':'tshirt',
                       'vest':'tshirt','t-shirt':'tshirt','tshirt':'tshirt','leather':'jacket','denim':'jacket' };

      let detCat = null, detColor = null;
      for (const [k,v] of Object.entries(cats)) { if (q.includes(k)) { detCat = v; break; } }
      for (const c of colors)                   { if (q.includes(c)) { detColor = c; break; } }
      const under1500 = /under\s*1[,.]?500|cheap|budget|below\s*1[,.]?500/.test(q);
      const under2500 = /under\s*2[,.]?500|below\s*2[,.]?500/.test(q);

      const items = document.querySelectorAll('.catalog-item');
      let shown = 0;
      items.forEach(item => {
        const title = (item.dataset.title || item.dataset.src || '').toLowerCase();
        const cat   = (item.dataset.cat  || '').toLowerCase();
        const priceStr = item.dataset.price || '';
        const price = parseInt(priceStr.replace(/[^0-9]/,'')) || 9999;
        let show = true;
        if (detCat   && !cat.includes(detCat)                              ) show = false;
        if (detColor && !title.includes(detColor)                          ) show = false;
        if (under1500 && price > 1500                                       ) show = false;
        if (under2500 && !under1500 && price > 2500                        ) show = false;
        item.style.display = show ? '' : 'none';
        if (show) shown++;
      });

      const parts = [];
      if (detColor) parts.push(detColor);
      if (detCat)   parts.push(detCat.replace('-',' '));
      if (under1500) parts.push('under Ksh 1,500');
      else if (under2500) parts.push('under Ksh 2,500');
      const label  = parts.length ? parts.join(' · ') : q;
      const result = document.getElementById('lpqResult');
      if (result) result.innerHTML = shown
        ? `Showing <strong>${shown}</strong> result${shown!==1?'s':''} for <strong>${label}</strong> &nbsp;<a href="#" onclick="clearSearch();return false;" style="color:#c06070;text-decoration:none;font-weight:600;">× Clear</a>`
        : `No results for <strong>${label}</strong>. <a href="#" onclick="clearSearch();return false;" style="color:#c06070;text-decoration:none;font-weight:600;">Clear search</a>`;
    };

    window.clearSearch = function () {
      document.querySelectorAll('.catalog-item').forEach(i => i.style.display = '');
      const inp = document.getElementById('lpqSearch'); if (inp) inp.value = '';
      const result = document.getElementById('lpqResult'); if (result) result.innerHTML = '';
    };
  }

  /* ─── SMART SIZE FINDER ─────────────────────────────────────── */
  function injectSizeFinder() {
    // Find the existing size note to insert before it
    const sizeNote = document.querySelector('.size-note');
    if (!sizeNote) return;

    const finder = document.createElement('div');
    finder.className = 'lpq-size-finder';
    finder.innerHTML = `
      <div class="lpq-sf-title">✦ AI Size Finder — Enter Your Measurements</div>
      <div class="lpq-sf-row">
        <span class="lpq-sf-label">Waist:</span>
        <input type="number" class="lpq-sf-input" id="lpqWaist" placeholder="e.g. 30" min="20" max="60" />
        <div class="lpq-sf-unit">
          <button id="lpqUnitIn" class="active" onclick="lpqSetUnit('in')">inches</button>
          <button id="lpqUnitCm" onclick="lpqSetUnit('cm')">cm</button>
        </div>
      </div>
      <div class="lpq-sf-row">
        <button onclick="lpqFindSize()" style="background:#c06070;color:#111;border:none;padding:.55rem 1.4rem;border-radius:6px;font-family:'Inter',sans-serif;font-size:.8rem;font-weight:800;cursor:pointer;letter-spacing:.08em;text-transform:uppercase;">Find My Size</button>
        <button onclick="lpqResetSF()" style="background:none;border:1px solid #ece0e3;color:#6b7280;padding:.55rem .9rem;border-radius:6px;font-family:'Inter',sans-serif;font-size:.78rem;cursor:pointer;">Reset</button>
      </div>
      <div class="lpq-sf-result" id="lpqSFResult"></div>
      <div class="lpq-sf-error" id="lpqSFError">Please enter a valid waist measurement.</div>
    `;
    sizeNote.parentNode.insertBefore(finder, sizeNote);

    let sfUnit = 'in';
    window.lpqSetUnit = function(u) {
      sfUnit = u;
      document.getElementById('lpqUnitIn').classList.toggle('active', u==='in');
      document.getElementById('lpqUnitCm').classList.toggle('active', u==='cm');
    };

    // waist (inches) → jeans size lookup
    const sizeMap = [
      { max:25.5, size:'27', uk:'UK 6',  us:'US 2',  fit:'XS' },
      { max:26.5, size:'27', uk:'UK 8',  us:'US 4',  fit:'Small' },
      { max:27.5, size:'28', uk:'UK 10', us:'US 6',  fit:'Small / Med' },
      { max:28.5, size:'29', uk:'UK 10', us:'US 6',  fit:'Small / Med' },
      { max:29.5, size:'30', uk:'UK 12', us:'US 8',  fit:'Medium' },
      { max:30.5, size:'30', uk:'UK 12', us:'US 8',  fit:'Medium' },
      { max:31.5, size:'32', uk:'UK 14', us:'US 10', fit:'Large' },
      { max:32.5, size:'32', uk:'UK 14', us:'US 10', fit:'Large' },
      { max:33.5, size:'34', uk:'UK 16', us:'US 12', fit:'XL' },
      { max:35.5, size:'34', uk:'UK 16', us:'US 12', fit:'XL' },
      { max:37.5, size:'36', uk:'UK 18', us:'US 14', fit:'2XL' },
      { max:39.5, size:'38', uk:'UK 20', us:'US 16', fit:'3XL' },
      { max:41.5, size:'40', uk:'UK 22', us:'US 18', fit:'4XL' },
      { max:99,   size:'42', uk:'UK 24', us:'US 20', fit:'5XL' },
    ];

    window.lpqFindSize = function() {
      const val = parseFloat(document.getElementById('lpqWaist')?.value || '');
      const err = document.getElementById('lpqSFError');
      const res = document.getElementById('lpqSFResult');
      if (!val || val < 18 || val > 60) {
        err.classList.add('show'); res.classList.remove('show'); return;
      }
      err.classList.remove('show');
      const waistIn = sfUnit === 'cm' ? val / 2.54 : val;
      const match = sizeMap.find(m => waistIn <= m.max) || sizeMap[sizeMap.length-1];
      const waMsg = encodeURIComponent(`Hi Lepique! I'm a size ${match.size} (${match.uk} / ${match.us}). Can you help me order?`);
      res.innerHTML = `
        <div class="lpq-sf-size">${match.size}</div>
        <div class="lpq-sf-sizelabel">Your Recommended Jeans Size</div>
        <div class="lpq-sf-note">${match.uk} · ${match.us} · ${match.fit}<br/>Based on a ${val}${sfUnit} waist measurement</div>
        <a href="https://wa.me/254721672900?text=${waMsg}" target="_blank" class="lpq-sf-btn">📱 Order Size ${match.size} on WhatsApp</a>
      `;
      res.classList.add('show');
    };

    window.lpqResetSF = function() {
      const inp = document.getElementById('lpqWaist'); if (inp) inp.value = '';
      document.getElementById('lpqSFResult')?.classList.remove('show');
      document.getElementById('lpqSFError')?.classList.remove('show');
    };
  }

  /* ─── AI HOMEPAGE SECTION ───────────────────────────────────── */
  function injectAISection() {
    // Insert before the trust section if on homepage
    const trust = document.querySelector('.trust-section');
    if (!trust) return;

    const sec = document.createElement('section');
    sec.className = 'lpq-ai-section';
    sec.setAttribute('data-reveal','');
    sec.innerHTML = `
      <div class="lpq-dots-bg"></div>
      <div style="position:relative;z-index:1;">
        <div class="section-tag">Powered by AI</div>
        <h2 class="section-title" style="color:#fff;">Your Personal Style Assistant</h2>
        <p class="section-sub">Not sure what to pick? Our AI asks 4 quick questions and recommends the perfect jeans, tops and jackets from our collection — then connects you to order instantly on WhatsApp.</p>
        <div class="lpq-ai-features">
          <div class="lpq-ai-feat" data-reveal="" data-delay="1">
            <span class="lpq-ai-feat-icon">🎯</span>
            <div class="lpq-ai-feat-title">Smart Style Match</div>
            <div class="lpq-ai-feat-desc">Tell us your style, fit, budget and occasion. We match you to the right pieces from 147+ styles in seconds.</div>
          </div>
          <div class="lpq-ai-feat" data-reveal="" data-delay="2">
            <span class="lpq-ai-feat-icon">📐</span>
            <div class="lpq-ai-feat-title">AI Size Finder</div>
            <div class="lpq-ai-feat-desc">Enter your waist measurement in inches or cm and get your exact Lepique jeans size — no guessing, no returns.</div>
          </div>
          <div class="lpq-ai-feat" data-reveal="" data-delay="3">
            <span class="lpq-ai-feat-icon">🔍</span>
            <div class="lpq-ai-feat-title">Natural Language Search</div>
            <div class="lpq-ai-feat-desc">Search our full catalogue in plain English. Try "black wide leg jeans under 2500" or "casual blue bodysuit".</div>
          </div>
        </div>
        <button class="lpq-ai-launch-btn" onclick="toggleAI()">
          <span>✦</span> Launch Style AI
        </button>
      </div>
    `;
    trust.parentNode.insertBefore(sec, trust);
  }

  /* ─── INIT ──────────────────────────────────────────────────── */
  function init() {
    injectAIWidget();
    initScrollReveal();

    const path = location.pathname;
    const isHome     = path === '/' || path.endsWith('index.html') || path === '';
    const isCatalogue = path.includes('catalogue');

    if (isHome) {
      initHeroTyping();
      injectAISection();
      injectSizeFinder();
    }
    if (isCatalogue) {
      initSmartSearch();
      injectSizeFinder();
    }
    // Smart size finder on any page with .size-note
    if (!isHome && !isCatalogue && document.querySelector('.size-note')) {
      injectSizeFinder();
    }

    // Expose toggleAI globally for the AI section button
    window.toggleAI = toggleAI;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // ─── SERVICE WORKER REGISTRATION ──────────────────────────────
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js', {scope: '/'}).catch(() => {});
    });
  }

  // ─── WEB VITALS — INP LONG ANIMATION FRAME OBSERVER ─────────
  if ('PerformanceObserver' in window) {
    try {
      const loafObs = new PerformanceObserver(list => {
        for (const entry of list.getEntries()) {
          if (entry.duration > 200) {
            console.debug('[Lepique perf] Long animation frame:', Math.round(entry.duration) + 'ms');
          }
        }
      });
      loafObs.observe({type: 'long-animation-frame', buffered: true});
    } catch(e) {}
  }
})();
