#!/usr/bin/env node
// 기준본(wstudycenter.com/data/branches.json) → center·와와 assets/branches.json 동기화 (2026-09-17 점검 후속, 퇴행 R4)
//
// 왜: center에서 고친 지점 데이터가 기준본에 없으면, 기준본을 그대로 복사하는 순간 고친 값이 되돌아간다.
//   - URL에 영향이 없는 수정(주말 안내·회비 종류 오타·수업 시간 표기·학교 목록 중복·키워드 동 이름 오타)은 기준본에 이미 반영했다.
//   - 아래 CENTER_OVERRIDES는 기준본에 넣으면 wstudycenter.com 주소(/school/증흥고/, /sejong/unknown/ 등)가 바뀌어
//     기준본에는 넣지 않은 center 전용 보정이다. center는 해당 옛 주소에 이동 안내 페이지를 두었다.
//     기준본의 학교명 오타를 wstudy 쪽에서 (옛 주소 이동 안내와 함께) 고치면 여기서 해당 항목을 지워도 된다.
//
// 사용:
//   node scripts/sync_branches_from_base.cjs          → 비교만(기본). 기준본+보정과 center/와와 파일이 다른 곳을 보여 준다
//   node scripts/sync_branches_from_base.cjs --write  → center(2칸 들여쓰기)·와와(1칸) assets/branches.json을 다시 쓴다
// 기준본 경로는 BRANCH_SRC 환경변수로 바꿀 수 있다. 루트 branches.js(홈 지도용, 필드 구성이 다름)는 이 스크립트가 다루지 않는다.
'use strict';
const fs = require('fs');
const path = require('path');

const WAWA = path.resolve(__dirname, '..');
const GROUP = path.resolve(WAWA, '..');
const BASE = process.env.BRANCH_SRC || path.join(GROUP, 'wstudycenter.com', 'data', 'branches.json');
const TARGETS = [
  { file: path.join(GROUP, 'center(wcoachingcenter.com)', 'assets', 'branches.json'), indent: 2 },
  { file: path.join(WAWA, 'assets', 'branches.json'), indent: 1 },
];

// center 전용 보정: [지점, 필드, 바꾸는 함수]
const renameSchool = (from, to) => (arr) => (arr || []).map((s) => (s === from ? to : s));
const renameKeyword = (from, to) => (arr) => (arr || []).map((s) => (s.startsWith(from) ? to + s.slice(from.length) : s));
const CENTER_OVERRIDES = [
  // 학교명 오타·약칭 (center 학교 페이지 주소도 바로잡고 옛 주소는 이동 안내)
  ['중동점', 'schools_high', renameSchool('증흥고', '중흥고')],
  ['중동점(W+)', 'schools_high', renameSchool('증흥고', '중흥고')],
  ['수성만촌점', 'schools_mid', renameSchool('동중', '대구동중')],
  ['수성만촌점', 'keywords', renameKeyword('동중', '대구동중')],
  ['석사점', 'schools_high', renameSchool('춘여고', '춘천여고')],
  // 세종은 시군구가 없어 center는 /sejong/sejong/ 주소를 쓴다(옛 /sejong/unknown/은 이동 안내). wstudy는 unknown 유지
  ['새롬점', 'district_slug', () => 'sejong'],
];

function load(p) { return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^﻿/, '')); }

const base = load(BASE);
const want = JSON.parse(JSON.stringify(base));
for (const [name, field, fn] of CENTER_OVERRIDES) {
  if (!want[name]) { console.warn(`[경고] 기준본에 ${name}이 없음`); continue; }
  want[name][field] = fn(want[name][field]);
}

const write = process.argv.includes('--write');
let diffs = 0;
for (const t of TARGETS) {
  const cur = fs.existsSync(t.file) ? load(t.file) : {};
  const names = new Set([...Object.keys(cur), ...Object.keys(want)]);
  const lines = [];
  for (const n of names) {
    if (!cur[n] || !want[n]) { lines.push(`  ${n}: ${cur[n] ? '기준본에 없음' : '대상에 없음'}`); continue; }
    for (const f of new Set([...Object.keys(cur[n]), ...Object.keys(want[n])])) {
      if (JSON.stringify(cur[n][f]) !== JSON.stringify(want[n][f])) {
        lines.push(`  ${n}.${f}: ${JSON.stringify(cur[n][f]).slice(0, 70)} → ${JSON.stringify(want[n][f]).slice(0, 70)}`);
      }
    }
  }
  diffs += lines.length;
  console.log(`${path.relative(GROUP, t.file)}: 차이 ${lines.length}건`);
  if (lines.length) console.log(lines.slice(0, 40).join('\n'));
  if (write && lines.length) {
    fs.writeFileSync(t.file, JSON.stringify(want, null, t.indent), 'utf8');
    console.log('  → 다시 씀');
  }
}
if (!write && diffs) console.log('\n--write 를 붙이면 위 차이대로 다시 씁니다. 먼저 차이가 의도한 것인지 볼 것.');
