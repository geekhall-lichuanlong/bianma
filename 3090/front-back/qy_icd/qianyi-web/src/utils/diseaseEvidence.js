// Keep model text as text. Vue interpolation escapes it before rendering.
export const splitDiseaseEvidence = (value = '', fallbackNote = '') => {
  const text = String(value || '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/\\r\\n|\\n/g, '\n')
    .replace(/\r\n/g, '\n')
    .trim()
  const marker = /使用本编码时应注意[：:]/.exec(text)
  const evidence = (marker ? text.slice(0, marker.index) : text)
    .replace(/^病历原文依据[：:]\s*/, '')
    .trim()
  const note = (marker ? text.slice(marker.index + marker[0].length) : String(fallbackNote || ''))
    .replace(/^使用本编码时应注意[：:]\s*/, '')
    .trim()
  const noteParagraphs = note
    .split(/\n+|[；;]\s*(?=[（(]\d+[）)])/)
    .map((part) => part.replace(/^\s*[（(]\d+[）)]\s*/, '').trim())
    .filter(Boolean)
  return { evidence, noteParagraphs }
}
