function normalizeTrimmedString(value) {
  return typeof value === 'string' ? value.trim() : ''
}

function requireTrimmedString(value, errorMessage) {
  const normalized = normalizeTrimmedString(value)
  if (!normalized) {
    throw new Error(errorMessage)
  }

  return normalized
}

function normalizeStringArray(values) {
  if (!Array.isArray(values)) {
    return []
  }

  return values
    .map((item) => normalizeTrimmedString(item))
    .filter(Boolean)
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

export {
  isPlainObject,
  normalizeStringArray,
  normalizeTrimmedString,
  requireTrimmedString,
}
