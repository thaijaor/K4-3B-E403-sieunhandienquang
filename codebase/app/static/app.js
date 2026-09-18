const $ = (id) => document.getElementById(id);
const state = {chat: null, lesson: null, selected: [], busy: new Set(), creating: false, generation: 0, persona: null, editing: false, saving: false, capabilities: null, navigating: false};

function node(tag, text, className) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (className) el.className = className;
  return el;
}
function button(text, action, className = 'secondary') {
  const el = node('button', text, className);
  el.type = 'button'; el.addEventListener('click', action); return el;
}
function error(id, message = '') { $(id).textContent = message; $(id).hidden = !message; }
async function api(path, method = 'GET', body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 38000);
  try {
    const response = await fetch(`/api${path}`, {method, credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-Tutor-Request': '1'}, ...(body === undefined ? {} : {body: JSON.stringify(body)}), signal: controller.signal});
    const data = await response.json();
    if (!response.ok) {
      const e = new Error(typeof data.detail === 'string' ? data.detail : 'Dữ liệu chưa hợp lệ. Kiểm tra lại nội dung.');
      e.status = response.status; throw e;
    }
    return data;
  } catch (e) {
    if (e.name === 'AbortError') throw new Error('Chưa nhận được kết quả. Tải lại hội thoại trước khi thử lại.');
    if (e instanceof TypeError) throw new Error('Mất kết nối với máy chủ. Nội dung của bạn vẫn được giữ lại.');
    throw e;
  } finally { clearTimeout(timer); }
}
function controls() {
  const pending = state.chat?.messages.some(m => m.role === 'user' && m.status === 'pending');
  const busy = state.creating || state.navigating || state.busy.has(state.chat?.id) || pending;
  $('question').disabled = !state.chat || state.creating || state.navigating;
  $('send').disabled = !state.chat || busy || !$('question').value.trim();
  $('new-chat').disabled = state.creating || state.navigating || !state.lesson;
  document.querySelectorAll('[data-lesson]').forEach(el => el.disabled = state.creating || state.navigating);
  $('compose-hint').textContent = busy ? 'Đang xử lý câu hỏi…' : 'Enter để gửi · Shift + Enter xuống dòng';
}
async function loadLesson(id) {
  const lesson = await api(`/lessons/${encodeURIComponent(id)}`);
  state.lesson = lesson; state.selected = [];
  document.querySelectorAll('[data-lesson]').forEach(el => {
    const active = el.dataset.lesson === id;
    el.classList.toggle('active', active);
    if (active) {el.setAttribute('aria-current', 'page'); el.closest('details').open = true;}
    else el.removeAttribute('aria-current');
    el.querySelector('.learning-label').hidden = !active;
  });
  $('lesson-title').textContent = lesson.title;
  $('lesson-subtitle').textContent = lesson.subtitle;
  $('lesson-sources').replaceChildren();
  for (const source of lesson.sources) {
    const card = node('article', undefined, 'source-card'); card.dataset.source = source.id; card.id = source.anchor; card.tabIndex = -1;
    card.append(node('h2', source.title));
    for (const block of source.text.split(/\n\s*\n/)) {
      if (block.split('\n').every(line => line.startsWith('- '))) {
        const list = node('ul'); block.split('\n').forEach(line => list.append(node('li', line.slice(2)))); card.append(list);
      } else card.append(node('p', block));
    }
    const footer = node('div', undefined, 'card-footer');
    footer.append(node('span', 'Markdown · Bài mẫu', 'small muted'), button('Hỏi về đoạn này', () => {
      setTutor(true); state.selected = [source.id]; selection(); $('question').focus();
      if (!$('question').value.trim()) $('question').value = 'Giải thích đoạn này'; controls();

    })); card.append(footer); $('lesson-sources').append(card);
  }
  selection();
}
function selection() {
  $('selection').hidden = !state.selected.length;
  $('selection-label').textContent = state.lesson?.sources.filter(s => state.selected.includes(s.id)).map(s => s.label).join(', ') || '';
  document.querySelectorAll('.source-card').forEach(el => el.classList.toggle('selected', state.selected.includes(el.dataset.source)));
}
async function newChat() {
  if (state.creating || !state.lesson) return;
  state.creating = true; const generation = ++state.generation; controls(); error('chat-error');
  try {
    const chat = await api('/chats', 'POST', {lesson_id: state.lesson.id});
    if (generation !== state.generation) return;
    state.chat = chat; localStorage.setItem('tutor.chat', chat.id);
    $('question').value = ''; state.selected = []; selection();
    renderMessages();
  } catch (e) {
    error('chat-error', e.message);
  } finally { state.creating = false; controls(); }
}
async function reloadChat(chatId) {
  const chat = await api(`/chats/${encodeURIComponent(chatId)}`);
  if (state.chat?.id === chatId) {state.chat = chat; renderMessages(); controls();}
  return chat;
}
async function openSource(sourceId, chatId = state.chat?.id) {
  const dialog = $('source-dialog');
  $('source-label').textContent = ''; $('source-text').textContent = 'Đang tải nguồn…';
  if (!dialog.open) dialog.showModal();
  try {
    const source = await api(`/sources/${encodeURIComponent(sourceId)}?chat_id=${encodeURIComponent(chatId)}`);
    const section = document.getElementById(source.anchor);
    if (section) {
      document.querySelectorAll('.citation-target').forEach(el => el.classList.remove('citation-target'));
      section.classList.add('citation-target'); section.scrollIntoView({block: 'center'});
    }
    $('source-title').textContent = source.title; $('source-label').textContent = source.label; $('source-text').textContent = source.text;
  } catch (e) { $('source-title').textContent = 'Không mở được nguồn'; $('source-text').textContent = e.message; }
}
function renderMessages() {
  const root = $('messages'); root.replaceChildren();
  if (!state.chat?.messages.length) {
    const empty = node('div', undefined, 'empty'); empty.append(node('span', '✦', 'spark'), node('h3', 'Mình cùng hiểu bài nhé'), node('p', `Đang mở: ${state.lesson?.title || ''}`), node('p', 'Hỏi về nội dung đang đọc. Mở nguồn để kiểm chứng câu trả lời.'));
    const suggestions = node('div', undefined, 'suggestions');
    for (const text of ['Tóm tắt ý chính', 'Giải thích đoạn này']) suggestions.append(button(text, () => { $('question').value = text; controls(); $('question').focus(); }));
    empty.append(suggestions); root.append(empty); return;
  }
  for (const m of state.chat.messages) {
    const bubble = node('article', undefined, `message ${m.role === 'user' ? 'user' : 'assistant'}`);
    const badge = {answer: 'TRẢ LỜI CÓ NGUỒN', clarify: 'CẦN LÀM RÕ', abstain: 'CHƯA THỂ TRẢ LỜI'}[m.decision];
    if (m.role === 'assistant' && badge) bubble.append(node('span', badge, `badge ${m.decision}`));
    bubble.append(node('p', m.text));
    if (m.status === 'pending') bubble.append(node('span', 'Đang chờ Tutor…', 'small muted'));
    if (m.status === 'failed') {
      bubble.append(node('div', m.error || 'Lượt hỏi chưa hoàn thành.', 'small'));
      if (m.retryable !== false) bubble.append(button('Thử lại câu hỏi này', () => send(m.request)));
      else bubble.append(button('Gửi thành câu hỏi mới', () => sendText(m.text)));
    }
    if (m.citations?.length) {
      const citations = node('div', undefined, 'citations');
      const chatId = state.chat.id;
      for (const citation of m.citations) {
        const source = state.lesson.sources.find(s => s.id === citation.source_id);
        citations.append(button(`↗ ${source?.label || citation.source_id}`, () => openSource(citation.source_id, chatId)));
      }
      bubble.append(citations);
    }
    const actions = node('div', undefined, 'actions');
    for (const action of m.actions || []) actions.append(button(action.label, () => action.type === 'open_source' ? openSource(action.value) : sendText(action.value)));
    if (m.role === 'assistant') {
      for (const text of ['Ngắn hơn', 'Có ví dụ', 'Mình hỏi ý khác']) actions.append(button(text, () => sendText(text), 'text-button'));
    }
    bubble.append(actions);
    for (const proposal of m.persona_proposals || []) bubble.append(proposalCard(proposal));
    root.append(bubble);
  }
  root.scrollTop = root.scrollHeight;
}
async function sendText(text) { $('question').value = text; controls(); await send(); }
async function send(retry) {
  if (!state.chat || state.creating || state.navigating || state.busy.has(state.chat.id) || state.chat.messages.some(m => m.status === 'pending')) return;
  const chatId = state.chat.id;
  const question = retry || {text: $('question').value.trim(), client_request_id: crypto.randomUUID(), selected_source_ids: [...state.selected]};
  if (!question.text) return;
  state.busy.add(chatId); error('chat-error');
  const old = state.chat.messages.find(m => m.request?.client_request_id === question.client_request_id);
  if (old) old.status = 'pending';
  else state.chat.messages.push({role: 'user', text: question.text, status: 'pending', request: question});
  if (!retry) $('question').value = '';
  renderMessages(); controls();
  let failure = '';
  try {
    await api(`/chats/${chatId}/messages`, 'POST', question);
    if (retry && state.chat?.id === chatId && $('question').value === question.text) $('question').value = '';
  }
  catch (e) { failure = e.message; if (state.chat?.id === chatId) error('chat-error', e.message); }
  finally {
    state.busy.delete(chatId);
    if (state.chat?.id === chatId) {
      try {
        await reloadChat(chatId);
        if (failure && !state.chat.messages.some(m => m.request?.client_request_id === question.client_request_id)) {
          state.chat.messages.push({role: 'user', text: question.text, status: 'failed', request: question, error: failure});
          if (!$('question').value) $('question').value = question.text;
          renderMessages();
        }
      }
      catch (e) {
        const pending = state.chat.messages.find(m => m.request?.client_request_id === question.client_request_id);
        if (pending) {pending.status = 'failed'; pending.error = 'Chưa xác định kết quả. Thử lại sẽ dùng cùng mã request.';}
        renderMessages(); error('chat-error', e.message);
      }
    }
    controls();
  }
}
function personaMode(editing) {
  state.editing = editing;
  $('persona-read').hidden = editing; $('persona-edit-area').hidden = !editing;
  $('persona-edit').hidden = editing; $('persona-save').hidden = !editing; $('persona-cancel').hidden = !editing;
  $('persona-clear').disabled = editing || state.saving || !state.persona;
  if (editing) { $('persona-text').value = state.persona?.text || ''; countPersona(); $('persona-text').focus(); }
}
function countPersona() { $('persona-count').textContent = `${Array.from($('persona-text').value).length} / 2.000 ký tự`; }
async function loadPersona() {
  error('persona-error');
  try {
    state.persona = await api('/persona');
    $('persona-read').textContent = state.persona.text || 'Persona đang trống. Bạn có thể thêm cách xưng hô, độ dài và cách giải thích mong muốn.';
    $('persona-status').textContent = `Cập nhật lúc ${state.persona.updated_at}`;
    $('persona-edit').disabled = false; $('persona-clear').disabled = state.editing;
  } catch (e) { error('persona-error', e.message); $('persona-read').textContent = state.persona?.text || 'Chưa tải được Persona.'; }
}
function savedPersona(result) {
  state.persona = result;
  $('persona-read').textContent = result.text || 'Persona đang trống.';
  $('persona-status').textContent = 'Đã lưu Persona. Áp dụng từ câu hỏi tiếp theo.';
  personaMode(false);
}
async function mutatePersona(path, method, payload) {
  if (state.saving) return;
  state.saving = true; error('persona-error');
  for (const id of ['persona-save', 'persona-clear', 'persona-reload', 'persona-cancel']) $(id).disabled = true;
  try {
    const result = await api(path, method, payload);
    savedPersona(result); return result;
  } catch (e) { error('persona-error', e.message); throw e; }
  finally {
    state.saving = false;
    for (const id of ['persona-save', 'persona-reload', 'persona-cancel']) $(id).disabled = false;
    $('persona-clear').disabled = state.editing || !state.persona;
  }
}
function proposalCard(proposal) {
  const card = node('section', undefined, 'proposal'); card.append(node('h3', 'Tutor đề xuất ghi nhớ'));
  card.append(node('span', 'Trước', 'diff-label'), node('pre', proposal.before || '(trống)', 'diff-before'), node('span', 'Sau', 'diff-label'), node('pre', proposal.after || '(trống)', 'diff-after'));
  if (proposal.status && proposal.status !== 'pending') {card.append(node('p', proposal.status === 'accepted' ? 'Đã lưu vào Persona' : 'Đã bỏ qua đề xuất', 'proposal-status')); return card;}
  const label = node('label', 'Sửa đề xuất trước khi lưu', 'small');
  const draft = node('textarea'); draft.value = proposal.after; draft.maxLength = 2000; draft.rows = 5;
  draft.id = `proposal-${proposal.id}`; label.htmlFor = draft.id; label.hidden = draft.hidden = true; card.append(label, draft);
  const status = node('p', '', 'proposal-status'); status.setAttribute('role', 'status');
  const actions = node('div', undefined, 'actions');
  const accept = button('Lưu', async () => {
    actions.querySelectorAll('button').forEach(b => b.disabled = true);
    try {
      const result = await api(`/persona/proposals/${proposal.id}/accept`, 'POST', {edited_text: draft.hidden ? null : draft.value});
      savedPersona(result); proposal.status = 'accepted'; actions.remove(); draft.hidden = label.hidden = true; status.textContent = 'Đã cập nhật Persona · Áp dụng từ câu hỏi tiếp theo';
    } catch (e) { status.textContent = e.message; actions.querySelectorAll('button').forEach(b => b.disabled = false); }
  }, 'primary');
  const edit = button('Sửa', () => {draft.hidden = label.hidden = false; draft.focus();});
  const reject = button('Không', async () => {
    actions.querySelectorAll('button').forEach(b => b.disabled = true);
    try {await api(`/persona/proposals/${proposal.id}/reject`, 'POST', {}); proposal.status = 'rejected'; actions.remove(); draft.hidden = label.hidden = true; status.textContent = 'Đã bỏ qua. Persona không đổi.';}
    catch (e) {status.textContent = e.message; actions.querySelectorAll('button').forEach(b => b.disabled = false);}
  }); actions.append(accept, edit, reject); card.append(actions, status); return card;
}
$('composer').addEventListener('submit', e => {e.preventDefault(); send();});
$('question').addEventListener('input', controls);
$('question').addEventListener('keydown', e => {if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {e.preventDefault(); send();}});
$('new-chat').addEventListener('click', () => newChat());
$('clear-selection').addEventListener('click', () => {state.selected = []; selection();});
function setTutor(open) {
  $('tutor-panel').hidden = !open;
  document.querySelector('.workspace').classList.toggle('chat-open', open);
  $('tutor-toggle').setAttribute('aria-expanded', String(open));
  if (open) {
    $('chat-body').hidden = false;
    $('collapse').textContent = '−';
    $('collapse').setAttribute('aria-expanded', 'true');
    $('collapse').setAttribute('aria-label', 'Thu gọn trợ giảng');
    if (matchMedia('(max-width:720px)').matches) setSidebar(false);
  }
}
function setSidebar(open) {
  $('lesson-sidebar').hidden = !open;
  document.querySelector('.workspace').classList.toggle('sidebar-hidden', !open);
  $('sidebar-open').setAttribute('aria-expanded', String(open));
}
async function switchLesson(id) {
  if (state.creating || state.navigating || id === state.lesson?.id) return;
  if ($('question').value.trim() && !confirm('Chuyển bài sẽ tạo chat mới và bỏ câu hỏi chưa gửi. Tiếp tục?')) return;
  state.navigating = true; state.chat = null; ++state.generation; controls();
  try {await loadLesson(id); await newChat();}
  catch (e) {error('chat-error', e.message); setTutor(true);}
  finally {state.navigating = false; controls();}
  if (matchMedia('(max-width:720px)').matches) setSidebar(false);
}
function lessonNavigation(lessons) {
  const days = new Map();
  for (const lesson of lessons) {
    if (!days.has(lesson.day)) {
      const group = node('details'); group.append(node('summary', lesson.day));
      days.set(lesson.day, group); $('lesson-nav').append(group);
    }
    const item = button('', () => switchLesson(lesson.id), 'lesson-link');
    item.dataset.lesson = lesson.id;
    item.append(node('span', lesson.title), node('span', 'Đang học', 'learning-label'));
    item.querySelector('.learning-label').hidden = true;
    days.get(lesson.day).append(item);
  }
}
$('tutor-toggle').addEventListener('click', () => setTutor($('tutor-panel').hidden));
$('tutor-close').addEventListener('click', () => {setTutor(false); $('tutor-toggle').focus();});
$('sidebar-close').addEventListener('click', () => {setSidebar(false); $('sidebar-open').focus();});
$('sidebar-open').addEventListener('click', () => {setSidebar($('lesson-sidebar').hidden); if (matchMedia('(max-width:720px)').matches) setTutor(false);});
$('history-close').addEventListener('click', () => $('history-dialog').close());
$('history-open').addEventListener('click', async () => {
  $('history-dialog').showModal(); $('history-list').replaceChildren(node('p', 'Đang tải…'));
  try {
    const chats = await api('/chats'); $('history-list').replaceChildren();
    if (!chats.length) $('history-list').append(node('p', 'Chưa có hội thoại.'));
    for (const chat of chats) {
      const item = button('', async () => {
        if (state.creating || state.navigating) return;
        if ($('question').value.trim() && !confirm('Bỏ câu hỏi chưa gửi để mở hội thoại này?')) return;
        state.navigating = true; controls();
        try {
          const restored = await api(`/chats/${encodeURIComponent(chat.id)}`);
          await loadLesson(restored.lesson_id); state.chat = restored; ++state.generation;
          localStorage.setItem('tutor.chat', restored.id); $('question').value = '';
          error('chat-error');
          renderMessages(); $('history-dialog').close(); setTutor(true);
        } catch (e) {item.append(node('p', e.message, 'error'));}
        finally {state.navigating = false; controls();}
      }, 'history-item');
      item.append(node('strong', chat.title), node('span', new Date(chat.created_at * 1000).toLocaleString('vi-VN'), 'small muted'));
      if (chat.id === state.chat?.id) item.append(node('span', 'Đang mở', 'learning-label'));
      $('history-list').append(item);
    }
  } catch (e) {$('history-list').replaceChildren(node('p', e.message, 'error'));}
});
$('collapse').addEventListener('click', () => {const hidden = !$('chat-body').hidden; $('chat-body').hidden = hidden; $('collapse').textContent = hidden ? '+' : '−'; $('collapse').setAttribute('aria-expanded', String(!hidden)); $('collapse').setAttribute('aria-label', hidden ? 'Mở trợ giảng' : 'Thu gọn trợ giảng');});
$('persona-open').addEventListener('click', async () => {$('persona-dialog').showModal(); await loadPersona();});
function closePersona() {
  if (state.saving) return;
  if (state.editing && $('persona-text').value !== state.persona?.text && !confirm('Bỏ thay đổi Persona chưa lưu?')) return;
  personaMode(false); $('persona-dialog').close();
}
$('persona-close').addEventListener('click', closePersona);
$('persona-dialog').addEventListener('cancel', e => {e.preventDefault(); closePersona();});
$('persona-edit').addEventListener('click', () => personaMode(true));
$('persona-cancel').addEventListener('click', () => {personaMode(false); error('persona-error');});
$('persona-text').addEventListener('input', countPersona);
$('persona-reload').addEventListener('click', loadPersona);
$('persona-save').addEventListener('click', () => mutatePersona('/persona', 'PUT', {text: $('persona-text').value}).catch(() => {}));
$('persona-clear').addEventListener('click', () => {if (confirm('Xoá phần “Tutor nhớ về bạn” khỏi Persona?')) mutatePersona('/persona/memory', 'DELETE').catch(() => {});});
$('source-close').addEventListener('click', () => $('source-dialog').close());

async function start() {
  try {
    state.capabilities = await api('/session', 'POST', {});
    const parts = [state.capabilities.ai_connected ? 'Đã cấu hình kết nối AI' : 'AI chưa kết nối', state.capabilities.persona_connected ? 'Đã cấu hình kết nối Persona' : 'Persona chưa kết nối'];
    if (state.capabilities.fixture_mode) parts.unshift('THỬ UI · AI/Persona mô phỏng, không phải kết quả AI thật');
    if (state.capabilities.sample_lessons) parts.push('Đang dùng bài mẫu tổng hợp');
    $('connection').textContent = parts.join(' · ');
    const lessons = await api('/lessons');
    if (!lessons.length) throw new Error('Chưa có bài học. Cần cấu hình danh mục nguồn.');
    lessonNavigation(lessons);
    if (matchMedia('(max-width:720px)').matches) setSidebar(false);
    const saved = localStorage.getItem('tutor.chat');
    if (saved) {
      try { state.chat = await api(`/chats/${encodeURIComponent(saved)}`); }
      catch (e) {if (e.status === 404) localStorage.removeItem('tutor.chat'); else throw e;}
    }
    await loadLesson(state.chat?.lesson_id || lessons[0].id);
    if (state.chat) {renderMessages(); controls();} else await newChat();
  } catch (e) {error('chat-error', e.message); $('connection').textContent = 'Không mở được phiên học. Tải lại trang để thử lại.';}
}
// Recover a pending turn after a reload without issuing a second AI request.
setInterval(async () => {
  if (!state.chat || state.busy.has(state.chat.id) || !state.chat.messages.some(m => m.status === 'pending')) return;
  try {await reloadChat(state.chat.id);} catch { /* Keep the visible pending state until connection returns. */ }
}, 3000);
start();
