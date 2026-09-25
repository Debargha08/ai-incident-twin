from app.simulation.models import Anomaly, TelemetrySnapshot


LATENCY_THRESHOLD_MS = 100.0
ERROR_RATE_THRESHOLD = 0.10
CPU_THRESHOLD = 80.0
MEMORY_THRESHOLD = 80.0


def detect_anomalies(snapshot: TelemetrySnapshot) -> list[Anomaly]:
    anomalies: list[Anomaly] = []

    if snapshot.latency_ms > LATENCY_THRESHOLD_MS:
        anomalies.append(
            Anomaly(
                service=snapshot.service,
                timestamp=snapshot.timestamp,
                signal="latency",
                value=snapshot.latency_ms,
                threshold=LATENCY_THRESHOLD_MS,
                message=(
                    f"Latency is {snapshot.latency_ms:.1f}ms "
                    f"(threshold: {LATENCY_THRESHOLD_MS:.1f}ms)"
                ),
            )
        )

    if snapshot.error_rate > ERROR_RATE_THRESHOLD:
        anomalies.append(
            Anomaly(
                service=snapshot.service,
                timestamp=snapshot.timestamp,
                signal="error_rate",
                value=snapshot.error_rate,
                threshold=ERROR_RATE_THRESHOLD,
                message=(
                    f"Error rate is {snapshot.error_rate:.2%} "
                    f"(threshold: {ERROR_RATE_THRESHOLD:.2%})"
                ),
            )
        )

    if snapshot.cpu_usage > CPU_THRESHOLD:
        anomalies.append(
            Anomaly(
                service=snapshot.service,
                timestamp=snapshot.timestamp,
                signal="cpu",
                value=snapshot.cpu_usage,
                threshold=CPU_THRESHOLD,
                message=(
                    f"CPU usage is {snapshot.cpu_usage:.1f}% "
                    f"(threshold: {CPU_THRESHOLD:.1f}%)"
                ),
            )
        )

    if snapshot.memory_usage > MEMORY_THRESHOLD:
        anomalies.append(
            Anomaly(
                service=snapshot.service,
                timestamp=snapshot.timestamp,
                signal="memory",
                value=snapshot.memory_usage,
                threshold=MEMORY_THRESHOLD,
                message=(
                    f"Memory usage is {snapshot.memory_usage:.1f}% "
                    f"(threshold: {MEMORY_THRESHOLD:.1f}%)"
                ),
            )
        )

    return anomalies
