// Regression for clipped chat controls. Run through playwright-cli run-code.
async (page) => {
  const results = [];
  await page.goto('http://127.0.0.1:8765');
  await page.waitForFunction(() => document.querySelector('#new-chat:not(:disabled)'));
  await page.locator('#tutor-toggle').click();
  for (const [width, height] of [[1920, 922], [1536, 738], [1280, 615], [1440, 738], [1366, 650], [1024, 600], [800, 500], [720, 600], [375, 667], [320, 568]]) {
    await page.setViewportSize({width, height});
    await page.evaluate(() => {
      // Deliberately exercise the combined status states that add panel height.
      const error = document.querySelector('#chat-error');
      error.hidden = false;
      error.textContent = 'Mất kết nối với máy chủ. Vui lòng thử lại.';
      document.querySelector('#selection').hidden = false;
      document.querySelector('#selection-label').textContent = 'Bài đang đọc · Đoạn nội dung đã chọn';
      const messages = document.querySelector('#messages');
      messages.replaceChildren();
      for (let i = 0; i < 30; i++) {
        const row = document.createElement('p'); row.textContent = `Tin nhắn kiểm tra bố cục ${i + 1}: nội dung dài vẫn cuộn trong hội thoại.`; messages.append(row);
      }
      if (innerWidth <= 720) document.querySelector('#tutor-panel').scrollIntoView({block:'start'});
    });
    const measurement = await page.evaluate(() => {
      const visible = id => {
        const el = document.getElementById(id), r = el.getBoundingClientRect();
        const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
        return {top:r.top, bottom:r.bottom, visible:r.top >= 0 && r.bottom <= innerHeight + 1 && r.left >= 0 && r.right <= innerWidth + 1 && (hit === el || el.contains(hit))};
      };
      const list = document.querySelector('#messages'); list.scrollTop = list.scrollHeight;
      return {send:visible('send'), persona:visible('persona-open'), newChat:visible('new-chat'), history:visible('history-open'), close:visible('tutor-close'), collapse:visible('collapse'), question:visible('question'), messagesHeight:list.clientHeight, messagesScroll:list.scrollTop, overflow:document.documentElement.scrollWidth > innerWidth};
    });
    if (![measurement.send,measurement.persona,measurement.newChat,measurement.history,measurement.close,measurement.collapse,measurement.question].every(x=>x.visible) || measurement.overflow || measurement.messagesHeight < 40 || measurement.messagesScroll === 0) throw new Error(`${width}x${height}: ${JSON.stringify(measurement)}`);
    results.push({viewport:`${width}x${height}`, ...measurement});
    if (width === 1536 || width === 320) await page.screenshot({path:`output/playwright/layout-chat-${width}.png`});
    await page.getByRole('button',{name:'Persona',exact:true}).click();
    await page.getByRole('button',{name:'Sửa',exact:true}).click();
    await page.getByRole('textbox',{name:'Nội dung Persona'}).fill('Nội dung dài để thử scroll trong drawer.\n'.repeat(45));
    const drawer = await page.evaluate(() => {
      const content = document.querySelector('.drawer-content'); content.scrollTop = content.scrollHeight;
      const visible = id => {const e = document.getElementById(id), r = e.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight + 1 && document.elementFromPoint(r.x + r.width / 2,r.y + r.height / 2)?.closest('button') === e;};
      return ['persona-save','persona-cancel','persona-close'].every(visible);
    });
    if (!drawer) throw new Error(`Drawer controls clipped at ${width}x${height}`);
    if (width === 1536 || width === 320) await page.screenshot({path:`output/playwright/layout-drawer-${width}.png`});
    await page.getByRole('button',{name:'Huỷ',exact:true}).click();
    await page.getByRole('button',{name:'Đóng Persona',exact:true}).click();
  }
  await page.evaluate(value=>window.__layoutCheck=value, {passed:results.length, results});
  return {passed:results.length, results};
}
