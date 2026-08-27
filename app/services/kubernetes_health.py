import os

from kubernetes import client, config


REQUEST_TIMEOUT_SECONDS = 10
VERSION_LABELS = (
    "app.kubernetes.io/version",
    "version",
)
SERVICE_LABELS = (
    "app.kubernetes.io/name",
    "app",
    "k8s-app",
)


def _api_client(context: str, kubeconfig_path: str | None, mode: str):
    if mode == "incluster":
        config.load_incluster_config()
        return client.ApiClient()

    if not context:
        raise ValueError("Kubernetes context is not configured")

    config_file = kubeconfig_path or os.getenv("OPSDECK_KUBECONFIG")
    return config.new_client_from_config(
        config_file=config_file,
        context=context,
        persist_config=False,
    )


def _first_label(labels: dict | None, names: tuple[str, ...]):
    labels = labels or {}
    return next((labels[name] for name in names if labels.get(name)), None)


def _parse_image_reference(image: str | None):
    image = image or ""
    repository_and_tag, separator, digest = image.partition("@")
    digest = digest if separator else None

    last_slash = repository_and_tag.rfind("/")
    last_colon = repository_and_tag.rfind(":")
    if last_colon > last_slash:
        repository = repository_and_tag[:last_colon]
        tag = repository_and_tag[last_colon + 1:] or None
    else:
        repository = repository_and_tag
        tag = None

    return {
        "repository": repository,
        "tag": tag,
        "digest": digest,
        "version": tag or digest or "latest",
    }


def _container_details(containers, statuses=None, labels=None):
    status_by_name = {status.name: status for status in (statuses or [])}
    label_version = _first_label(labels, VERSION_LABELS)
    service = _first_label(labels, SERVICE_LABELS)
    details = []

    for container in containers or []:
        parsed = _parse_image_reference(container.image)
        status = status_by_name.get(container.name)
        image_id = getattr(status, "image_id", None) if status else None
        actual_digest = None
        if image_id and "@" in image_id:
            actual_digest = image_id.rsplit("@", 1)[1]

        details.append({
            "name": container.name,
            "service": service or container.name,
            "image": container.image,
            "repository": parsed["repository"],
            "version": label_version or parsed["version"],
            "tag": parsed["tag"],
            "digest": parsed["digest"],
            "image_id": image_id,
            "actual_digest": actual_digest,
            "ready": getattr(status, "ready", None) if status else None,
            "restarts": (getattr(status, "restart_count", None) or 0) if status else None,
        })
    return details


def namespace_health(
    environment: str,
    context: str,
    namespace: str,
    kubeconfig_path: str | None = None,
    mode: str = "kubeconfig",
):
    try:
        api_client = _api_client(context, kubeconfig_path, mode)
        core = client.CoreV1Api(api_client)
        apps = client.AppsV1Api(api_client)
        batch = client.BatchV1Api(api_client)
        autoscaling = client.AutoscalingV2Api(api_client)
        policy = client.PolicyV1Api(api_client)

        timeout = REQUEST_TIMEOUT_SECONDS
        pods = core.list_namespaced_pod(namespace, _request_timeout=timeout).items
        deps = apps.list_namespaced_deployment(namespace, _request_timeout=timeout).items
        sts = apps.list_namespaced_stateful_set(namespace, _request_timeout=timeout).items
        jobs = batch.list_namespaced_job(namespace, _request_timeout=timeout).items
        pvcs = core.list_namespaced_persistent_volume_claim(namespace, _request_timeout=timeout).items
        hpas = autoscaling.list_namespaced_horizontal_pod_autoscaler(namespace, _request_timeout=timeout).items
        pdbs = policy.list_namespaced_pod_disruption_budget(namespace, _request_timeout=timeout).items
        events = core.list_namespaced_event(namespace, _request_timeout=timeout).items

        out = {
            "environment": environment,
            "namespace": namespace,
            "state": "healthy",
            "deployments": [],
            "statefulsets": [],
            "pods": [],
            "images": [],
            "jobs": [],
            "pvcs": [],
            "hpas": [],
            "pdbs": [],
            "warnings": [],
            "summary": {},
        }
        image_catalog = {}

        def degrade():
            out["state"] = "degraded"

        def register_images(kind, name, containers):
            for container in containers:
                key = container["image"]
                entry = image_catalog.setdefault(key, {
                    "image": container["image"],
                    "repository": container["repository"],
                    "versions": set(),
                    "tags": set(),
                    "declared_digests": set(),
                    "actual_digests": set(),
                    "image_ids": set(),
                    "services": set(),
                    "containers": set(),
                    "workloads": set(),
                    "pods": set(),
                })
                entry["versions"].add(container["version"])
                if container["tag"]: entry["tags"].add(container["tag"])
                if container["digest"]: entry["declared_digests"].add(container["digest"])
                if container["actual_digest"]: entry["actual_digests"].add(container["actual_digest"])
                if container["image_id"]: entry["image_ids"].add(container["image_id"])
                entry["services"].add(container["service"])
                entry["containers"].add(container["name"])
                if kind == "Pod":
                    entry["pods"].add(name)
                else:
                    entry["workloads"].add(f"{kind}/{name}")

        for d in deps:
            desired = d.spec.replicas or 0
            ready = d.status.ready_replicas or 0
            state = "healthy" if desired == ready else "degraded"
            if state != "healthy": degrade()
            containers = _container_details(
                d.spec.template.spec.containers,
                labels=d.spec.template.metadata.labels or d.metadata.labels,
            )
            init_containers = _container_details(
                d.spec.template.spec.init_containers,
                labels=d.spec.template.metadata.labels or d.metadata.labels,
            )
            register_images("Deployment", d.metadata.name, containers + init_containers)
            out["deployments"].append({
                "name": d.metadata.name,
                "ready": ready,
                "desired": desired,
                "state": state,
                "containers": containers,
                "init_containers": init_containers,
            })

        for s in sts:
            desired = s.spec.replicas or 0
            ready = s.status.ready_replicas or 0
            state = "healthy" if desired == ready else "degraded"
            if state != "healthy": degrade()
            containers = _container_details(
                s.spec.template.spec.containers,
                labels=s.spec.template.metadata.labels or s.metadata.labels,
            )
            init_containers = _container_details(
                s.spec.template.spec.init_containers,
                labels=s.spec.template.metadata.labels or s.metadata.labels,
            )
            register_images("StatefulSet", s.metadata.name, containers + init_containers)
            out["statefulsets"].append({
                "name": s.metadata.name,
                "ready": ready,
                "desired": desired,
                "state": state,
                "containers": containers,
                "init_containers": init_containers,
            })

        for p in pods:
            container_statuses = p.status.container_statuses or []
            init_statuses = p.status.init_container_statuses or []
            restarts = sum((c.restart_count or 0) for c in container_statuses + init_statuses)
            waiting = [
                c.state.waiting.reason
                for c in container_statuses + init_statuses
                if c.state and c.state.waiting and c.state.waiting.reason
            ]
            state = "healthy" if p.status.phase in ("Running", "Succeeded") and not waiting else "degraded"
            if state != "healthy": degrade()
            elif restarts >= 5:
                state = "warning"

            containers = _container_details(
                p.spec.containers,
                statuses=container_statuses,
                labels=p.metadata.labels,
            )
            init_containers = _container_details(
                p.spec.init_containers,
                statuses=init_statuses,
                labels=p.metadata.labels,
            )
            register_images("Pod", p.metadata.name, containers + init_containers)
            owners = [
                {"kind": owner.kind, "name": owner.name}
                for owner in (p.metadata.owner_references or [])
            ]
            out["pods"].append({
                "name": p.metadata.name,
                "phase": p.status.phase,
                "restarts": restarts,
                "waiting": waiting,
                "state": state,
                "owners": owners,
                "containers": containers,
                "init_containers": init_containers,
            })

        for j in jobs:
            failed = j.status.failed or 0
            active = j.status.active or 0
            succeeded = j.status.succeeded or 0
            state = "degraded" if failed else "healthy"
            if failed: degrade()
            out["jobs"].append({"name": j.metadata.name, "failed": failed, "active": active, "succeeded": succeeded, "state": state})

        for pvc in pvcs:
            phase = pvc.status.phase or "Unknown"
            state = "healthy" if phase == "Bound" else "degraded"
            if state != "healthy": degrade()
            out["pvcs"].append({"name": pvc.metadata.name, "phase": phase, "state": state})

        for hpa in hpas:
            out["hpas"].append({"name": hpa.metadata.name, "current_replicas": hpa.status.current_replicas, "desired_replicas": hpa.status.desired_replicas})

        for pdb in pdbs:
            disruptions = pdb.status.disruptions_allowed if pdb.status else None
            state = "warning" if disruptions == 0 else "healthy"
            out["pdbs"].append({"name": pdb.metadata.name, "disruptions_allowed": disruptions, "state": state})

        warning_events = [e for e in events if getattr(e, "type", None) == "Warning"]
        warning_events.sort(key=lambda e: getattr(e, "last_timestamp", None) or getattr(e.metadata, "creation_timestamp", None), reverse=True)
        out["warnings"] = [
            {"reason": e.reason, "message": e.message, "object": f"{e.involved_object.kind}/{e.involved_object.name}"}
            for e in warning_events[:20]
        ]

        for entry in image_catalog.values():
            out["images"].append({
                key: sorted(value) if isinstance(value, set) else value
                for key, value in entry.items()
            })
        out["images"].sort(key=lambda item: item["image"])

        versions = sorted({version for image in out["images"] for version in image["versions"]})
        out["summary"] = {
            "deployments": len(out["deployments"]),
            "statefulsets": len(out["statefulsets"]),
            "pods": len(out["pods"]),
            "jobs": len(out["jobs"]),
            "pvcs": len(out["pvcs"]),
            "images": len(out["images"]),
            "versions": versions,
            "warning_events": len(out["warnings"]),
        }
        return out
    except Exception as exc:
        return {"environment": environment, "namespace": namespace, "state": "unknown", "error": str(exc)}
