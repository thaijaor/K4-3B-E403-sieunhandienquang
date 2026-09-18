// UI/contract verification with explicit test doubles, never an AI quality score.
async page => {
  const checks = [];
  const check = (ok, label) => {if (!ok) throw Error(label); checks.push(label);};
  await page.setViewportSize({width:1440,height:800});
  await page.context().clearCookies();
  await page.goto('http://127.0.0.1:8765');
  await page.evaluate(() => localStorage.removeItem('tutor.chat'));
  await page.reload();
  await page.waitForFunction(() => !document.getElementById('new-chat').disabled);
  const lessons = await (await page.request.get('http://127.0.0.1:8765/api/lessons')).json();
  for (const lesson of lessons) {
    const item = page.locator(`[data-lesson="${lesson.id}"]`);
    await item.locator('..').evaluate(el => el.open = true);
    await item.click();
    await page.waitForFunction(title => document.getElementById('lesson-title').textContent === title && !document.getElementById('new-chat').disabled, lesson.title);
    const full = await (await page.request.get('http://127.0.0.1:8765/api/lessons/' + lesson.id)).json();
    check(await page.locator('.source-card').count() === full.sources.length, `all sections: ${lesson.id}`);
    check((await page.locator('#lesson-subtitle').innerText()).includes('Không phải học liệu chính thức'), `attribution: ${lesson.id}`);
    const last = full.sources.at(-1);
    const card = page.locator(`[data-source="${last.id}"]`);
    await card.getByRole('button', {name:'Hỏi về đoạn này'}).click();
    check((await page.locator('#selection-label').innerText()).includes(last.title), `last section selected: ${lesson.id}`);
    await page.locator('#question').fill('Tóm tắt phần đã chọn');
    const sent = page.waitForRequest(r => r.method() === 'POST' && /\/messages$/.test(r.url()));
    await page.locator('#send').click();
    const request = await sent;
    check(JSON.stringify(request.postDataJSON().selected_source_ids) === JSON.stringify([last.id]), `selected source sent: ${lesson.id}`);
    await page.locator('.citations button').last().click();
    await page.waitForFunction(text => document.getElementById('source-text').textContent.includes(text), last.text.split(/\n\s*\n/)[0].slice(0, 80));
    check(await page.locator('.citation-target').getAttribute('id') === last.anchor, `last section citation: ${lesson.id}`);
    await page.locator('#source-close').click();
    await page.locator('#tutor-close').click();
  }
  for (const [width,height] of [[1440,800],[1024,600],[375,667],[320,568]]) {
    await page.setViewportSize({width,height});
    const card = page.locator('.source-card').last();
    await card.scrollIntoViewIfNeeded();
    check(await card.getByRole('button',{name:'Hỏi về đoạn này'}).isVisible(), `end of long lesson reachable: ${width}`);
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `no horizontal overflow: ${width}`);
    await page.screenshot({path:`output/playwright/lesson-end-${width}.png`});
  }
  console.log(JSON.stringify({kind:'UI-double',checks},null,2));
}
