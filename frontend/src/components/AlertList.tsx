import type { Alert } from "../types";

type Props = {
  alerts: Alert[];
};

export function AlertList({ alerts }: Props) {
  if (!alerts.length) {
    return <div className="empty">暂无异动告警</div>;
  }
  return (
    <div className="alert-list">
      {alerts.map((alert) => (
        <article className="alert-card" key={alert.id}>
          <div className="alert-head">
            <strong>{alert.item_name}</strong>
            <span className={`severity ${alert.severity.toLowerCase()}`}>{alert.severity}</span>
          </div>
          <div className="alert-meta">
            <span>{new Date(alert.created_at).toLocaleString()}</span>
            <span>{alert.alert_type}</span>
            <span>{alert.direction}</span>
          </div>
          <p>{alert.detail}</p>
        </article>
      ))}
    </div>
  );
}
