from dataclasses import dataclass


@dataclass(frozen=True)
class DependencyEdge:
    service: str
    dependency: str


class DependencyGraph:
    def __init__(self, services) -> None:
        self.edges = [
            DependencyEdge(
                service=service.name,
                dependency=dependency,
            )
            for service in services.values()
            for dependency in service.dependencies
        ]

    def dependencies_of(self, service_name: str) -> list[str]:
        return [
            edge.dependency
            for edge in self.edges
            if edge.service == service_name
        ]

    def dependents_of(self, service_name: str) -> list[str]:
        return [
            edge.service
            for edge in self.edges
            if edge.dependency == service_name
        ]

    def all_edges(self) -> list[DependencyEdge]:
        return list(self.edges)
