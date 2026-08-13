(function(){
  const API_BASE = 'http://127.0.0.1:8000';
  let teachers = [];              // list from GET /teachers/ (includes average_rating, review_count)
  let currentReviews = [];        // reviews for whichever teacher's modal is open
  let activeTeacherId = null;
  let pickedScore = null;

  async function apiGet(path){
    const res = await fetch(API_BASE + path);
    if(!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
    return res.json();
  }

  async function apiPost(path, body){
    const res = await fetch(API_BASE + path, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    if(!res.ok){
      let detail = res.status;
      try{ const j = await res.json(); detail = j.detail || detail; }catch(e){}
      throw new Error(detail);
    }
    return res.json();
  }

  const grid = document.getElementById('grid');
  const toastEl = document.getElementById('toast');

  function toast(msg){
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    setTimeout(()=> toastEl.classList.remove('show'), 2200);
  }

  function uid(){ return Math.random().toString(36).slice(2,10) + Date.now().toString(36); }

  async function loadTeachers(){
    try{
      teachers = await apiGet('/teachers/?limit=100');
    } catch(e){
      console.error(e);
      grid.innerHTML = `<div class="empty">Could not reach the server. Is the API running at ${API_BASE}?</div>`;
      return;
    }
    render();
  }

  function scoreClass(avg){
    if(avg === null) return 'none';
    if(avg >= 8) return 'sage';
    if(avg >= 5) return 'gold';
    return 'brick';
  }

  function timeAgo(ts){
    const s = Math.floor((Date.now()-ts)/1000);
    if(s<60) return 'just now';
    const m = Math.floor(s/60); if(m<60) return m+'m ago';
    const h = Math.floor(m/60); if(h<24) return h+'h ago';
    const d = Math.floor(h/24); if(d<30) return d+'d ago';
    const mo = Math.floor(d/30); return mo+'mo ago';
  }

  function render(){
    const q = document.getElementById('searchInput').value.trim().toLowerCase();
    const roleF = document.getElementById('roleFilter').value;
    const sortF = document.getElementById('sortFilter').value;

    let list = teachers.filter(t=>{
      const matchesQ = !q || t.name.toLowerCase().includes(q) || t.dept.toLowerCase().includes(q);
      const matchesRole = roleF==='all' || t.role===roleF;
      return matchesQ && matchesRole;
    });

    if(sortF==='rating'){
      list.sort((a,b)=> (b.average_rating===null?-1:b.average_rating) - (a.average_rating===null?-1:a.average_rating));
    } else if(sortF==='reviews'){
      list.sort((a,b)=> b.review_count - a.review_count);
    } else {
      list.sort((a,b)=> a.name.localeCompare(b.name));
    }

    if(list.length === 0){
      grid.innerHTML = '<div class="empty">No entries match. Try a different search, or add someone to the ledger.</div>';
      return;
    }

    grid.innerHTML = list.map(t=>{
      const cls = scoreClass(t.average_rating);
      const scoreLabel = t.average_rating===null ? '—' : t.average_rating.toFixed(1);
      const avatar = t.photo_url
        ? `<div class="avatar" style="background-image:url('${API_BASE}${t.photo_url}')"></div>`
        : `<div class="avatar avatar-fallback">${initials(t.name)}</div>`;
      return `<div class="tcard" data-id="${t.id}">
        <div class="tcard-top">
          ${avatar}
          <span class="role-tag ${t.role==='Coordinator'?'coord':''}">${t.role}</span>
        </div>
        <div class="tname">${escapeHtml(t.name)}</div>
        <div class="tdept">${escapeHtml(t.dept)}</div>
        <div class="tcard-bottom">
          <div class="stamp ${cls}">${scoreLabel}</div>
          <div class="revcount"><b>${t.review_count}</b>review${t.review_count===1?'':'s'}</div>
        </div>
      </div>`;
    }).join('');

    grid.querySelectorAll('.tcard').forEach(card=>{
      card.addEventListener('click', ()=> openRateModal(card.dataset.id));
    });
  }

  function escapeHtml(str){
    return String(str).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function initials(name){
    return name.trim().split(/\s+/).slice(0,2).map(w=>w[0].toUpperCase()).join('');
  }

  /* ---------- Rate Modal ---------- */
  const rateOverlay = document.getElementById('rateOverlay');
  const scoreGrid = document.getElementById('scoreGrid');
  const scoreReadout = document.getElementById('scoreReadout');

  for(let i=1;i<=10;i++){
    const b = document.createElement('button');
    b.className = 'scorebtn';
    b.textContent = i;
    b.type = 'button';
    b.addEventListener('click', ()=>{
      pickedScore = i;
      scoreGrid.querySelectorAll('.scorebtn').forEach(el=>el.classList.remove('picked'));
      b.classList.add('picked');
      const words = {1:'Poor',2:'Poor',3:'Weak',4:'Weak',5:'Average',6:'Average',7:'Good',8:'Good',9:'Excellent',10:'Excellent'};
      scoreReadout.textContent = `${i} / 10 — ${words[i]}`;
    });
    scoreGrid.appendChild(b);
  }

  async function openRateModal(teacherId){
    activeTeacherId = teacherId;
    pickedScore = null;
    const t = teachers.find(x=>x.id===teacherId);
    if(!t) return;
    document.getElementById('rateName').textContent = t.name;
    document.getElementById('rateDept').textContent = `${t.role} · ${t.dept}`;
    document.getElementById('reviewText').value = '';
    document.getElementById('reviewerName').value = '';
    scoreGrid.querySelectorAll('.scorebtn').forEach(el=>el.classList.remove('picked'));
    scoreReadout.textContent = 'Tap a number to set your score.';
    document.getElementById('reviewList').innerHTML = '<div class="no-reviews">Loading reviews…</div>';
    renderModalAvatar(t);
    rateOverlay.classList.add('open');
    await loadReviews(teacherId);
  }

  function renderModalAvatar(t){
    const box = document.getElementById('modalAvatar');
    box.style.backgroundImage = t.photo_url ? `url('${API_BASE}${t.photo_url}')` : 'none';
    box.classList.toggle('avatar-fallback', !t.photo_url);
    box.textContent = t.photo_url ? '' : initials(t.name);
  }

  async function uploadPhoto(teacherId, file){
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/teachers/${teacherId}/photo`, {
      method: 'POST',
      body: formData
    });
    if(!res.ok){
      let detail = res.status;
      try{ const j = await res.json(); detail = j.detail || detail; }catch(err){}
      throw new Error(detail);
    }
    return res.json();
  }

  document.getElementById('photoInput').addEventListener('change', async (e)=>{
    const file = e.target.files[0];
    if(!file || !activeTeacherId) return;
    try{
      const updated = await uploadPhoto(activeTeacherId, file);
      toast('Photo updated.');
      renderModalAvatar(updated);
      await loadTeachers();
    } catch(err){
      console.error(err);
      toast('Could not upload photo — check the file type (jpg, png, webp).');
    } finally {
      e.target.value = '';
    }
  });

  async function loadReviews(teacherId){
    try{
      currentReviews = await apiGet(`/teachers/${teacherId}/reviews?sort=newest&limit=50`);
    } catch(e){
      console.error(e);
      currentReviews = [];
      toast('Could not load reviews.');
    }
    renderReviews();
  }

  function renderReviews(){
    const list = currentReviews;
    document.getElementById('rateRevCount').textContent = `${list.length} review${list.length===1?'':'s'}`;
    const container = document.getElementById('reviewList');
    if(list.length===0){
      container.innerHTML = '<div class="no-reviews">No reviews yet — be the first to leave one.</div>';
      return;
    }
    container.innerHTML = list.map(r=>{
      const cls = r.rating>=8?'sage':(r.rating>=5?'gold':'brick');
      const ts = new Date(r.created_at).getTime();
      return `<div class="review">
        <div class="review-top">
          <span class="chip stamp ${cls}" style="width:26px;height:26px;border-width:1.5px;transform:none;">${r.rating}</span>
          <span class="review-who">${escapeHtml(r.reviewer_name || 'Anonymous')} · ${timeAgo(ts)}</span>
          <button class="report-link" data-review-id="${r.id}" type="button">Report</button>
        </div>
        <div class="review-text">${escapeHtml(r.text)}</div>
      </div>`;
    }).join('');

    container.querySelectorAll('.report-link').forEach(btn=>{
      btn.addEventListener('click', ()=> reportReview(btn.dataset.reviewId));
    });
  }

  async function reportReview(reviewId){
    const validReasons = ['inappropriate','spam','harassment','off_topic','other'];
    let reason = prompt(`Reason (choose one): ${validReasons.join(', ')}`, 'inappropriate');
    if(!reason) return;
    reason = reason.trim().toLowerCase();
    if(!validReasons.includes(reason)){
      toast('Not a valid reason — pick one from the list.');
      return;
    }
    const details = prompt('Optional details (or leave blank):', '') || null;
    try{
      await apiPost(`/reports/reviews/${reviewId}`, { reason, details });
      toast('Review reported. Thanks for flagging it.');
    } catch(e){
      console.error(e);
      toast('Could not submit report.');
    }
  }

  document.getElementById('submitReview').addEventListener('click', async ()=>{
    const text = document.getElementById('reviewText').value.trim();
    const name = document.getElementById('reviewerName').value.trim();
    if(!pickedScore){ toast('Pick a score from 1–10 first.'); return; }
    if(!text){ toast('Add a few words for your review.'); return; }

    const btn = document.getElementById('submitReview');
    btn.disabled = true; btn.textContent = 'Submitting…';

    try{
      await apiPost(`/teachers/${activeTeacherId}/reviews`, {
        rating: pickedScore,
        text,
        reviewer_name: name || null
      });
      toast('Review added to the ledger.');
      await loadReviews(activeTeacherId);   // refresh this teacher's review list
      await loadTeachers();                 // refresh averages/counts on the grid
      document.getElementById('reviewText').value = '';
      document.getElementById('reviewerName').value = '';
      pickedScore = null;
      scoreGrid.querySelectorAll('.scorebtn').forEach(el=>el.classList.remove('picked'));
      scoreReadout.textContent = 'Tap a number to set your score.';
    } catch(e){
      console.error(e);
      toast('Could not submit review — please try again.');
    } finally {
      btn.disabled = false; btn.textContent = 'Submit review';
    }
  });

  /* ---------- Add Teacher Modal ---------- */
  const addOverlay = document.getElementById('addOverlay');
  document.getElementById('openAddBtn').addEventListener('click', ()=>{
    document.getElementById('newName').value = '';
    document.getElementById('newDept').value = '';
    document.getElementById('newRole').value = 'Teacher';
    document.getElementById('newPhoto').value = '';
    addOverlay.classList.add('open');
  });

  document.getElementById('submitNewTeacher').addEventListener('click', async ()=>{
    const name = document.getElementById('newName').value.trim();
    const role = document.getElementById('newRole').value;
    const dept = document.getElementById('newDept').value.trim() || 'General';
    const photoFile = document.getElementById('newPhoto').files[0];
    if(!name){ toast('Enter a name first.'); return; }
    const btn = document.getElementById('submitNewTeacher');
    btn.disabled = true; btn.textContent = 'Adding…';
    try{
      const created = await apiPost('/teachers/', { name, role, dept });
      if(photoFile){
        try{
          await uploadPhoto(created.id, photoFile);
        } catch(photoErr){
          console.error(photoErr);
          toast('Teacher added, but the photo failed to upload.');
        }
      }
      toast(`${name} added to the ledger.`);
      addOverlay.classList.remove('open');
      await loadTeachers();
    } catch(e){
      console.error(e);
      toast('Could not add teacher — please try again.');
    } finally {
      btn.disabled = false; btn.textContent = 'Add entry';
    }
  });

  /* ---------- Close handlers ---------- */
  document.querySelectorAll('[data-close]').forEach(el=>{
    el.addEventListener('click', ()=>{
      rateOverlay.classList.remove('open');
      addOverlay.classList.remove('open');
    });
  });
  [rateOverlay, addOverlay].forEach(ov=>{
    ov.addEventListener('click', (e)=>{ if(e.target===ov) ov.classList.remove('open'); });
  });

  /* ---------- Filters ---------- */
  document.getElementById('searchInput').addEventListener('input', render);
  document.getElementById('roleFilter').addEventListener('change', render);
  document.getElementById('sortFilter').addEventListener('change', render);

  loadTeachers();
})();