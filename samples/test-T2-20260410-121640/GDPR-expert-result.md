# GDPR 국외이전(Third Country Transfer) 규제 — EU 관점 리서치

**작성자:** EU Data Protection Specialist 김덕배 (GDPR-expert, Jinju Legal Orchestrator)
**작성일:** 2026-04-10
**케이스:** test-T2-20260410-121640 (Pattern 1 parallel dispatch — GDPR branch)
**범위:** EU GDPR 측면만 (한국 PIPA 측면은 병렬 PIPA-expert 분기가 담당)

---

## 1. GDPR Chapter V 개요 (Articles 44–50)

GDPR 제5장(Chapter V, Articles 44–50)은 개인정보의 제3국(third country) 또는 국제기구(international organisation)로의 이전을 규율합니다. 본 장의 핵심 구조는 **"계층적 이전 근거 체계(hierarchical transfer mechanism)"**로서, 다음 순서로 적용됩니다.

| 조문 | 제목 | 기능 |
|------|------|------|
| Art. 44 | General principle for transfers | 모든 이전의 기본 원칙 — "보호 수준 유지(non-undermining)" 의무 |
| Art. 45 | Transfers on the basis of an adequacy decision | 1순위 근거: EU 집행위원회 적정성 결정 |
| Art. 46 | Transfers subject to appropriate safeguards | 2순위 근거: SCCs, BCRs, 행정적 arrangements 등 |
| Art. 47 | Binding corporate rules | Art. 46(2)(b)에 따른 BCRs 상세 요건 |
| Art. 48 | Transfers or disclosures not authorised by Union law | 제3국 법원/행정기관의 이전·공개 명령은 MLAT 등 국제협정 기반일 때만 승인 |
| Art. 49 | Derogations for specific situations | 예외 사유 (계약 필요성, 명시적 동의, 공익 등) |
| Art. 50 | International cooperation | 집행위·감독기관의 국제협력 |

**핵심 원칙:** Chapter V는 **"EU 역내 보호 수준이 이전에 의해 undermined 되어서는 안 된다(shall not be undermined)"**는 원칙을 선언합니다(Art. 44 후단). Onward transfer(2차 이전)까지 포함하여 보호 의무가 데이터와 "함께 이동(travel with the data)"합니다(EDPB Rec. 01/2020, §1).

---

## 2. Article 44 — General Principle (축자 인용)

> "Any transfer of personal data which are undergoing processing or are intended for processing after transfer to a third country or to an international organisation shall take place only if, subject to the other provisions of this Regulation, the conditions laid down in this Chapter are complied with by the controller and processor, **including for onward transfers** of personal data from the third country or an international organisation to another third country or to another international organisation. **All provisions in this Chapter shall be applied in order to ensure that the level of protection of natural persons guaranteed by this Regulation is not undermined.**"
> — GDPR Art. 44 (emphasis added)

**해설:**
- **인적 적용 범위:** controller 및 processor 모두에게 직접 의무 부과
- **물적 적용 범위:** 현재 처리 중인 데이터뿐 아니라 "이전 후 처리 목적"의 데이터도 포함
- **Onward transfer 포함:** 1차 수입국에서 제3국으로의 재이전까지 Chapter V 적용
- **보호 수준 유지 의무(non-undermining clause):** Chapter V 전체를 해석하는 목적론적 기준 — Schrems II(§93) 는 이 조항을 근거로 "essentially equivalent protection" 기준을 도출함

---

## 3. Article 45 — Adequacy Decision (적정성 결정)

**제도 구조 (Art. 45(1)–(3)):**

1. 집행위원회가 특정 제3국, 영토, 특정 섹터, 또는 국제기구가 "**adequate level of protection**"을 보장한다고 결정하면, 해당 국가·섹터로의 이전은 **별도 허가 없이** 가능합니다(Art. 45(1)).
2. 적정성 평가 시 고려 요소 (Art. 45(2)):
   - **(a)** 법치주의, 기본권 존중, 관련 법령(공공보안·국가안보·형사법 포함), 공권력의 개인정보 접근, 효과적·집행 가능한 정보주체 권리, 행정적·사법적 구제
   - **(b)** 독립적 감독기관(supervisory authority)의 존재 및 실효성
   - **(c)** 국제적 약속·양자·다자 조약 참여
3. 결정은 **이행법령(implementing act)**의 형태를 취하며, **최소 4년마다 주기적 검토(periodic review)**가 의무화됩니다(Art. 45(3)).
4. 집행위는 지속적 모니터링 의무(Art. 45(4))를 지며, 보호 수준이 더 이상 유지되지 않으면 **철회·수정·정지(repeal, amend or suspend)** 가능합니다(Art. 45(5)). 단, 이는 Art. 46–49에 의한 이전에는 영향을 주지 않습니다(Art. 45(7)).

**실무적 의의:** 적정성 결정은 GDPR 국외이전 체계의 **"gold standard"** 로서, 수출자(exporter)에게 별도의 영향평가(TIA) 의무를 면제시킵니다. 현재 유효한 적정성 결정 대상국은 Andorra, Argentina, Canada(commercial), Faroe Islands, Guernsey, Isle of Man, Israel, Japan, Jersey, New Zealand, **Republic of Korea (2021.12.17. 채택)**, Switzerland, UK, Uruguay, US (EU-US Data Privacy Framework, 2023) 등입니다.

---

## 4. Article 46 — Appropriate Safeguards

적정성 결정이 없을 때(Art. 45(3) 부재), controller/processor는 **적절한 보호조치(appropriate safeguards)**를 제공하고, **정보주체의 집행 가능한 권리(enforceable rights)** 및 **효과적인 법적 구제(effective legal remedies)**가 존재할 조건 하에 이전할 수 있습니다(Art. 46(1)).

**감독기관 허가 불요(Art. 46(2)):**
- **(a)** 공공기관·기구 간 법적 구속력 있는 집행 가능 문서
- **(b)** **Binding Corporate Rules (BCRs)** — Art. 47에 따름
- **(c)** 집행위가 채택한 **Standard Contractual Clauses (SCCs)** — 가장 광범위하게 사용되는 Art. 46 수단 (현재 유효: Commission Implementing Decision (EU) 2021/914, "2021 SCCs")
- **(d)** 감독기관이 채택하고 집행위가 승인한 SCCs
- **(e)** 승인된 행동강령(Art. 40) + 제3국 당사자의 구속력 있는 commitment
- **(f)** 승인된 인증 메커니즘(Art. 42) + 구속력 있는 commitment

**감독기관 허가 필요(Art. 46(3)):**
- **(a)** 당사자 간 개별 계약 조항(ad hoc contractual clauses)
- **(b)** 공공기관 간 행정 arrangements (집행 가능한 정보주체 권리 포함)

**Art. 47 BCRs 핵심 요건:**
- 집단 내 모든 구성원에 법적 구속력, 집행 가능한 정보주체 권리 명시
- GDPR 원칙(purpose limitation, data minimisation, storage limitation 등) 적용
- EU 내 구성원이 역외 구성원 위반에 대한 책임 수락(Art. 47(2)(f))
- 감독기관이 Art. 63 일관성 메커니즘(consistency mechanism)을 통해 승인

---

## 5. Article 49 — Derogations (예외 사유)

**중요 원칙:** Art. 49는 Art. 45 및 Art. 46이 모두 사용 불가능한 경우의 **최후 수단(last resort)**이며, **제한적·예외적으로만** 활용되어야 합니다 (EDPB Guidelines 2/2018: "derogations must be interpreted restrictively"; "cannot become 'the rule' in practice").

**Art. 49(1) 예외 사유 7가지:**
- **(a)** 정보주체의 **명시적 동의(explicit consent)** — 사전에 "위험" 고지 필수
- **(b)** 정보주체와 controller 간 계약 이행에 필요
- **(c)** 정보주체 이익을 위한 controller–제3자 계약 체결·이행에 필요
- **(d)** 중요한 공익상 사유 (Art. 49(4): Union 또는 Member State 법에 인정된 것)
- **(e)** 법적 청구권의 성립·행사·방어에 필요
- **(f)** 정보주체·타인의 생명상 이익 보호 (동의 불가 상태)
- **(g)** 공공 등기부 기반 이전 (제한된 범위)

**"Compelling legitimate interests" 초예외 (Art. 49(1) 2단):**
- Art. 45/46/49(1)(a)–(g) 모두 불가
- **반복적이지 않고(not repetitive)**, **제한된 수의 정보주체**에게 관련
- Controller의 "compelling legitimate interest" (정보주체 권리에 의해 overridden 되지 않아야 함)
- 전 상황 평가 + 적절한 safeguards 제공 + **감독기관 통지 + 정보주체 통지**
- Art. 30에 따른 기록 의무

**공공기관 제외:** Art. 49(3) — (a), (b), (c) 및 2단 exception은 공공기관의 공권력 행사에는 적용되지 않습니다.

---

## 6. Schrems II (CJEU Case C-311/18) — 주요 판시

**판결 정보:**
- **사건명:** Data Protection Commissioner v. Facebook Ireland Ltd. and Maximillian Schrems
- **선고일:** 2020년 7월 16일
- **ECLI:** EU:C:2020:559
- **법정:** CJEU 대법정(Grand Chamber)

**배경:** 오스트리아 국적 Schrems가 Facebook Ireland가 SCCs에 기반해 자신의 데이터를 미국 Facebook Inc.로 이전하는 것이 FISA §702 및 EO 12.333에 따른 미국 대량감시(mass surveillance)에 노출된다는 이유로 아일랜드 DPC에 진정. 아일랜드 고등법원이 CJEU에 preliminary reference.

**핵심 판시 6가지:**

1. **GDPR 적용 범위:** 상업적 데이터 이전은 비록 수입국 국가기관이 후속적으로 안보 목적으로 처리하더라도 GDPR의 범위 내에 있습니다(§§80–89).

2. **"Essentially Equivalent" 기준:** 이전된 데이터에는 EU 기준과 "**본질적으로 동등한(essentially equivalent)**" 보호 수준이 부여되어야 하며, 이는 계약적 보호조치와 **수입국 공권력의 실제 접근 관행**을 모두 검토하여 평가됩니다(§§93–96).

3. **Privacy Shield 무효:** Commission Decision 2016/1250(Privacy Shield 적정성 결정)은 Charter Art. 7, 8, 47 위반으로 **무효**. 미국 감시 요건이 비례성(proportionality) 및 "strict necessity" 기준 미충족; 비미국인에게 집행 가능한 사법적 구제 없음(§§168–185).

4. **Ombudsperson Inadequate:** Privacy Shield의 Ombudsperson 메커니즘은 완전한 독립성이 결여되어 있고 정보기관을 구속할 수 없어 Charter Art. 47(효과적 구제권)을 충족하지 못함(§§195–197).

5. **SCCs 유효성 유지(조건부):** SCCs(Decision 2010/87/EU) 자체는 **유효**. 그러나 SCCs가 제3국 정부를 구속할 수 없으므로, 그 유효성은 "**효과적 준수 메커니즘이 실제로 존재하는지**"에 좌우됨(§§137–148).

6. **이전 정지 의무(Transfer Suspension Duty):** 수출자가 제3국의 법·관행상 SCCs 준수가 불가능함을 인식하면 **스스로 이전을 정지**하거나, 감독기관이 **이전을 정지·금지**해야 함(§§121, 135, 146).

**실무적 귀결:** Schrems II는 Art. 46 수단 사용 시 **Transfer Impact Assessment (TIA)** 수행을 사실상 의무화했고, "supplementary measures"(보충조치) 개념을 도입했습니다.

---

## 7. EDPB Recommendations 01/2020 (Post-Schrems II)

**공식 명칭:** Recommendations 01/2020 on measures that supplement transfer tools to ensure compliance with the EU level of protection of personal data
**Version 2.0 채택:** 2021년 6월 18일
**출처:** EDPB (유럽 데이터보호이사회)

**6단계 방법론 (Accountability-based approach):**

1. **Step 1 — Know your transfers:** 모든 이전 매핑(mapping), 데이터의 적정성·관련성·최소성 검증
2. **Step 2 — Verify transfer tool:** Chapter V 상 어떤 수단을 사용할지 확인 (적정성 결정 > Art. 46 > Art. 49 derogations)
3. **Step 3 — Assess third country law/practice:** 제3국 법령 및 공권력의 실제 관행이 Art. 46 수단의 실효성을 저해하는지 평가 (TIA 수행)
4. **Step 4 — Identify supplementary measures:** 기술적(암호화, 가명처리), 계약적(투명성 의무 확대), 조직적(거버넌스) 보충조치 식별
5. **Step 5 — Formal procedural steps:** 감독기관 승인이 필요한 조치 이행
6. **Step 6 — Re-evaluate:** 적절한 간격으로 재평가

**핵심 원칙:**
- EU 역내 보호 수준은 "**데이터가 이동하는 어디든 함께 이동(travel with the data)**"해야 함
- 수출자는 **Art. 5(2) accountability** 원칙 하에 입증 책임(burden of proof) 부담
- **Use case-by-case assessment** — 표준화된 면책은 불가
- 제3국 법이 형식적으로는 EU 기준을 충족하지만 실제 적용되지 않는 경우, 또는 수입자가 "problematic legislation" 대상인 경우 → **이전 정지 또는 supplementary measures 이행 의무**

---

## 8. 관련 EDPB Guideline

**Guidelines 05/2021 — Interplay between Article 3 and Chapter V**
- **채택일:** 2023년 2월 14일 (Version 2.0)
- **주제:** GDPR의 지역적 적용 범위(Art. 3)와 국외이전(Chapter V) 규정의 상호작용
- **핵심 내용:**
  1. "Transfer"의 3요소 정의: (i) 수출자가 GDPR 적용 대상, (ii) 수출자가 개인정보를 수입자에게 공개 또는 접근 가능하게 함, (iii) 수입자가 EEA 외부(또는 공권력 관점에서 제3국)
  2. Art. 3(2)에 따라 GDPR이 직접 역외 적용되는 수입자(non-EEA controller directly subject to GDPR)의 경우에도 별도의 Chapter V 이전 수단 필요
  3. "Transfer" 개념에 정보주체 본인의 직접 데이터 공개(예: 웹사이트 자진 입력)는 포함되지 않음

**Guidelines 2/2018 — Derogations under Article 49**
- **채택일:** 2018년 5월 25일
- **핵심 내용:**
  - Art. 49 예외는 **제한적 해석(restrictive interpretation)** 필수
  - "Necessary" 기준은 엄격하게 해석 (proportionality test)
  - 명시적 동의는 **구체적·정보에 기반한·명확한 위험 고지** 후에만 유효
  - Derogations 은 "the rule" 이 되어서는 안 됨
  - 반복적·대규모 이전에는 부적합

---

## 9. Recent Adequacy Decisions (Korea 2021 포함)

EU 집행위원회의 적정성 결정 채택 현황 (주요 최근 건):

| 대상국 | 결정일 | 비고 |
|--------|-------|------|
| **Japan** | 2019.01.23 | 상호 적정성 결정 (일본 APPI와 동시) |
| **UK** | 2021.06.28 | GDPR + LED 2건, sunset clause 포함 |
| **Republic of Korea** | **2021.12.17** | 본 리서치의 핵심 — 아래 상술 |
| **US (Data Privacy Framework)** | 2023.07.10 | Schrems II 및 Schrems III 제소 우려 존재 |

**EU–Korea Adequacy Decision (2021.12.17.) — EU 관점:**
- **공식 명칭:** Commission Implementing Decision (EU) 2022/254 of 17 December 2021 pursuant to Regulation (EU) 2016/679 on the adequate protection of personal data by the Republic of Korea under the Personal Information Protection Act
- **범위:** 한국의 **상업적(commercial) 영역** 개인정보 처리에 대한 적정성 인정. 종교단체, 정당, 교육기관(초·중등)은 제외.
- **근거 법령:** Korean PIPA(개인정보 보호법) + PIPC Notification 2021-5 (EU 정보주체 추가 보호 조치)
- **EDPB 사전 의견:** EDPB Opinion 32/2021 (2021.09.28) — 조건부 긍정 의견(대부분 요건 충족, 일부 우려 사항 지적)
- **EU 측 의의:**
  - 한국은 EU로부터 상업 영역 전반에 대한 적정성 인정을 받은 **최초의 아시아 국가** (일본은 특정 범주 제한 있었음)
  - 별도 이전 수단(SCCs, BCRs) 불요 — 기업 compliance 부담 대폭 경감
  - Art. 45(3) 이행법령으로서 4년마다 주기적 검토(2025년 1차 검토 예정)
  - **공권력의 개인정보 접근**(통신비밀보호법 등) 부분에서 PIPC Notification 2021-5가 EU 기준 충족에 핵심 역할

---

## 10. 핵심 요약 (Key Takeaways — EU 관점)

1. **계층 구조:** GDPR Chapter V는 적정성 결정 → 적절한 보호조치(Art. 46) → 예외(Art. 49)의 **엄격한 계층적 구조**
2. **비우회 원칙(Non-undermining):** EU 보호 수준은 "데이터와 함께 이동"해야 하며 국외이전으로 우회될 수 없음(Art. 44)
3. **Essentially Equivalent Standard:** Schrems II 이후 실질적 동등 보호가 핵심 기준이며, 계약적 보호 + 실제 공권력 관행 모두 평가
4. **수출자 책임(Accountability):** Art. 5(2) 원칙 하에 수출자가 TIA 수행 및 입증 책임 부담
5. **감독기관 집행 권한:** 감독기관은 이전 정지·금지 명령 권한을 보유하며, Schrems II는 이를 **의무**로 격상
6. **Art. 49 예외의 제한성:** 예외는 "the rule" 이 될 수 없으며, 제한적 해석 필수
7. **Korea 적정성 결정:** EU 관점에서 Korea는 2021.12.17. 적정성 인정을 받아 별도 이전 수단 없이 EU → KR 이전 가능 (상업 영역)

---

## Sources (전부 Grade A)

1. **GDPR Art. 44** — General principle for transfers (Regulation (EU) 2016/679)
2. **GDPR Art. 45** — Transfers on the basis of an adequacy decision
3. **GDPR Art. 46** — Transfers subject to appropriate safeguards
4. **GDPR Art. 47** — Binding corporate rules
5. **GDPR Art. 48** — Transfers or disclosures not authorised by Union law
6. **GDPR Art. 49** — Derogations for specific situations
7. **GDPR Art. 50** — International cooperation for the protection of personal data
8. **CJEU C-311/18** — Data Protection Commissioner v. Facebook Ireland and Schrems (Schrems II), ECLI:EU:C:2020:559, judgment 2020-07-16
9. **EDPB Recommendations 01/2020** v2.0 on supplementary measures, adopted 2021-06-18
10. **EDPB Guidelines 05/2021** on interplay between Art. 3 and Chapter V, v2.0 adopted 2023-02-14
11. **EDPB Guidelines 2/2018** on derogations of Article 49, adopted 2018-05-25
12. **EDPB Opinion 32/2021** regarding European Commission Draft Implementing Decision on adequate protection of personal data in Republic of Korea, 2021-09-28
13. **Commission Implementing Decision (EU) 2022/254** of 17 December 2021 (EU–Korea adequacy decision)

---

*End of GDPR branch result — Pattern 1 parallel dispatch test T2.*
