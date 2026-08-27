import os

from kubernetes import client, config


REQUEST_TIMEOUT_SECONDS = 10


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
            'environment': environment,
            'namespace': namespace,
            'state': 'healthy',
            'deployments': [],
            'statefulsets': [],
            'pods': [],
            'jobs': [],
            'pvcs': [],
            'hpas': [],
            'pdbs': [],
            'warnings': [],
            'summary': {},
        }

        def degrade():
            out['state'] = 'degraded'

        for d in deps:
            desired = d.spec.replicas or 0
            ready = d.status.ready_replicas or 0
            state = 'healthy' if desired == ready else 'degraded'
            if state != 'healthy': degrade()
            out['deployments'].append({'name': d.metadata.name, 'ready': ready, 'desired': desired, 'state': state})

        for s in sts:
            desired = s.spec.replicas or 0
            ready = s.status.ready_replicas or 0
            state = 'healthy' if desired == ready else 'degraded'
            if state != 'healthy': degrade()
            out['statefulsets'].append({'name': s.metadata.name, 'ready': ready, 'desired': desired, 'state': state})

        for p in pods:
            restarts = sum((c.restart_count or 0) for c in (p.status.container_statuses or []))
            waiting = [c.state.waiting.reason for c in (p.status.container_statuses or []) if c.state and c.state.waiting and c.state.waiting.reason]
            state = 'healthy' if p.status.phase in ('Running', 'Succeeded') and not waiting else 'degraded'
            if state != 'healthy': degrade()
            elif restarts >= 5:
                state = 'warning'
            out['pods'].append({'name': p.metadata.name, 'phase': p.status.phase, 'restarts': restarts, 'waiting': waiting, 'state': state})

        for j in jobs:
            failed = j.status.failed or 0
            active = j.status.active or 0
            succeeded = j.status.succeeded or 0
            state = 'degraded' if failed else 'healthy'
            if failed: degrade()
            out['jobs'].append({'name': j.metadata.name, 'failed': failed, 'active': active, 'succeeded': succeeded, 'state': state})

        for pvc in pvcs:
            phase = pvc.status.phase or 'Unknown'
            state = 'healthy' if phase == 'Bound' else 'degraded'
            if state != 'healthy': degrade()
            out['pvcs'].append({'name': pvc.metadata.name, 'phase': phase, 'state': state})

        for hpa in hpas:
            out['hpas'].append({'name': hpa.metadata.name, 'current_replicas': hpa.status.current_replicas, 'desired_replicas': hpa.status.desired_replicas})

        for pdb in pdbs:
            disruptions = pdb.status.disruptions_allowed if pdb.status else None
            state = 'warning' if disruptions == 0 else 'healthy'
            out['pdbs'].append({'name': pdb.metadata.name, 'disruptions_allowed': disruptions, 'state': state})

        warning_events = [e for e in events if getattr(e, 'type', None) == 'Warning']
        warning_events.sort(key=lambda e: getattr(e, 'last_timestamp', None) or getattr(e.metadata, 'creation_timestamp', None), reverse=True)
        out['warnings'] = [
            {'reason': e.reason, 'message': e.message, 'object': f"{e.involved_object.kind}/{e.involved_object.name}"}
            for e in warning_events[:20]
        ]
        out['summary'] = {
            'deployments': len(out['deployments']),
            'statefulsets': len(out['statefulsets']),
            'pods': len(out['pods']),
            'jobs': len(out['jobs']),
            'pvcs': len(out['pvcs']),
            'warning_events': len(out['warnings']),
        }
        return out
    except Exception as exc:
        return {'environment': environment, 'namespace': namespace, 'state': 'unknown', 'error': str(exc)}
