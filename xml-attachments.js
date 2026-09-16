/* Shared streaming XML preprocessing. Keep media in the original Blob, not RAM. */
window.BackupXml = {
  async *chunks(file, checkCancelled = () => {}) {
    const reader = file.stream().getReader();
    const decoder = new TextDecoder('utf-8', {ignoreBOM: true});
    const encoder = new TextEncoder();
    let offset = 0, inTag = false, tail = '', quote = '', media = false, start = 0;
    try {
      while (true) {
        checkCancelled();
        const {done, value} = await reader.read();
        const text = decoder.decode(value, {stream: !done});
        let out = '', i = 0;
        while (i < text.length) {
          if (quote) {
            const end = text.indexOf(quote, i);
            const stop = end < 0 ? text.length : end;
            const segment = text.slice(i, stop);
            if (!media) out += segment;
            offset += encoder.encode(segment).length;
            i = stop;
            if (end < 0) break;
            out += media ? `${quote} data-offset="${start}" data-slen="${offset - start}"` : quote;
            offset++; i++; quote = ''; media = false; tail = /^<part\s/.test(tail) ? '<part ' : ' ';
          } else {
            const c = String.fromCodePoint(text.codePointAt(i)); i += c.length;
            out += c;
            offset += c.charCodeAt(0) < 128 ? 1 : encoder.encode(c).length;
            if (c === '<') { inTag = true; tail = '<'; }
            else if (inTag && (c === '"' || c === "'")) {
              quote = c;
              media = /^<part\s/.test(tail) && /\sdata\s*=\s*$/.test(tail);
              // The tag name is retained separately in tail across attributes.
              if (media) start = offset;
            } else if (c === '>') { inTag = false; tail = ''; }
            else if (inTag) tail += c;
          }
        }
        yield {text: out, bytesRead: offset};
        if (done) break;
      }
      if (quote || inTag) throw new Error('Incomplete XML: the backup ends inside a tag or attachment.');
    } finally {
      await reader.cancel();
      reader.releaseLock();
    }
  }
};
