type Props = {
  label: string;
  value: string;
  tone?: "neutral" | "up" | "down";
};

export function Metric({ label, value, tone = "neutral" }: Props) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong className={tone}>{value}</strong>
    </div>
  );
}
