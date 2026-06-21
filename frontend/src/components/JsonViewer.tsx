interface Props {
  value: unknown;
  depth?: number;
}

export default function JsonViewer({ value, depth = 0 }: Props) {
  if (Array.isArray(value)) {
    return (
      <details className="json-node" open={depth < 1}>
        <summary>Array [{value.length}]</summary>
        <div className="json-children">
          {value.map((item, index) => (
            <div className="json-row" key={index}>
              <span className="json-key">{index}</span>
              <JsonViewer value={item} depth={depth + 1} />
            </div>
          ))}
        </div>
      </details>
    );
  }

  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    return (
      <details className="json-node" open={depth < 2}>
        <summary>Object {"{"}{entries.length}{"}"}</summary>
        <div className="json-children">
          {entries.map(([key, item]) => (
            <div className="json-row" key={key}>
              <span className="json-key">{key}</span>
              <JsonViewer value={item} depth={depth + 1} />
            </div>
          ))}
        </div>
      </details>
    );
  }

  return <span className={`json-value ${typeof value}`}>{formatValue(value)}</span>;
}

function formatValue(value: unknown) {
  if (typeof value === "string") {
    if (value.length > 180) {
      return `"${value.slice(0, 96)}...${value.slice(-40)}" (${value.length} chars)`;
    }
    return `"${value}"`;
  }
  return String(value);
}

