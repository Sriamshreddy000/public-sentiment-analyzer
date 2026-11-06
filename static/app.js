const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// pro-X / support -> green, anti-X / oppose -> red, everything else grey
const tone = (label) =>
  /^(pro-|support)/.test(label) ? "pro" : /^(anti-|oppose)/.test(label) ? "anti" : "neutral";

const OPTION_IDS = ["opt-posts", "opt-sort", "opt-comments", "opt-order"];
const fmtTime = (ts) => new Date(ts * 1000).toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
const countLine = (t) =>
  (t.num_comments != null ? `${t.num_comments} on Reddit · ` : "") +
  (t.comment_count ? `${t.comment_count} fetched` : '<span class="warn">⚠ no comments fetched</span>');

let activeIndex = null;

// ---------- "current data" bar ----------
function describe(o) {
  const per = o.comments === "all" ? "all comments" : `${o.comments} comments each`;
  return `${o.posts} ${o.sort} posts · ${per} · ${o.comment_order === "top" ? "most upvoted" : "newest"} comments`;
}

async function loadSummary(presetControls = false) {
  const s = await (await fetch("/api/summary")).json();
  const bar = $("databar");
  if (!s.topics) { bar.textContent = "No data yet."; return; }
  let text = `Current data: ${s.topics} topics · ${s.comments} comments · fetched ${fmtTime(s.fetched_utc)}`;
  text += s.options ? ` · settings: ${describe(s.options)}` : " · settings: from the CLI";
  bar.textContent = text;
  if (presetControls && s.options) {
    $("opt-posts").value = String(s.options.posts);
    $("opt-sort").value = s.options.sort;
    $("opt-comments").value = String(s.options.comments);
    $("opt-order").value = s.options.comment_order;
  }
}

// ---------- topic list ----------
async function loadTopics() {
  const list = $("topic-list");
  try {
    const topics = await (await fetch("/api/topics")).json();
    if (!topics.length) {
      list.innerHTML = '<li class="muted pad">No topics yet. Pick your settings above and click “Refresh”.</li>';
      return;
    }
    list.innerHTML = topics.map((t) => `
      <li class="item ${t.index === activeIndex ? "active" : ""}" data-i="${t.index}">
        <div class="t">${esc(t.title)}</div>
        <div class="meta">r/${esc(t.subreddit)} · ${countLine(t)}${
          t.mode === "entity" ? " · " + esc(t.entities.join(" vs ")) : ""}</div>
      </li>`).join("");
    list.querySelectorAll(".item").forEach((el) =>
      el.addEventListener("click", () => openTopic(Number(el.dataset.i))));
  } catch {
    list.innerHTML = '<li class="muted pad">Could not reach the server.</li>';
  }
}

// ---------- topic report ----------
async function openTopic(i) {
  activeIndex = i;
  document.querySelectorAll(".topics .item").forEach((el) =>
    el.classList.toggle("active", Number(el.dataset.i) === i));
  $("report").innerHTML = '<p class="muted">Loading report…</p>';
  document.querySelector(".report-pane").scrollTop = 0;
  const res = await fetch(`/api/topics/${i}`);
  if (!res.ok) { $("report").innerHTML = '<p class="muted">Topic not found.</p>'; return; }
  renderReport(await res.json());
}

function renderReport(r) {
  let html = `
    <h2>${esc(r.title)}</h2>
    <div class="sub">r/${esc(r.subreddit)} · ${countLine(r)}${
      r.url ? ` · <a href="${esc(r.url)}" target="_blank" rel="noopener">Open on Reddit ↗</a>` : ""}</div>
    <div class="chips">
      <span class="chip">${r.mode === "entity" ? "Entity vs entity" : "Topic stance"}</span>
      ${r.entities.map((e) => `<span class="chip">${esc(e)}</span>`).join("")}
    </div>`;

  if (!r.total) {
    const why = !r.comment_count
      ? `Couldn't fetch comments for this post: ${esc(r.fetch_error || "unknown reason")}. Try refreshing.`
      : `${r.comment_count} comments were fetched, but none were long enough to analyze or they haven't been labeled yet. Try refreshing.`;
    html += `<div class="card"><p class="muted">${why}</p></div>`;
    $("report").innerHTML = html;
    return;
  }

  html += `<div class="card"><h3>Stance distribution · ${r.total} comments used</h3>` +
    r.distribution.map((d) => `
      <div class="row ${tone(d.label)}">
        <span class="lab" title="${esc(d.label)}">${esc(d.label)}</span>
        <div class="track"><div class="fill" style="width:${d.pct}%"></div></div>
        <span class="num">${d.count} (${d.pct}%)</span>
      </div>`).join("") +
    `<div class="note">${r.excluded
      ? `${r.excluded} of ${r.comment_count} fetched comments were shorter than ${r.min_len} characters and excluded.`
      : `All ${r.comment_count} fetched comments were used.`}</div></div>`;

  if (!r.reasons.length) {
    html += `<div class="card"><h3>Reasons</h3><p class="muted">All neutral — no strong leaning detected.</p></div>`;
  } else {
    html += r.reasons.map((x) => `
      <div class="card reason ${tone(x.label)}">
        <h4>${esc(x.label)}</h4>
        <div class="kw chips">${x.keywords.length
          ? x.keywords.map((k) => `<span class="chip">${esc(k)}</span>`).join("")
          : '<span class="muted small">Not enough data for keywords</span>'}</div>
        ${x.examples.map((e) => `<blockquote>${esc(e)}</blockquote>`).join("")}
      </div>`).join("");
  }
  $("report").innerHTML = html;
}

// ---------- refresh ----------
let poll = null;

async function startRefresh() {
  const comments = $("opt-comments").value;
  const body = {
    posts: Number($("opt-posts").value),
    sort: $("opt-sort").value,
    comments: comments === "all" ? "all" : Number(comments),
    comment_order: $("opt-order").value,
  };
  if (comments === "all" &&
      !confirm("Analyzing every comment can take a long time (possibly an hour or more for busy posts). Continue?")) return;
  const res = await fetch("/api/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.ok || res.status === 409) watchRefresh();  // 409 = one is already running
}

function setControlsDisabled(disabled) {
  $("refresh").disabled = disabled;
  OPTION_IDS.forEach((id) => ($(id).disabled = disabled));
}

function watchRefresh() {
  setControlsDisabled(true);
  $("progress").classList.remove("hidden", "error");
  clearInterval(poll);
  poll = setInterval(async () => {
    const s = await (await fetch("/api/refresh/status")).json();
    $("progress-fill").style.width = `${(s.step / s.total_steps) * 100}%`;
    $("progress-text").textContent = s.error
      ? s.error
      : s.running ? `Step ${s.step}/${s.total_steps}: ${s.label}…` : "Done";
    $("progress-detail").textContent = s.running ? s.detail : "";
    if (!s.running) {
      clearInterval(poll);
      setControlsDisabled(false);
      if (s.error) $("progress").classList.add("error");
      else setTimeout(() => $("progress").classList.add("hidden"), 2500);
      activeIndex = null;
      $("report").innerHTML =
        '<div class="empty"><h2>Pick a topic</h2><p>Data refreshed — select a topic on the left.</p></div>';
      loadTopics();
      loadSummary();
    }
  }, 1500);
}

$("refresh").addEventListener("click", startRefresh);
loadTopics();
loadSummary(true);
// If a refresh was already running (e.g. page reloaded), resume showing progress
fetch("/api/refresh/status").then((r) => r.json()).then((s) => { if (s.running) watchRefresh(); });
