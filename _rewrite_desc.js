// 검색 결과 설명문(meta description·og:description)을 페이지에 이미 있는 사실로 다시 쓴다.
// 사용: node desc.js [--write]   (cwd = 저장소 루트)
const fs = require('fs'), path = require('path');
const WRITE = process.argv.includes('--write');
const root = process.cwd();
const MAX = 80;

function walk(d, out) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    if (e.name.startsWith('.') || e.name === 'node_modules') continue;
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name === 'index.html') out.push(p);
  }
  return out;
}
const hash = s => { let h = 2166136261; for (const c of s) { h ^= c.codePointAt(0); h = Math.imul(h, 16777619); } return h >>> 0; };
const descOf = h => (h.match(/<meta name="description" content="([^"]*)"/) || [])[1];
const eul = w => ((w.charCodeAt(w.length - 1) - 0xac00) % 28 ? '을' : '를');
const hasFee = h => h.includes('수강료 안내');

// 학교 목록에서 초·중·고 하나씩 고른다(없으면 앞에서부터)
function pickSchools(list, n) {
  const out = [];
  for (const re of [/초$/, /중$/, /고$/]) { const s = list.find(x => re.test(x) && !out.includes(x)); if (s) out.push(s); }
  for (const s of list) if (out.length < n && !out.includes(s)) out.push(s);
  return out.slice(0, n).join('·');
}
// 길이 안에 들어오는 첫 후보를 고른다
function fit(cands, seed) {
  const start = hash(seed) % cands.length;
  for (let i = 0; i < cands.length; i++) { const c = cands[(start + i) % cands.length]; for (const v of c) if (v.length <= MAX) return v; }
  return null;
}

const RE_HUB = /^(\S+) ((?:[가-힣]+학원·?)+) 추천\. 와와학습코칭센터 (\S+)에서 초중고 자기주도학습 전문 코칭\.(?: 학년별 밀착 맞춤 코칭\.)?$/;
const RE_SUB = /^(\S+) ([가-힣]+)학원, 와와학습코칭센터 (\S+)에서 (\S+) 밀착 맞춤 [가-힣]+ 코칭\.(?: (.+) 학생 등록 가능\.)?$/;
const RE_SCH = /^(\S+) 학원, 와와학습코칭센터 (\S+) (\d+)개 지점에서 \S+ 학생 등록 가능\. (\S+) (내신 대비|교과 복습과 학습 습관 코칭)\.$/;
const RE_BR = /^(\S+) (\S+) (\S+) · (\S+ \S+) · 초중고 자기주도학습 전문 · (.+)$/;

function build(rel, h) {
  const d = descOf(h); if (!d) return null;
  const fee = hasFee(h);
  let m;
  if ((m = d.match(RE_HUB))) {
    const [, D, subjRaw, B] = m;
    const subs = subjRaw.split('·').map(s => s.replace(/학원$/, ''));
    const SJ = subs.length <= 2 ? subs.map(s => s + '학원').join('·') : subs.join('·') + ' 학원';
    // 학년 범위·학교는 같은 동의 과목 페이지 설명문에서 가져온다
    let G = '초중고', schools = [];
    for (const s of ['math', 'english', 'korean', 'science', 'social']) {
      const f = path.join(root, path.dirname(rel), s, 'index.html');
      if (!fs.existsSync(f)) continue;
      const sm = (descOf(fs.readFileSync(f, 'utf8')) || '').match(RE_SUB);
      if (sm) { G = sm[4]; schools = sm[5].split(', '); break; }
    }
    // 말투: 검색어를 앞에, 사실을 명사로 끊어 쉼표로, 끝은 무료 상담 ('~합니다' 설명문·'찾는다면'·'~부터 ~까지' 쓰지 않는다)
    const tail = fee ? '수강료 공개, 무료 상담.' : '무료 상담.';
    const mk = n => {
      const S = pickSchools(schools, n);
      if (!S) return [[`${D} ${SJ} 와와학습코칭센터 ${B}. ${G} 개별 진도 수업. ${tail}`, `${D} ${SJ} 와와학습코칭센터 ${B}. 개별 진도 수업, 무료 상담.`]];
      return [
        [`${D} ${SJ} 와와학습코칭센터 ${B}. ${S} 학생 등록 가능, ${G} 개별 진도 수업. ${tail}`],
        [`${D} ${SJ}, ${S} 가까운 와와학습코칭센터 ${B}. ${G} 개별 진도 수업. ${tail}`],
        [`${D} ${SJ} 와와학습코칭센터 ${B}. ${G} 개별 진도 수업, ${S} 진도 맞춤. ${tail}`],
      ];
    };
    return fit(mk(3), rel) || fit(mk(2), rel) || fit(mk(1), rel) || fit(mk(0), rel);
  }
  if ((m = d.match(RE_SUB))) {
    const [, D, X, B, G, sl] = m; const schools = sl ? sl.split(', ') : [];
    const tail = fee ? '수강료 공개, 무료 상담.' : '무료 상담.';
    if (!schools.length) return fit([[`${D} ${X}학원 와와학습코칭센터 ${B}. ${G} ${X} 개별 진도 수업. ${tail}`]], rel);
    const exam = /[중고]/.test(G) ? ', 학교 시험 대비' : '';
    const mk = n => {
      const S = pickSchools(schools, n);
      return [
        [`${D} ${X}학원 와와학습코칭센터 ${B}. ${G} ${X} 개별 진도 수업, ${S} 학생 등록 가능. ${tail}`],
        [`${D} ${X}학원, ${S} 가까운 와와학습코칭센터 ${B}. ${G} ${X} 개별 진도${exam}. ${tail}`,
         `${D} ${X}학원, ${S} 가까운 와와학습코칭센터 ${B}. ${G} ${X} 개별 진도. ${tail}`],
        [`${D} ${X}학원 와와학습코칭센터 ${B}. ${S} 학생 등록 가능, ${G} ${X} 수업. ${tail}`],
      ];
    };
    return fit(mk(3), rel) || fit(mk(2), rel) || fit(mk(1), rel);
  }
  if ((m = d.match(RE_SCH))) {
    const [, , SG, cnt, SJ, kind] = m; const N = m[1];
    const cands = kind === '내신 대비' ? [
      [`${N} 학원 ${SG} 와와학습코칭센터. ${SJ} 내신 대비, 개별 진도 수업. ${N} 학생 등록 가능, 무료 상담.`,
       `${N} 학원 ${SG} 와와학습코칭센터. ${SJ} 내신 대비, 개별 진도 수업. 무료 상담.`],
      [`${N} 학원, ${SG} 와와학습코칭센터 ${cnt}개 지점. ${SJ} 내신 대비, ${N} 학생 등록 가능. 무료 상담.`],
      [`${N} 내신 학원 ${SG} 와와학습코칭센터. ${SJ} 개별 진도 수업, 학교 시험 대비. 무료 상담.`],
    ] : [
      [`${N} 학원 ${SG} 와와학습코칭센터. ${SJ} 교과 복습, 공부 습관 코칭. ${N} 학생 등록 가능, 무료 상담.`,
       `${N} 학원 ${SG} 와와학습코칭센터. ${SJ} 교과 복습, 공부 습관 코칭. 무료 상담.`],
      [`${N} 학원, ${SG} 와와학습코칭센터 ${cnt}개 지점. ${SJ} 교과 복습, 개별 진도 수업. 무료 상담.`],
      [`${N} 근처 학원 ${SG} 와와학습코칭센터. ${SJ} 개별 진도 수업, 공부 습관 코칭. 무료 상담.`],
    ];
    return fit(cands, rel);
  }
  if ((m = d.match(RE_BR))) {
    const [, , SG, DG, B, sl] = m; const SJ = sl.split(', ').join('·');
    const cands = [
      [`${B}, ${SG} ${DG} 자기주도학습 학원. ${SJ} 개별 진도 수업. ${fee ? '수강료·수업 시간 공개, ' : ''}무료 상담.`,
       `${B}, ${SG} ${DG} 자기주도학습 학원. ${SJ} 수업, 무료 상담.`],
      [`${SG} ${DG} ${B}. 초중고 ${SJ} 개별 진도 수업${fee ? ', 수강료·수업 시간 공개' : ''}. 무료 상담.`,
       `${SG} ${DG} ${B}. ${SJ} 수업, 무료 상담.`],
    ];
    return fit(cands, rel);
  }
  return undefined; // 정해진 틀이 아님 → 손대지 않는다
}

const files = walk(root, []);
const stat = { changed: 0, skip: 0, nofit: [], kinds: {} }, samples = [], lens = [];
const seen = new Map();
for (const f of files) {
  const rel = path.relative(root, f).split(path.sep).join('/');
  const h = fs.readFileSync(f, 'utf8');
  const old = descOf(h);
  const nd = build(rel, h);
  if (nd === undefined || !old) { stat.skip++; continue; }
  if (nd === null) { stat.nofit.push(rel); continue; }
  if (/["<>&]/.test(nd)) throw new Error('escape ' + rel);
  const cnt = h.split(`content="${old}"`).length - 1;
  if (cnt !== 2) { stat.nofit.push(rel + ' (desc count ' + cnt + ')'); continue; }
  if (seen.has(nd)) console.log('DUP', rel, seen.get(nd)); seen.set(nd, rel);
  lens.push(nd.length); stat.changed++;
  samples.push(rel + '\n   - ' + old + '\n   + ' + nd);
  if (WRITE) fs.writeFileSync(f, h.split(`content="${old}"`).join(`content="${nd}"`));
}
const pick = process.argv.find(a => a.startsWith('--grep='));
const show = pick ? samples.filter(s => s.includes(pick.slice(7))) : samples.filter((_, i) => i % 23 === 0);
console.log(show.join('\n'));
console.log(JSON.stringify({ files: files.length, changed: stat.changed, skip: stat.skip, nofit: stat.nofit.length, maxLen: Math.max(...lens), minLen: Math.min(...lens) }));
console.log(stat.nofit.slice(0, 20).join('\n'));
