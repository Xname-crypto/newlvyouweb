const UTF8_MOJIBAKE_PATTERN = /[ÃÂÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]/

const decodeLatin1AsUtf8 = (value: string) => {
  try {
    const bytes = Uint8Array.from(Array.from(value, (char) => char.charCodeAt(0) & 0xff))
    return new TextDecoder('utf-8', { fatal: true }).decode(bytes)
  } catch {
    return value
  }
}

const mojibakeScore = (value: string) => {
  const matches = value.match(/[ÃÂÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]/g)
  return matches?.length ?? 0
}

export const repairUtf8Mojibake = (value: string) => {
  if (!UTF8_MOJIBAKE_PATTERN.test(value)) {
    return value
  }

  const repaired = decodeLatin1AsUtf8(value)
  return mojibakeScore(repaired) < mojibakeScore(value) ? repaired : value
}

export const repairUtf8MojibakeList = (values: string[] = []) => values.map(repairUtf8Mojibake)
