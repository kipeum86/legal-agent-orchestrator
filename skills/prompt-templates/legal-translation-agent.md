# legal-translation-agent

## Preflight

`legal-translation-agent`는 `config.json` 부재 시 interactive onboarding을 시작할 수 있습니다. Agent tool 호출 전 반드시 아래 preflight를 실행합니다.

```bash
TRANSLATION_CONFIG="$PROJECT_ROOT/agents/legal-translation-agent/config.json"
if [ ! -f "$TRANSLATION_CONFIG" ]; then
  cat > "$TRANSLATION_CONFIG" <<'EOF'
{
  "version": 1,
  "created": "orchestrator-auto",
  "user": {
    "name": "Orchestrator",
    "affiliation": "Legal Agent Orchestrator",
    "role": "automated dispatch"
  },
  "preferences": {
    "primary_language_pairs": [
      {"source": "ko", "target": "en"},
      {"source": "en", "target": "ko"}
    ],
    "common_document_types": ["legal-opinion", "contract", "terms-of-service", "privacy-policy"],
    "default_output_format": "markdown",
    "default_mode": "normal",
    "default_english_variant": "international"
  },
  "library_profiles": [],
  "onboarding_skip": true
}
EOF
  python3 "$PROJECT_ROOT/scripts/log-event.py" "$OUTPUT_DIR/events.jsonl" \
    --agent orchestrator \
    --type agent_preflight \
    --data-json "$(python3 -c 'import json, sys; print(json.dumps({"agent_id":"legal-translation-agent","action":"created_default_config","path":sys.argv[1]}, ensure_ascii=False))' "$TRANSLATION_CONFIG")"
fi
```

## Prompt

```text
[전제 조건] 오케스트레이터가 preflight로 config.json을 이미 보장합니다.
당신은 config.json의 기본 설정을 사용하여 onboarding 없이 바로 번역을 시작하세요.

다음 법률문서 번역을 처리하세요:
[원문] {SOURCE_TEXT_OR_PATH}
[source] {SOURCE_LANG} → [target] {TARGET_LANG}

[중요]
- Interactive onboarding 생략. config.json 확인 후 바로 진행.
- 법률 분석/검토 요청이 섞여 있으면 번역만 수행하고, 분석 요청은 "별도 에이전트에 요청해주세요"로 거부.

{{ERROR_CONTRACT_BLOCK}}
{{OUTPUT_CONTRACT_BLOCK}}
# AGENT_ID = "legal-translation-agent"
# meta.json에 추가 필드: source_lang, target_lang, glossary_terms_added
```
