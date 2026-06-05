import type { Snapshot } from "../types";

type Props = {
  data: Snapshot[];
  field: "lowest_price" | "sell_count" | "buy_count" | "volume_24h";
  kind?: "line" | "bar";
};

export function MiniChart({ data, field, kind = "line" }: Props) {
  const values = data.map((row) => Number(row[field]));
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const width = 560;
  const height = 180;
  const points = values.map((value, index) => {
    const x = values.length <= 1 ? 0 : (index / (values.length - 1)) * width;
    const y = height - ((value - min) / Math.max(max - min, 1)) * (height - 18) - 9;
    return `${x},${y}`;
  });
  if (!values.length) {
    return <div className="empty-chart">暂无数据</div>;
  }
  return (
    <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img">
      {kind === "bar" ? (
        values.map((value, index) => {
          const barWidth = width / values.length - 3;
          const barHeight = ((value - min) / Math.max(max - min, 1)) * (height - 18) + 4;
          return (
            <rect
              key={`${value}-${index}`}
              x={(index / values.length) * width}
              y={height - barHeight}
              width={Math.max(3, barWidth)}
              height={barHeight}
              rx="2"
            />
          );
        })
      ) : (
        <polyline points={points.join(" ")} fill="none" strokeWidth="3" />
      )}
    </svg>
  );
}
