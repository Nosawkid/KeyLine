const state = { token: localStorage.getItem("keyline_token"), user: null, apps: [], selected: null, keys: [] };
const $ = (selector) => document.querySelector(selector);
const api = async (path, options = {}) => {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(path, { ...options, headers });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Something went wrong.");
  return data;
};
const toast = (message) => { const el=$("#toast"); el.textContent=message; el.classList.add("show"); setTimeout(()=>el.classList.remove("show"),2600); };
const showDashboard = (visible) => { $("#welcome").classList.toggle("hidden", visible); $("#dashboard").classList.toggle("hidden", !visible); $("#sign-out").classList.toggle("hidden", !visible); };
const escapeHtml = (text="") => text.replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));

async function loadApps() { state.apps = await api("/applications"); $("#app-count").textContent=state.apps.length; $("#app-label").textContent=`${state.apps.length} total`; renderApps(); if(state.selected) await selectApp(state.selected.id); }
function renderApps() { const el=$("#applications"); el.innerHTML=state.apps.length ? state.apps.map(app=>`<button class="application ${state.selected?.id===app.id?"active":""}" data-id="${app.id}"><span class="app-icon">⌁</span><span><b>${escapeHtml(app.name)}</b><small>${escapeHtml(app.description || "No description")}</small></span></button>`).join("") : `<div class="empty-state"><div class="empty-orb">+</div><h2>Nothing here yet</h2><p>Create your first application to begin.</p></div>`; el.querySelectorAll(".application").forEach(button=>button.onclick=()=>selectApp(button.dataset.id)); }
async function selectApp(id) { state.selected=state.apps.find(app=>app.id===id); renderApps(); $("#empty-state").classList.add("hidden"); $("#app-details").classList.remove("hidden"); $("#selected-name").textContent=state.selected.name; $("#selected-description").textContent=state.selected.description || "No description provided."; state.keys=await api(`/applications/${id}/keys`); $("#key-count").textContent=state.keys.length; $("#keys-total").textContent=`${state.keys.length} total`; renderKeys(); try { const usage=await api(`/applications/${id}/usage?limit=1`); $("#request-count").textContent=usage.total; } catch { $("#request-count").textContent="—"; } }
function renderKeys() { const el=$("#keys"); el.innerHTML=state.keys.length ? state.keys.map(key=>`<div class="key"><div><b>${escapeHtml(key.name)}</b><code>${escapeHtml(key.key_prefix)}••••••••••</code><span class="status ${key.is_active?"":"off"}">${key.is_active ? "● Active" : "● Revoked"}</span></div><div class="key-meta">${key.expires_at ? `Expires ${new Date(key.expires_at).toLocaleDateString()}` : "No expiry"}<br><button class="text-button revoke" data-id="${key.id}" ${key.is_active?"":"disabled"}>Revoke</button></div></div>`).join("") : `<p class="subtle">No keys yet. Create one when you’re ready.</p>`; el.querySelectorAll(".revoke").forEach(button=>button.onclick=()=>revoke(button.dataset.id)); }
async function revoke(id) { if(!confirm("Revoke this key? This cannot be undone.")) return; try { await api(`/keys/${id}`,{method:"DELETE"}); toast("Key revoked"); await selectApp(state.selected.id); } catch(error){toast(error.message)} }

let mode="login";
$(".auth-tabs").onclick=(event)=>{const tab=event.target.closest(".tab");if(!tab)return;mode=tab.dataset.mode;document.querySelectorAll(".tab").forEach(item=>item.classList.toggle("active",item===tab));$("#password").autocomplete=mode==="login"?"current-password":"new-password";};
$("#auth-form").onsubmit=async(event)=>{event.preventDefault();const error=$("#auth-error");error.textContent="";try{const data=await api(`/auth/${mode}`,{method:"POST",body:JSON.stringify({email:$("#email").value,password:$("#password").value})});state.token=data.access_token;state.user=data.user;localStorage.setItem("keyline_token",state.token);$("#user-email").textContent=data.user.email;showDashboard(true);await loadApps();}catch(err){error.textContent=err.message;}};
$("#new-app").onclick=()=>$("#app-dialog").showModal(); $("#new-key").onclick=()=>$("#key-dialog").showModal();
$("#app-form").onsubmit=async(event)=>{event.preventDefault();try{const app=await api("/applications",{method:"POST",body:JSON.stringify({name:$("#app-name").value,description:$("#app-description").value||null})});$("#app-dialog").close();event.target.reset();await loadApps();await selectApp(app.id);toast("Application created");}catch(err){$("#app-error").textContent=err.message;}};
$("#key-form").onsubmit=async(event)=>{event.preventDefault();try{const expires=$("#key-expires").value;const key=await api(`/applications/${state.selected.id}/keys`,{method:"POST",body:JSON.stringify({name:$("#key-name").value,expires_at:expires?new Date(expires).toISOString():null})});$("#key-dialog").close();event.target.reset();$("#secret-value").textContent=key.api_key;$("#secret-dialog").showModal();await selectApp(state.selected.id);}catch(err){$("#key-error").textContent=err.message;}};
$("#copy-key").onclick=async()=>{await navigator.clipboard.writeText($("#secret-value").textContent);$("#copy-key").textContent="Copied";setTimeout(()=>$("#copy-key").textContent="Copy",1500);};
$("#sign-out").onclick=()=>{localStorage.removeItem("keyline_token");state.token=null;state.selected=null;showDashboard(false);};
async function initialize(){if(!state.token)return;try{state.user=await api("/auth/me");$("#user-email").textContent=state.user.email;showDashboard(true);await loadApps();}catch{localStorage.removeItem("keyline_token");state.token=null;}}
initialize();
