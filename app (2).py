# -*- coding: utf-8 -*-
"""
信号機入札ナビ
中小企業庁「官公需情報ポータルサイト検索API」(http://www.kkj.go.jp/api/) を利用して、
信号機関連(国家公安委員会発注)の入札公告を検索できるシンプルなWebアプリ。

起動方法:
    pip install -r requirements.txt
    python app.py
    ブラウザで http://localhost:5001 を開く
"""

from __future__ import annotations

import json
import os

from flask import Flask, jsonify, request, Response

import kkj_client

app = Flask(__name__)


@app.route("/api/search")
def api_search():
    prefecture = request.args.get("prefecture", "").strip()
    category = request.args.get("category", "").strip()
    procedure_type = request.args.get("procedureType", "").strip()
    certification = request.args.get("certification", "").strip()

    data = kkj_client.search(
        prefecture=prefecture,
        category=category,
        procedure_type=procedure_type,
        certification=certification,
    )

    status_code = 200
    if data["error"]:
        status_code = 502 if "接続" in data["error"] or "解析" in data["error"] else 400

    return jsonify(data), status_code


INDEX_HTML = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>信号機入札ナビ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@600;700&family=Noto+Sans+JP:wght@400;500;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#F7F8F5;
    --panel:#FFFFFF;
    --ink:#1B2A3D;
    --muted:#6B7383;
    --line:#E3E6E1;
    --accent:#2E5C8A;
    --accent-dark:#1E4266;
    --red:#D64545;
    --yellow:#E8A93A;
    --green:#3C8A5B;
    --gray:#9AA2AC;
  }
  *{box-sizing:border-box;}
  body{
    margin:0;
    background:var(--bg);
    color:var(--ink);
    font-family:'Noto Sans JP',sans-serif;
  }
  .topbar{
    background:var(--ink);
    color:#fff;
    padding:22px 28px;
    display:flex;
    align-items:center;
    gap:16px;
  }
  .signal-mark{
    width:22px;height:56px;
    background:#0F1826;
    border-radius:6px;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
    padding:5px 0;
    flex-shrink:0;
  }
  .signal-mark span{
    width:10px;height:10px;border-radius:50%;
    margin:0 auto;
    opacity:0.35;
  }
  .signal-mark span.on.r{background:var(--red);opacity:1;box-shadow:0 0 6px var(--red);}
  .signal-mark span.r{background:var(--red);}
  .signal-mark span.y{background:var(--yellow);}
  .signal-mark span.g{background:var(--green);}
  .topbar h1{
    font-family:'Barlow Semi Condensed',sans-serif;
    font-weight:700;
    font-size:28px;
    letter-spacing:0.02em;
    margin:0;
  }
  .topbar p{margin:2px 0 0;font-size:13px;color:#B9C2CF;}
  main{max-width:960px;margin:0 auto;padding:24px 20px 80px;}
  .panel{
    background:var(--panel);
    border:1px solid var(--line);
    border-radius:10px;
    padding:18px;
    margin-bottom:22px;
  }
  .search-row{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;}
  .field{display:flex;flex-direction:column;gap:5px;}
  .field label{font-size:12px;color:var(--muted);font-weight:500;}
  .field input, .field select{
    border:1px solid var(--line);
    border-radius:6px;
    padding:9px 10px;
    font-size:14px;
    font-family:inherit;
    background:#fff;
    color:var(--ink);
    min-width:140px;
  }
  .field.grow{flex:1;min-width:220px;}
  .field.grow input{width:100%;}
  button.search-btn{
    background:var(--accent);
    color:#fff;
    border:none;
    border-radius:6px;
    padding:10px 22px;
    font-size:14px;
    font-weight:500;
    cursor:pointer;
    font-family:'Noto Sans JP',sans-serif;
  }
  button.search-btn:hover{background:var(--accent-dark);}
  .status-line{font-size:13px;color:var(--muted);margin:0 0 14px 2px;}
  .status-line b{color:var(--ink);font-family:'Roboto Mono',monospace;}
  .keyword-note{font-size:11.5px;color:var(--muted);margin:12px 2px 0;}
  .legend{display:flex;gap:16px;font-size:12px;color:var(--muted);margin:0 0 14px 2px;flex-wrap:wrap;}
  .legend .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle;}
  .card{
    display:flex;
    background:var(--panel);
    border:1px solid var(--line);
    border-radius:8px;
    margin-bottom:12px;
    overflow:hidden;
  }
  .card .strip{width:6px;flex-shrink:0;}
  .strip.red{background:var(--red);}
  .strip.yellow{background:var(--yellow);}
  .strip.green{background:var(--green);}
  .strip.gray{background:var(--gray);}
  .card-body{padding:14px 16px;flex:1;}
  .card-title{font-size:15px;font-weight:700;margin:0 0 6px;line-height:1.4;}
  .card-title a{color:var(--ink);text-decoration:none;}
  .card-title a:hover{color:var(--accent);text-decoration:underline;}
  .meta{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12.5px;color:var(--muted);}
  .meta b{color:var(--ink);font-weight:500;}
  .badge{
    display:inline-block;
    font-size:11px;
    padding:2px 8px;
    border-radius:10px;
    background:#EEF2F6;
    color:var(--accent-dark);
    font-weight:500;
  }
  .dates{margin-top:8px;font-family:'Roboto Mono',monospace;font-size:12px;color:var(--ink);display:flex;gap:16px;flex-wrap:wrap;}
  .dates span b{color:var(--muted);font-family:'Noto Sans JP',sans-serif;font-weight:500;margin-right:4px;}
  .attachments{margin-top:10px;display:flex;flex-wrap:wrap;gap:8px;}
  .attachments a{
    display:inline-flex;align-items:center;gap:4px;
    font-size:11.5px;
    color:var(--accent-dark);
    background:#F0F4F8;
    border:1px solid var(--line);
    border-radius:6px;
    padding:4px 9px;
    text-decoration:none;
  }
  .attachments a:hover{border-color:var(--accent);color:var(--accent);}
  .attachments a::before{content:"📎";font-size:11px;}
  .empty{padding:40px 10px;text-align:center;color:var(--muted);font-size:14px;}
  .pagination{display:flex;gap:6px;justify-content:center;margin:22px 0 8px;flex-wrap:wrap;}
  .pagination button{
    min-width:34px;height:34px;
    border:1px solid var(--line);
    background:#fff;
    color:var(--ink);
    border-radius:6px;
    font-family:'Roboto Mono',monospace;
    font-size:13px;
    cursor:pointer;
  }
  .pagination button:hover{border-color:var(--accent);color:var(--accent);}
  .pagination button.active{background:var(--accent);border-color:var(--accent);color:#fff;}
  .pagination button:disabled{opacity:0.35;cursor:default;}
  .pagination button.nav{font-family:'Noto Sans JP',sans-serif;padding:0 12px;width:auto;}
  .error{padding:14px;background:#FCEBEB;border:1px solid #E9BBBB;color:#8A2C2C;border-radius:8px;margin-bottom:16px;font-size:13.5px;}
  footer{max-width:960px;margin:0 auto;padding:0 20px 40px;font-size:12px;color:var(--muted);}
  footer a{color:var(--accent);}
</style>
</head>
<body>

<div class="topbar">
  <div class="signal-mark">
    <span class="r on"></span><span class="y"></span><span class="g"></span>
  </div>
  <div>
    <h1>信号機入札ナビ</h1>
    <p>信号機・信号灯器・信号制御機など信号機関連の入札公告のうち、国家公安委員会の案件だけを検索（締切が近い順）</p>
  </div>
</div>

<main>
  <div class="panel">
    <form id="searchForm">
      <div class="search-row">
        <div class="field">
          <label for="prefecture">都道府県</label>
          <select id="prefecture" name="prefecture"><option value="">すべて</option></select>
        </div>
        <div class="field">
          <label for="category">分類</label>
          <select id="category" name="category">
            <option value="">すべて</option>
            <option value="2">工事</option>
            <option value="1">物品</option>
            <option value="3">役務</option>
          </select>
        </div>
        <div class="field">
          <label for="procedureType">公示種別</label>
          <select id="procedureType" name="procedureType">
            <option value="">すべて</option>
            <option value="1">一般競争入札</option>
            <option value="2">簡易公募型競争入札</option>
            <option value="3">簡易公募型指名競争入札</option>
          </select>
        </div>
        <div class="field">
          <label for="certification">入札資格</label>
          <select id="certification" name="certification">
            <option value="">すべて</option>
            <option value="A">A</option>
            <option value="B">B</option>
            <option value="C">C</option>
            <option value="D">D</option>
          </select>
        </div>
        <button class="search-btn" type="submit">検索する</button>
      </div>
    </form>
    <p class="keyword-note">検索対象キーワード: 信号機 / 信号灯器 / 信号制御機 / 押ボタン信号 / 歩行者用灯器 / 灯器 / 信号柱 / 交通信号（発注機関: 国家公安委員会）</p>
  </div>

  <div class="legend">
    <span><span class="dot" style="background:var(--red)"></span>締切間近(3日以内)</span>
    <span><span class="dot" style="background:var(--yellow)"></span>締切まで10日以内</span>
    <span><span class="dot" style="background:var(--green)"></span>余裕あり</span>
    <span><span class="dot" style="background:var(--gray)"></span>締切日情報なし</span>
  </div>

  <div id="statusLine" class="status-line"></div>
  <div id="results"></div>
  <div id="pagination" class="pagination"></div>
</main>

<footer>
  本アプリは中小企業庁「<a href="https://www.kkj.go.jp/s/" target="_blank" rel="noopener">官公需情報ポータルサイト</a>」の検索APIを利用しています。個別の案件の詳細・最新状況は各発注機関に直接ご確認ください。すべての入札情報を網羅するものではありません。
</footer>

<script>
const PREF = __PREF_JSON__;
const prefSelect = document.getElementById('prefecture');
PREF.forEach(([code, name]) => {
  const opt = document.createElement('option');
  opt.value = code; opt.textContent = name;
  prefSelect.appendChild(opt);
});

const form = document.getElementById('searchForm');
const resultsEl = document.getElementById('results');
const statusEl = document.getElementById('statusLine');
const paginationEl = document.getElementById('pagination');

const PAGE_SIZE = 20;
let allResults = [];
let currentPage = 1;

const CATEGORY_LABEL = {"1":"物品","2":"工事","3":"役務"};

function fmtDate(s){
  if(!s) return null;
  return s.slice(0,10);
}

function renderPage(){
  resultsEl.innerHTML = '';
  const totalPages = Math.max(1, Math.ceil(allResults.length / PAGE_SIZE));
  if(currentPage > totalPages) currentPage = totalPages;
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageItems = allResults.slice(start, start + PAGE_SIZE);

  if(allResults.length === 0){
    resultsEl.innerHTML = '<div class="empty">該当する入札情報が見つかりませんでした。条件を変えてお試しください。</div>';
    paginationEl.innerHTML = '';
    return;
  }

  pageItems.forEach(r => {
    const card = document.createElement('div');
    card.className = 'card';
    const catLabel = CATEGORY_LABEL[r.category] || r.category || '';
    const loc = [r.prefectureName, r.cityName].filter(Boolean).join(' ');
    const attachmentsHtml = (r.attachments && r.attachments.length)
      ? `<div class="attachments">${r.attachments.map(a => `<a href="${a.uri}" target="_blank" rel="noopener">${a.name}</a>`).join('')}</div>`
      : '';
    card.innerHTML = `
      <div class="strip ${r.status}"></div>
      <div class="card-body">
        <p class="card-title"><a href="${r.externalDocumentURI || '#'}" target="_blank" rel="noopener">${r.projectName || '(件名不明)'}</a></p>
        <div class="meta">
          ${r.organizationName ? `<span><b>発注機関:</b> ${r.organizationName}</span>` : ''}
          ${loc ? `<span><b>地域:</b> ${loc}</span>` : ''}
          ${catLabel ? `<span class="badge">${catLabel}</span>` : ''}
          ${r.procedureType ? `<span class="badge">${r.procedureType}</span>` : ''}
          ${r.certification ? `<span class="badge">資格 ${r.certification}</span>` : ''}
        </div>
        <div class="dates">
          ${r.cftIssueDate ? `<span><b>公告日</b>${fmtDate(r.cftIssueDate)}</span>` : ''}
          ${r.tenderSubmissionDeadline ? `<span><b>入札締切</b>${fmtDate(r.tenderSubmissionDeadline)}</span>` : ''}
          ${r.openingTendersEvent ? `<span><b>開札日</b>${fmtDate(r.openingTendersEvent)}</span>` : ''}
        </div>
        ${attachmentsHtml}
      </div>
    `;
    resultsEl.appendChild(card);
  });

  renderPagination(totalPages);
  window.scrollTo({top: 0, behavior: 'instant'});
}

function renderPagination(totalPages){
  paginationEl.innerHTML = '';
  if(totalPages <= 1) return;

  const makeBtn = (label, page, opts = {}) => {
    const btn = document.createElement('button');
    btn.textContent = label;
    if(opts.nav) btn.classList.add('nav');
    if(page === currentPage) btn.classList.add('active');
    if(opts.disabled) btn.disabled = true;
    btn.addEventListener('click', () => { currentPage = page; renderPage(); });
    return btn;
  };

  paginationEl.appendChild(makeBtn('前へ', currentPage - 1, {nav:true, disabled: currentPage === 1}));

  const windowSize = 4;
  let startPage = Math.max(1, currentPage - windowSize);
  let endPage = Math.min(totalPages, currentPage + windowSize);

  if(startPage > 1) paginationEl.appendChild(makeBtn('1', 1));
  if(startPage > 2){
    const dots = document.createElement('span');
    dots.textContent = '…';
    dots.style.alignSelf = 'center';
    dots.style.color = 'var(--muted)';
    paginationEl.appendChild(dots);
  }
  for(let p = startPage; p <= endPage; p++){
    paginationEl.appendChild(makeBtn(String(p), p));
  }
  if(endPage < totalPages - 1){
    const dots = document.createElement('span');
    dots.textContent = '…';
    dots.style.alignSelf = 'center';
    dots.style.color = 'var(--muted)';
    paginationEl.appendChild(dots);
  }
  if(endPage < totalPages) paginationEl.appendChild(makeBtn(String(totalPages), totalPages));

  paginationEl.appendChild(makeBtn('次へ', currentPage + 1, {nav:true, disabled: currentPage === totalPages}));
}

async function runSearch(){
  const params = new URLSearchParams({
    prefecture: document.getElementById('prefecture').value,
    category: document.getElementById('category').value,
    procedureType: document.getElementById('procedureType').value,
    certification: document.getElementById('certification').value,
  });
  resultsEl.innerHTML = '<div class="empty">検索中...</div>';
  statusEl.textContent = '';
  paginationEl.innerHTML = '';
  try{
    const resp = await fetch('/api/search?' + params.toString());
    const data = await resp.json();
    if(data.error){
      resultsEl.innerHTML = `<div class="error">${data.error}</div>`;
      return;
    }
    allResults = data.results;
    currentPage = 1;
    statusEl.innerHTML = `ヒット件数: <b>${data.searchHits}</b> 件（取得: ${allResults.length}件・締切が近い順）`;
    renderPage();
  }catch(e){
    resultsEl.innerHTML = '<div class="error">通信エラーが発生しました。</div>';
  }
}

form.addEventListener('submit', (e) => { e.preventDefault(); runSearch(); });
runSearch();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    html = INDEX_HTML.replace("__PREF_JSON__", json.dumps(kkj_client.PREFECTURES, ensure_ascii=False))
    return Response(html, mimetype="text/html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
